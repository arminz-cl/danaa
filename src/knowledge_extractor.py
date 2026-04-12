import os
import json
import logging
import asyncio
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KnowledgeExtractor:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = model
        # Use v1beta for Gemini 2.0 features and JSON response support
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

        
        self.system_prompt = (
            "You are a Knowledge Engineer. Your task is to extract clear, concise 'Knowledge Cards' from Iranian community chat transcripts regarding Canadian immigration.\n\n"
            "Each Knowledge Card must represent a single fact, rule, or common experience.\n"
            "Return the output as a JSON list of objects with these fields:\n"
            "- topic: (string) The main subject (e.g., 'PGWP Deadline', 'Biometrics')\n"
            "- fact: (string) The distilled knowledge in Farsi. Be precise and clear.\n"
            "- type: (string) One of: 'rule', 'experience', 'advice'\n"
            "- confidence: (int 1-10) How reliable this info seems based on the discussion.\n\n"
            "Rules:\n"
            "1. Only extract information that is useful for others.\n"
            "2. If multiple people agree on something, give it higher confidence.\n"
            "3. If something is a personal case that might not apply to others, mark it as 'experience'.\n"
            "4. Language: Topic is English, Fact is Farsi.\n"
            "IMPORTANT: Return ONLY a valid JSON object with a 'cards' key containing the list."
        )

    async def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Sends a chunk of text to Gemini to extract knowledge cards."""
        if not self.api_key:
            logger.error("GOOGLE_API_KEY not found in .env")
            return []

        payload = {
            "contents": [{
                "parts": [{"text": f"{self.system_prompt}\n\nExtract from this transcript:\n{text}"}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, timeout=60.0)
                if response.status_code != 200:
                    logger.error(f"Gemini API Error: {response.text}")
                    return []
                
                result = response.json()
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(content_text)
                return data.get("cards", data if isinstance(data, list) else [])
            except Exception as e:
                logger.error(f"Error during extraction: {e}")
                return []

    def _prepare_chunks(self, data: List[Dict[str, Any]], chunk_size: int = 25) -> List[str]:
        """Groups raw data into text chunks for the LLM."""
        chunks = []
        current_chunk = []
        
        for item in data:
            if item.get("type") == "conversation_chain":
                text = " | ".join([f"{m['user_hash']}: {m['text']}" for m in item.get("messages", [])])
            else:
                text = item.get("content", "")
            
            if len(text.strip()) < 20:
                continue

            current_chunk.append(text)
            
            if len(current_chunk) >= chunk_size:
                chunks.append("\n---\n".join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append("\n---\n".join(current_chunk))
            
        return chunks

    async def process_file(self, input_path: str, output_path: str, max_tokens: int = 100000):
        """Processes the *last* part of the file and saves results with metadata."""
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chars_limit = max_tokens * 3.5
        subset = []
        current_chars = 0
        
        for item in reversed(data):
            item_str = json.dumps(item, ensure_ascii=False)
            current_chars += len(item_str)
            if current_chars > chars_limit:
                break
            subset.append(item)
        
        subset.reverse()
        if not subset:
            return

        earliest_timestamp = subset[0].get("timestamp", "unknown")
        logger.info(f"Processing {len(subset)} items from {input_path} (Starting from {earliest_timestamp})...")
        
        chunks = self._prepare_chunks(subset)
        all_cards = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Extracting chunk {i+1}/{len(chunks)}...")
            cards = await self.extract_from_text(chunk)
            
            if cards:
                for card in cards:
                    card["source_file"] = os.path.basename(input_path)
                all_cards.extend(cards)
            
            # Gemini is fast and has high limits, so we only need a tiny delay
            await asyncio.sleep(1)

        output_data = {
            "metadata": {
                "source": input_path,
                "earliest_processed_message": earliest_timestamp,
                "extraction_date": "2026-04-11",
                "token_limit": max_tokens,
                "model": self.model
            },
            "cards": all_cards
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(all_cards)} cards to {output_path}")

async def main():
    extractor = KnowledgeExtractor()
    
    # Process both files with 100k tokens each (FREEDOM!)
    tasks = [
        extractor.process_file(
            "data/processed/pgwp_cleaned_20260411.json", 
            "data/knowledge_base/pgwp_cards.json",
            max_tokens=100000
        ),
        extractor.process_file(
            "data/processed/express_entry_20260411_cleaned.json", 
            "data/knowledge_base/express_entry_cards.json",
            max_tokens=100000
        )
    ]
    
    for task in tasks:
        await task

if __name__ == "__main__":
    asyncio.run(main())
