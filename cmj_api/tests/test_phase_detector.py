import numpy as np
from app.core.preprocessor import preprocess
from app.core.phase_detector import detect_phases
from app.core.metrics import compute_metrics
from tests.conftest import build_test_cmj, FS


def test_all_phases_present():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    for attr in ("quiet", "unweighting", "braking", "propulsive", "flight", "landing"):
        assert getattr(result.phases, attr) is not None


def test_phase_temporal_ordering():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    p = result.phases
    assert p.quiet.end_s <= p.unweighting.start_s + 0.05
    assert p.unweighting.end_s <= p.braking.end_s
    assert p.braking.end_s <= p.propulsive.end_s
    assert p.propulsive.end_s <= p.flight.end_s
    assert p.flight.end_s <= p.landing.end_s


def test_velocity_positive_at_takeoff():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    assert result.velocity[result.phases.flight.start_idx] > 0


def test_jump_height_physiological():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    m = compute_metrics(
        prep.time, prep.force, result.velocity,
        result.phases, prep.body_weight_n, prep.mass_kg,
    )
    assert 0.10 < m.jump_height_m < 1.0


def test_landing_subphases_ordered():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    assert result.phases.landing_detail is not None
    ld = result.phases.landing_detail
    assert ld.loading.end_s <= ld.attenuation.end_s
    assert ld.attenuation.end_s <= ld.control.end_s


def test_flight_force_near_zero():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    result = detect_phases(prep)
    fs_idx = result.phases.flight.start_idx
    fe_idx = result.phases.flight.end_idx
    assert float(np.mean(prep.force[fs_idx:fe_idx])) < 50
