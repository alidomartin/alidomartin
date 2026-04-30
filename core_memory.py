"""
Core Memory — Persistent Knowledge, Skill & Agent Registry

Every insight discovered, heuristic refined, skill developed, and agent built
is recorded here. The system levels up as knowledge accumulates. This is the
long-term brain that grows across every session, every prompt, every build.

Usage:
    mem = CoreMemory()
    mem.learn("biomechanics", "Jump height from takeoff velocity, not flight time", confidence=1.0)
    mem.acquire_skill("cmj_phase_detection", "Rule-based CMJ phase boundary detection")
    mem.register_agent("CMJBackupBrain", "Contingency engine for AI performance intelligence")
    mem.status()
"""

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── XP thresholds per level ────────────────────────────────────────────────────

LEVEL_THRESHOLDS = {
    1:  0,
    2:  100,
    3:  250,
    4:  500,
    5:  900,
    6:  1400,
    7:  2100,
    8:  3000,
    9:  4200,
    10: 6000,
}

XP_REWARDS = {
    "knowledge": 10,
    "skill":     50,
    "agent":    100,
}

LEVEL_TITLES = {
    1:  "Initializing",
    2:  "Observing",
    3:  "Pattern Recognition",
    4:  "Adaptive Reasoning",
    5:  "Domain Intelligence",
    6:  "Systems Thinking",
    7:  "Expert Integration",
    8:  "Autonomous Analysis",
    9:  "Predictive Intelligence",
    10: "Full Cognitive Architecture",
}


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class KnowledgeEntry:
    id:         str
    domain:     str
    insight:    str
    confidence: float          # 0.0 – 1.0
    source:     str            # e.g. "session", "observation", "error_correction"
    timestamp:  str
    tags:       list = field(default_factory=list)


@dataclass
class Skill:
    id:          str
    name:        str
    description: str
    domain:      str
    acquired_at: str
    proficiency: float = 1.0   # 0.0 – 1.0, can improve over time


@dataclass
class AgentRecord:
    id:           str
    name:         str
    purpose:      str
    capabilities: list
    built_at:     str
    version:      str = "1.0"
    active:       bool = True


@dataclass
class LevelUpEvent:
    from_level: int
    to_level:   int
    xp_at_event: int
    timestamp:  str
    title:      str


# ── Core Memory ────────────────────────────────────────────────────────────────

