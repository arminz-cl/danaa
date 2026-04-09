import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Echoes back the user's message in Farsi with a disclaimer.
    The answer itself doesn't include the timestamp, but the disclaimer does.
    """
    if not update or not update.message:
        return

    chat_id = update.message.chat_id
    user_text = update.message.text
    
    # Accuracy disclaimer in Farsi (Rule 3 in doc/RULES.md)
    # The timestamp is included here in the disclaimer section.
    disclaimer = (
        "\n\n---\n"
        "⚠️ *سلب مسئولیت:* اطلاعات بر اساس تاریخچه گروه‌ها ارائه شده و توصیه حقوقی یا حرفه‌ای نیست. "
        "لطفاً صحت اطلاعات را از منابع رسمی بررسی کنید زیرا ممکن است اطلاعات قدیمی یا نادرست باشد.\n"
        f"📅 *زمان پاسخ:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    response_text = (
        f"سلام! من **دانا** هستم. 🇮🇷🇨🇦\n\n"
        f"شما پرسیدید: «{user_text}»\n\n"
        "در حال حاضر من در فاز ۱ (پایه) هستم. "
        "به زودی می‌توانم در تاریخچه گروه‌ها جستجو کنم و پاسخ شما را پیدا کنم!"
        f"{disclaimer}"
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode="Markdown"
    )

def main():
    """Starts the bot using Polling."""
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env file.")
        return

    print("Danaa Bot is starting... (Polling mode)")
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add a handler for all text messages
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(text_handler)
    
    application.run_polling()

if __name__ == "__main__":
    main()
