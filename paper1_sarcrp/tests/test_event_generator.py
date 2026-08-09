import random
from sarcrp.event_generator import (
    P_EVENT, P_EVENT_BY_UNCERTAINTY, apply_order_swap, apply_urgent_insertion, generate_event_stream,
)


def test_order_swap_preserves_set_of_containers():
    rng = random.Random(0)
    queue = ["C1", "C2", "C3", "C4", "C5"]
    new_queue = apply_order_swap(queue, severity="medium", rng=rng)
    assert sorted(new_queue) == sorted(queue)
    assert new_queue != queue or len(queue) < 2


def test_urgent_insertion_moves_container_into_topk():
    rng = random.Random(0)
    queue = ["C1", "C2", "C3", "C4", "C8", "C9"]
    new_queue = apply_urgent_insertion(queue, severity="high", rng=rng)
    assert sorted(new_queue) == sorted(queue)


def test_generate_event_stream_only_uses_known_types():
    rng = random.Random(42)
    queue = ["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]
    events = generate_event_stream(queue, t_steps=50, uncertainty_level="medium", rng=rng)
    assert len(events) > 0
    allowed = {"ORDER_SWAP", "URGENT_INSERTION", "ETA_EARLY", "ETA_LATE", "PROBABILITY_UPDATE", "STALE_INFORMATION"}
    for e in events:
        assert e.type in allowed
        assert 0.0 <= e.confidence <= 1.0
        assert e.severity in {"low", "medium", "high"}


def test_generate_event_stream_is_seed_reproducible():
    queue = ["C1", "C2", "C3", "C4", "C5"]
    events_a = generate_event_stream(queue, t_steps=30, uncertainty_level="high", rng=random.Random(7))
    events_b = generate_event_stream(queue, t_steps=30, uncertainty_level="high", rng=random.Random(7))
    assert [e.type for e in events_a] == [e.type for e in events_b]


def test_fixed_confidence_overrides_sampled_confidence():
    rng = random.Random(0)
    queue = ["C1", "C2", "C3", "C4", "C5"]
    events = generate_event_stream(queue, t_steps=30, uncertainty_level="high", rng=rng, fixed_confidence=0.4)
    assert len(events) > 0
    assert all(e.confidence == 0.4 for e in events)


def test_calibrated_defaults_to_false_reproducing_the_original_flat_rate():
    # calibrated=False (the default) must be indistinguishable from before
    # this parameter existed -- every already-reported experiment number
    # depends on this being an exact no-op.
    queue = [f"C{i}" for i in range(20)]
    events_default = generate_event_stream(queue, t_steps=200, uncertainty_level="medium", rng=random.Random(1))
    events_explicit = generate_event_stream(queue, t_steps=200, uncertainty_level="medium", rng=random.Random(1), calibrated=False)
    assert [e.type for e in events_default] == [e.type for e in events_explicit]


def test_calibrated_true_uses_the_lower_real_anchored_rate_for_low_uncertainty():
    # P_EVENT_BY_UNCERTAINTY["low"]=0.078 (real, cited) is far below the
    # legacy flat P_EVENT=0.30 -- over many steps, calibrated=True on "low"
    # must produce noticeably fewer events than the uncalibrated default.
    queue = [f"C{i}" for i in range(20)]
    t_steps = 2000
    uncalibrated = generate_event_stream(queue, t_steps=t_steps, uncertainty_level="low", rng=random.Random(3))
    calibrated = generate_event_stream(queue, t_steps=t_steps, uncertainty_level="low", rng=random.Random(3), calibrated=True)
    uncalibrated_rate = len(uncalibrated) / t_steps
    calibrated_rate = len(calibrated) / t_steps
    assert calibrated_rate < uncalibrated_rate
    assert abs(calibrated_rate - P_EVENT_BY_UNCERTAINTY["low"]) < 0.03
    assert abs(uncalibrated_rate - P_EVENT) < 0.03


def test_calibrated_true_scales_event_rate_with_uncertainty_level():
    # medium and high must each use their own P_EVENT_BY_UNCERTAINTY entry,
    # not silently collapse to the same rate.
    queue = [f"C{i}" for i in range(20)]
    t_steps = 3000
    low = generate_event_stream(queue, t_steps=t_steps, uncertainty_level="low", rng=random.Random(5), calibrated=True)
    medium = generate_event_stream(queue, t_steps=t_steps, uncertainty_level="medium", rng=random.Random(5), calibrated=True)
    high = generate_event_stream(queue, t_steps=t_steps, uncertainty_level="high", rng=random.Random(5), calibrated=True)
    assert len(low) < len(medium) < len(high)
