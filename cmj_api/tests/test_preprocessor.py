import numpy as np
from app.core.preprocessor import preprocess
from tests.conftest import build_test_cmj, BW, FS


def test_body_weight_within_tolerance():
    _, f = build_test_cmj(bw=700.0)
    prep = preprocess(f, FS)
    assert abs(prep.body_weight_n - 700.0) < 20.0


def test_time_vector_matches_force_length():
    _, f = build_test_cmj()
    prep = preprocess(f, FS)
    assert len(prep.time) == len(prep.force)


def test_mass_derived_from_bw():
    _, f = build_test_cmj(bw=700.0)
    prep = preprocess(f, FS)
    assert abs(prep.mass_kg - 700.0 / 9.81) < 1.0


def test_smoothing_reduces_variance():
    _, f = build_test_cmj()
    noisy = f + np.random.default_rng(0).normal(0, 50, len(f))
    prep_smooth = preprocess(noisy, FS, smooth=True)
    prep_raw = preprocess(noisy, FS, smooth=False)
    assert prep_smooth.force.std() < prep_raw.force.std()
