"""
Telegram handlers for Jarvis.

Commands:
  /start   — Initialize session
  /help    — Command reference
  /status  — HUD system status
  /clear   — Wipe conversation memory
  /mode    — Switch operational mode
  /voice   — Toggle voice responses on/off
  /briefing — Request a Jarvis daily briefing

Messages: text + voice notes both handled.
"""

import io
import logging
from datetime import datetime

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from ai import JarvisAI
from config import OWNER_NAME, ALLOWED_USER_IDS, N1_BOT_TOKEN, N1_CHAT_ID
import voice as voice_module

logger = logging.getLogger(__name__)

jarvis = JarvisAI()

VALID_MODES = {"standard", "research", "tactical", "analysis"}

MODE_DESC = {
    "STANDARD": "Balanced, comprehensive assistance for any task.",
    "RESEARCH": "Deep analytical focus — thorough exploration, maximum context.",
    "TACTICAL": "Rapid decisive output — bullets, speed, no preamble.",
    "ANALYSIS": "Structured data output — quantitative, systematic breakdowns.",
}

GREETING = {
    range(5, 12): "morning",
    range(12, 18): "afternoon",
    range(18, 24): "evening",
    range(0, 5): "evening",
}


def _time_of_day() -> str:
    h = datetime.now().hour
    for r, label in GREETING.items():
        if h in r:
            return label
    return "day"


# ── Authorization ──────────────────────────────────────────────────────────────

