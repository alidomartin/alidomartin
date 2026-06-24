from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    GRAVITY: float = 9.81
    QUIET_PHASE_MIN_DURATION_S: float = 1.0
    QUIET_PHASE_CV_THRESHOLD: float = 0.01
    BODY_WEIGHT_WINDOW_S: float = 0.5
    FLIGHT_FORCE_THRESHOLD_N: float = 20.0
    UNWEIGHTING_BW_FRACTION: float = 0.99
    DEFAULT_SAMPLE_RATE: int = 1000
    SMOOTHING_SIGMA: float = 2.0
    MAX_UPLOAD_SIZE_MB: int = 50
    DB_PATH: Path = Path("data/cmj.db")

    model_config = {"env_prefix": "CMJ_"}


settings = Settings()
