import json
import re
import hashlib
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PII Scrubbing Patterns
PHONE_PATTERN = re.compile(r'(\+?\d{1,3}[- ]?)?\d{10}')
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

def hash_user(user_id: str) -> str:
    """Creates a non-reversible SHA-256 hash of the user ID for anonymization."""
    if not user_id:
        return "user_unknown"
    return f"user_{hashlib.sha256(user_id.encode()).hexdigest()[:12]}"

def scrub_text(text: str) -> str:
    """Removes phone numbers and emails from the text."""
    if not isinstance(text, str):
        return ""
    text = PHONE_PATTERN.sub("[PHONE REDACTED]", text)
    text = EMAIL_PATTERN.sub("[EMAIL REDACTED]", text)
    return text

def extract_text(message: Dict[str, Any]) -> str:
    """Extracts and cleans text from various Telegram message formats (plain, bold, link, etc.)."""
    text_parts = message.get("text", "")
    if isinstance(text_parts, list):
        # Telegram sometimes sends text as a list of objects (plain, bold, link, etc.)
        full_text = ""
        for part in text_parts:
            if isinstance(part, str):
                full_text += part
            elif isinstance(part, dict):
                full_text += part.get("text", "")
        text_parts = full_text
    
    return scrub_text(text_parts)

class DataProcessor:
    def __init__(self, raw_file_path: str, group_name: str):
        self.raw_file_path = raw_file_path
        self.group_name = group_name
        self.messages_map = {} # id -> message object
        self.processed_data = []

    def calculate_reaction_score(self, reactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarizes reactions into a simple score. 
        Positive: 👍, ❤️, 🔥, 🙏, 👌, 👏
        Negative: 👎, 🤡, 🤨
        """
        pos_emojis = {"👍", "❤️", "🔥", "🙏", "👌", "👏"}
        neg_emojis = {"👎", "🤡", "🤨"}
        
        pos_count = 0
        neg_count = 0
        
        for r in reactions:
            emoji = r.get("emoji", "")
            count = r.get("count", 0)
            if emoji in pos_emojis:
                pos_count += count
            elif emoji in neg_emojis:
                neg_count += count
        
        return {
            "score": pos_count - neg_count,
            "positive": pos_count,
            "negative": neg_count
        }

    def load_data(self) -> Dict[str, Any]:
        """Loads the raw JSON file."""
        if not os.path.exists(self.raw_file_path):
            raise FileNotFoundError(f"File not found: {self.raw_file_path}")
        
        with open(self.raw_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def process(self):
        """Main processing pipeline."""
        data = self.load_data()
        raw_messages = data.get("messages", [])
        
        logger.info(f"Processing {len(raw_messages)} messages from group: {self.group_name}")

        # First pass: Index all valid messages and scrub PII
        for msg in raw_messages:
            if msg.get("type") != "message":
                continue
            
            msg_id = msg.get("id")
            text = extract_text(msg)
            
            # Skip very short or empty messages (unless they are part of a reply chain)
            if not text or len(text.strip()) < 2:
                if not msg.get("reply_to_message_id"):
                    continue

            msg_obj = {
                "id": msg_id,
                "timestamp": msg.get("date"),
                "unix_time": int(msg.get("date_unixtime", 0)),
                "user_hash": hash_user(str(msg.get("from_id"))),
                "text": text,
                "reply_to": msg.get("reply_to_message_id"),
                "group": self.group_name,
                "reactions": self.calculate_reaction_score(msg.get("reactions", [])),
                "is_processed": False
            }
            self.messages_map[msg_id] = msg_obj

        # Second pass: Build Conversation Chains
        for msg_id, msg in self.messages_map.items():
            if msg["is_processed"]:
                continue
            
            # If it's a reply, we handle it starting from its root later
            if msg["reply_to"] and msg["reply_to"] in self.messages_map:
                continue
            
            # Start a new chain or standalone message
            chain = self.build_chain(msg_id)
            if chain:
                self.processed_data.append(chain)

        logger.info(f"Generated {len(self.processed_data)} structured knowledge objects.")

    def build_chain(self, root_id: int) -> Optional[Dict[str, Any]]:
        """Recursively builds a conversation tree starting from a root message."""
        root_msg = self.messages_map.get(root_id)
        if not root_msg:
            return None

        # Find all direct replies to this root
        replies = [m for m in self.messages_map.values() if m["reply_to"] == root_id]
        
        root_msg["is_processed"] = True
        
        # Determine if it's a chain or a standalone informational message
        if not replies:
            if len(root_msg["text"]) < 50:
                return None
            
            return {
                "id": f"info_{root_id}",
                "type": "individual_info",
                "timestamp": root_msg["timestamp"],
                "unix_time": root_msg["unix_time"],
                "group": self.group_name,
                "content": root_msg["text"],
                "user_hash": root_msg["user_hash"],
                "reactions": root_msg["reactions"]
            }

        # It's a chain
        chain_messages = [root_msg]
        for reply in replies:
            reply["is_processed"] = True
            chain_messages.append(reply)

        return {
            "id": f"chain_{root_id}",
            "type": "conversation_chain",
            "timestamp": root_msg["timestamp"],
            "unix_time": root_msg["unix_time"],
            "group": self.group_name,
            "messages": [
                {
                    "text": m["text"],
                    "timestamp": m["timestamp"],
                    "user_hash": m["user_hash"],
                    "reactions": m["reactions"]
                } for m in chain_messages
            ]
        }

    def save(self, output_path: str):
        """Saves the processed data to a JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.processed_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Processed data saved to: {output_path}")

if __name__ == "__main__":
    raw_path = "data/raw/pgwp/result.json"
    output_path = "data/processed/pgwp_cleaned.json"
    
    try:
        processor = DataProcessor(raw_path, "pgwp")
        processor.process()
        processor.save(output_path)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
