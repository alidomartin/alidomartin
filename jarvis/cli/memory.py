from datetime import datetime
from pathlib import Path


class Memory:
    def __init__(self, vault_root: Path, max_recent_chars: int = 4000):
        self.root = vault_root / "06-MEMORY"
        self.conversations = self.root / "conversations"
        self.preferences = self.root / "preferences.md"
        self.conversations.mkdir(parents=True, exist_ok=True)
        self.max_recent_chars = max_recent_chars

    def _today_log(self) -> Path:
        return self.conversations / f"{datetime.now():%Y-%m-%d}.md"

    def log(self, role: str, text: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        log = self._today_log()
        if not log.exists():
            log.write_text(f"# Conversation log {datetime.now():%Y-%m-%d}\n")
        with log.open("a") as f:
            f.write(f"\n**{role}** ({ts}):\n{text}\n")

    def recent_summary(self) -> str:
        prefs = (
            self.preferences.read_text()
            if self.preferences.exists()
            else "(no preferences set)"
        )
        recent = ""
        logs = sorted(self.conversations.glob("*.md"), reverse=True)[:2]
        if logs:
            combined = "\n\n".join(p.read_text() for p in logs)
            recent = combined[-self.max_recent_chars :]
        return (
            f"### Preferences\n{prefs}\n\n"
            f"### Recent conversation\n{recent or '(no prior conversations)'}"
        )
