import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, processed_dir: str = "data/processed", kb_dir: str = "data/knowledge_base"):
        self.processed_dir = processed_dir
        self.kb_dir = kb_dir
        self.knowledge_base = []
        self.knowledge_cards = []
        self._load_processed_data()
        self._load_cards()

    def _load_processed_data(self):
        """Loads all cleaned knowledge base files from the processed directory."""
        if not os.path.exists(self.processed_dir):
            logger.warning(f"Processed directory not found: {self.processed_dir}")
            return

        for filename in os.listdir(self.processed_dir):
            if filename.endswith(".json") and "_cleaned" in filename:
                path = os.path.join(self.processed_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        items = json.load(f)
                        self.knowledge_base.extend(items)
                    logger.info(f"Loaded {len(items)} items from {filename}")
                except Exception as e:
                    logger.error(f"Error loading {path}: {e}")

        logger.info(f"Total items in knowledge base: {len(self.knowledge_base)}")

    def _load_cards(self):
        """Loads knowledge cards from the kb_dir recursively."""
        if not os.path.exists(self.kb_dir):
            return

        for root, dirs, files in os.walk(self.kb_dir):
            for filename in files:
                if filename.endswith(".json") and "_cards" in filename:
                    path = os.path.join(root, filename)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict):
                                self.knowledge_cards.extend(data.get("cards", []))
                            elif isinstance(data, list):
                                self.knowledge_cards.extend(data)
                    except Exception as e:
                        logger.error(f"Error loading cards from {path}: {e}")
        logger.info(f"Loaded {len(self.knowledge_cards)} knowledge cards.")

    def _calculate_relevance(self, text: str, query_words: List[str]) -> float:
        """Calculates a simple relevance score based on keyword matches."""
        score = 0
        text_lower = text.lower()
        for word in query_words:
            if word.lower() in text_lower:
                score += 10 
        return score

    def _get_item_text(self, item: Dict[str, Any]) -> str:
        """Extracts the searchable text from a knowledge object."""
        if item.get("type") == "conversation_chain":
            # Combine all messages in the chain for searching
            return " ".join([m["text"] for m in item.get("messages", [])])
        return item.get("content", "")

    def search_cards(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Searches specifically for distilled knowledge cards."""
        if not query or not self.knowledge_cards:
            return []

        query_words = query.strip().split()
        results = []
        for card in self.knowledge_cards:
            # Search both topic and fact
            text = f"{card.get('topic', '')} {card.get('fact', '')}"
            score = self._calculate_relevance(text, query_words)
            if score > 0:
                # Boost based on confidence
                score += card.get("confidence", 0)
                results.append({"card": card, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return [r["card"] for r in results[:top_k]]

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Searches the knowledge base and returns the top_k most relevant items."""
        if not query or not self.knowledge_base:
            return []

        query_words = query.strip().split()
        results = []

        for item in self.knowledge_base:
            text = self._get_item_text(item)
            relevance_score = self._calculate_relevance(text, query_words)
            
            if relevance_score == 0:
                continue

            # Recency Bonus (within the last 6 months - 180 days)
            # 1772342213 is roughly early 2026. 
            # We'll use a simple boost for later unix timestamps.
            # (Higher unix_time = more recent)
            recency_bonus = (item.get("unix_time", 0) / 10**8) # Scaled bonus

            # Popularity Bonus (based on reactions)
            popularity_bonus = 0
            if item.get("type") == "conversation_chain":
                # Average/Sum reaction scores in the chain
                popularity_bonus = sum([m.get("reactions", {}).get("score", 0) for m in item.get("messages", [])])
            else:
                popularity_bonus = item.get("reactions", {}).get("score", 0)

            total_score = relevance_score + recency_bonus + (popularity_bonus * 2)
            
            results.append({
                "item": item,
                "score": total_score
            })

        # Sort by total score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        return [r["item"] for r in results[:top_k]]

    def format_context(self, search_results: List[Dict[str, Any]], knowledge_cards: List[Dict[str, Any]] = None, max_chars_per_msg: int = 400, max_total_chars: int = 3000) -> str:
        """Formats search results and knowledge cards into a text block for the AI."""
        context_blocks = []
        
        # 1. Add Distilled Facts (Knowledge Cards)
        if knowledge_cards:
            fact_lines = []
            for card in knowledge_cards:
                fact_lines.append(f"- [{card['topic']}] {card['fact']} (Confidence: {card['confidence']}/10)")
            
            fact_block = "--- CONFIRMED KNOWLEDGE / FACTS ---\n" + "\n".join(fact_lines)
            context_blocks.append(fact_block)

        # 2. Add Community Experiences (Raw Results)
        if search_results:
            experience_lines = ["--- COMMUNITY CONVERSATIONS / EXPERIENCES ---"]
            for i, res in enumerate(search_results):
                timestamp = res.get("timestamp", "Unknown Date")
                if res.get("type") == "conversation_chain":
                    messages = res.get("messages", [])
                    formatted_msgs = []
                    for m in messages:
                        text = m['text']
                        if len(text) > max_chars_per_msg:
                            text = text[:max_chars_per_msg] + "... (truncated)"
                        formatted_msgs.append(f"  - {m['user_hash']}: {text}")
                    chain_text = "\n".join(formatted_msgs)
                    block = f"Snippet {i+1} ({timestamp}):\n{chain_text}"
                else:
                    content = res.get("content", "")
                    if len(content) > max_chars_per_msg:
                        content = content[:max_chars_per_msg] + "... (truncated)"
                    block = f"Snippet {i+1} ({timestamp}):\n  - {content}"
                experience_lines.append(block)
            
            context_blocks.append("\n\n".join(experience_lines))

        full_context = "\n\n".join(context_blocks) if context_blocks else "No relevant community history or facts found."
        
        # Hard limit to prevent Telegram 4096 char overflow
        if len(full_context) > max_total_chars:
            full_context = full_context[:max_total_chars] + "\n\n... (برخی از منابع به دلیل طولانی بودن حذف شدند)"
            
        return full_context

if __name__ == "__main__":
    # Test Search
    searcher = SearchService("data/processed/pgwp_cleaned.json")
    query = "ددلاین ورک پرمیت" # "Work permit deadline"
    results = searcher.search(query)
    
    print(f"--- Search Results for: '{query}' ---")
    print(searcher.format_context(results))
