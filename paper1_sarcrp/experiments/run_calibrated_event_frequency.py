"""Q1 reviewer critique (Positioning/Practical Significance): the event
generator's P_EVENT=0.30 was an uncalibrated internal constant, identical
across "low/medium/high" uncertainty_level -- uncertainty only changed
event MAGNITUDE (severity, confidence), never how OFTEN a disruption
happens, which is not a realistic model of what "uncertainty level" should
mean operationally.

sarcrp.event_generator.P_EVENT_BY_UNCERTAINTY anchors "low" to a real,
cited statistic (Port of Casablanca, optimized truck appointment system:
7.8% of arrivals rescheduled from their preferred time -- "A Novel Truck
Appointment System for Container Terminals", MDPI Sustainability
17(13):5740, 2025). "medium"/"high" are explicit, disclosed extrapolations
(2.5x/4.5x), not independently cited -- no descriptive statistic for a
medium/high-disruption terminal was found in the accessible literature.

This reruns the SC4 mean-impact / trigger-rate analysis on REPORT_SEEDS
under calibrated=True (both alone and combined with R1.1's
NORMALIZED_WEIGHTS) and reports the real numbers against the existing
uncalibrated baseline, honestly -- whichever direction they move.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.impact_estimator import DEFAULT_WEIGHTS, NORMALIZED_WEIGHTS  # noqa: E402
from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.sanity_checks import run_sanity_checks  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402


def main():
    _start = time.monotonic()
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    print(f"instance uncertainty_level: {instance['uncertainty_level']!r}")

    configs = [
        ("uncalibrated, default weights", dict(weights=DEFAULT_WEIGHTS, calibrated=False)),
        ("uncalibrated, normalized weights", dict(weights=NORMALIZED_WEIGHTS, calibrated=False)),
        ("calibrated, default weights", dict(weights=DEFAULT_WEIGHTS, calibrated=True)),
        ("calibrated, normalized weights", dict(weights=NORMALIZED_WEIGHTS, calibrated=True)),
    ]
    for label, kwargs in configs:
        report = run_sanity_checks(instance, seeds=REPORT_SEEDS, **kwargs)
        print(f"{label:35s} mean_impact={report.mean_impact:.4f}  trigger_rate={report.trigger_rate:.4f}  "
              f"SC4={'PASS' if report.sc4_impact_reasonable else 'FAIL'}")

    print("\nSame instance relabeled uncertainty_level='low' -- isolates the real Casablanca "
          "anchor (0.078) against the legacy flat rate (0.30), the largest contrast in the table:")
    low_instance = dict(instance, uncertainty_level="low")
    for label, kwargs in [("uncalibrated (flat 0.30)", dict(weights=DEFAULT_WEIGHTS, calibrated=False)),
                           ("calibrated (real 0.078 anchor)", dict(weights=DEFAULT_WEIGHTS, calibrated=True))]:
        report = run_sanity_checks(low_instance, seeds=REPORT_SEEDS, **kwargs)
        print(f"  {label:35s} mean_impact={report.mean_impact:.4f}  trigger_rate={report.trigger_rate:.4f}  "
              f"SC4={'PASS' if report.sc4_impact_reasonable else 'FAIL'}")

    log_run("run_calibrated_event_frequency.py", {"seeds": list(REPORT_SEEDS), "instance": instance["instance_id"]},
            time.monotonic() - _start, [])


if __name__ == "__main__":
    main()
