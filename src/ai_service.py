import os
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq Client
# You will get your key from https://console.groq.com/
client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# System Prompt in Farsi to define Danaa's persona
SYSTEM_PROMPT = (
    "شما «دانا» هستید، یک دستیار هوشمند برای مهاجران ایرانی در کانادا. "
    "وظیفه شما پاسخگویی به سوالات مربوط به مهاجرت، قوانین، بیمه و سیستم‌های مالی کانادا است. "
    "لحن شما باید حرفه‌ای، همدلانه و دقیق باشد. "
    "همیشه تاکید کنید که پاسخ‌های شما جنبه اطلاع‌رسانی دارد و توصیه حقوقی رسمی نیست. "
    "اگر سوالی خارج از حوزه اطلاعات شما بود، صادقانه اعلام کنید."
)

async def get_ai_answer(user_question: str) -> str:
    """
    Sends the user's question to Groq and returns the AI-generated answer.
    """
    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return "متأسفانه در حال حاضر در اتصال به هوش مصنوعی مشکلی پیش آمده است. لطفاً کمی بعد دوباره تلاش کنید."
