from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
from app.schemas.phase import PhaseBreakdown
from app.schemas.metrics import CMJMetrics


class TrialUploadRequest(BaseModel):
    athlete_id: Optional[str] = None
    session_id: Optional[str] = None
    sample_rate: int = Field(default=1000, ge=100, le=10000)
    force_data: list[float] = Field(..., min_length=100)
    bilateral: bool = False
    force_data_right: Optional[list[float]] = None
    hardware: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("force_data")
    @classmethod
    def validate_force_range(cls, v: list[float]) -> list[float]:
        if any(f < -100 or f > 20_000 for f in v):
            raise ValueError("Force values outside physiological range (-100 to 20000 N)")
        return v

    @model_validator(mode="after")
    def validate_bilateral(self) -> "TrialUploadRequest":
        if self.bilateral and self.force_data_right is None:
            raise ValueError("force_data_right required when bilateral=True")
        if self.force_data_right is not None and len(self.force_data_right) != len(self.force_data):
            raise ValueError("Left and right force arrays must have equal length")
        return self


class TrialResponse(BaseModel):
    trial_id: str
    athlete_id: Optional[str]
    session_id: Optional[str]
    created_at: datetime
    sample_rate: int
    duration_s: float
    status: str
    error: Optional[str] = None
    phases: Optional[PhaseBreakdown] = None
    metrics: Optional[CMJMetrics] = None

    model_config = {"from_attributes": True}
