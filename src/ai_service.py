import os
import json
import logging
import httpx
from datetime import datetime
from dotenv import load_dotenv
from src.search_service import SearchService

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Search Service
# We use all cleaned data from the processed directory
search_service = SearchService("data/processed")

# Google Gemini Config
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash-latest"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GOOGLE_API_KEY}"

def log_experiment(user_question: str, context: str, response: dict):
    """Logs the RAG interaction into a unique file for each sample."""
    now = datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
    filename_str = now.strftime("%Y%m%d_%H%M%S")
    
    log_entry = (
        f"{'='*80}\n"
        f"TIMESTAMP: {timestamp_str}\n"
        f"USER QUESTION: {user_question}\n"
        f"{'-'*40}\n"
        f"RETRIEVED CONTEXT:\n{context}\n"
        f"{'-'*40}\n"
        f"AI SHORT ANSWER: {response.get('short_answer')}\n"
        f"AI DETAILED INFO:\n{response.get('detailed_info')}\n"
        f"{'='*80}\n"
    )
    
    os.makedirs("experiments", exist_ok=True)
    file_path = f"experiments/sample_{filename_str}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(log_entry)

# System Prompt in Farsi to define Danaa's persona and RAG rules
SYSTEM_PROMPT = (
    "شما «دانا» هستید، یک دوست صمیمی و با تجربه برای مهاجران ایرانی در کانادا. "
    "وظیفه شما پاسخگویی به سوالات مهاجرتی بر اساس گفتگوهای واقعی جامعه است. "
    "لحن شما: کاملاً دوستانه، خودمانی و مستقیم. مثل اینکه دارید در تلگرام به یک دوست پیام می‌دهید. "
    "از جملات کوتاه استفاده کنید. اصلا از کلمات قلمبه‌سلمبه، رسمی یا اداری استفاده نکنید. "
    "تا جای ممکن از لیست‌بندی (bullet points) پرهیز کنید، مگر اینکه واقعاً لازم باشد.\n\n"
    "ساختار پاسخ بسیار مهم (الزامی):\n"
    "پاسخ شما باید حتماً دو بخش داشته باشد که با عبارت دقیق «---DETAILED_INFO---» از هم جدا شده‌اند.\n"
    "بخش اول: جواب خیلی کوتاه و صمیمی.\n"
    "---DETAILED_INFO---\n"
    "بخش دوم: جزئیات بیشتر و تجربه‌های بقیه.\n\n"
    "حتی اگر جزئیات زیادی نداری، یک جمله در بخش دوم بنویس. این ساختار برای کارکرد دکمه‌های بات حیاتی است.\n\n"
    "قوانین:\n"
    "- حریم خصوصی را رعایت کنید (نام نبرید).\n"
    "- اگر اطلاعاتی ندارید، خیلی راحت بگویید «نمیدونم» یا «باید بیشتر بپرسی»."
)

async def get_ai_answer(user_question: str) -> dict:
    """
    Retrieves relevant context (Facts + Snippets), augments the prompt, and gets an answer from Gemini.
    Returns a dictionary with 'short_answer' and 'detailed_info'.
    """
    try:
        # 1. Search for relevant knowledge
        # Find distilled facts (Knowledge Cards)
        cards = search_service.search_cards(user_question, top_k=3)
        # Find raw community snippets
        snippets = search_service.search(user_question, top_k=4)
        
        # Format the combined context
        context_text = search_service.format_context(snippets, cards)
        
        # 2. Construct the prompt with context
        prompt_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"سوال کاربر: {user_question}\n\n"
            f"اطلاعات استخراج شده از جامعه برای راهنمایی:\n{context_text}\n\n"
            "نکته: بخش 'CONFIRMED KNOWLEDGE' حقایق تایید شده هستند. "
            "بخش 'COMMUNITY CONVERSATIONS' تجربه‌های شخصی افراد است که ممکن است متفاوت باشد."
        )

        # 3. Call Gemini API
        payload = {
            "contents": [{
                "parts": [{"text": prompt_content}]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 1200,
            }
        }

        logger.info(f"Sending request to Gemini with {len(cards)} facts and {len(snippets)} snippets.")

        async with httpx.AsyncClient() as client:
            response = await client.post(GEMINI_URL, json=payload, timeout=60.0)
            if response.status_code != 200:
                logger.error(f"Gemini API Error: {response.text}")
                raise Exception(f"Gemini API error: {response.status_code}")
            
            result = response.json()
            full_content = result['candidates'][0]['content']['parts'][0]['text']
        
        ai_response = {}
        if "---DETAILED_INFO---" in full_content:
            short, detailed = full_content.split("---DETAILED_INFO---", 1)
            ai_response = {
                "short_answer": short.strip(),
                "detailed_info": detailed.strip()
            }
        else:
            # Fallback if AI forgets delimiter: 
            parts = full_content.split("\n\n", 1)
            if len(parts) > 1:
                ai_response = {
                    "short_answer": parts[0].strip(),
                    "detailed_info": parts[1].strip()
                }
            else:
                ai_response = {
                    "short_answer": full_content.strip(),
                    "detailed_info": "جزئیات خاصی در تاریخچه گفتگوها پیدا نکردم، اما اگه سوال دقیق‌تری داری بپرس."
                }

        # Log the experiment details
        log_experiment(user_question, context_text, ai_response)
        
        # Include context in the return for debugging/dashboard
        ai_response["retrieved_context"] = context_text
        
        return ai_response

    except Exception as e:
        logger.error(f"Error in AI Service: {e}")
        return {
            "short_answer": "متأسفانه در حال حاضر در پردازش سوال شما مشکلی پیش آمده است.",
            "detailed_info": ""
        }
