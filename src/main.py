import os
from fastapi import FastAPI, Request
from telegram import Update
from src.bot import handle_message

app = FastAPI(title="Danaa Bot API")

@app.get("/")
async def root():
    return {"message": "Danaa Bot is running! 🇮🇷🇨🇦"}

@app.post("/webhook")
async def webhook(request: Request):
    """
    Endpoint for Telegram Webhooks.
    """
    data = await request.json()
    update = Update.de_json(data, None)
    await handle_message(update)
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
