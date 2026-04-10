import asyncio
import logging
from src.ai_service import get_ai_answer

# Configure logging to see the context count
logging.basicConfig(level=logging.INFO)

async def test_rag():
    question = "ددلاین سابمیت ورک پرمیت برای ونکوور چه ساعتی است؟"
    print(f"--- Question: {question} ---")
    
    answer = await get_ai_answer(question)
    
    print("\n--- Danaa's Answer ---")
    print(answer)

if __name__ == "__main__":
    asyncio.run(test_rag())
