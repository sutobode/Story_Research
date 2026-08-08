import json
import socket
import subprocess
import time
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[2]  # .../paper1_sarcrp


def get_git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_PACKAGE_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def log_run(script_name: str, params: dict, duration_sec: float, output_paths: list[str], log_dir: Path | None = None) -> Path:
    """Appends one JSON line per run to experiments/logs/run_log.jsonl:
    timestamp, the git commit the code was at, hostname, the exact params
    used, wall-clock duration, and where the output landed. A costly run's
    provenance is always on record this way, not just whatever happened to
    be printed to stdout at the time."""
    log_dir = log_dir or (_PACKAGE_ROOT / "experiments" / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "script": script_name,
        "git_commit": get_git_commit(),
        "hostname": socket.gethostname(),
        "params": params,
        "duration_sec": round(duration_sec, 3),
        "output_paths": output_paths,
    }
    log_path = log_dir / "run_log.jsonl"
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return log_path
