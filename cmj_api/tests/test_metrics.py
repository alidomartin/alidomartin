from app.core.preprocessor import preprocess
from app.core.phase_detector import detect_phases
from app.core.metrics import compute_metrics
from tests.conftest import build_test_cmj, FS, BW


def _run(bw=BW):
    _, f = build_test_cmj(bw=bw)
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    return compute_metrics(prep.time, prep.force, result.velocity, result.phases, prep.body_weight_n, prep.mass_kg)


def test_body_weight_accurate():
    m = _run(bw=700.0)
    assert abs(m.body_weight_n - 700.0) < 20


def test_mass_accurate():
    m = _run()
    assert abs(m.body_mass_kg - BW / 9.81) < 1.0


def test_propulsive_impulse_positive():
    assert _run().propulsive.impulse_ns > 0


def test_peak_power_positive():
    assert _run().peak_power_w > 0


def test_flight_time_physiological():
    m = _run()
    assert 100 < m.flight_time_ms < 1000


def test_mrsi_positive():
    assert _run().landing.mrsi > 0


def test_rfd_values_positive():
    m = _run()
    assert m.braking_rfd_ns2 > 0
    assert m.propulsive_rfd_ns2 > 0
