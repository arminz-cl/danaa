import os
import logging
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

# System Prompt in Farsi to define Danaa's persona and RAG rules
SYSTEM_PROMPT = (
    "شما «دانا» هستید، یک دوست صمیمی و با تجربه برای مهاجران ایرانی در کانادا. "
    "وظیفه شما پاسخگویی به سوالات مهاجرتی بر اساس گفتگوهای واقعی جامعه است. "
    "لحن شما: کاملاً دوستانه، خودمانی و مستقیم. مثل اینکه دارید در تلگرام به یک دوست پیام می‌دهید. "
    "از جملات کوتاه استفاده کنید. اصلا از کلمات قلمبه‌سلمبه، رسمی یا اداری استفاده نکنید. "
    "تا جای ممکن از لیست‌بندی (bullet points) پرهیز کنید، مگر اینکه واقعاً لازم باشد.\n\n"
    "ساختار پاسخ:\n"
    "۱. بخش اول (پاسخ کوتاه): جواب اصلی را خیلی سریع و در یک خط بدهید.\n"
    "---DETAILED_INFO---\n"
    "۲. بخش دوم (جزئیات): اگر نکته اضافه‌ای هست یا کسی قبلاً تجربه‌ای داشته، اینجا بگویید.\n\n"
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
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.4, # Lower temperature for more direct answers
            max_tokens=1200
        )
        
        full_content = response.choices[0].message.content
        
        if "---DETAILED_INFO---" in full_content:
            short, detailed = full_content.split("---DETAILED_INFO---", 1)
            return {
                "short_answer": short.strip(),
                "detailed_info": detailed.strip()
            }
        else:
            return {
                "short_answer": full_content.strip(),
                "detailed_info": ""
            }

    except Exception as e:
        logger.error(f"Error in AI Service: {e}")
        return {
            "short_answer": "متأسفانه در حال حاضر در پردازش سوال شما مشکلی پیش آمده است.",
            "detailed_info": ""
        }
