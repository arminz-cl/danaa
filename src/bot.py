import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, filters
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
    ai_response_dict = await get_ai_answer(user_text)
    short_answer = ai_response_dict.get("short_answer", "")
    detailed_info = ai_response_dict.get("detailed_info", "")

    # Store detailed info in user_data to retrieve later on button click
    # Use message_id as key to distinguish between different queries
    if not context.user_data:
        context.user_data["details"] = {}
    
    # Simplified disclaimer in Farsi (integrated timestamp)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    disclaimer = (
        "\n\n---\n"
        f"⚠️ این پاسخ بر اساس دانش عمومی در {timestamp} است، توصیه تخصصی نیست و ممکن است اشتباه باشد."
    )

    # Force RTL directionality using RLM (\u200f)
    RLM = "\u200f"
    
    # Apply RLM to short answer and disclaimer
    short_answer_rtl = short_answer.replace("\n", f"\n{RLM}")
    disclaimer_rtl = disclaimer.replace("\n", f"\n{RLM}")
    response_text = f"{RLM}{short_answer_rtl}{disclaimer_rtl}"

    # Only show the button if there is detailed info
    reply_markup = None
    if detailed_info:
        keyboard = [[InlineKeyboardButton("بیشتر بدانید 🔍", callback_data="show_more")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # Store RTL-formatted detailed info
        detailed_info_rtl = f"{RLM}" + detailed_info.replace("\n", f"\n{RLM}")
        context.user_data["last_detail"] = detailed_info_rtl

    await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    await query.answer()

    if query.data == "show_more":
        detailed_info = context.user_data.get("last_detail", "متأسفانه جزئیات بیشتری در دسترس نیست.")
        
        await query.edit_message_text(
            text=f"{query.message.text}\n\n**جزئیات بیشتر:**\n{detailed_info}",
            parse_mode="Markdown",
            reply_markup=None # Remove the button after showing details
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

    # Add callback query handler
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Bot is starting polling...")
    application.run_polling()
