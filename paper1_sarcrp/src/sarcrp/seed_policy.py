"""Seed policy (Task 34): seeds 0-9 were read by hand while diagnosing the
Task 30 mutation bug (e.g. seed 7's per-event trace, medium uncertainty) and
must never be the sole evidence behind a reported claim -- not because any
parameter was tuned to them (none was), but because a reviewer cannot
verify that after the fact, and "we looked at these seeds during
development" is a real (if mild) form of selection even when unintentional.

DEV_SEEDS remains available for smoke tests and reproducing a known
bug/behavior. REPORT_SEEDS is the fresh, never-inspected set every
"record this for the report" step in this plan must use instead."""

DEV_SEEDS = tuple(range(10))
REPORT_SEEDS = tuple(range(20, 40))  # 20 seeds (spec 23.6's stated minimum), none inspected during development
