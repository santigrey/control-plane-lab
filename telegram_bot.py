import asyncio
import logging
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import tempfile, os

import os
from dotenv import dotenv_values as _dv
_env = _dv('/home/jes/control-plane/.env')
BOT_TOKEN = _env.get("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE = "http://localhost:8000"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/telegram_bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    logger.info(f"chat from {user_id}: {text}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/chat",
                json={"message": text, "session_id": f"telegram-{user_id}"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()
                reply = data.get("response") or data.get("message") or str(data)
    except Exception as e:
        logger.error(f"chat error: {e}")
        reply = f"Error contacting Alexandra: {e}"
    await update.message.reply_text(reply)



async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    logger.info(f"voice message from {user_id}")
    tmp_path = out_path = None
    try:
        # Download voice file from Telegram
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
            tmp_path = tmp.name
        await file.download_to_drive(tmp_path)
        logger.info(f"downloaded voice to {tmp_path}, size={os.path.getsize(tmp_path)}")

        async with aiohttp.ClientSession() as session:
            # Step 1: Transcribe
            with open(tmp_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename='voice.ogg', content_type='audio/ogg')
                async with session.post(
                    f"{API_BASE}/voice/transcribe",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    td = await resp.json()
                    text = (td.get('text') or '').strip()
            logger.info(f"transcribed: {text!r}")
            if not text:
                await update.message.reply_text("Sorry, I couldn't make out what you said.")
                return

            # Step 2: Get Alexandra's response
            async with session.post(
                f"{API_BASE}/chat",
                json={"message": text, "session_id": f"telegram-{user_id}"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                cd = await resp.json()
                reply = cd.get("response") or str(cd)
            logger.info(f"reply: {reply[:80]!r}")

            # Step 3: Synthesize voice response
            async with session.post(
                f"{API_BASE}/voice/speak",
                json={"text": reply},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                audio_bytes = await resp.read()

        # Step 4: Send voice reply
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as out:
            out.write(audio_bytes)
            out_path = out.name
        with open(out_path, 'rb') as af:
            await update.message.reply_voice(voice=af)
        logger.info(f"sent voice reply {len(audio_bytes)} bytes")

    except Exception as e:
        logger.error(f"voice error: {e}", exc_info=True)
        await update.message.reply_text(f"Voice error: {e}")
    finally:
        for p in [tmp_path, out_path]:
            try: os.unlink(p)
            except: pass

async def brief_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/brief from {update.effective_user.id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/dashboard/daily_brief",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                reply = data.get("brief") or data.get("text") or data.get("content") or str(data)
    except Exception as e:
        logger.error(f"brief error: {e}")
        reply = f"Error fetching brief: {e}"
    await update.message.reply_text(reply[:4096])


async def tasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/tasks from {update.effective_user.id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/agent",
                json={"prompt": "list all pending_approval tasks"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json()
                reply = data.get("result") or data.get("response") or data.get("output") or str(data)
    except Exception as e:
        logger.error(f"tasks error: {e}")
        reply = f"Error fetching tasks: {e}"
    await update.message.reply_text(reply[:4096])


async def approve_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /approve <task_id>")
        return
    task_id = context.args[0]
    logger.info(f"/approve {task_id} from {update.effective_user.id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/tasks/{task_id}/approve",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                reply = data.get("message") or data.get("status") or f"Task {task_id} approved."
    except Exception as e:
        logger.error(f"approve error: {e}")
        reply = f"Error approving {task_id}: {e}"
    await update.message.reply_text(reply)


async def reject_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /reject <task_id>")
        return
    task_id = context.args[0]
    logger.info(f"/reject {task_id} from {update.effective_user.id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE}/tasks/{task_id}/reject",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                reply = data.get("message") or data.get("status") or f"Task {task_id} rejected."
    except Exception as e:
        logger.error(f"reject error: {e}")
        reply = f"Error rejecting {task_id}: {e}"
    await update.message.reply_text(reply)


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"/status from {update.effective_user.id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/healthz",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                data = await resp.json()
                reply = str(data)
    except Exception as e:
        logger.error(f"status error: {e}")
        reply = f"Error fetching status: {e}"
    await update.message.reply_text(reply)


def main() -> None:
    logger.info("Starting Alexandra Telegram bot")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("brief", brief_handler))
    app.add_handler(CommandHandler("tasks", tasks_handler))
    app.add_handler(CommandHandler("approve", approve_handler))
    app.add_handler(CommandHandler("reject", reject_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
