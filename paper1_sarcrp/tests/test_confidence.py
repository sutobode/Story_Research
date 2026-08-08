import math
from sarcrp.confidence import compute_confidence


def test_zero_age_returns_base_confidence():
    assert compute_confidence(base_confidence=0.9, age=0, tau_age=10.0) == 0.9


def test_decay_matches_formula():
    # Conf(I) = base_confidence * exp(-age / tau_age)  (spec 38.4)
    result = compute_confidence(base_confidence=1.0, age=10, tau_age=10.0)
    assert math.isclose(result, math.exp(-1.0), rel_tol=1e-9)


def test_older_age_gives_lower_confidence():
    fresh = compute_confidence(base_confidence=1.0, age=1, tau_age=10.0)
    stale = compute_confidence(base_confidence=1.0, age=50, tau_age=10.0)
    assert stale < fresh
