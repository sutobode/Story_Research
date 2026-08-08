import json
from pathlib import Path
from sarcrp.sanity_checks import run_sanity_checks, SanityReport


def test_run_sanity_checks_on_the_mvp_instance():
    instance_path = Path(__file__).parent.parent / "experiments" / "instances" / "small_layout_mvp.json"
    instance = json.loads(instance_path.read_text())
    report = run_sanity_checks(instance, seeds=tuple(range(10)))
    assert isinstance(report, SanityReport)
    assert isinstance(report.sc1_not_too_easy, bool)
    assert isinstance(report.sc2_not_too_hard, bool)
    assert 0.0 <= report.mean_impact <= 1.0
    assert set(report.event_type_frequency.keys()) <= {
        "ORDER_SWAP", "URGENT_INSERTION", "ETA_EARLY", "ETA_LATE",
        "PROBABILITY_UPDATE", "STALE_INFORMATION",
    }
    assert abs(sum(report.event_type_frequency.values()) - 1.0) < 1e-6
