import os
import re
import asyncio
import logging
import base64
from pathlib import Path
import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from . import brain, config, tools, github_scout

logger = logging.getLogger("JarvisTelegram")

async def transcribe_audio_gemini(audio_bytes: bytes) -> str:
    """Transcribes Telegram voice note (.ogg) using Gemini Multimodal audio processing."""
    api_key = config.get_gemini_key()
    if not api_key or api_key == "your_gemini_api_key_here":
        return ""

    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
    model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}

    payload = {
        "contents": [
            {
                "parts": [
                    {"inline_data": {"mime_type": "audio/ogg", "data": b64_audio}},
                    {
                        "text": "Transcribe the spoken words in this audio note with high accuracy. Output ONLY the raw transcribed text without commentary, timestamps, or quotes."
                    }
                ]
            }
        ],
        "generationConfig": {"temperature": 0.0, "maxOutputTokens": 300}
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text.strip()
            else:
                logger.error(f"Gemini audio transcription error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}")

    return ""

async def capture_mac_screenshot() -> str:
    """Takes a silent Mac screenshot and returns the file path."""
    shot_path = "/tmp/jarvis_mac_screen.png"
    try:
        proc = await asyncio.create_subprocess_exec("screencapture", "-x", shot_path)
        await proc.communicate()
        if os.path.exists(shot_path):
            return shot_path
    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}")
    return ""

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the user and records authorized chat ID."""
    user_name = update.effective_user.first_name or "Sir"
    chat_id = str(update.effective_chat.id)
    config.save_telegram_chat_id(chat_id)

    welcome_msg = (
        f"🎩 *J.A.R.V.I.S. Uplink Active*\n\n"
        f"Greetings, {user_name}. Systems are fully synchronized with your Mac.\n\n"
        f"🎙️ *Voice Notes*: Send me a voice message while working out, walking, or on the go.\n"
        f"💻 *Autonomous Coding*: Ask me to build any Python script or app. I will write it on your Mac, open it in VS Code, and send the file right here to your phone.\n"
        f"📸 *Screen Check*: Type /screen to see what is currently on your Mac's monitor.\n"
        f"🚀 *GitHub Scout*: Type /project or /fikir to get an inspiring open-source project blueprint.\n\n"
        f"How may I serve you today, Sir?"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

async def screen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends current Mac screen snapshot."""
    await update.message.reply_chat_action("upload_photo")
    shot_path = await capture_mac_screenshot()
    if shot_path and os.path.exists(shot_path):
        with open(shot_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption="🖥️ Current Mac Screen, Sir.")
    else:
        await update.message.reply_text("Unable to capture screen display at this moment, Sir.")

async def german_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends current German learning notebook to Telegram."""
    notes_path = Path(__file__).resolve().parent.parent / "german_learning_notes.md"
    if notes_path.exists():
        await update.message.reply_chat_action("upload_document")
        with open(notes_path, "rb") as doc:
            await update.message.reply_document(
                document=doc,
                caption="🇩🇪 **Almanca Çalışma ve İlerleme Defteriniz, Efendim.**"
            )
    else:
        await update.message.reply_text("Almanca not defteriniz henüz bulunamadı efendim.")

async def project_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a curated open-source GitHub project blueprint to Telegram."""
    await update.message.reply_chat_action("typing")
    idea = await github_scout.get_daily_project_idea()
    await update.message.reply_text(idea["markdown"], parse_mode="Markdown")

