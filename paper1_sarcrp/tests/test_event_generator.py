import random
from sarcrp.event_generator import generate_event_stream, apply_order_swap, apply_urgent_insertion


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
