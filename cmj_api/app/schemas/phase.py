from __future__ import annotations
from pydantic import BaseModel
from typing import Optional


class PhaseWindow(BaseModel):
    start_s: float
    end_s: float
    start_idx: int
    end_idx: int
    duration_ms: float


class LandingSubPhases(BaseModel):
    loading: PhaseWindow
    attenuation: PhaseWindow
    control: PhaseWindow


class PhaseBreakdown(BaseModel):
    quiet: PhaseWindow
    unweighting: PhaseWindow
    braking: PhaseWindow
    transfer_s: float
    propulsive: PhaseWindow
    flight: PhaseWindow
    landing: PhaseWindow
    landing_detail: Optional[LandingSubPhases] = None
