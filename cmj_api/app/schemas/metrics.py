from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class PhaseMetrics(BaseModel):
    avg_force_n: float
    peak_force_n: float
    avg_relative_force: float
    peak_relative_force: float
    impulse_ns: float
    duration_ms: float


class LandingMetrics(BaseModel):
    peak_grf_n: float
    peak_grf_bw: float
    loading_rate_kns: float
    contact_velocity_ms: float
    attenuation_rate_kns: float
    control_time_ms: float
    total_landing_time_ms: float
    mrsi: float
    lpi_ms: float


class CMJMetrics(BaseModel):
    body_weight_n: float
    body_mass_kg: float
    jump_height_m: float
    takeoff_velocity_ms: float
    flight_time_ms: float
    unweighting: PhaseMetrics
    braking: PhaseMetrics
    propulsive: PhaseMetrics
    landing: LandingMetrics
    braking_rfd_ns2: Optional[float] = None
    propulsive_rfd_ns2: Optional[float] = None
    peak_power_w: Optional[float] = None
    avg_propulsive_power_w: Optional[float] = None
    asymmetry_index_pct: Optional[float] = None
