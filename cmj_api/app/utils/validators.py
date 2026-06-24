import numpy as np
from app.config import settings


class InsufficientDataError(ValueError):
    pass


class SignalQualityError(ValueError):
    pass


def validate_signal(force: np.ndarray, sample_rate: int) -> None:
    min_s = settings.QUIET_PHASE_MIN_DURATION_S + 1.5
    if len(force) < int(min_s * sample_rate):
        raise InsufficientDataError(
            f"Signal too short ({len(force) / sample_rate:.1f}s). Minimum required: {min_s:.1f}s"
        )
    if not np.all(np.isfinite(force)):
        raise SignalQualityError("Force data contains NaN or Inf values")
    if float(np.mean(force[:sample_rate])) < 100:
        raise SignalQualityError("Initial force too low — athlete may not be standing on plate")