def _is_authorized(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True  # open if no IDs configured
    return user_id in ALLOWED_USER_IDS


async def _deny(update: Update) -> None:
    await update.message.reply_text(
        "Access denied. I serve only Mr. Martin. "
        "You are not authorised to operate this system."
    )


# ── N1 Bot bridge ──────────────────────────────────────────────────────────────

async def _notify_n1(text: str) -> None:
    """Forward a message to N1 bot if configured."""
    if not N1_BOT_TOKEN or not N1_CHAT_ID:
        return
    try:
        from telegram import Bot
        bot = Bot(token=N1_BOT_TOKEN)
        await bot.send_message(chat_id=N1_CHAT_ID, text=text)
    except Exception as exc:
        logger.warning("N1 bot notification failed: %s", exc)


# ── Helper: send long reply in chunks ─────────────────────────────────────────

async def _send_text(update: Update, text: str) -> None:
    if len(text) <= 4096:
        await update.message.reply_text(text)
    else:
        for i in range(0, len(text), 4096):
            await update.message.reply_text(text[i : i + 4096])


async def _send_voice_reply(update: Update, text: str) -> None:
    clean = voice_module.strip_markdown(text)
    ogg = voice_module.synthesize(clean)
    if ogg:
        await update.message.reply_voice(voice=io.BytesIO(ogg), filename="jarvis.ogg")
    else:
        # Fallback to text if TTS fails
        await _send_text(update, text)


# ── Commands ───────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    user_id = update.effective_user.id
    jarvis.clear(user_id)

    msg = (
        f"*J.A.R.V.I.S. ONLINE*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Good {_time_of_day()}, Mr. {OWNER_NAME}.\n\n"
        f"All systems are operational and standing by.\n"
        f"_Just A Rather Very Intelligent System — at your service._\n\n"
        f"Send me any message or voice note to begin.\n"
        f"Type /help for the full command reference."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    msg = (
        "*J.A.R.V.I.S. COMMAND INTERFACE*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Session Commands:*\n"
        "/start — Initialise new session\n"
        "/status — Live system status report\n"
        "/clear — Wipe conversation memory\n"
        "/briefing — Request a strategic daily briefing\n\n"
        "*Mode Commands:*\n"
        "/mode — Show / change operational mode\n"
        "`/mode standard` — Balanced assistance _(default)_\n"
        "`/mode research` — Deep analytical focus\n"
        "`/mode tactical` — Rapid decisive responses\n"
        "`/mode analysis` — Structured data outputs\n\n"
        "*Voice Commands:*\n"
        "/voice — Toggle voice responses on / off\n"
        "🎙 _Send a voice note_ — Jarvis will transcribe and respond\n\n"
        "/help — This reference\n\n"
        "_Speak or type freely, Mr. Martin — I am always listening._"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    user_id = update.effective_user.id
    now = datetime.now()
    depth = jarvis.session_depth(user_id)
    mode = jarvis.get_mode(user_id)
    v_mode = "ON" if jarvis.is_voice_mode(user_id) else "OFF"
    n1_status = "LINKED" if N1_BOT_TOKEN else "OFFLINE"

    msg = (
        "⚡ *J.A.R.V.I.S. SYSTEM STATUS*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 `AI Core:           ONLINE`\n"
        "🟢 `Knowledge Base:    ACTIVE`\n"
        "🟢 `Response Matrix:   NOMINAL`\n"
        "🟢 `Security Layer:    ENGAGED`\n"
        f"{'🟢' if N1_BOT_TOKEN else '🔴'} `N1 Bot Bridge:    {n1_status}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 `Date:     {now.strftime('%a, %b %d %Y')}`\n"
        f"🕐 `Time:     {now.strftime('%H:%M:%S')}`\n"
        f"⚙️  `Mode:     {mode}`\n"
        f"🔊 `Voice:    {v_mode}`\n"
        f"💬 `Session:  {depth} exchange{'s' if depth != 1 else ''}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"_All systems nominal, Mr. {OWNER_NAME}._"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    jarvis.clear(update.effective_user.id)
    await update.message.reply_text(
        f"Memory cleared, Mr. {OWNER_NAME}. Starting with a clean slate.",
    )


async def cmd_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    user_id = update.effective_user.id
    args = ctx.args or []

    if not args or args[0].lower() not in VALID_MODES:
        current = jarvis.get_mode(user_id)
        msg = (
            f"*Current mode:* `{current}`\n\n"
            "*Available modes:*\n"
            "`standard` — Balanced assistance\n"
            "`research` — Deep analytical focus\n"
            "`tactical` — Rapid decisive responses\n"
            "`analysis` — Structured data outputs\n\n"
            "_Usage:_ `/mode <mode_name>`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    new_mode = args[0].upper()
    jarvis.set_mode(user_id, new_mode)
    desc = MODE_DESC.get(new_mode, "")
    await update.message.reply_text(
        f"⚙️ Mode switched to *{new_mode}*.\n_{desc}_",
        parse_mode="Markdown",
    )


async def cmd_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    user_id = update.effective_user.id
    is_on = jarvis.toggle_voice_mode(user_id)
    status = "enabled" if is_on else "disabled"
    emoji = "🔊" if is_on else "🔇"
    await update.message.reply_text(
        f"{emoji} Voice responses *{status}*, Mr. {OWNER_NAME}.",
        parse_mode="Markdown",
    )


async def cmd_briefing(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not _is_authorized(update.effective_user.id):
        await _deny(update)
        return

    user_id = update.effective_user.id
    await update.message.chat.send_action(ChatAction.TYPING)

    prompt = (
        f"Please deliver a morning briefing for Mr. {OWNER_NAME}. "
        "Include: current date and day of week, a motivational situational framing, "
        "three strategic priorities for today based on our recent conversation context "
        "(or general high-impact recommendations if no prior context), "
        "and a closing statement. Keep it sharp and energising — JARVIS style."
    )

    try:
        reply = await jarvis.respond(user_id, prompt)
        await _send_text(update, reply)

        if jarvis.is_voice_mode(user_id):
            await update.message.chat.send_action(ChatAction.RECORD_VOICE)
            await _send_voice_reply(update, reply)

        await _notify_n1(f"[JARVIS BRIEFING]\n{reply}")

    except Exception as exc:
        logger.error("Briefing error: %s", exc)
        await update.message.reply_text(
            f"Apologies, Mr. {OWNER_NAME} — briefing system encountered an error: `{type(exc).__name__}`",
            parse_mode="Markdown",
        )


# ── Text message handler ───────────────────────────────────────────────────────

async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await _deny(update)
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        reply = await jarvis.respond(user_id, update.message.text, is_voice=False)
        await _send_text(update, reply)

        if jarvis.is_voice_mode(user_id):
            await update.message.chat.send_action(ChatAction.RECORD_VOICE)
            await _send_voice_reply(update, reply)

    except Exception as exc:
        logger.error("Text handler error: %s", exc)
        await update.message.reply_text(
            f"I apologise, Mr. {OWNER_NAME} — system error: `{type(exc).__name__}`. "
            "Please try again in a moment.",
            parse_mode="Markdown",
        )


# ── Voice message handler ──────────────────────────────────────────────────────

async def handle_voice(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return

    user_id = update.effective_user.id
    if not _is_authorized(user_id):
        await _deny(update)
        return

    await update.message.chat.send_action(ChatAction.TYPING)

    # Download the voice file
    try:
        voice_file = await update.message.voice.get_file()
        ogg_bytes = await voice_file.download_as_bytearray()
    except Exception as exc:
        logger.error("Voice download error: %s", exc)
        await update.message.reply_text(
            f"I was unable to receive your voice message, Mr. {OWNER_NAME}. "
            "Please try again."
        )
        return

    # Transcribe
    transcription = voice_module.transcribe(bytes(ogg_bytes))

    if not transcription:
        await update.message.reply_text(
            f"I'm sorry, Mr. {OWNER_NAME} — I could not transcribe that audio. "
            "Please try speaking more clearly or type your request."
        )
        return

    # Acknowledge with transcription
    await update.message.reply_text(
        f"_Transcribed: \"{transcription}\"_",
        parse_mode="Markdown",
    )

    await update.message.chat.send_action(ChatAction.TYPING)

    # Get Jarvis response
    try:
        reply = await jarvis.respond(user_id, transcription, is_voice=True)
        await _send_text(update, reply)

        # Voice response — always reply with voice when prompted by voice
        await update.message.chat.send_action(ChatAction.RECORD_VOICE)
        await _send_voice_reply(update, reply)

    except Exception as exc:
        logger.error("Voice response error: %s", exc)
        await update.message.reply_text(
            f"Apologies, Mr. {OWNER_NAME} — I encountered an error processing your request.",
        )
