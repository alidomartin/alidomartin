import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OWNER_NAME: str = os.getenv("OWNER_NAME", "Martin")

_raw_ids = os.getenv("ALLOWED_USER_IDS", "")
ALLOWED_USER_IDS: list[int] = [
    int(uid.strip()) for uid in _raw_ids.split(",") if uid.strip().isdigit()
]

# N1 bot integration (optional cross-bot sync)
N1_BOT_TOKEN: str = os.getenv("N1_BOT_TOKEN", "")
N1_CHAT_ID: str = os.getenv("N1_CHAT_ID", "")

MODEL: str = "claude-opus-4-7"
MAX_TOKENS: int = 8096
MAX_HISTORY: int = 40  # messages to retain per user session
