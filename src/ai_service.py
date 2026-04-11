import os
import json
import logging
from datetime import datetime
from groq import AsyncGroq
from dotenv import load_dotenv
from src.search_service import SearchService

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Groq Client
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# Initialize Search Service
# We use the cleaned data from the pgwp group
search_service = SearchService("data/processed/pgwp_cleaned.json")

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
    Retrieves relevant context, augments the prompt, and gets an answer from Groq.
    Returns a dictionary with 'short_answer' and 'detailed_info'.
    """
    try:
        # 1. Search for relevant community context
        search_results = search_service.search(user_question, top_k=4)
        context_text = search_service.format_context(search_results)
        
        # 2. Construct the prompt with context
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user", 
                "content": f"سوال کاربر: {user_question}\n\nمتن مستندات جامعه برای راهنمایی:\n{context_text}"
            }
        ]

        logger.info(f"Sending request to Groq with {len(search_results)} context blocks.")

        # 3. Call Groq API
        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            temperature=0.4, # Lower temperature for more direct answers
            max_tokens=1200
        )
        
        full_content = response.choices[0].message.content
        
        ai_response = {}
        if "---DETAILED_INFO---" in full_content:
            short, detailed = full_content.split("---DETAILED_INFO---", 1)
            ai_response = {
                "short_answer": short.strip(),
                "detailed_info": detailed.strip()
            }
        else:
            # Fallback if AI forgets delimiter: 
            # If there's a newline, split it. Otherwise, use whole content.
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
        if "rate_limit_exceeded" in str(e).lower():
            logger.warning(f"Rate limit hit: {e}")
            return {
                "short_answer": "ببخشید، الان سرم یه کم شلوغه و تعداد درخواست‌ها زیاده. لطفاً یکم دیگه دوباره امتحان کن، حتماً جواب میدم! 🙏",
                "detailed_info": "محدودیت تعداد درخواست‌های API (Rate Limit) رخ داده است. این مشکل معمولاً بعد از چند دقیقه برطرف می‌شود."
            }
        
        logger.error(f"Error in AI Service: {e}")
        return {
            "short_answer": "متأسفانه در حال حاضر در پردازش سوال شما مشکلی پیش آمده است.",
            "detailed_info": ""
        }
