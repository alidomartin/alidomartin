from __future__ import annotations
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.trial import TrialUploadRequest, TrialResponse
from app.schemas.phase import PhaseBreakdown
from app.schemas.metrics import CMJMetrics
from app.core.preprocessor import preprocess
from app.core.phase_detector import detect_phases
from app.core.metrics import compute_metrics
from app.utils.validators import validate_signal
from app.utils.parsers import parse_hardware_csv
from app.db import crud
from app.db.models import Trial

router = APIRouter(prefix="/trials", tags=["trials"])


@router.post("/", response_model=TrialResponse, status_code=201)
async def upload_trial(payload: TrialUploadRequest, db: Session = Depends(get_db)):
    """Submit raw force plate data for CMJ phase analysis."""
    force = np.array(payload.force_data, dtype=float)
    force_right = np.array(payload.force_data_right, dtype=float) if payload.force_data_right else None

    phases_data = None
    metrics_data = None
    status = "analyzed"
    error = None

    try:
        validate_signal(force, payload.sample_rate)
        prep = preprocess(force, payload.sample_rate)
        result = detect_phases(prep)
        metrics = compute_metrics(
            prep.time, prep.force, result.velocity,
            result.phases, prep.body_weight_n, prep.mass_kg,
            force_right=force_right,
        )
        phases_data = result.phases.model_dump()
        metrics_data = metrics.model_dump()
    except ValueError as exc:
        status = "insufficient_data"
        error = str(exc)
    except Exception as exc:
        status = "error"
        error = f"Analysis failed: {exc}"

    trial = crud.create_trial(
        db,
        athlete_id=payload.athlete_id,
        session_id=payload.session_id,
        sample_rate=payload.sample_rate,
        duration_s=len(force) / payload.sample_rate,
        hardware=payload.hardware,
        notes=payload.notes,
        bilateral=payload.bilateral,
        status=status,
        error=error,
        phases_json=phases_data,
        metrics_json=metrics_data,
    )
    return _to_response(trial)


@router.post("/upload-csv", response_model=TrialResponse, status_code=201)
async def upload_csv(
    file: UploadFile = File(...),
    sample_rate: int = Query(default=1000, ge=100, le=10000),
    athlete_id: str | None = Query(default=None),
    vendor: str | None = Query(default=None, description="hawkin | amti | kistler | bertec | vald"),
    db: Session = Depends(get_db),
):
    """Upload a CSV file from any force plate vendor and analyze."""
    content = await file.read()
    try:
        force_arr, detected_sr = parse_hardware_csv(content, vendor)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"CSV parse error: {exc}")

    effective_sr = detected_sr if vendor == "hawkin" else sample_rate
    payload = TrialUploadRequest(
        athlete_id=athlete_id,
        sample_rate=effective_sr,
        force_data=force_arr.tolist(),
        hardware=vendor,
    )
    return await upload_trial(payload, db)


@router.get("/", response_model=list[TrialResponse])
def list_trials(
    athlete_id: str | None = Query(default=None),
    session_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    trials = crud.list_trials(db, athlete_id=athlete_id, session_id=session_id,
                               limit=limit, offset=offset)
    return [_to_response(t) for t in trials]


@router.get("/{trial_id}", response_model=TrialResponse)
def get_trial(trial_id: str, db: Session = Depends(get_db)):
    trial = crud.get_trial(db, trial_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    return _to_response(trial)


def _to_response(trial: Trial) -> TrialResponse:
    return TrialResponse(
        trial_id=trial.id,
        athlete_id=trial.athlete_id,
        session_id=trial.session_id,
        created_at=trial.created_at,
        sample_rate=trial.sample_rate,
        duration_s=trial.duration_s,
        status=trial.status,
        error=trial.error,
        phases=PhaseBreakdown(**trial.phases_json) if trial.phases_json else None,
        metrics=CMJMetrics(**trial.metrics_json) if trial.metrics_json else None,
    )
