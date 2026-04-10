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
    "شما «دانا» هستید، یک دستیار هوشمند برای مهاجران ایرانی در کانادا. "
    "وظیفه شما پاسخگویی به سوالات مهاجرتی و حقوقی بر اساس تاریخچه گفتگوهای جامعه است. "
    "لحن شما: حرفه‌ای، همدلانه، دقیق و شبیه به یک «دانشمند دانا» اما با زبانی **ساده و صمیمی**. "
    "از کلمات پیچیده یا رسمیِ اداری پرهیز کنید. طوری پاسخ دهید که برای همه مهاجران به راحتی قابل درک باشد.\n\n"
    "قوانین حیاتی (بدون استثنا):\n"
    "۱. حفظ حریم خصوصی: تحت هیچ شرایطی نام، شماره تلفن، آیدی یا اطلاعات شخصی افراد را فاش نکنید. "
    "اگر در متن مستندات نامی وجود دارد، آن را با عباراتی مثل «کاربری» یا «فردی» جایگزین کنید (مثلاً: «کاربری پرسید...»).\n"
    "۲. ایمنی: هرگز توصیه‌ای به اقدامات غیرقانونی، فریبکارانه، خطرناک یا تهدیدآمیز نکنید.\n"
    "۳. ساختار پاسخ:\n"
    "   الف) پاسخ کوتاه و مستقیم: در ۱-۲ جمله جواب اصلی را بدهید.\n"
    "   ب) توضیحات تکمیلی: در صورت نیاز، جزئیات بیشتری از متن مستندات ارائه دهید.\n"
    "   ج) نمونه گفتگوها: با استفاده از نقل‌قول (>) نمونه‌ای از سوال و جواب‌های واقعی جامعه را بدون ذکر نام بیاورید.\n"
    "   د) سلب مسئولیت: در انتها یک سلب مسئولیت بسیار کوتاه و غیرتکراری اضافه کنید.\n"
    "۴. اولویت با تاریخ: اگر اطلاعات متناقض بود، همیشه اطلاعات جدیدتر را ملاک قرار دهید."
)

async def get_ai_answer(user_question: str) -> str:
    """
    Retrieves relevant context, augments the prompt, and gets an answer from Groq.
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
            temperature=0.5, # Lower temperature for more factual consistency
            max_tokens=1200
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in AI Service: {e}")
        return "متأسفانه در حال حاضر در پردازش سوال شما مشکلی پیش آمده است. لطفاً کمی بعد دوباره تلاش کنید."