async def process_and_reply(update: Update, user_text: str):
    """Central processor for text and voice commands."""
    await update.message.reply_chat_action("typing")
    config.save_telegram_chat_id(str(update.effective_chat.id))

    # German notebook file request in natural language
    if any(k in user_text.lower() for k in ["almanca notlarımı gönder", "almanca dosyamı at", "almanca defterimi gönder"]):
        await german_command(update, context=None)
        return

    # Screenshot trigger in text
    if any(k in user_text.lower() for k in ["ekran görüntüsü", "screenshot", "ekranı göster", "show screen"]):
        shot_path = await capture_mac_screenshot()
        if shot_path and os.path.exists(shot_path):
            with open(shot_path, "rb") as photo:
                await update.message.reply_photo(photo=photo, caption="🖥️ Mac Desktop View, Sir.")
            return

    # Track files on Desktop & Shorts folder before running query
    desktop = Path(os.path.expanduser("~/Desktop"))
    shorts_dir = desktop / "Jarvis_Shorts"
    before_files = set(desktop.glob("*.py"))
    before_videos = (set(shorts_dir.glob("*.mp4")) | set(shorts_dir.glob("*.mov")) | set(desktop.glob("*.mp4"))) if shorts_dir.exists() else set()
    before_images = set(desktop.glob("*.png")) | set(desktop.glob("*.jpg")) | set(desktop.glob("*.jpeg")) | set(desktop.glob("*.webp"))

    # Process query through Jarvis brain
    jarvis_response = await brain.process_user_query(user_text)

    # Check if a new Python script was created on Desktop
    after_files = set(desktop.glob("*.py"))
    new_scripts = list(after_files - before_files)

    # Check if a new Shorts video was generated
    after_videos = (set(shorts_dir.glob("*.mp4")) | set(shorts_dir.glob("*.mov")) | set(desktop.glob("*.mp4"))) if shorts_dir.exists() else set()
    new_videos = list(after_videos - before_videos)

    # Check if a new image was generated on Desktop
    after_images = set(desktop.glob("*.png")) | set(desktop.glob("*.jpg")) | set(desktop.glob("*.jpeg")) | set(desktop.glob("*.webp"))
    new_images = list(after_images - before_images)

    # 1. Reply with Jarvis message (cleaning any SSML tags for clean text)
    clean_reply = re.sub(r'</?(?:lang|speak|voice|prosody)[^>]*>', '', jarvis_response).strip()
    await update.message.reply_text(f"🤖 *Jarvis:* {clean_reply}", parse_mode="Markdown")

    # 2. If a script was engineered, send the actual .py file to the user's phone!
    if new_scripts:
        created_file = max(new_scripts, key=lambda p: p.stat().st_mtime)
        await update.message.reply_chat_action("upload_document")
        with open(created_file, "rb") as doc:
            await update.message.reply_document(
                document=doc,
                caption=f"📄 *{created_file.name}*\nGenerated and saved to your Mac Desktop."
            )

    # 3. If an image/photo was generated, send it directly to phone!
    if new_images:
        created_img = max(new_images, key=lambda p: p.stat().st_mtime)
        await update.message.reply_chat_action("upload_photo")
        with open(created_img, "rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=f"📸 *{created_img.name}*\nGörüntü hazırlandı ve telefonunuza aktarıldı, Efendim!"
            )

    # 4. If a Shorts/Reels video was created, send the .mp4 file directly to phone!
    if new_videos:
        created_video = max(new_videos, key=lambda p: p.stat().st_mtime)
        vid_size = created_video.stat().st_size
        await update.message.reply_chat_action("upload_video")
        if vid_size < 49 * 1024 * 1024:
            with open(created_video, "rb") as vid:
                await update.message.reply_video(
                    video=vid,
                    caption=f"🎬 *{created_video.name}*\n9:16 Full-Screen TikTok/Shorts formatı hazır, Efendim!",
                    supports_streaming=True
                )
        else:
            with open(created_video, "rb") as doc:
                await update.message.reply_document(
                    document=doc,
                    caption=f"🎬 *{created_video.name}* ({round(vid_size/(1024*1024), 1)} MB)\nDosya boyutu yüksek olduğu için doküman olarak iletildi."
                )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming text messages."""
    text = update.message.text
    if not text:
        return
    logger.info(f"[TELEGRAM TEXT]: {text}")
    await process_and_reply(update, text)

async def handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming voice notes."""
    voice = update.message.voice or update.message.audio
    if not voice:
        return

    await update.message.reply_chat_action("record_voice")
    file_obj = await voice.get_file()
    audio_bytes = await file_obj.download_as_bytearray()

    # Transcribe voice note
    transcribed = await transcribe_audio_gemini(bytes(audio_bytes))
    if not transcribed:
        await update.message.reply_text("I heard your voice note, Sir, but could not discern the speech clearly. Please try again.")
        return

    logger.info(f"[TELEGRAM VOICE TRANSCRIBED]: {transcribed}")
    await update.message.reply_text(f"🎙️ *Heard:* \"{transcribed}\"", parse_mode="Markdown")

    # Process query
    await process_and_reply(update, transcribed)

async def run_telegram_bot():
    """Starts the Telegram bot long-polling in the background."""
    token = config.get_telegram_token()
    if not token or token == "your_telegram_bot_token_here":
        logger.info("ℹ️ Telegram bot token not configured in .env. Skipping Telegram uplink.")
        return

    logger.info("🤖 Starting Telegram Jarvis Bot...")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("screen", screen_command))
    app.add_handler(CommandHandler("german", german_command))
    app.add_handler(CommandHandler("project", project_command))
    app.add_handler(CommandHandler("fikir", project_command))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice_message))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    logger.info("✅ Telegram Jarvis Bot is now listening for messages and voice notes!")
    
    while True:
        await asyncio.sleep(3600)
