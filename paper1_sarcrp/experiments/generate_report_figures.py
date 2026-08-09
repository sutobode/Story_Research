"""Generates the report's two figures as standalone PDFs via matplotlib
(tikz/pgfplots were unavailable -- the server's texlive2019 install has no
internet-reachable CTAN mirror for tlmgr, so figures are rendered here
instead and included via \\includegraphics). Run once; commit the
resulting PDFs alongside main.tex/main.pdf so the report doesn't depend
on re-running this script to build.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT_DIR = Path(__file__).parent.parent.parent / "writeups" / "paper1_q1_report" / "figures"


def make_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    def box(x, y, w, h, text, fc="white"):
        ax.add_patch(plt.Rectangle((x, y), w, h, fill=True, facecolor=fc, edgecolor="black"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8)

    def arrow(x1, y1, x2, y2, label=None):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black"))
        if label:
            ax.text((x1 + x2) / 2 + 0.15, (y1 + y2) / 2, label, fontsize=7, style="italic")

    box(0.2, 4.7, 2.0, 0.9, "Retrieval queue\nchanges ($Q_{old}\\to Q_{new}$)")
    box(2.7, 4.7, 2.0, 0.9, "Compute Impact\n(Eq. impact)")
    box(5.2, 4.7, 2.0, 0.9, "Impact $\\geq \\theta_{impact}$?", fc="#f0f0f0")
    box(7.7, 4.7, 2.0, 0.9, "KEEP $P_{old}$")
    box(5.2, 3.2, 2.0, 0.9, "Freeze first $h_f$\nactions of $P_{old}$")
    box(5.2, 1.7, 2.0, 0.9, "Generate $C_0..C_3$,\nscore via Eq. objective")
    box(5.2, 0.2, 2.0, 0.9, "Fallback margin:\n$J_{old}-J_{best}>\\tau$?\n(+carried\\_gain)", fc="#f0f0f0")
    box(2.5, 0.2, 2.0, 0.9, "KEEP $P_{old}$\n(carry gain forward)")
    box(7.7, 0.2, 2.0, 0.9, "UPDATE to $C_{best}$")

    arrow(2.2, 5.15, 2.7, 5.15)
    arrow(4.7, 5.15, 5.2, 5.15)
    arrow(7.2, 5.15, 7.7, 5.15, "no")
    arrow(6.2, 4.7, 6.2, 4.1, "yes")
    arrow(6.2, 3.2, 6.2, 2.6)
    arrow(6.2, 1.7, 6.2, 1.1)
    arrow(5.2, 0.65, 4.5, 0.65, "no")
    arrow(7.2, 0.65, 7.7, 0.65, "yes")

    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "pipeline.pdf")
    plt.close(fig)


def make_exp1_cost_chart():
    levels = ["low", "medium", "high"]
    data = {
        "Static": [7.042, 7.052, 7.059],
        "Full Reopt.": [19.045, 21.866, 23.333],
        "Periodic": [11.118, 11.644, 11.612],
        "MPC": [16.632, 17.789, 18.888],
        "SAR-CRP": [7.042, 7.052, 7.059],
    }
    x = range(len(levels))
    width = 0.15
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, (label, values) in enumerate(data.items()):
        offset = (i - (len(data) - 1) / 2) * width
        ax.bar([xi + offset for xi in x], values, width=width, label=label)
    ax.set_xticks(list(x))
    ax.set_xticklabels(levels)
    ax.set_ylabel("Mean total cost $J$")
    ax.set_xlabel("Uncertainty level")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=5, fontsize=8)
    fig.tight_layout()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_DIR / "exp1_cost.pdf")
    plt.close(fig)


if __name__ == "__main__":
    make_pipeline_diagram()
    make_exp1_cost_chart()
    print(f"Wrote {OUT_DIR / 'pipeline.pdf'} and {OUT_DIR / 'exp1_cost.pdf'}")
