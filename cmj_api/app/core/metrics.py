from __future__ import annotations
import numpy as np
from typing import Optional
from app.config import settings
from app.schemas.metrics import CMJMetrics, PhaseMetrics, LandingMetrics
from app.schemas.phase import PhaseBreakdown


def compute_metrics(
    time: np.ndarray,
    force: np.ndarray,
    velocity: np.ndarray,
    phases: PhaseBreakdown,
    body_weight_n: float,
    mass_kg: float,
    force_right: Optional[np.ndarray] = None,
) -> CMJMetrics:
    g = settings.GRAVITY
    bw = body_weight_n

    flight_start = phases.flight.start_idx
    takeoff_vel = float(velocity[flight_start])

    if takeoff_vel > 0:
        jump_height_m = takeoff_vel ** 2 / (2 * g)
    else:
        flight_time_s = phases.flight.duration_ms / 1000
        jump_height_m = g * flight_time_s ** 2 / 8
        takeoff_vel = g * flight_time_s / 2

    def phase_metrics(pw: PhaseBreakdown) -> PhaseMetrics:
        s, e = pw.start_idx, pw.end_idx
        f_seg = force[s:e]
        t_seg = time[s:e]
        if len(f_seg) == 0:
            return PhaseMetrics(
                avg_force_n=0, peak_force_n=0, avg_relative_force=0,
                peak_relative_force=0, impulse_ns=0, duration_ms=0,
            )
        avg_f = float(np.mean(f_seg))
        peak_f = float(np.max(f_seg))
        impulse = float(np.trapz(f_seg, t_seg))
        return PhaseMetrics(
            avg_force_n=round(avg_f, 2),
            peak_force_n=round(peak_f, 2),
            avg_relative_force=round(avg_f / bw, 4),
            peak_relative_force=round(peak_f / bw, 4),
            impulse_ns=round(impulse, 4),
            duration_ms=round(pw.duration_ms, 2),
        )

    def rfd(pw: PhaseBreakdown) -> float:
        s, e = pw.start_idx, pw.end_idx
        f_seg = force[s:e]
        t_seg = time[s:e]
        if len(f_seg) < 2:
            return 0.0
        return float(np.max(np.diff(f_seg) / np.diff(t_seg)))

    prop_s, prop_e = phases.propulsive.start_idx, phases.propulsive.end_idx
    power = force[prop_s:prop_e] * velocity[prop_s:prop_e]
    peak_power = float(np.max(power)) if len(power) > 0 else 0.0
    avg_prop_power = float(np.mean(power)) if len(power) > 0 else 0.0

    asym: Optional[float] = None
    if force_right is not None:
        force_left = force - force_right
        li = float(np.trapz(force_left[prop_s:prop_e], time[prop_s:prop_e]))
        ri = float(np.trapz(force_right[prop_s:prop_e], time[prop_s:prop_e]))
        total = li + ri
        if total > 0:
            asym = round(abs(li - ri) / total * 100, 2)

    landing_m = _landing_metrics(time, force, velocity, phases, bw, jump_height_m)

    return CMJMetrics(
        body_weight_n=round(bw, 2),
        body_mass_kg=round(mass_kg, 3),
        jump_height_m=round(jump_height_m, 4),
        takeoff_velocity_ms=round(takeoff_vel, 4),
        flight_time_ms=round(phases.flight.duration_ms, 2),
        unweighting=phase_metrics(phases.unweighting),
        braking=phase_metrics(phases.braking),
        propulsive=phase_metrics(phases.propulsive),
        landing=landing_m,
        braking_rfd_ns2=round(rfd(phases.braking), 2),
        propulsive_rfd_ns2=round(rfd(phases.propulsive), 2),
        peak_power_w=round(peak_power, 2),
        avg_propulsive_power_w=round(avg_prop_power, 2),
        asymmetry_index_pct=asym,
    )


def _landing_metrics(
    time: np.ndarray,
    force: np.ndarray,
    velocity: np.ndarray,
    phases: PhaseBreakdown,
    bw: float,
    jump_height_m: float,
) -> LandingMetrics:
    ld = phases.landing_detail
    if ld is None:
        return LandingMetrics(
            peak_grf_n=0, peak_grf_bw=0, loading_rate_kns=0, contact_velocity_ms=0,
            attenuation_rate_kns=0, control_time_ms=0,
            total_landing_time_ms=phases.landing.duration_ms,
            mrsi=0, lpi_ms=0,
        )

    load_s = ld.loading.start_idx
    load_e = ld.loading.end_idx
    atten_s = ld.attenuation.start_idx
    atten_e = ld.attenuation.end_idx

    peak_grf = float(np.max(force[load_s : load_e + 1])) if load_e > load_s else float(force[load_e])
    contact_vel = abs(float(velocity[load_s])) if load_s < len(velocity) else 0.0

    load_dur_s = ld.loading.duration_ms / 1000
    loading_rate = (peak_grf - float(force[load_s])) / load_dur_s / 1000 if load_dur_s > 0 else 0.0

    min_grf = float(np.min(force[atten_s : atten_e + 1])) if atten_e > atten_s else peak_grf
    atten_dur_s = ld.attenuation.duration_ms / 1000
    atten_rate = (peak_grf - min_grf) / atten_dur_s / 1000 if atten_dur_s > 0 else 0.0

    total_land_ms = phases.landing.duration_ms
    total_land_s = total_land_ms / 1000
    mrsi = jump_height_m / total_land_s if total_land_s > 0 else 0.0
    lpi = contact_vel / total_land_ms if total_land_ms > 0 else 0.0

    return LandingMetrics(
        peak_grf_n=round(peak_grf, 2),
        peak_grf_bw=round(peak_grf / bw, 3),
        loading_rate_kns=round(loading_rate, 3),
        contact_velocity_ms=round(contact_vel, 4),
        attenuation_rate_kns=round(atten_rate, 3),
        control_time_ms=round(ld.control.duration_ms, 2),
        total_landing_time_ms=round(total_land_ms, 2),
        mrsi=round(mrsi, 4),
        lpi_ms=round(lpi, 6),
    )
