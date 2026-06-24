from __future__ import annotations
import uuid
from sqlalchemy.orm import Session
from app.db.models import Trial


def create_trial(db: Session, **kwargs) -> Trial:
    trial = Trial(id=str(uuid.uuid4()), **kwargs)
    db.add(trial)
    db.commit()
    db.refresh(trial)
    return trial


def get_trial(db: Session, trial_id: str) -> Trial | None:
    return db.get(Trial, trial_id)


def list_trials(
    db: Session,
    athlete_id: str | None = None,
    session_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Trial]:
    q = db.query(Trial)
    if athlete_id:
        q = q.filter(Trial.athlete_id == athlete_id)
    if session_id:
        q = q.filter(Trial.session_id == session_id)
    return q.order_by(Trial.created_at.desc()).offset(offset).limit(limit).all()
