import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "experiments"))
from generate_report_figures import make_exp1_cost_chart, make_pipeline_diagram, OUT_DIR  # noqa: E402


def test_figures_render_to_nonempty_pdfs():
    make_pipeline_diagram()
    make_exp1_cost_chart()
    for name in ("pipeline.pdf", "exp1_cost.pdf"):
        path = OUT_DIR / name
        assert path.exists()
        assert path.stat().st_size > 1000  # a real rendered PDF, not an empty/broken stub
