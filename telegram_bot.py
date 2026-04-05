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
GATE_API_BASE = "http://127.0.0.1:8002"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("/tmp/telegram_bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


# --- IoT Approval Gate helpers ---

async def _gate_post(endpoint: str, payload: dict) -> dict:
    """POST to the approval gate HTTP API."""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{GATE_API_BASE}{endpoint}",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            return await resp.json()


# --- Handlers ---

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


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    caption = update.message.caption or "What's in this image?"
    logger.info(f"photo from {user_id}, caption: {caption!r}")
    tmp_path = None
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
        await file.download_to_drive(tmp_path)
        logger.info(f"downloaded photo to {tmp_path}, size={os.path.getsize(tmp_path)}")
        async with aiohttp.ClientSession() as session:
            with open(tmp_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename='photo.jpg', content_type='image/jpeg')
                form.add_field('prompt', f'Extract all details from this image. The user says: {caption}')
                async with session.post(
                    f"{API_BASE}/vision/analyze",
                    data=form,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    vd = await resp.json()
                    vision_text = vd.get('response') or vd.get('text') or vd.get('description') or str(vd)
            logger.info(f"vision result: {vision_text[:120]!r}")
            combined = (
                f"The user sent a photo. Here's what the image shows: {vision_text}\n\n"
                f"The user asked: {caption}\n\n"
                "Use your tools to fulfill the request."
            )
            async with session.post(
                f"{API_BASE}/chat",
                json={"message": combined, "session_id": f"telegram-{user_id}"},
                timeout=aiohttp.ClientTimeout(total=90),
            ) as resp:
                cd = await resp.json()
                reply = cd.get("response") or cd.get("message") or str(cd)
            logger.info(f"chat reply: {reply[:120]!r}")
    except Exception as e:
        logger.error(f"photo error: {e}", exc_info=True)
        reply = f"Error processing photo: {e}"
    finally:
        if tmp_path:
            try: os.unlink(tmp_path)
            except: pass
    await update.message.reply_text(reply[:4096])

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
        await update.message.reply_text("Usage: /approve <task_id or request_id>")
        return
    target_id = context.args[0]
    user_id = update.effective_user.id
    logger.info(f"/approve {target_id} from {user_id}")

    # Route: if request_id starts with 'req_' -> IoT approval gate
    if target_id.startswith('req_'):
        try:
            data = await _gate_post('/approve', {
                'request_id': target_id,
                'user_id': user_id,
            })
            status = data.get('status', 'unknown')
            action = data.get('action', '')
            entity = data.get('entity_id', '')
            if status == 'approved':
                reply = f"APPROVED: {action} on {entity}\nRequest {target_id} executed."
            else:
                reply = f"Gate response: {data}"
        except Exception as e:
            logger.error(f"gate approve error: {e}")
            reply = f"Error approving via gate: {e}"
    else:
        # Original orchestrator task approval
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_BASE}/tasks/{target_id}/approve",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    data = await resp.json()
                    reply = data.get("message") or data.get("status") or f"Task {target_id} approved."
        except Exception as e:
            logger.error(f"approve error: {e}")
            reply = f"Error approving {target_id}: {e}"
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


async def deny_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deny a Tier 3 IoT approval request via the approval gate."""
    if not context.args:
        await update.message.reply_text("Usage: /deny <request_id>")
        return
    request_id = context.args[0]
    user_id = update.effective_user.id
    logger.info(f"/deny {request_id} from {user_id}")
    try:
        data = await _gate_post('/deny', {
            'request_id': request_id,
            'user_id': user_id,
        })
        status = data.get('status', 'unknown')
        action = data.get('action', '')
        entity = data.get('entity_id', '')
        if status == 'denied':
            reply = f"DENIED: {action} on {entity}\nRequest {request_id} rejected."
        else:
            reply = f"Gate response: {data}"
    except Exception as e:
        logger.error(f"gate deny error: {e}")
        reply = f"Error denying via gate: {e}"
    await update.message.reply_text(reply)


async def blackout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activate camera blackout via the approval gate."""
    user_id = update.effective_user.id
    logger.info(f"/blackout from {user_id}")
    try:
        data = await _gate_post('/blackout', {'user_id': user_id})
        if data.get('camera_blackout'):
            reply = "CAMERA BLACKOUT ACTIVATED\nAll camera access disabled for Alexandra.\nSend /cameras_on to restore."
        else:
            reply = f"Gate response: {data}"
    except Exception as e:
        logger.error(f"blackout error: {e}")
        reply = f"Error activating blackout: {e}"
    await update.message.reply_text(reply)


async def cameras_on_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restore camera access via the approval gate."""
    user_id = update.effective_user.id
    logger.info(f"/cameras_on from {user_id}")
    try:
        data = await _gate_post('/cameras_on', {'user_id': user_id})
        if not data.get('camera_blackout', True):
            reply = "Camera access restored for Alexandra."
        else:
            reply = f"Gate response: {data}"
    except Exception as e:
        logger.error(f"cameras_on error: {e}")
        reply = f"Error restoring cameras: {e}"
    await update.message.reply_text(reply)


async def gate_status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show approval gate status and pending requests."""
    user_id = update.effective_user.id
    logger.info(f"/gate from {user_id}")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GATE_API_BASE}/healthz",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                health = await resp.json()
            async with session.get(
                f"{GATE_API_BASE}/pending",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                pending = await resp.json()

        lines = [
            f"Approval Gate: {health.get('status', '?')}",
            f"Camera Blackout: {'YES' if health.get('camera_blackout') else 'No'}",
            f"Pending Approvals: {pending.get('count', 0)}",
        ]
        for rid, info in pending.get('pending', {}).items():
            lines.append(f"  {rid}: {info.get('action')} on {info.get('entity_id')}")
        reply = '\n'.join(lines)
    except Exception as e:
        logger.error(f"gate status error: {e}")
        reply = f"Error checking gate: {e}"
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
    app.add_handler(CommandHandler("deny", deny_handler))
    app.add_handler(CommandHandler("blackout", blackout_handler))
    app.add_handler(CommandHandler("cameras_on", cameras_on_handler))
    app.add_handler(CommandHandler("gate", gate_status_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(MessageHandler(filters.VOICE, voice_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
