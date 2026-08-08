import math


def compute_confidence(base_confidence: float, age: int, tau_age: float = 10.0) -> float:
    """Conf(I) = base_confidence * exp(-age / tau_age)  (spec 38.4, default tau_age=10)."""
    return base_confidence * math.exp(-age / tau_age)
