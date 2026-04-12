import os
import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import httpx
from dotenv import load_dotenv

# Force override to ensure the key from .env is used
load_dotenv(override=True)

# Create logs directory if it doesn't exist
if not os.path.exists("logs"):
    os.makedirs("logs")

# Configure logging
log_filename = "logs/extractor.log"
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KnowledgeExtractor:
    def __init__(self, model: str = "gemini-2.5-flash-lite"):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = model
        # Use v1beta for Gemini 2.5 Flash features like JSON response support
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
            return None

        # Standard payload for Gemini 2.5 Flash v1beta (Proven via terminal)
        payload = {
            "contents": [{
                "parts": [{"text": f"{self.system_prompt}\n\nExtract from this transcript:\n{text}"}]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, timeout=60.0)
                
                if response.status_code != 200:
                    logger.error(f"Gemini API Error: {response.text}")
                    return None
                
                result = response.json()
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                
                # Robust parsing
                try:
                    data = json.loads(content_text)
                    return data.get("cards", data if isinstance(data, list) else [])
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse AI response as JSON: {content_text[:100]}...")
                    return None # Critical parsing error

            except Exception as e:
                logger.error(f"Error during extraction: {e}")
                return None

    def _prepare_chunks(self, data: List[Dict[str, Any]], chunk_size: int = 25) -> List[str]:
        """Groups raw data into text chunks for the LLM."""
        chunks = []
        current_chunk = []
        
        for item in data:
            if item.get("type") == "conversation_chain":
                text = " | ".join([f"{m['user_hash']}: {m['text']}" for m in item.get("messages", [])])
            else:
                text = item.get("content", "")
            
            if not text or len(text.strip()) < 20:
                continue

            current_chunk.append(text)
            
            if len(current_chunk) >= chunk_size:
                chunks.append("\n---\n".join(current_chunk))
                current_chunk = []
        
        if current_chunk:
            chunks.append("\n---\n".join(current_chunk))
            
        return chunks

    async def process_file(self, input_path: str, base_output_dir: str, start_date: str = "2026-01-01", end_date: str = "2026-12-31"):
        """Processes messages day-by-day within a date range (newest first)."""
        if not os.path.exists(input_path):
            logger.error(f"Input file not found: {input_path}")
            return

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Filter for messages within the specified date range
        subset = [
            item for item in data 
            if item.get("timestamp", "")[:10] >= start_date 
            and item.get("timestamp", "")[:10] <= end_date
        ]
        
        if not subset:
            logger.warning(f"No messages found between {start_date} and {end_date} in {input_path}")
            return

        # Group by day (YYYY-MM-DD)
        days_data = {}
        for item in subset:
            day = item.get("timestamp", "")[:10] # YYYY-MM-DD
            if day not in days_data:
                days_data[day] = []
            days_data[day].append(item)

        # Sort days in REVERSE order (newest first)
        sorted_days = sorted(days_data.keys(), reverse=True)
        logger.info(f"Found {len(sorted_days)} days of data between {start_date} and {end_date} in {input_path}")
        
        group_name = os.path.basename(input_path).split('_')[0] # e.g. pgwp or express

        for day_str in sorted_days:
            # Create folder structure YYYY/MM/DD
            year, month, day = day_str.split('-')
            day_dir = os.path.join(base_output_dir, year, month, day)
            day_file = os.path.join(day_dir, f"{group_name}_cards.json")

            # SKIP IF ALREADY DONE (Resume functionality)
            if os.path.exists(day_file):
                logger.info(f"Skipping {day_str} for {group_name} (Already processed)")
                continue

            day_items = days_data[day_str]
            logger.info(f"Processing {day_str} ({len(day_items)} items) for {group_name}...")
            
            chunks = self._prepare_chunks(day_items)
            day_cards = []
            
            any_success = False
            for i, chunk in enumerate(chunks):
                logger.info(f"  -> Extracting chunk {i+1}/{len(chunks)} for {day_str}...")
                cards = await self.extract_from_text(chunk)
                
                # Check for API error (extract_from_text returns [] but could be error)
                # We need to distinguish between 'no cards' and 'error'
                # Let's assume if it returns cards or it was a 200 OK we continue.
                # Actually, the logic is: if any chunk in a day triggers an error, 
                # we shouldn't mark the whole day as 'done'.
                
                if cards is not None: # We need to update extract_from_text to return None on error
                    any_success = True
                    for card in cards:
                        card["source_file"] = os.path.basename(input_path)
                        card["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        card["message_date"] = day_str
                    day_cards.extend(cards)
                else:
                    logger.error(f"  !! Skipping save for {day_str} due to extraction failure.")
                    any_success = False
                    break
                
                # Respect 15 RPM limit (using 10s to be extra safe with free tier)
                await asyncio.sleep(10)

            # Save this day's work ONLY if we successfully reached the API for all chunks
            if any_success:
                os.makedirs(day_dir, exist_ok=True)
                output_data = {
                    "metadata": {
                        "source": input_path,
                        "date": day_str,
                        "extraction_date": datetime.now().strftime("%Y-%m-%d"),
                        "model": self.model,
                        "total_cards": len(day_cards)
                    },
                    "cards": day_cards
                }
                with open(day_file, 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, ensure_ascii=False, indent=2)
                
                if day_cards:
                    logger.info(f"  => Saved {len(day_cards)} cards for {day_str}")
                else:
                    logger.info(f"  => No cards found for {day_str}, saved empty result to skip in future.")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract knowledge cards from chat history.")
    parser.add_argument("--start", type=str, default="2026-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-12-31", help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    extractor = KnowledgeExtractor()
    
    # Base dir for knowledge base
    kb_dir = "data/knowledge_base"

    # Process range for both files
    logger.info(f"Starting distillation from {args.start} to {args.end}")
    
    await extractor.process_file(
        "data/processed/pgwp_cleaned_20260411.json", 
        kb_dir,
        start_date=args.start,
        end_date=args.end
    )
    
    await extractor.process_file(
        "data/processed/express_entry_20260411_cleaned.json", 
        kb_dir,
        start_date=args.start,
        end_date=args.end
    )

if __name__ == "__main__":
    asyncio.run(main())
