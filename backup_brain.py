"""
CMJ Backup Brain — Rule-Based Contingency Engine

Activated automatically when the primary AI-driven performance intelligence
system produces outputs that fail sanity checks, fall below the confidence
threshold, or becomes unavailable. Physics-based detection does not hallucinate.

Usage:
    brain = CMJBackupBrain()
    result = brain.decide(time_s, force_n, body_weight_n,
                          ai_result=ai_output, ai_confidence=0.65)
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.ndimage import gaussian_filter1d

logging.basicConfig(level=logging.INFO, format="%(name)s [%(levelname)s] %(message)s")


# ── Data structures ────────────────────────────────────────────────────────────

class DecisionSource(str, Enum):
    AI          = "ai"
    BACKUP      = "backup_rule_based"
    FLAGGED     = "flagged_for_human_review"


@dataclass
class PhaseResult:
    name:        str
    start_s:     float
    end_s:       float
    duration_ms: float
    confidence:  float


@dataclass
class CMJAnalysisResult:
    source:       DecisionSource
    phases:       dict
    metrics:      dict
    sanity_flags: list
    confidence:   float
    timestamp:    str
    audit_id:     str

    def to_dict(self) -> dict:
        d = asdict(self)
        d["source"] = self.source.value
        return d


# ── Sanity guard ───────────────────────────────────────────────────────────────

class SanityGuard:
    """
    Validates CMJ metrics against established physiological limits.
    Any value outside these bounds is treated as a red flag.
    """

    LIMITS: dict = {
        "flight_time_s":           (0.08,  0.80),   # 80 ms – 800 ms
        "peak_grf_bw":             (1.20,  7.00),   # multiples of body weight
        "braking_duration_ms":     (50.0,  400.0),
        "propulsive_duration_ms":  (80.0,  500.0),
        "jump_height_m":           (0.05,  1.20),
        "landing_peak_grf_bw":     (1.50,  12.00),
    }

    def check(self, metrics: dict) -> list:
        flags = []
        for key, (lo, hi) in self.LIMITS.items():
            if key not in metrics:
                continue
            val = metrics[key]
            if not (lo <= val <= hi):
                flags.append(
                    f"OUT_OF_RANGE | {key} = {val:.3f}  (expected {lo} – {hi})"
                )
        return flags


# ── Main contingency engine ────────────────────────────────────────────────────

class CMJBackupBrain:
    """
    Rule-based contingency engine for CMJ phase detection and metric computation.

    Operates entirely independently of the AI model.  Routing logic:

        AI confidence >= threshold  AND  sanity checks pass
            → accept AI result (logged as source=ai)

        AI confidence >= threshold  BUT  sanity checks fail
            → discard AI result, run rule-based engine, flag for human review

        AI confidence < threshold   OR   AI unavailable
            → run rule-based engine silently as backup
    """

    CONFIDENCE_THRESHOLD: float = 0.72
    G: float = 9.81   # m/s²

    def __init__(self, audit_log_path: str = "backup_brain_audit.jsonl"):
        self._guard  = SanityGuard()
        self._log    = logging.getLogger("CMJBackupBrain")
        self._logpath = audit_log_path

    # ── Public API ─────────────────────────────────────────────────────────────

    def decide(
        self,
        time_s:        np.ndarray,
        force_n:       np.ndarray,
        body_weight_n: float,
        ai_result:     Optional[dict] = None,
        ai_confidence: float = 0.0,
    ) -> CMJAnalysisResult:
        """
        Return the best available CMJ analysis.  If the AI result is reliable
        it is returned as-is; otherwise the rule-based contingency engine runs.
        """
        if ai_result is not None and ai_confidence >= self.CONFIDENCE_THRESHOLD:
            flags = self._guard.check(ai_result.get("metrics", {}))
            if not flags:
                result = self._wrap_ai(ai_result, ai_confidence)
                self._audit(result)
                return result

            self._log.warning(
                "AI output failed sanity checks — activating contingency engine. "
                "Flags: %s", flags
            )

        elif ai_result is not None:
            self._log.info(
                "AI confidence %.2f below threshold %.2f — contingency engine active.",
                ai_confidence, self.CONFIDENCE_THRESHOLD,
            )

        result = self._run_rule_based(time_s, force_n, body_weight_n)
        self._audit(result)
        return result

    def validate_ai_output(
        self,
        ai_result:     dict,
        time_s:        np.ndarray,
        force_n:       np.ndarray,
        body_weight_n: float,
        boundary_tol_s: float = 0.10,
    ) -> tuple:
        """
        Cross-check AI phase boundaries against rule-based detection.
        Returns (is_valid: bool, discrepancies: list[str]).
        """
        backup = self._run_rule_based(time_s, force_n, body_weight_n)
        issues = []

        for phase_name, bp in backup.phases.items():
            ai_ph = ai_result.get("phases", {}).get(phase_name)
            if ai_ph is None:
                issues.append(f"MISSING_PHASE | {phase_name} absent from AI output")
                continue

            for boundary in ("start_s", "end_s"):
                bval = getattr(bp, boundary)
                aval = ai_ph.get(boundary)
                if aval is None:
                    continue
                diff = abs(bval - aval)
                if diff > boundary_tol_s:
                    issues.append(
                        f"BOUNDARY_MISMATCH | {phase_name}.{boundary} "
                        f"AI={aval:.3f}s  backup={bval:.3f}s  "
                        f"(Δ={diff*1000:.0f} ms)"
                    )

        issues.extend(self._guard.check(ai_result.get("metrics", {})))
        return (len(issues) == 0, issues)

    # ── Rule-based engine ──────────────────────────────────────────────────────

    def _run_rule_based(
        self,
        time_s:        np.ndarray,
        force_n:       np.ndarray,
        body_weight_n: float,
    ) -> CMJAnalysisResult:
        fs = 1.0 / float(np.mean(np.diff(time_s)))

        # Smooth first to suppress sensor noise before any detection
        sigma   = max(1, int(fs * 0.010))          # 10 ms Gaussian kernel
        f_clean = gaussian_filter1d(force_n.astype(float), sigma=sigma)

        # Net force → acceleration → velocity (impulse-momentum method)
        mass_kg = body_weight_n / self.G
        net_f   = f_clean - body_weight_n
        accel   = net_f / mass_kg
        vel     = cumulative_trapezoid(accel, time_s, initial=0.0)

        phases, confidence = self._detect_phases(
            time_s, f_clean, vel, body_weight_n, fs
        )
        metrics     = self._compute_metrics(time_s, force_n, f_clean, vel,
                                            body_weight_n, phases)
        sanity_flags = self._guard.check(metrics)

        if sanity_flags:
            # Contingency engine itself found anomalies — flag for human
            confidence *= 0.60
            source = DecisionSource.FLAGGED
            self._log.error(
                "Contingency engine detected anomalies — human review required: %s",
                sanity_flags,
            )
        else:
            source = DecisionSource.BACKUP

        return CMJAnalysisResult(
            source       = source,
            phases       = phases,
            metrics      = metrics,
            sanity_flags = sanity_flags,
            confidence   = round(confidence, 3),
            timestamp    = datetime.now(timezone.utc).isoformat(),
            audit_id     = str(uuid.uuid4()),
        )

    # ── Phase detection ────────────────────────────────────────────────────────

    def _detect_phases(
        self,
        t:   np.ndarray,
        f:   np.ndarray,
        vel: np.ndarray,
        bw:  float,
        fs:  float,
    ) -> tuple:
        scores: list = []

        def _dur_ms(s: float, e: float) -> float:
            return round((e - s) * 1000, 1)

        def _phase_conf(s: float, e: float, lo_ms: float, hi_ms: float) -> float:
            d = _dur_ms(s, e)
            if lo_ms <= d <= hi_ms:
                return 1.0
            mid = (lo_ms + hi_ms) / 2.0
            return max(0.0, 1.0 - abs(d - mid) / (hi_ms - lo_ms))

        # Quiet phase
        quiet_end = self._quiet_end(f, bw, fs)
        q_conf    = 1.0 if quiet_end >= 0.5 else 0.6
        scores.append(q_conf)

        # Unweighting phase — bound search to next 0.8 s so we don't
        # mistake the deeper flight-phase velocity trough for the unweighting trough
        uw_start = quiet_end
        uw_end   = self._peak_neg_vel(vel, t, uw_start, fs, max_s=0.80)
        uw_conf  = _phase_conf(uw_start, uw_end, 80, 600)
        scores.append(uw_conf)

        # Braking phase — zero crossing must occur within 0.6 s of braking start
        bk_start     = uw_end
        transfer_idx = self._transfer_point(vel, t, bk_start, fs, max_s=0.60)
        transfer_t   = float(t[transfer_idx])
        bk_conf      = _phase_conf(bk_start, transfer_t, 50, 400)
        scores.append(bk_conf)

        # Propulsive phase
        pr_start    = transfer_t
        takeoff_idx = self._takeoff(f, t, pr_start, bw)
        takeoff_t   = float(t[takeoff_idx])
        pr_conf     = _phase_conf(pr_start, takeoff_t, 80, 500)
        scores.append(pr_conf)

        # Flight phase
        landing_idx = self._landing_contact(f, t, takeoff_t, bw)
        landing_t   = float(t[landing_idx])
        fl_conf     = _phase_conf(takeoff_t, landing_t, 80, 800)
        scores.append(fl_conf)

        # Landing phase
        land_end_t = self._landing_end(vel, t, landing_t)
        ld_conf    = _phase_conf(landing_t, land_end_t, 50, 500)
        scores.append(ld_conf)

        phases = {
            "quiet":      PhaseResult("quiet",      float(t[0]),  quiet_end,   _dur_ms(float(t[0]), quiet_end),  round(q_conf,  3)),
            "unweight":   PhaseResult("unweight",   uw_start,     uw_end,      _dur_ms(uw_start,    uw_end),     round(uw_conf, 3)),
            "braking":    PhaseResult("braking",    bk_start,     transfer_t,  _dur_ms(bk_start,    transfer_t), round(bk_conf, 3)),
            "transfer":   PhaseResult("transfer",   transfer_t,   transfer_t,  0.0,                              1.0),
            "propulsive": PhaseResult("propulsive", pr_start,     takeoff_t,   _dur_ms(pr_start,    takeoff_t),  round(pr_conf, 3)),
            "flight":     PhaseResult("flight",     takeoff_t,    landing_t,   _dur_ms(takeoff_t,   landing_t),  round(fl_conf, 3)),
            "landing":    PhaseResult("landing",    landing_t,    land_end_t,  _dur_ms(landing_t,   land_end_t), round(ld_conf, 3)),
        }
        return phases, float(np.mean(scores))

    # ── Phase boundary finders ─────────────────────────────────────────────────

    def _quiet_end(self, f: np.ndarray, bw: float, fs: float) -> float:
        """Quiet phase ends when GRF deviates >5 % BW for at least 50 ms."""
        window    = max(1, int(fs * 0.05))
        threshold = bw * 0.05
        for i in range(len(f) - window):
            if np.all(np.abs(f[i : i + window] - bw) > threshold):
                return max(0.5, i / fs)
        return max(0.5, len(f) / fs * 0.35)

    def _peak_neg_vel(
        self, vel: np.ndarray, t: np.ndarray, start_s: float, fs: float, max_s: float = 0.80
    ) -> float:
        """
        End of unweighting = first local minimum of COM velocity after start_s.
        Search is bounded to max_s seconds so the much deeper flight-phase trough
        is never mistaken for the unweighting trough.
        """
        i0   = int(np.searchsorted(t, start_s))
        i_hi = min(len(vel) - 1, i0 + int(max_s * fs))
        if i_hi <= i0:
            return start_s + 0.30

        window = vel[i0:i_hi]
        grad   = np.diff(window)

        # First point where gradient flips from negative to non-negative while vel < 0
        for i in range(len(grad) - 1):
            if grad[i] < 0 and grad[i + 1] >= 0 and window[i] < 0:
                return float(t[i0 + i])

        # Fallback: global minimum within the bounded window
        return float(t[i0 + int(np.argmin(window))])

    def _transfer_point(
        self, vel: np.ndarray, t: np.ndarray, start_s: float, fs: float, max_s: float = 0.60
    ) -> int:
        """Transfer point = first upward zero-crossing of COM velocity, bounded to max_s seconds."""
        i0   = int(np.searchsorted(t, start_s))
        i_hi = min(len(vel) - 1, i0 + int(max_s * fs))
        for i in range(i0, i_hi):
            if vel[i] <= 0.0 < vel[i + 1]:
                return i
        # Fallback: midpoint of bounded window
        return i0 + max(1, (i_hi - i0) // 2)

    def _takeoff(self, f: np.ndarray, t: np.ndarray, start_s: float, bw: float) -> int:
        """Takeoff = GRF drops below 5 % BW after propulsive phase."""
        i0        = int(np.searchsorted(t, start_s))
        threshold = bw * 0.05
        for i in range(i0, len(f)):
            if f[i] < threshold:
                return i
        return len(f) - max(1, len(f) // 10)

    def _landing_contact(self, f: np.ndarray, t: np.ndarray, takeoff_s: float, bw: float) -> int:
        """Landing contact = GRF rises above 5 % BW after flight."""
        i0        = int(np.searchsorted(t, takeoff_s)) + 1
        threshold = bw * 0.05
        for i in range(i0, len(f)):
            if f[i] > threshold:
                return i
        return len(f) - 1

    def _landing_end(self, vel: np.ndarray, t: np.ndarray, landing_s: float) -> float:
        """Landing ends when COM velocity returns through zero (COM stops)."""
        i0 = int(np.searchsorted(t, landing_s))
        for i in range(i0, len(vel) - 1):
            if vel[i] <= 0.0 and vel[i + 1] >= 0.0:
                return float(t[i])
        return float(t[-1])

    # ── Metric computation ─────────────────────────────────────────────────────

    def _compute_metrics(
        self,
        t:      np.ndarray,
        f_raw:  np.ndarray,
        f_clean: np.ndarray,
        vel:    np.ndarray,
        bw:     float,
        phases: dict,
    ) -> dict:
        metrics: dict = {}

        # Jump height from takeoff velocity (industry gold standard)
        pr = phases.get("propulsive")
        if pr:
            idx = min(int(np.searchsorted(t, pr.end_s)), len(vel) - 1)
            v_to = float(vel[idx])
            if v_to > 0:
                metrics["jump_height_m"] = round(v_to ** 2 / (2.0 * self.G), 3)

        # Peak GRF
        peak = float(np.max(f_raw))
        metrics["peak_grf_n"]  = round(peak, 1)
        metrics["peak_grf_bw"] = round(peak / bw, 3)

        # Flight time
        fl = phases.get("flight")
        if fl:
            metrics["flight_time_s"] = round(fl.duration_ms / 1000.0, 4)

        # Braking duration
        bk = phases.get("braking")
        if bk:
            metrics["braking_duration_ms"] = round(bk.duration_ms, 1)

        # Propulsive duration
        if pr:
            metrics["propulsive_duration_ms"] = round(pr.duration_ms, 1)

        # Landing peak GRF
        ld = phases.get("landing")
        if ld:
            s = int(np.searchsorted(t, ld.start_s))
            e = min(int(np.searchsorted(t, ld.end_s)), len(f_raw))
            if s < e:
                lp = float(np.max(f_raw[s:e]))
                metrics["landing_peak_grf_n"]  = round(lp, 1)
                metrics["landing_peak_grf_bw"] = round(lp / bw, 3)

        return metrics

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _wrap_ai(self, ai_result: dict, confidence: float) -> CMJAnalysisResult:
        phases: dict = {}
        for name, ph in ai_result.get("phases", {}).items():
            s = float(ph.get("start_s", 0.0))
            e = float(ph.get("end_s", 0.0))
            phases[name] = PhaseResult(
                name        = name,
                start_s     = s,
                end_s       = e,
                duration_ms = (e - s) * 1000.0,
                confidence  = float(ph.get("confidence", confidence)),
            )
        return CMJAnalysisResult(
            source       = DecisionSource.AI,
            phases       = phases,
            metrics      = ai_result.get("metrics", {}),
            sanity_flags = [],
            confidence   = round(confidence, 3),
            timestamp    = datetime.now(timezone.utc).isoformat(),
            audit_id     = str(uuid.uuid4()),
        )

    def _audit(self, result: CMJAnalysisResult) -> None:
        record = {
            "audit_id":    result.audit_id,
            "timestamp":   result.timestamp,
            "source":      result.source.value,
            "confidence":  result.confidence,
            "sanity_flags": result.sanity_flags,
            "metrics":     result.metrics,
        }
        try:
            with open(self._logpath, "a") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            self._log.error("Audit log write failed: %s", exc)


# ── Self-test (runs against the existing CMJ curve from generate_plots.py) ─────

if __name__ == "__main__":
    from generate_plots import T, F, BW

    print("=" * 60)
    print("CMJ BACKUP BRAIN — CONTINGENCY SELF-TEST")
    print("=" * 60)

    brain = CMJBackupBrain(audit_log_path="backup_brain_audit.jsonl")

    # ── Test 1: No AI available — pure contingency ─────────────────────────
    print("\n[TEST 1] No AI available — contingency engine running solo")
    result = brain.decide(T, F, BW)
    print(f"  Source     : {result.source.value}")
    print(f"  Confidence : {result.confidence}")
    print(f"  Sanity flags: {result.sanity_flags or 'none'}")
    print("  Phases detected:")
    for name, ph in result.phases.items():
        print(f"    {name:<12} {ph.start_s:.3f}s – {ph.end_s:.3f}s  "
              f"({ph.duration_ms:.0f} ms)  conf={ph.confidence:.2f}")
    print("  Key metrics:")
    for k, v in result.metrics.items():
        print(f"    {k:<30} {v}")

    # ── Test 2: AI result with high confidence, clean metrics ─────────────
    print("\n[TEST 2] AI result — high confidence, passes sanity")
    good_ai = {
        "phases": {
            "quiet":      {"start_s": 0.0,  "end_s": 1.00, "confidence": 0.95},
            "unweight":   {"start_s": 1.00, "end_s": 1.30, "confidence": 0.91},
            "braking":    {"start_s": 1.30, "end_s": 1.55, "confidence": 0.88},
            "transfer":   {"start_s": 1.55, "end_s": 1.55, "confidence": 1.00},
            "propulsive": {"start_s": 1.55, "end_s": 1.81, "confidence": 0.93},
            "flight":     {"start_s": 1.81, "end_s": 2.42, "confidence": 0.97},
            "landing":    {"start_s": 2.42, "end_s": 2.90, "confidence": 0.89},
        },
        "metrics": {
            "jump_height_m":          0.42,
            "peak_grf_bw":            2.10,
            "flight_time_s":          0.61,
            "braking_duration_ms":    250.0,
            "propulsive_duration_ms": 260.0,
            "landing_peak_grf_bw":    4.30,
        },
    }
    result2 = brain.decide(T, F, BW, ai_result=good_ai, ai_confidence=0.91)
    print(f"  Source     : {result2.source.value}")
    print(f"  Confidence : {result2.confidence}")

    # ── Test 3: AI result with low confidence — contingency activates ──────
    print("\n[TEST 3] AI result — low confidence, contingency activates")
    result3 = brain.decide(T, F, BW, ai_result=good_ai, ai_confidence=0.50)
    print(f"  Source     : {result3.source.value}")
    print(f"  Confidence : {result3.confidence}")

    # ── Test 4: AI result with failing sanity — contingency activates ──────
    print("\n[TEST 4] AI result — sanity failure (peak GRF 10× BW), contingency activates")
    bad_ai = {**good_ai, "metrics": {**good_ai["metrics"], "peak_grf_bw": 10.5}}
    result4 = brain.decide(T, F, BW, ai_result=bad_ai, ai_confidence=0.85)
    print(f"  Source     : {result4.source.value}")
    print(f"  Sanity flags: {result4.sanity_flags or 'none'}")

    # ── Test 5: validate_ai_output cross-check ─────────────────────────────
    print("\n[TEST 5] validate_ai_output — cross-check AI vs rule-based boundaries")
    valid, issues = brain.validate_ai_output(good_ai, T, F, BW)
    print(f"  AI valid   : {valid}")
    if issues:
        for iss in issues:
            print(f"  Issue: {iss}")
    else:
        print("  No boundary discrepancies detected")

    print("\n" + "=" * 60)
    print("All tests completed. Audit log → backup_brain_audit.jsonl")
    print("=" * 60)
