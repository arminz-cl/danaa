import os
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime
from dotenv import load_dotenv
from src.ai_service import get_ai_answer

# Load environment variables
load_dotenv()

# Setup logging
log_dir = "logs/bot"
os.makedirs(log_dir, exist_ok=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Standard log handler
info_handler = RotatingFileHandler(f"{log_dir}/bot.log", maxBytes=10*1024*1024, backupCount=5)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)

# Error log handler
error_handler = RotatingFileHandler(f"{log_dir}/bot.errors", maxBytes=10*1024*1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(info_handler)
logger.addHandler(error_handler)
logger.addHandler(logging.StreamHandler())

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Passes the user's message to the AI service and replies with the AI-generated answer.
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
    retrieved_context = ai_response_dict.get("retrieved_context", "")

    # Force RTL directionality using RLM (\u200f)
    RLM = "\u200f"
    
    # Simplified disclaimer in Farsi (integrated timestamp)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    disclaimer = (
        "\n\n---\n"
        f"⚠️ این پاسخ بر اساس دانش عمومی در {timestamp} است، توصیه تخصصی نیست و ممکن است اشتباه باشد."
    )

    # Apply RLM to short answer and disclaimer
    short_answer_rtl = short_answer.replace("\n", f"\n{RLM}")
    disclaimer_rtl = disclaimer.replace("\n", f"\n{RLM}")
    response_text = f"{RLM}{short_answer_rtl}{disclaimer_rtl}"

    # Only show the button if there is detailed info
    reply_markup = None
    if detailed_info:
        keyboard = [[InlineKeyboardButton("جزئیات بیشتر 🔍", callback_data="show_more")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=response_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # Store data using the message_id to allow multiple independent interactions
    if "rag_storage" not in context.user_data:
        context.user_data["rag_storage"] = {}
    
    storage_id = str(sent_message.message_id)
    context.user_data["rag_storage"][storage_id] = {
        "detailed_info": f"{RLM}" + detailed_info.replace("\n", f"\n{RLM}"),
        "retrieved_context": f"{RLM}" + retrieved_context.replace("\n", f"\n{RLM}")
    }

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles button clicks."""
    query = update.callback_query
    if not query:
        return
        
    await query.answer()
    
    RLM = "\u200f"
    message_id = str(query.message.message_id)
    
    # Retrieve data for this specific message
    storage = context.user_data.get("rag_storage", {}).get(message_id, {})
    
    if query.data == "show_more":
        detailed_info = storage.get("detailed_info", "متأسفانه جزئیات بیشتری در دسترس نیست.")
        
        # After showing details, offer the "References" button
        keyboard = [[InlineKeyboardButton("منابع 📚", callback_data="show_refs")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        new_text = f"{query.message.text}\n\n{RLM}**جزئیات بیشتر:**\n{detailed_info}"
        
        try:
            await query.edit_message_text(
                text=new_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Error editing message for show_more: {e}")
            # Fallback: if too long, just show the detailed info without original text
            await query.edit_message_text(
                text=f"{RLM}**جزئیات بیشتر:**\n{detailed_info}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    
    elif query.data == "show_refs":
        context_data = storage.get("retrieved_context", "متأسفانه منابعی یافت نشد.")
        
        # We replace the text entirely for references to avoid character limits
        ref_text = f"{RLM}**منابع و تاریخچه‌ی گفتگوها:**\n\n{context_data}"
        
        try:
            await query.edit_message_text(
                text=ref_text,
                parse_mode="Markdown",
                reply_markup=None # Final step, remove buttons
            )
        except Exception as e:
            logger.error(f"Error editing message for show_refs: {e}")
            # Final fallback: extreme truncation
            await query.edit_message_text(
                text=f"{RLM}**منابع (بسیار کوتاه شده):**\n\n{context_data[:1000]}...",
                parse_mode="Markdown",
                reply_markup=None
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

if __name__ == "__main__":
    main()
