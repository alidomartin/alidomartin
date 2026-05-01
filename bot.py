#!/usr/bin/env python3
"""Telegram bot for CMJ Force-Time Curve phase guide."""

import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent / "images"

PHASES = {
    "quiet": {
        "name": "Quiet Phase",
        "image": "quiet_phase.png",
        "description": (
            "The first phase of the CMJ. The athlete stands still for at least "
            "*1 second* before movement begins. During this period *system weight* "
            "(body weight in Newtons) is calculated.\n\n"
            "Cue the athlete to stand still to keep the validity of the weighing period high."
        ),
    },
    "unweighting": {
        "name": "Unweighting Phase",
        "image": "unweighting_phase.png",
        "description": (
            "The athlete begins the countermovement by *relaxing the agonist muscles*, "
            "resulting in combined flexion of the hips and knees. Force drops *below "
            "system weight* — the athlete is essentially in free fall.\n\n"
            "Defined by a *negative velocity* that is continuing to descend."
        ),
    },
    "braking": {
        "name": "Braking Phase",
        "image": "braking_phase.png",
        "description": (
            "The athlete decelerates their *center-of-mass (COM)*. Braking begins when "
            "COM velocity is still negative but ascending toward *0 m/s*.\n\n"
            "Commences from *peak negative COM velocity* through to when COM velocity "
            "increases to zero."
        ),
    },
    "transfer": {
        "name": "Transfer Point",
        "image": "transfer_point.png",
        "description": (
            "Also called the *switch phase*, this occurs between braking and propulsive "
            "phases — the brief *isometric portion* when velocity is zero.\n\n"
            "An athlete who spends *less time at the bottom* of the 'V' is more efficient "
            "at transferring momentum."
        ),
    },
    "propulsive": {
        "name": "Propulsive Phase",
        "image": "propulsive_phase.png",
        "description": (
            "The athlete forcefully extends hips, knees, and ankles to *propel their COM "
            "vertically*. Begins when a *positive COM velocity* is achieved (threshold: 0.01 m/s).\n\n"
            "Key metrics: average/peak relative propulsive force and average/peak propulsive "
            "power (*PRPP*). If an athlete struggles here, Cleans, Trap Bar Jumps, or "
            "Pin Squats may help."
        ),
    },
    "flight": {
        "name": "Flight Phase",
        "image": "flight_phase.png",
        "description": (
            "The athlete leaves the force plates from *take-off* until *touchdown*. "
            "Flight time is the outcome of every muscle action and generation of momentum.\n\n"
            "Note: *Jump Height is calculated using takeoff velocity* (industry gold standard), "
            "not flight time."
        ),
    },
    "landing": {
        "name": "Landing Phase",
        "image": "landing_phase.png",
        "description": (
            "The final CMJ phase. Begins when the athlete *contacts the force plate* after "
            "the flight phase. The athlete applies a net impulse equal to the propulsion "
            "impulse to decelerate COM to zero.\n\n"
            "Bilateral force plates can show discrepancies between limbs — key for "
            "*return-to-play* and *injury risk* assessment."
        ),
    },
    "loading": {
        "name": "Landing Phase 1: Loading",
        "image": "loading_phase.png",
        "description": (
            "From *initial contact* to *peak GRF*. The loading rate and peak force reflect "
            "how rapidly and forcefully the athlete accepts ground contact.\n\n"
            "A higher loading rate can increase injury risk.\n"
            "Key metrics: *Peak GRF*, *Loading Rate*, *v at contact*."
        ),
    },
    "attenuation": {
        "name": "Landing Phase 2: Attenuation",
        "image": "attenuation_phase.png",
        "description": (
            "From *peak GRF* to the *local minimum*. The athlete is absorbing and "
            "attenuating the impact force.\n\n"
            "The force attenuation rate and average force indicate how efficiently the "
            "athlete disperses impact energy through eccentric muscle action."
        ),
    },
    "control": {
        "name": "Landing Phase 3: Control",
        "image": "control_phase.png",
        "description": (
            "From the *local minimum* to when *COM velocity = 0* (COM stops). "
            "This brief phase reflects the athlete's ability to stabilize after "
            "the main impact is absorbed.\n\n"
            "Key metrics: *Control Time*, *mRSI*, *LPI*. Shorter control time = greater efficiency."
        ),
    },
}

JUMP_PHASES = ["quiet", "unweighting", "braking", "transfer", "propulsive", "flight", "landing"]
LANDING_PHASES = ["loading", "attenuation", "control"]


def _phase_keyboard(group: str = "jump") -> InlineKeyboardMarkup:
    keys = JUMP_PHASES if group == "jump" else LANDING_PHASES
    buttons = [[InlineKeyboardButton(PHASES[k]["name"], callback_data=f"phase:{k}")] for k in keys]
    if group == "jump":
        buttons.append([InlineKeyboardButton("Landing sub-phases ▶", callback_data="group:landing")])
    else:
        buttons.append([InlineKeyboardButton("◀ Jump phases", callback_data="group:jump")])
    return InlineKeyboardMarkup(buttons)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to the *CMJ Force-Time Curve Guide* bot!\n\n"
        "Use /phases to browse all phases interactively, or /help to see all commands.",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Available commands:*\n\n"
        "/phases — Browse all CMJ phases interactively\n"
        "/phase <name> — Get info on a specific phase\n"
        "    e.g. `/phase braking`, `/phase loading`\n\n"
        "*Phase names:* quiet, unweighting, braking, transfer, propulsive, flight, "
        "landing, loading, attenuation, control",
        parse_mode="Markdown",
    )


async def phases_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Select a *CMJ phase* to learn more:",
        parse_mode="Markdown",
        reply_markup=_phase_keyboard("jump"),
    )


async def phase_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /phase <name>\nTry /help for a list of phase names.")
        return

    key = context.args[0].lower()
    if key not in PHASES:
        await update.message.reply_text(
            f"Unknown phase '{key}'.\nTry /help for a list of phase names."
        )
        return

    await _send_phase(update.message.reply_photo, key)


async def _send_phase(reply_fn, key: str) -> None:
    phase = PHASES[key]
    image_path = IMAGES_DIR / phase["image"]
    caption = f"*{phase['name']}*\n\n{phase['description']}"

    if image_path.exists():
        with open(image_path, "rb") as img:
            await reply_fn(photo=img, caption=caption, parse_mode="Markdown")
    else:
        # Fall back to text if image is missing
        logger.warning("Image not found: %s", image_path)
        await reply_fn.__self__.reply_text(caption, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("group:"):
        group = data.split(":", 1)[1]
        await query.edit_message_text(
            "Select a *CMJ phase* to learn more:",
            parse_mode="Markdown",
            reply_markup=_phase_keyboard(group),
        )
    elif data.startswith("phase:"):
        key = data.split(":", 1)[1]
        phase = PHASES[key]
        image_path = IMAGES_DIR / phase["image"]
        caption = f"*{phase['name']}*\n\n{phase['description']}"

        if image_path.exists():
            with open(image_path, "rb") as img:
                await query.message.reply_photo(photo=img, caption=caption, parse_mode="Markdown")
        else:
            await query.message.reply_text(caption, parse_mode="Markdown")


def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("phases", phases_command))
    app.add_handler(CommandHandler("phase", phase_command))
    app.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
