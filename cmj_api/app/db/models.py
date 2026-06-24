from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
import uuid


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Trial(Base):
    __tablename__ = "trials"

    id = Column(String, primary_key=True, default=_uuid)
    athlete_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sample_rate = Column(Integer, nullable=False)
    duration_s = Column(Float, nullable=False)
    hardware = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    bilateral = Column(Boolean, default=False)
    status = Column(String, nullable=False, default="analyzed")
    error = Column(Text, nullable=True)
    phases_json = Column(JSON, nullable=True)
    metrics_json = Column(JSON, nullable=True)
