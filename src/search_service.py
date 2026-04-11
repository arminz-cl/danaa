import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, processed_file_path: str):
        self.processed_file_path = processed_file_path
        self.knowledge_base = []
        self._load_kb()

    def _load_kb(self):
        """Loads the cleaned knowledge base from JSON."""
        if not os.path.exists(self.processed_file_path):
            logger.warning(f"Knowledge base not found: {self.processed_file_path}")
            return
        
        with open(self.processed_file_path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)
        logger.info(f"Loaded {len(self.knowledge_base)} knowledge objects into SearchService.")

    def _calculate_relevance(self, text: str, query_words: List[str]) -> float:
        """Calculates a simple relevance score based on keyword matches."""
        score = 0
        text_lower = text.lower()
        for word in query_words:
            if word.lower() in text_lower:
                score += 10 # 10 points per keyword match
        return score

    def _get_item_text(self, item: Dict[str, Any]) -> str:
        """Extracts the searchable text from a knowledge object."""
        if item.get("type") == "conversation_chain":
            # Combine all messages in the chain for searching
            return " ".join([m["text"] for m in item.get("messages", [])])
        return item.get("content", "")

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

    def format_context(self, search_results: List[Dict[str, Any]], max_chars_per_msg: int = 500) -> str:
        """Formats search results into a clean text block for the AI prompt."""
        if not search_results:
            return "No relevant community history found."

        context_blocks = []
        for i, res in enumerate(search_results):
            timestamp = res.get("timestamp", "Unknown Date")
            
            if res.get("type") == "conversation_chain":
                messages = res.get("messages", [])
                formatted_msgs = []
                for m in messages:
                    text = m['text']
                    if len(text) > max_chars_per_msg:
                        text = text[:max_chars_per_msg] + "... (truncated)"
                    formatted_msgs.append(f"- {m['user_hash']}: {text}")
                
                chain_text = "\n".join(formatted_msgs)
                block = f"Context {i+1} (Discussion from {timestamp}):\n{chain_text}"
            else:
                content = res.get("content", "")
                if len(content) > max_chars_per_msg:
                    content = content[:max_chars_per_msg] + "... (truncated)"
                block = f"Context {i+1} (Information from {timestamp}):\n- {content}"
            
            context_blocks.append(block)

        return "\n\n".join(context_blocks)

if __name__ == "__main__":
    # Test Search
    searcher = SearchService("data/processed/pgwp_cleaned.json")
    query = "ددلاین ورک پرمیت" # "Work permit deadline"
    results = searcher.search(query)
    
    print(f"--- Search Results for: '{query}' ---")
    print(searcher.format_context(results))
