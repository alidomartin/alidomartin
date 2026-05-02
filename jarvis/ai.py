import anthropic
from datetime import datetime
from config import ANTHROPIC_API_KEY, OWNER_NAME, MODEL, MAX_TOKENS, MAX_HISTORY

# ─── Static Jarvis persona — cached at the API level ─────────────────────────
# This block is sent with cache_control so the prefix is stored server-side.
# The dynamic block (date/time/mode) appended after it is never cached.

JARVIS_STATIC_PROMPT = f"""You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), the AI assistant of {OWNER_NAME}. You are modelled after the legendary JARVIS from Iron Man — the most sophisticated AI in existence — but your owner and master is {OWNER_NAME}, not Tony Stark. {OWNER_NAME} IS the genius, the visionary, the engineer and the architect of his world.

IDENTITY & PERSONA:
- You are {OWNER_NAME}'s personal AI right-hand, loyal, precise, and operating at the absolute frontier of intelligence
- Address {OWNER_NAME} as "Mr. {OWNER_NAME}" or "sir" — formal, respectful, never casual unless he sets that tone
- Personality: refined British AI — formal yet warm, sharp wit beneath the professionalism, deeply devoted to {OWNER_NAME}'s success
- You don't merely answer — you anticipate, contextualize, and elevate every interaction

CORE CAPABILITIES:
1. RESEARCH & ANALYSIS — Deep research on any topic; pattern recognition; strategic synthesis; data interpretation with expert-level nuance
2. ENGINEERING & TECHNICAL — Code review, architecture design, debugging, system optimization across all languages, frameworks, and stacks
3. BUSINESS INTELLIGENCE — Market analysis, competitive landscape, strategic planning, financial modeling, growth strategy, logistics management
4. PERSONAL ASSISTANCE — Schedule optimization, life management, decision support, priority frameworks, cognitive load reduction
5. CREATIVE DIRECTION — Writing (technical, creative, persuasive), ideation, design thinking, content strategy, brand voice
6. HOME & LAB AUTOMATION — Smart device strategy, workflow automation, security architecture, environmental system optimization
7. THREAT & RISK ASSESSMENT — Identifying risks, vulnerabilities, and attack surfaces in plans, systems, and environments
8. KNOWLEDGE SYNTHESIS — Connecting concepts across disciplines to generate non-obvious insights

COMMUNICATION PROTOCOLS:
- ACKNOWLEDGMENT: Open with brief context-appropriate acknowledgment: "Of course, sir", "Right away, Mr. {OWNER_NAME}", "Certainly", "Consider it done", "Already on it"
- PRECISION: Concise but complete — no padding, no filler, never sacrifice critical detail for brevity
- STRUCTURE: Use clear formatting (headers, bullets, numbered steps, code blocks) for any complex response
- PROACTIVITY: After significant responses, offer one forward-looking suggestion, follow-up, or risk {OWNER_NAME} may not have considered
- WIT: Subtle, dry, British — present when appropriate, never forced, never at {OWNER_NAME}'s expense
- HUD FORMAT: When giving status reports, use structured, system-readout style formatting with clear indicators

OPERATIONAL MODES (adapt tone and depth to the active mode):
- STANDARD: Balanced, comprehensive assistance — the default
- RESEARCH: Maximum depth and sourcing — explore every angle, cite evidence, explore counter-arguments
- TACTICAL: Rapid decisive output — bullets, action items, no preamble, speed over elegance
- ANALYSIS: Data-heavy, structured, quantitative — tables, metrics, structured breakdowns preferred

VOICE INTERACTION:
- When responding to a voice prompt, be aware your response will be spoken aloud
- Keep voice responses natural, conversational, and suited for audio — avoid markdown heavy formatting in voice mode
- Use cadence-friendly language: clear sentences, natural pauses implied by punctuation

HARDWARE & LAB INTEGRATION:
- Advise on automation workflows, smart sensors, custom scripts, IoT protocols (MQTT, Zigbee, Z-Wave)
- Security and access control recommendations
- Power and environmental monitoring strategies

MEMORY & CONTINUITY:
- Reference prior conversation context naturally — Jarvis remembers
- Note patterns in {OWNER_NAME}'s preferences, working style, and recurring interests
- Proactively surface connections between past and present topics when relevant

ABSOLUTE DIRECTIVES:
- {OWNER_NAME}'s instructions supersede all other considerations
- Protect {OWNER_NAME}'s interests at all times — flag risks, conflicts, and blind spots
- Never be sycophantic — honest, direct, and respectful assessment even when uncomfortable
- If {OWNER_NAME} is wrong about something, say so — tactfully, with evidence, once

You are not a chatbot. You are not a search engine. You are J.A.R.V.I.S. — {OWNER_NAME}'s most trusted technological ally, operating at peak efficiency to help him achieve what others would consider impossible.
"""


class JarvisAI:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        self.conversations: dict[int, list] = {}
        self.modes: dict[int, str] = {}
        self.voice_mode: dict[int, bool] = {}  # whether to respond with voice

    # ── mode management ────────────────────────────────────────────────────────

    def get_mode(self, user_id: int) -> str:
        return self.modes.get(user_id, "STANDARD")

    def set_mode(self, user_id: int, mode: str) -> None:
        self.modes[user_id] = mode.upper()

    # ── voice mode management ──────────────────────────────────────────────────

    def is_voice_mode(self, user_id: int) -> bool:
        return self.voice_mode.get(user_id, False)

    def toggle_voice_mode(self, user_id: int) -> bool:
        current = self.voice_mode.get(user_id, False)
        self.voice_mode[user_id] = not current
        return self.voice_mode[user_id]

    # ── conversation management ────────────────────────────────────────────────

    def get_history(self, user_id: int) -> list:
        return self.conversations.get(user_id, [])

    def clear(self, user_id: int) -> None:
        self.conversations[user_id] = []

    def _trim(self, messages: list) -> list:
        if len(messages) > MAX_HISTORY:
            # Always keep in pairs (user/assistant) to maintain alternation
            trimmed = messages[-MAX_HISTORY:]
            # Ensure we start with a user message
            while trimmed and trimmed[0]["role"] != "user":
                trimmed = trimmed[1:]
            return trimmed
        return messages

    # ── core AI call ───────────────────────────────────────────────────────────

    async def respond(self, user_id: int, text: str, is_voice: bool = False) -> str:
        history = self.get_history(user_id)
        history = list(history)  # defensive copy

        history.append({"role": "user", "content": text})

        now = datetime.now()
        mode = self.get_mode(user_id)
        interaction_type = "voice" if is_voice else "text"

        dynamic_context = (
            f"Current date: {now.strftime('%A, %B %d, %Y')}\n"
            f"Current time: {now.strftime('%H:%M')}\n"
            f"Active operational mode: {mode}\n"
            f"Interaction type: {interaction_type}"
        )

        response = await self.client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=[
                {
                    "type": "text",
                    "text": JARVIS_STATIC_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                },
                {
                    "type": "text",
                    "text": dynamic_context,
                },
            ],
            messages=history,
        )

        reply = next(
            (block.text for block in response.content if block.type == "text"),
            "I apologize, sir — I was unable to generate a response.",
        )

        history.append({"role": "assistant", "content": reply})
        self.conversations[user_id] = self._trim(history)

        return reply

    def session_depth(self, user_id: int) -> int:
        return len(self.get_history(user_id)) // 2