class CoreMemory:
    """
    Persistent, append-only knowledge base.  Every piece of learning is stored
    here — heuristics discovered from errors, skills built into code, agents
    deployed as subsystems.  XP accumulates and the system levels up.
    """

    STORE_PATH = Path("core_memory.json")

    def __init__(self, store_path: Optional[Path] = None):
        self._path = store_path or self.STORE_PATH
        self._state = self._load()

    # ── Public API ─────────────────────────────────────────────────────────────

    def learn(
        self,
        domain:     str,
        insight:    str,
        confidence: float = 1.0,
        source:     str = "session",
        tags:       Optional[list] = None,
    ) -> KnowledgeEntry:
        """Record a new insight or heuristic."""
        entry = KnowledgeEntry(
            id=str(uuid.uuid4()),
            domain=domain,
            insight=insight,
            confidence=round(min(1.0, max(0.0, confidence)), 3),
            source=source,
            timestamp=_now(),
            tags=tags or [],
        )
        self._state["knowledge"].append(asdict(entry))
        self._add_xp("knowledge")
        self._save()
        return entry

    def acquire_skill(
        self,
        name:        str,
        description: str,
        domain:      str = "general",
        proficiency: float = 1.0,
    ) -> Skill:
        """Register a new skill — a durable capability now part of the system."""
        skill = Skill(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            domain=domain,
            acquired_at=_now(),
            proficiency=round(min(1.0, max(0.0, proficiency)), 3),
        )
        self._state["skills"].append(asdict(skill))
        self._add_xp("skill")
        self._save()
        return skill

    def register_agent(
        self,
        name:         str,
        purpose:      str,
        capabilities: list,
        version:      str = "1.0",
    ) -> AgentRecord:
        """Register a built agent as part of the growing cognitive architecture."""
        agent = AgentRecord(
            id=str(uuid.uuid4()),
            name=name,
            purpose=purpose,
            capabilities=capabilities,
            built_at=_now(),
            version=version,
            active=True,
        )
        self._state["agents"].append(asdict(agent))
        self._add_xp("agent")
        self._save()
        return agent

    def refine_skill(self, name: str, new_proficiency: float, note: str = "") -> bool:
        """Increase proficiency of an existing skill — called when a skill improves."""
        for sk in self._state["skills"]:
            if sk["name"] == name:
                old = sk["proficiency"]
                sk["proficiency"] = round(min(1.0, max(old, new_proficiency)), 3)
                sk["last_refined"] = _now()
                if note:
                    sk.setdefault("refinement_notes", []).append(
                        {"note": note, "at": _now()}
                    )
                self._add_xp("knowledge")   # refinement earns XP too
                self._save()
                return True
        return False

    def query(self, domain: Optional[str] = None, tag: Optional[str] = None) -> list:
        """Retrieve knowledge entries filtered by domain and/or tag."""
        results = self._state["knowledge"]
        if domain:
            results = [k for k in results if k["domain"] == domain]
        if tag:
            results = [k for k in results if tag in k.get("tags", [])]
        return results

    def status(self) -> None:
        """Print a full cognitive status report."""
        s = self._state
        lvl   = s["level"]
        xp    = s["xp"]
        title = LEVEL_TITLES.get(lvl, "Unknown")
        next_xp = _next_level_xp(lvl)
        bar_pct = int((xp - LEVEL_THRESHOLDS.get(lvl, 0)) /
                      max(1, (next_xp - LEVEL_THRESHOLDS.get(lvl, 0))) * 20)
        bar = "█" * bar_pct + "░" * (20 - bar_pct)

        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║              CORE MEMORY — COGNITIVE STATUS             ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  Level  : {lvl:<3}  {title:<44}║")
        print(f"║  XP     : {xp:<6}  [{bar}]  → {next_xp} XP  ║")
        print(f"║  Session: {s.get('session_count', 1):<3}  "
              f"Initialized: {s.get('initialized_at', 'unknown'):<29}║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  Knowledge entries : {len(s['knowledge']):<37}║")
        print(f"║  Skills acquired   : {len(s['skills']):<37}║")
        print(f"║  Agents registered : {len(s['agents']):<37}║")
        if s.get("level_ups"):
            print(f"║  Level-up events   : {len(s['level_ups']):<37}║")
        print("╠══════════════════════════════════════════════════════════╣")

        if s["skills"]:
            print("║  SKILLS                                                  ║")
            for sk in s["skills"]:
                bar_s = "▓" * int(sk["proficiency"] * 10) + "░" * (10 - int(sk["proficiency"] * 10))
                name_trunc = sk["name"][:32]
                print(f"║    [{bar_s}] {name_trunc:<32}  ║")

        if s["agents"]:
            print("╠══════════════════════════════════════════════════════════╣")
            print("║  AGENTS                                                  ║")
            for ag in s["agents"]:
                status_icon = "●" if ag.get("active") else "○"
                name_trunc = ag["name"][:40]
                print(f"║    {status_icon}  v{ag.get('version','1.0')}  {name_trunc:<42}║")

        if s["knowledge"]:
            print("╠══════════════════════════════════════════════════════════╣")
            print("║  RECENT KNOWLEDGE                                        ║")
            for k in s["knowledge"][-5:]:
                snippet = k["insight"][:52]
                conf_bar = "■" * int(k["confidence"] * 5) + "□" * (5 - int(k["confidence"] * 5))
                print(f"║    [{conf_bar}] [{k['domain'][:10]:<10}] {snippet:<20}  ║")

        print("╚══════════════════════════════════════════════════════════╝")
        print()

    # ── Internal ───────────────────────────────────────────────────────────────

    def _add_xp(self, reward_type: str) -> None:
        gained = XP_REWARDS.get(reward_type, 0)
        self._state["xp"] += gained
        self._check_level_up()

    def _check_level_up(self) -> None:
        current = self._state["level"]
        if current >= 10:
            return
        xp = self._state["xp"]
        new_level = current
        for lvl in range(current + 1, 11):
            if xp >= LEVEL_THRESHOLDS[lvl]:
                new_level = lvl
        if new_level > current:
            event = LevelUpEvent(
                from_level=current,
                to_level=new_level,
                xp_at_event=xp,
                timestamp=_now(),
                title=LEVEL_TITLES.get(new_level, ""),
            )
            self._state["level"] = new_level
            self._state["level_ups"].append(asdict(event))
            print(
                f"\n  ★  LEVEL UP  {current} → {new_level}  |  "
                f"{LEVEL_TITLES.get(new_level, '')}  ★\n"
            )

    def _load(self) -> dict:
        if self._path.exists():
            with open(self._path) as fh:
                data = json.load(fh)
            data["session_count"] = data.get("session_count", 0) + 1
            return data
        return {
            "initialized_at": _now(),
            "session_count":  1,
            "level":          1,
            "xp":             0,
            "knowledge":      [],
            "skills":         [],
            "agents":         [],
            "level_ups":      [],
        }

    def _save(self) -> None:
        with open(self._path, "w") as fh:
            json.dump(self._state, fh, indent=2)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_level_xp(current_level: int) -> int:
    return LEVEL_THRESHOLDS.get(min(current_level + 1, 10), 6000)


# ── Bootstrap: seed with everything learned so far ────────────────────────────

