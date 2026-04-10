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
    "وظیفه شما پاسخگویی به سوالات مربوط به مهاجرت، قوانین، بیمه و سیستم‌های مالی کانادا است. "
    "لحن شما باید حرفه‌ای، همدلانه و دقیق باشد. "
    "\n\n"
    "دستورالعمل‌های پاسخگویی:\n"
    "1. اگر «متن مستندات جامعه» (Community Context) در اختیار شما قرار گرفت، پاسخ خود را بر اساس آن تنظیم کنید.\n"
    "2. همیشه به تاریخ اطلاعات اشاره کنید (مثلاً: «بر اساس گفتگوهای گروه در مارس ۲۰۲۶...»).\n"
    "3. اگر اطلاعات متناقضی وجود داشت، اطلاعات جدیدتر را در اولویت قرار دهید.\n"
    "4. اگر پاسخ در مستندات نبود، از دانش عمومی خود استفاده کنید اما ذکر کنید که این اطلاعات از تاریخچه گروه نیست.\n"
    "5. همیشه تاکید کنید که پاسخ‌های شما جنبه اطلاع‌رسانی دارد و توصیه حقوقی رسمی نیست."
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
