from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Optional
from app.config import settings
from app.core.velocity import compute_velocity, compute_displacement
from app.core.preprocessor import PreprocessResult
from app.schemas.phase import PhaseBreakdown, PhaseWindow, LandingSubPhases


@dataclass
class DetectionResult:
    phases: PhaseBreakdown
    velocity: np.ndarray
    displacement: np.ndarray


def detect_phases(prep: PreprocessResult) -> DetectionResult:
    time = prep.time
    force = prep.force
    sr = prep.sample_rate
    bw = prep.body_weight_n
    mass = prep.mass_kg
    quiet_end = prep.quiet_end_idx

    velocity = compute_velocity(force, time, bw, mass)
    velocity[:quiet_end] = 0.0
    displacement = compute_displacement(velocity, time)

    unweight_start = _find_unweighting_start(force, bw, quiet_end)
    peak_neg_vel_idx = _find_peak_negative_velocity(velocity, unweight_start)
    transfer_idx = _find_transfer_point(velocity, peak_neg_vel_idx)
    takeoff_idx = _find_takeoff(force, transfer_idx, sr)
    landing_idx = _find_landing(force, takeoff_idx, sr)

    def win(s: int, e: int) -> PhaseWindow:
        e = min(e, len(force) - 1)
        return PhaseWindow(
            start_s=float(time[s]),
            end_s=float(time[e]),
            start_idx=s,
            end_idx=e,
            duration_ms=float((e - s) / sr * 1000),
        )

    landing_detail = _detect_landing_subphases(force, velocity, time, landing_idx, sr)

    phases = PhaseBreakdown(
        quiet=win(0, quiet_end),
        unweighting=win(unweight_start, peak_neg_vel_idx),
        braking=win(peak_neg_vel_idx, transfer_idx),
        transfer_s=float(time[transfer_idx]),
        propulsive=win(transfer_idx, takeoff_idx),
        flight=win(takeoff_idx, landing_idx),
        landing=win(landing_idx, len(force) - 1),
        landing_detail=landing_detail,
    )

    return DetectionResult(phases=phases, velocity=velocity, displacement=displacement)


def _find_unweighting_start(force: np.ndarray, bw: float, quiet_end: int) -> int:
    threshold = bw * settings.UNWEIGHTING_BW_FRACTION
    candidates = np.where(force[quiet_end:] < threshold)[0]
    return quiet_end + int(candidates[0]) if len(candidates) else quiet_end


def _find_peak_negative_velocity(velocity: np.ndarray, start: int) -> int:
    search_end = min(start + len(velocity) // 2, len(velocity))
    return start + int(np.argmin(velocity[start:search_end]))


def _find_transfer_point(velocity: np.ndarray, braking_start: int) -> int:
    for i in range(braking_start, len(velocity) - 1):
        if velocity[i] <= 0.0 and velocity[i + 1] > 0.0:
            return i + 1
    return braking_start + int(np.argmin(np.abs(velocity[braking_start:])))


def _find_takeoff(force: np.ndarray, propulsive_start: int, sr: int) -> int:
    threshold = settings.FLIGHT_FORCE_THRESHOLD_N
    sustained = int(0.05 * sr)
    count = 0
    for i in range(propulsive_start, len(force)):
        if force[i] < threshold:
            count += 1
            if count >= sustained:
                return i - sustained + 1
        else:
            count = 0
    return len(force) - 1


def _find_landing(force: np.ndarray, flight_start: int, sr: int) -> int:
    search_from = flight_start + int(0.05 * sr)
    threshold = settings.FLIGHT_FORCE_THRESHOLD_N * 5
    for i in range(search_from, len(force)):
        if force[i] > threshold:
            return i
    return len(force) - 1


def _detect_landing_subphases(
    force: np.ndarray,
    velocity: np.ndarray,
    time: np.ndarray,
    landing_start: int,
    sr: int,
) -> Optional[LandingSubPhases]:
    end = min(landing_start + int(0.25 * sr), len(force))
    if end <= landing_start + 10:
        return None

    land_f = force[landing_start:end]

    # Loading: contact to peak GRF
    peak_local = int(np.argmax(land_f))
    peak_idx = landing_start + peak_local

    # Attenuation: peak GRF to local minimum (force stops decreasing)
    atten_local = peak_local
    for i in range(peak_local + 1, len(land_f)):
        if land_f[i] < land_f[i - 1]:
            atten_local = i
        elif i > peak_local + 5:
            break
    atten_end_idx = landing_start + atten_local

    # Control: local minimum to COM velocity reaches zero
    ctrl_end_idx = atten_end_idx
    search_end = min(atten_end_idx + int(0.15 * sr), len(velocity))
    for i in range(atten_end_idx, search_end):
        if velocity[i] >= 0.0:
            ctrl_end_idx = i
            break
    else:
        ctrl_end_idx = min(atten_end_idx + int(0.05 * sr), len(force) - 1)

    def win(s: int, e: int) -> PhaseWindow:
        e = min(e, len(force) - 1)
        return PhaseWindow(
            start_s=float(time[s]),
            end_s=float(time[e]),
            start_idx=s,
            end_idx=e,
            duration_ms=float((e - s) / sr * 1000),
        )

    return LandingSubPhases(
        loading=win(landing_start, peak_idx),
        attenuation=win(peak_idx, atten_end_idx),
        control=win(atten_end_idx, ctrl_end_idx),
    )