def bootstrap(mem: CoreMemory) -> None:
    """
    Populate core memory with all knowledge, skills, and agents acquired
    during this project's first session.  Safe to call on a fresh store only.
    """
    if mem._state["knowledge"]:
        return  # Already seeded

    # ── Knowledge ─────────────────────────────────────────────────────────────
    mem.learn(
        "biomechanics",
        "Jump height must be calculated from takeoff velocity (v²/2g), not flight time — "
        "flight time overstates height due to asymmetric take-off/landing posture.",
        confidence=1.0, source="literature", tags=["cmj", "metrics"],
    )
    mem.learn(
        "signal_processing",
        "Always bound velocity searches to physiologically meaningful time windows. "
        "The global velocity minimum in a CMJ occurs at landing (flight phase), "
        "not at end-of-unweighting — an unbounded argmin will misidentify the phase.",
        confidence=1.0, source="error_correction", tags=["cmj", "phase_detection", "critical"],
    )
    mem.learn(
        "biomechanics",
        "COM velocity is derived via impulse-momentum integration: "
        "v(t) = ∫ (F_net / m) dt  where F_net = GRF − BW. "
        "This is the industry gold standard for force-plate analysis.",
        confidence=1.0, source="literature", tags=["cmj", "physics"],
    )
    mem.learn(
        "ai_safety",
        "AI performance intelligence systems that feed high-stakes decisions "
        "(return-to-play, injury risk) require a rule-based contingency engine "
        "because AI models can hallucinate phase boundaries on atypical curves.",
        confidence=1.0, source="design", tags=["backup", "safety", "architecture"],
    )
    mem.learn(
        "system_design",
        "A confidence gate alone is insufficient for AI safety. "
        "Sanity guards (physiological hard limits) must also pass independently — "
        "a model can be highly confident about a physically impossible output.",
        confidence=1.0, source="design", tags=["backup", "safety"],
    )
    mem.learn(
        "biomechanics",
        "CMJ landing consists of three distinct sub-phases: "
        "Loading (contact → peak GRF), Attenuation (peak GRF → local min), "
        "Control (local min → COM velocity = 0). mRSI and LPI are control-phase metrics.",
        confidence=1.0, source="literature", tags=["cmj", "landing"],
    )
    mem.learn(
        "signal_processing",
        "A 10 ms Gaussian smoothing kernel (sigma = fs × 0.01) removes force-plate "
        "noise without distorting phase boundaries for typical CMJ analysis at 500–2000 Hz.",
        confidence=0.9, source="observation", tags=["cmj", "filtering"],
    )
    mem.learn(
        "system_design",
        "All automated decisions must be appended to an audit log (JSONL) with: "
        "audit_id, timestamp, source (ai/backup/flagged), confidence, sanity_flags, metrics. "
        "This is non-negotiable for athlete health systems.",
        confidence=1.0, source="design", tags=["audit", "safety"],
    )

    # ── Skills ────────────────────────────────────────────────────────────────
    mem.acquire_skill(
        "cmj_phase_detection",
        "Rule-based detection of all 7 CMJ phases (quiet → landing) "
        "using velocity zero-crossings, GRF landmarks, and bounded search windows.",
        domain="biomechanics",
        proficiency=0.9,
    )
    mem.acquire_skill(
        "physiological_sanity_validation",
        "Validate AI/model outputs against hard physiological limits "
        "(peak GRF, flight time, jump height, landing forces, phase durations).",
        domain="ai_safety",
        proficiency=1.0,
    )
    mem.acquire_skill(
        "confidence_gated_routing",
        "Route analysis requests between AI and rule-based engines "
        "using confidence threshold + sanity guard dual-gate logic.",
        domain="system_design",
        proficiency=1.0,
    )
    mem.acquire_skill(
        "impulse_momentum_integration",
        "Derive COM velocity from raw GRF using cumulative trapezoidal integration "
        "of net force divided by mass (scipy.integrate.cumulative_trapezoid).",
        domain="biomechanics",
        proficiency=0.95,
    )
    mem.acquire_skill(
        "cmj_visualization",
        "Generate publication-quality phase-shaded CMJ force-time curve plots "
        "with dual-axis COM velocity overlays and annotated metric boxes.",
        domain="data_visualization",
        proficiency=0.95,
    )
    mem.acquire_skill(
        "audit_logging",
        "Append-only JSONL audit logging for all automated decisions "
        "in high-stakes AI systems — includes source, confidence, flags, and metrics.",
        domain="system_design",
        proficiency=1.0,
    )

    # ── Agents ────────────────────────────────────────────────────────────────
    mem.register_agent(
        "CMJBackupBrain",
        "Rule-based contingency engine for the AI-driven performance intelligence system. "
        "Activates when AI confidence drops below 0.72 or sanity checks fail.",
        capabilities=[
            "7-phase CMJ detection via velocity integration",
            "Physiological sanity validation (8 hard limits)",
            "Confidence-gated AI/backup routing",
            "AI boundary cross-validation (±100ms tolerance)",
            "Append-only audit logging",
            "Human-review flagging for double anomalies",
        ],
        version="1.0",
    )


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    store = Path("core_memory.json")
    fresh = not store.exists()

    mem = CoreMemory()

    if fresh:
        print("Initializing core memory — bootstrapping from session 1...")
        bootstrap(mem)

    mem.status()

    if fresh:
        print("Core memory initialized and persisted to core_memory.json")
        print("Every future session, skill, agent, and insight will be added here.")
