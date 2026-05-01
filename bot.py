#!/usr/bin/env python3
"""Telegram userbot for CMJ Force-Time Curve phase guide (MTProto via Telethon)."""

import os
import logging
from pathlib import Path
from telethon import TelegramClient, events
from telethon.tl.types import InputMessagesFilterEmpty

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
            "**Quiet Phase**\n\n"
            "The first phase of the CMJ. The athlete stands still for at least "
            "**1 second** before movement begins. During this period **system weight** "
            "(body weight in Newtons) is calculated.\n\n"
            "Cue the athlete to stand still to keep the validity of the weighing period high."
        ),
    },
    "unweighting": {
        "name": "Unweighting Phase",
        "image": "unweighting_phase.png",
        "description": (
            "**Unweighting Phase**\n\n"
            "The athlete begins the countermovement by **relaxing the agonist muscles**, "
            "resulting in combined flexion of the hips and knees. Force drops **below "
            "system weight** — the athlete is essentially in free fall.\n\n"
            "Defined by a **negative velocity** that is continuing to descend."
        ),
    },
    "braking": {
        "name": "Braking Phase",
        "image": "braking_phase.png",
        "description": (
            "**Braking Phase**\n\n"
            "The athlete decelerates their **center-of-mass (COM)**. Braking begins when "
            "COM velocity is still negative but ascending toward **0 m/s**.\n\n"
            "Commences from **peak negative COM velocity** through to when COM velocity "
            "increases to zero."
        ),
    },
    "transfer": {
        "name": "Transfer Point",
        "image": "transfer_point.png",
        "description": (
            "**Transfer Point**\n\n"
            "Also called the **switch phase**, this occurs between braking and propulsive "
            "phases — the brief **isometric portion** when velocity is zero.\n\n"
            "An athlete who spends **less time at the bottom** of the 'V' is more efficient "
            "at transferring momentum."
        ),
    },
    "propulsive": {
        "name": "Propulsive Phase",
        "image": "propulsive_phase.png",
        "description": (
            "**Propulsive Phase**\n\n"
            "The athlete forcefully extends hips, knees, and ankles to **propel their COM "
            "vertically**. Begins when a **positive COM velocity** is achieved (threshold: 0.01 m/s).\n\n"
            "Key metrics: average/peak relative propulsive force and average/peak propulsive "
            "power (**PRPP**). If an athlete struggles here, Cleans, Trap Bar Jumps, or "
            "Pin Squats may help."
        ),
    },
    "flight": {
        "name": "Flight Phase",
        "image": "flight_phase.png",
        "description": (
            "**Flight Phase**\n\n"
            "The athlete leaves the force plates from **take-off** until **touchdown**. "
            "Flight time is the outcome of every muscle action and generation of momentum.\n\n"
            "Note: **Jump Height is calculated using takeoff velocity** (industry gold standard), "
            "not flight time."
        ),
    },
    "landing": {
        "name": "Landing Phase",
        "image": "landing_phase.png",
        "description": (
            "**Landing Phase**\n\n"
            "The final CMJ phase. Begins when the athlete **contacts the force plate** after "
            "the flight phase. The athlete applies a net impulse equal to the propulsion "
            "impulse to decelerate COM to zero.\n\n"
            "Bilateral force plates can show discrepancies between limbs — key for "
            "**return-to-play** and **injury risk** assessment."
        ),
    },
    "loading": {
        "name": "Landing Phase 1: Loading",
        "image": "loading_phase.png",
        "description": (
            "**Landing Phase 1: Loading**\n\n"
            "From **initial contact** to **peak GRF**. The loading rate and peak force reflect "
            "how rapidly and forcefully the athlete accepts ground contact.\n\n"
            "A higher loading rate can increase injury risk.\n"
            "Key metrics: **Peak GRF**, **Loading Rate**, **v at contact**."
        ),
    },
    "attenuation": {
        "name": "Landing Phase 2: Attenuation",
        "image": "attenuation_phase.png",
        "description": (
            "**Landing Phase 2: Attenuation**\n\n"
            "From **peak GRF** to the **local minimum**. The athlete is absorbing and "
            "attenuating the impact force.\n\n"
            "The force attenuation rate and average force indicate how efficiently the "
            "athlete disperses impact energy through eccentric muscle action."
        ),
    },
    "control": {
        "name": "Landing Phase 3: Control",
        "image": "control_phase.png",
        "description": (
            "**Landing Phase 3: Control**\n\n"
            "From the **local minimum** to when **COM velocity = 0** (COM stops). "
            "This brief phase reflects the athlete's ability to stabilize after "
            "the main impact is absorbed.\n\n"
            "Key metrics: **Control Time**, **mRSI**, **LPI**. Shorter control time = greater efficiency."
        ),
    },
}

JUMP_PHASES = ["quiet", "unweighting", "braking", "transfer", "propulsive", "flight", "landing"]
LANDING_PHASES = ["loading", "attenuation", "control"]

HELP_TEXT = (
    "**CMJ Phase Guide — Commands**\n\n"
    "`.phases` — list all jump phases\n"
    "`.landing` — list all landing sub-phases\n"
    "`.phase <name>` — details + image for a phase\n\n"
    "**Phase names:** quiet, unweighting, braking, transfer, propulsive, flight, "
    "landing, loading, attenuation, control"
)


def _get_client() -> TelegramClient:
    api_id = os.environ.get("TELEGRAM_API_ID")
    api_hash = os.environ.get("TELEGRAM_API_HASH")
    if not api_id or not api_hash:
        raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set.")
    return TelegramClient("cmj_session", int(api_id), api_hash)


client = _get_client()


@client.on(events.NewMessage(pattern=r"^\.start$"))
async def cmd_start(event):
    await event.respond(
        "**CMJ Force-Time Curve Guide**\n\n"
        "Use `.help` to see available commands."
    )


@client.on(events.NewMessage(pattern=r"^\.help$"))
async def cmd_help(event):
    await event.respond(HELP_TEXT)


@client.on(events.NewMessage(pattern=r"^\.phases$"))
async def cmd_phases(event):
    lines = "\n".join(f"• `{k}` — {PHASES[k]['name']}" for k in JUMP_PHASES)
    await event.respond(f"**Jump Phases**\n\n{lines}\n\nUse `.phase <name>` for details.")


@client.on(events.NewMessage(pattern=r"^\.landing$"))
async def cmd_landing(event):
    lines = "\n".join(f"• `{k}` — {PHASES[k]['name']}" for k in LANDING_PHASES)
    await event.respond(f"**Landing Sub-Phases**\n\n{lines}\n\nUse `.phase <name>` for details.")


@client.on(events.NewMessage(pattern=r"^\.phase (.+)$"))
async def cmd_phase(event):
    key = event.pattern_match.group(1).strip().lower()
    if key not in PHASES:
        await event.respond(
            f"Unknown phase `{key}`.\n\nUse `.help` for a list of phase names."
        )
        return

    phase = PHASES[key]
    image_path = IMAGES_DIR / phase["image"]

    if image_path.exists():
        await client.send_file(
            event.chat_id,
            str(image_path),
            caption=phase["description"],
        )
    else:
        await event.respond(phase["description"])


def main() -> None:
    phone = os.environ.get("TELEGRAM_PHONE")
    if not phone:
        raise RuntimeError("TELEGRAM_PHONE must be set.")

    logger.info("Connecting...")
    with client:
        client.start(phone=phone)
        logger.info("Userbot running. Listening for commands (.start, .help, .phases, .phase <name>)")
        client.run_until_disconnected()


if __name__ == "__main__":
    main()
