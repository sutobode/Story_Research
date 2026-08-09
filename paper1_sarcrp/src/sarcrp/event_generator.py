import random

from sarcrp.schemas import Event

SEVERITY_RANK_SHIFT = {"low": (1, 2), "medium": (3, 5), "high": (6, 8)}
CONFIDENCE_RANGE_BY_UNCERTAINTY = {
    "low": (0.80, 1.00),
    "medium": (0.50, 0.90),
    "high": (0.20, 0.80),
}
EVENT_TYPE_WEIGHTS = {
    "ORDER_SWAP": 0.40,
    "URGENT_INSERTION": 0.25,
    "ETA_SHIFT": 0.20,  # resolves to ETA_EARLY or ETA_LATE
    "PROBABILITY_UPDATE": 0.10,
    "STALE_INFORMATION": 0.05,
}

# Calibration (Q1 reviewer critique on practical significance): P_EVENT was
# a single flat 0.30 for every uncertainty_level -- "low/medium/high" only
# changed event MAGNITUDE (severity, confidence) once an event occurred,
# never how OFTEN one occurred at all, which is not a realistic model of
# what "uncertainty level" should mean operationally.
#
# P_EVENT_BY_UNCERTAINTY["low"]=0.078 is a REAL, cited anchor: Port of
# Casablanca, under an optimized truck appointment system (TAS), had 7.8%
# of truck arrivals rescheduled from their preferred appointment time
# ("A Novel Truck Appointment System for Container Terminals", MDPI
# Sustainability 17(13):5740, 2025, real operational data). This is a
# best-case/optimized-TAS disruption rate, so it anchors "low" uncertainty,
# not an average case.
#
# "medium"/"high" are NOT independently cited -- no descriptive statistic
# for a "medium" or "high"-disruption terminal (e.g. no TAS, or a
# congested/less-optimized one) was found in the accessible literature.
# They are a reasoned scaling of the one real anchor (2.5x, 4.5x), kept
# deliberately explicit and separate from the "low" anchor so a future
# revision can replace them with real data without re-deriving anything.
P_EVENT_BY_UNCERTAINTY = {
    "low": 0.078,     # real: Port of Casablanca, optimized TAS (cited above)
    "medium": 0.195,  # assumption: 2.5x the real low-uncertainty anchor
    "high": 0.351,    # assumption: 4.5x the real low-uncertainty anchor
}
P_EVENT = 0.30  # unchanged, original flat default -- every existing experiment/test keeps using this exact value


def _sample_severity(uncertainty_level: str, rng: random.Random) -> str:
    # Higher uncertainty biases toward larger severities.
    weights = {"low": 0.30, "medium": 0.40, "high": 0.30}
    if uncertainty_level == "high":
        weights = {"low": 0.15, "medium": 0.35, "high": 0.50}
    elif uncertainty_level == "low":
        weights = {"low": 0.55, "medium": 0.35, "high": 0.10}
    return rng.choices(list(weights.keys()), weights=list(weights.values()), k=1)[0]


def _sample_confidence(uncertainty_level: str, rng: random.Random) -> float:
    lo, hi = CONFIDENCE_RANGE_BY_UNCERTAINTY[uncertainty_level]
    return rng.uniform(lo, hi)


def _rank_shift_for(severity: str, rng: random.Random) -> int:
    lo, hi = SEVERITY_RANK_SHIFT[severity]
    return rng.randint(lo, hi)


def apply_order_swap(queue: list[str], severity: str, rng: random.Random) -> list[str]:
    if len(queue) < 2:
        return list(queue)
    shift = min(_rank_shift_for(severity, rng), len(queue) - 1)
    i = rng.randint(0, len(queue) - 1 - shift)
    j = i + shift
    new_queue = list(queue)
    new_queue[i], new_queue[j] = new_queue[j], new_queue[i]
    return new_queue


def apply_urgent_insertion(queue: list[str], severity: str, rng: random.Random) -> list[str]:
    if not queue:
        return list(queue)
    pool = [c for c in queue if c not in queue[:3]] or list(queue)
    container = rng.choice(pool)
    new_queue = [c for c in queue if c != container]
    insert_at = min(_rank_shift_for(severity, rng), len(new_queue))
    new_queue.insert(insert_at, container)
    return new_queue


def apply_eta_shift(queue: list[str], severity: str, rng: random.Random) -> list[str]:
    # ETA_EARLY/ETA_LATE both change rank; direction is chosen by the caller.
    return apply_order_swap(queue, severity, rng)


def _sample_event_type(rng: random.Random) -> str:
    types = list(EVENT_TYPE_WEIGHTS.keys())
    weights = list(EVENT_TYPE_WEIGHTS.values())
    return rng.choices(types, weights=weights, k=1)[0]


def generate_event_stream(
    initial_queue: list[str],
    t_steps: int,
    uncertainty_level: str,
    rng: random.Random,
    event_id_prefix: str = "e",
    fixed_confidence: float | None = None,
    calibrated: bool = False,
) -> list[Event]:
    """calibrated=False (default) reproduces every existing experiment's
    exact numbers via the original flat P_EVENT=0.30. calibrated=True uses
    P_EVENT_BY_UNCERTAINTY instead, so event frequency (not just magnitude)
    depends on uncertainty_level, anchored to a real cited disruption rate
    (see P_EVENT_BY_UNCERTAINTY's docstring above)."""
    queue = list(initial_queue)
    events: list[Event] = []
    p_event = P_EVENT_BY_UNCERTAINTY[uncertainty_level] if calibrated else P_EVENT

    for t in range(1, t_steps + 1):
        if rng.random() > p_event:
            continue

        sampled = _sample_event_type(rng)
        severity = _sample_severity(uncertainty_level, rng)
        confidence = fixed_confidence if fixed_confidence is not None else _sample_confidence(uncertainty_level, rng)
        old_queue = list(queue)

        if sampled == "ORDER_SWAP":
            queue = apply_order_swap(queue, severity, rng)
            event_type = "ORDER_SWAP"
        elif sampled == "URGENT_INSERTION":
            queue = apply_urgent_insertion(queue, severity, rng)
            event_type = "URGENT_INSERTION"
        elif sampled == "ETA_SHIFT":
            queue = apply_eta_shift(queue, severity, rng)
            event_type = "ETA_EARLY" if rng.random() < 0.5 else "ETA_LATE"
        elif sampled == "PROBABILITY_UPDATE":
            event_type = "PROBABILITY_UPDATE"
            # queue unchanged; probability bookkeeping happens outside the queue itself.
        else:
            event_type = "STALE_INFORMATION"
            # queue unchanged; caller delays timestamp_observed for this event.

        affected = sorted(set(old_queue) ^ set(queue)) or (old_queue[:1] if old_queue else [])
        events.append(
            Event(
                event_id=f"{event_id_prefix}{len(events):04d}",
                time_step=t,
                type=event_type,
                severity=severity,
                affected_containers=affected,
                old_queue=old_queue,
                new_queue=list(queue),
                confidence=confidence,
                timestamp_generated=t,
                timestamp_observed=t,
                metadata={},
            )
        )

    return events
