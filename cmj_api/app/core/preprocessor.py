from __future__ import annotations
import numpy as np
from scipy.ndimage import gaussian_filter1d
from dataclasses import dataclass
from app.config import settings


@dataclass
class PreprocessResult:
    time: np.ndarray
    force: np.ndarray
    body_weight_n: float
    mass_kg: float
    quiet_end_idx: int
    sample_rate: int


def preprocess(raw_force: np.ndarray, sample_rate: int, smooth: bool = True) -> PreprocessResult:
    n = len(raw_force)
    time = np.arange(n, dtype=float) / sample_rate
    force = (
        gaussian_filter1d(raw_force.astype(float), sigma=settings.SMOOTHING_SIGMA)
        if smooth
        else raw_force.astype(float)
    )
    quiet_end_idx, body_weight_n = _detect_body_weight(force, sample_rate)
    mass_kg = body_weight_n / settings.GRAVITY
    return PreprocessResult(
        time=time,
        force=force,
        body_weight_n=body_weight_n,
        mass_kg=mass_kg,
        quiet_end_idx=quiet_end_idx,
        sample_rate=sample_rate,
    )


def _detect_body_weight(force: np.ndarray, sample_rate: int) -> tuple[int, float]:
    """
    Slide a half-second window over the first 2 seconds.
    Pick the window with the lowest CV — that is the quiet phase.
    """
    window_n = int(settings.BODY_WEIGHT_WINDOW_S * sample_rate)
    max_search = min(int(settings.QUIET_PHASE_MIN_DURATION_S * 2 * sample_rate), len(force) - window_n)
    step = max(1, window_n // 10)

    best_cv = float("inf")
    best_start = 0

    for start in range(0, max_search, step):
        seg = force[start : start + window_n]
        mean = seg.mean()
        if mean <= 0:
            continue
        cv = seg.std() / mean
        if cv < best_cv:
            best_cv = cv
            best_start = start

    quiet_end_idx = best_start + window_n
    body_weight_n = float(force[best_start:quiet_end_idx].mean())
    return quiet_end_idx, body_weight_n
