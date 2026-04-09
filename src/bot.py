import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from datetime import datetime
from dotenv import load_dotenv
from src.ai_service import get_ai_answer

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Passes the user's message to Groq and replies with the AI-generated answer.
    """
    if not update or not update.message:
        return

    chat_id = update.message.chat_id
    user_text = update.message.text
    user_name = update.message.from_user.username or "Unknown"
    
    logger.info(f"Received message from @{user_name} ({chat_id}): {user_text}")

    # Send a 'typing' status while AI generates the answer
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    # Call AI Service
    ai_response = await get_ai_answer(user_text)
    
    logger.info(f"AI Response to @{user_name}: {ai_response[:100]}...")

    # Accuracy disclaimer in Farsi (as per doc/RULES.md)
    disclaimer = (
        "\n\n---\n"
        "⚠️ *سلب مسئولیت:* اطلاعات بر اساس دانش عمومی هوش مصنوعی ارائه شده و توصیه حقوقی یا حرفه‌ای نیست. "
        "لطفاً صحت اطلاعات را از منابع رسمی بررسی کنید زیرا ممکن است اطلاعات قدیمی یا نادرست باشد.\n"
        f"📅 *زمان پاسخ:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    response_text = f"{ai_response}{disclaimer}"

    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode="Markdown"
    )

def main():
    """Starts the bot using Polling."""
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in .env file.")
        return

    logger.info("Initializing Danaa Bot application...")
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Add a handler for all text messages
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(text_handler)
    
    logger.info("Bot is starting polling...")
    application.run_polling()
