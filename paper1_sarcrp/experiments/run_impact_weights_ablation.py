"""R1.1 (reviewer critique on the Q1 report): DEFAULT_WEIGHTS silently caps
the achievable impact score at 0.75 (not the nominal 1.0), because
i_blocking is structurally 0.0 throughout Paper 1's scope (Paper 1 never
executes an action's physical effect between two impact estimations -- see
impact_estimator._blocking_impact's docstring). theta_impact=0.30 is
therefore compared against 40% of the score's effective range, not 30% of
its nominal one. This reruns the sanity-check benchmark under an honestly
renormalized weight set (NORMALIZED_WEIGHTS) on REPORT_SEEDS (the fresh,
never-inspected 20-seed set -- see seed_policy.py) and reports whether the
paper's own "trigger rarely fires" finding (SC4 fails, mean_impact=0.090
under default weights, DEV_SEEDS) survives the fix.
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

    default_report = run_sanity_checks(instance, seeds=REPORT_SEEDS, weights=DEFAULT_WEIGHTS)
    normalized_report = run_sanity_checks(instance, seeds=REPORT_SEEDS, weights=NORMALIZED_WEIGHTS)

    print(f"DEFAULT_WEIGHTS:    mean_impact={default_report.mean_impact:.4f}  "
          f"trigger_rate={default_report.trigger_rate:.4f}  SC4={'PASS' if default_report.sc4_impact_reasonable else 'FAIL'}")
    print(f"NORMALIZED_WEIGHTS: mean_impact={normalized_report.mean_impact:.4f}  "
          f"trigger_rate={normalized_report.trigger_rate:.4f}  SC4={'PASS' if normalized_report.sc4_impact_reasonable else 'FAIL'}")

    log_run("run_impact_weights_ablation.py", {"seeds": list(REPORT_SEEDS)}, time.monotonic() - _start, [])


if __name__ == "__main__":
    main()
