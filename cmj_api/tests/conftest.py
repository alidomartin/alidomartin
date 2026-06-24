import pytest
import numpy as np
from scipy.ndimage import gaussian_filter1d
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db
from app.db.models import Base

BW = 700.0
FS = 1000

_test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


def _override_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=_test_engine)
    app.dependency_overrides[get_db] = _override_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def build_test_cmj(bw: float = BW, fs: int = FS) -> tuple[np.ndarray, np.ndarray]:
    t = np.arange(0, 3.0, 1 / fs)
    f = np.ones_like(t) * bw
    rng = np.random.default_rng(42)

    def idx(s: float) -> int:
        return int(s * fs)

    f[: idx(1.0)] += rng.normal(0, 3, idx(1.0))
    s, e = idx(1.0), idx(1.3)
    x = np.linspace(0, np.pi, e - s)
    f[s:e] = bw - 280 * np.sin(x) ** 1.4
    s, e = idx(1.3), idx(1.55)
    x = np.linspace(0, 1, e - s)
    f[s:e] = f[s - 1] + (bw * 1.75 - f[s - 1]) * (3 * x ** 2 - 2 * x ** 3)
    s, e = idx(1.55), idx(1.81)
    x = np.linspace(0, 1, e - s)
    f[s:e] = bw * 2.1 * np.sin(np.pi * x) ** 0.75
    f[e - 30 : e] *= np.linspace(1, 0, 30)
    s, e = idx(1.81), idx(2.42)
    f[s:e] = 0
    s = idx(2.42)
    n = len(f) - s
    x = np.linspace(0, 1, n)
    f[s:] = bw + 1800 * np.exp(-x * 12) * (1 - np.exp(-x * 60)) + 400 * np.exp(-x * 5) * np.cos(2 * np.pi * x * 3)
    f[s : s + 8] = np.linspace(0, f[s + 8], 8)
    f = gaussian_filter1d(f, sigma=2)
    return t, f


@pytest.fixture
def cmj_force():
    _, f = build_test_cmj()
    return f


@pytest.fixture
def cmj_time_force():
    return build_test_cmj()
