import os
from telegram import Bot, Update
from datetime import datetime
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env if present
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
# Initialize the bot only if TOKEN is available, to avoid errors during local runs
bot = Bot(token=TOKEN) if TOKEN else None

async def handle_message(update: Update):
    """
    Echoes back the user's message with a disclaimer and status.
    """
    if not update or not update.message:
        return

    chat_id = update.message.chat_id
    user_text = update.message.text
    
    # Accuracy disclaimer (as per doc/RULES.md)
    disclaimer = (
        "\n\n---\n"
        "⚠️ *Disclaimer:* Information is based on community history, not professional advice. "
        "Verify with official sources as information may be outdated or inaccurate.\n"
        f"📅 *Timestamp:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    response_text = (
        f"Hello! I'm **Danaa** (دانـا). 🇮🇷🇨🇦\n\n"
        f"You asked: \"{user_text}\"\n\n"
        "Currently, I'm in Phase 1 (Foundation). "
        "Soon, I'll be able to search through community history to provide answers!"
        f"{disclaimer}"
    )

    if bot:
        await bot.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode="Markdown"
        )
    else:
        print(f"[LOCAL RUN] Bot Token not found. Bot response would have been:\n{response_text}")
