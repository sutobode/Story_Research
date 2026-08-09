"""R1.2 (reviewer critique on the Q1 report): the validated carried_gain
lookahead margin (Scenario E, run_existence_proof.py) lets a foregone gain
accumulate across rounds with no cap and no decay. Is Scenario E's real win
an artifact of that unbounded accumulation, or does it survive under more
conservative variants? Reruns Scenario E on REPORT_SEEDS under:
  - default:        carried_gain_cap=None, carried_gain_decay=1.0 (validated mechanism, unchanged)
  - decayed_half:    carried_gain_decay=0.5 (halves the incoming carry every hop)
  - capped_tight:    carried_gain_cap=0.05 (bounds the carry far below instance A's own gain, ~0.21)
  - capped_and_decayed: both at once
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from run_existence_proof import run_scenario_e  # noqa: E402

from sarcrp.run_logging import log_run  # noqa: E402
from sarcrp.seed_policy import REPORT_SEEDS  # noqa: E402
from sarcrp.stats import cliffs_delta, wilcoxon_signed_rank  # noqa: E402

CONFIGS = {
    "default": {"carried_gain_cap": None, "carried_gain_decay": 1.0},
    "decayed_half": {"carried_gain_cap": None, "carried_gain_decay": 0.5},
    "capped_tight": {"carried_gain_cap": 0.05, "carried_gain_decay": 1.0},
    "capped_and_decayed": {"carried_gain_cap": 0.05, "carried_gain_decay": 0.5},
}


def run_config(name: str, cap: float | None, decay: float) -> dict:
    results = [run_scenario_e(seed, carried_gain_cap=cap, carried_gain_decay=decay) for seed in REPORT_SEEDS]
    updates_lookahead = sum(r["lookahead_decision_b"] == "UPDATE" for r in results)
    better_count = sum(r["lookahead_better"] for r in results)
    myopic_totals = [r["myopic_total"] for r in results]
    lookahead_totals = [r["lookahead_total"] for r in results]
    wr = wilcoxon_signed_rank(lookahead_totals, myopic_totals)
    delta = cliffs_delta(lookahead_totals, myopic_totals)
    return {
        "config": name, "cap": cap, "decay": decay,
        "updates_lookahead": updates_lookahead, "n_seeds": len(REPORT_SEEDS),
        "lookahead_better_count": better_count, "wilcoxon_p": wr.p_value, "cliffs_delta": delta,
    }


def main():
    _start = time.monotonic()
    for name, params in CONFIGS.items():
        r = run_config(name, params["carried_gain_cap"], params["carried_gain_decay"])
        print(f"{r['config']:20s} cap={r['cap']} decay={r['decay']}  "
              f"UPDATE@B={r['updates_lookahead']}/{r['n_seeds']}  "
              f"better={r['lookahead_better_count']}/{r['n_seeds']}  "
              f"wilcoxon_p={r['wilcoxon_p']:.6f}  cliffs_delta={r['cliffs_delta']:.3f}")
    log_run("run_carried_gain_ablation.py", {"seeds": list(REPORT_SEEDS), "configs": list(CONFIGS)}, time.monotonic() - _start, [])


if __name__ == "__main__":
    main()
