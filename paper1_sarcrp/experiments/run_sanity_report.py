import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from sarcrp.sanity_checks import run_sanity_checks  # noqa: E402


def main():
    instance = json.loads((Path(__file__).parent / "instances" / "small_layout_mvp.json").read_text())
    report = run_sanity_checks(instance)
    print(f"SC1 (not too easy):    {'PASS' if report.sc1_not_too_easy else 'FAIL'}")
    print(f"SC2 (not too hard):    {'PASS' if report.sc2_not_too_hard else 'FAIL'}")
    print(f"SC3 event frequency:   {report.event_type_frequency}")
    print(f"SC4 (mean impact in [0.2,0.8]): {'PASS' if report.sc4_impact_reasonable else 'FAIL'} (mean={report.mean_impact:.3f})")


if __name__ == "__main__":
    main()
