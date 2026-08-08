import json
from sarcrp.run_logging import log_run


def test_log_run_writes_the_required_fields(tmp_path):
    log_path = log_run("test_script.py", {"seeds": [1, 2, 3]}, duration_sec=1.234, output_paths=["out.csv"], log_dir=tmp_path)
    assert log_path.exists()
    entry = json.loads(log_path.read_text().strip().split("\n")[-1])
    assert entry["script"] == "test_script.py"
    assert entry["params"] == {"seeds": [1, 2, 3]}
    assert entry["duration_sec"] == 1.234
    assert entry["output_paths"] == ["out.csv"]
    assert "git_commit" in entry
    assert "hostname" in entry
    assert "timestamp" in entry


def test_log_run_appends_without_overwriting(tmp_path):
    log_run("a.py", {}, 1.0, [], log_dir=tmp_path)
    log_run("b.py", {}, 2.0, [], log_dir=tmp_path)
    lines = (tmp_path / "run_log.jsonl").read_text().strip().split("\n")
    assert len(lines) == 2
