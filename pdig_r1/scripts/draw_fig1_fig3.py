"""PDIG R1: redraw Fig 1 (reification loop) and Fig 3 (governance architectures) without
embedded titles and without the superseded 2x/17x/21x figures. Output: ../figures/Fig1.tif, Fig3.tif"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "figures"
plt.rcParams["font.family"] = "DejaVu Serif"


def box(ax, x, y, w, h, text, fc, tc="white", ec=None, lw=1.5, size=11):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                fc=fc, ec=ec or fc, lw=lw))
    ax.text(x, y, text, ha="center", va="center", color=tc, fontsize=size, weight="bold")


def arrow(ax, p, q, color="#555555", ls="-", rad=0.0, lw=2.2):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16, color=color, lw=lw,
                                 linestyle=ls, connectionstyle=f"arc3,rad={rad}"))


# Fig 1
fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
ax.set_xlim(0, 10); ax.set_ylim(0, 9); ax.axis("off")
box(ax, 5, 7.7, 2.6, 1.0, "Documentation\nrequirements", "#3d8eb0")
box(ax, 8.2, 4.5, 2.7, 1.2, "Clinical-\nadministrative\nnegotiation", "#a64d7c", size=10)
box(ax, 5, 1.3, 2.6, 1.0, "Coded data\n(MMDS)", "#707070")
box(ax, 1.8, 4.5, 2.7, 1.0, "Policy, metrics,\nAI training", "#e9975a")
box(ax, 5, 4.5, 2.4, 1.2, "Adaptive AI\nsystem", "white", tc="#b23a2e", ec="#b23a2e", lw=2.5)
arrow(ax, (6.3, 7.3), (7.6, 5.05), rad=-0.2)
arrow(ax, (7.6, 3.95), (6.3, 1.75), rad=-0.2)
arrow(ax, (3.7, 1.75), (2.4, 3.95), rad=-0.2)
arrow(ax, (2.4, 5.05), (3.7, 7.3), rad=-0.2)
arrow(ax, (5, 1.85), (5, 3.85), color="#b23a2e", ls="--")
arrow(ax, (5, 5.15), (5, 7.15), color="#b23a2e", ls="--")
ax.text(5.15, 2.85, "learns from\ncoded data", color="#b23a2e", fontsize=9, style="italic")
ax.text(5.15, 6.15, "outputs written\ninto the record", color="#b23a2e", fontsize=9, style="italic")
ax.text(0.2, 0.15, "Outer loop: human speed (Stage 0)", fontsize=9, color="#555555", style="italic")
ax.text(9.8, 0.15, "Inner loop: machine speed (Stages 2 and 3)", fontsize=9, color="#b23a2e",
        style="italic", ha="right")
fig.savefig(OUT / "Fig1.png", bbox_inches="tight")
fig.savefig(OUT / "Fig1.tif", bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})

# Fig 3
fig, ax = plt.subplots(figsize=(12, 6.2), dpi=300)
ax.set_xlim(0, 12); ax.set_ylim(0, 6.2); ax.axis("off")
cols = [("Clinical-first", "#4e8f52", "Patient safety and\ndiagnostic quality", 0.8,
         ["Red-flag guard", "Differential-diagnosis coach"],
         "Stable if clinical correctness\nis observed; drifts if\nobservability is low"),
        ("Equilibrium", "#3a7bc8", "Balanced clinical and\nadministrative performance", 0.5,
         ["Visit scribe", "Billing optimiser"],
         "Near the threshold;\nrequires longitudinal\nmonitoring"),
        ("Business-first", "#e06c2b", "Operational and\nfinancial performance", 0.2,
         ["Denial analyser", "Capacity planner"],
         "Above the threshold at\nall observability levels\nstudied")]
for i, (name, c, obj, wc, comps, risk) in enumerate(cols):
    x = 2 + 4 * i
    box(ax, x, 5.7, 3.6, 0.6, name, c, size=13)
    ax.text(x, 5.05, "OBJECTIVE", ha="center", fontsize=8, weight="bold", color="#444444")
    ax.text(x, 4.6, obj, ha="center", va="center", fontsize=10)
    ax.text(x, 3.95, "REGION OF THE WEIGHT SPACE (LABEL)", ha="center", fontsize=8, weight="bold", color="#444444")
    left = x - 1.5
    ax.add_patch(plt.Rectangle((left, 3.45), 3.0 * wc, 0.3, fc="#6aa36e", ec="#4e8f52"))
    ax.add_patch(plt.Rectangle((left + 3.0 * wc, 3.45), 3.0 * (1 - wc), 0.3, fc="#ee8b52", ec="#e06c2b"))
    ax.text(x, 3.22, f"clinical {wc:.1f}  /  administrative {1 - wc:.1f}", ha="center", va="center", fontsize=9)
    ax.text(x, 2.95, "TYPICAL COMPONENTS", ha="center", fontsize=8, weight="bold", color="#444444")
    for j, comp in enumerate(comps):
        ax.add_patch(FancyBboxPatch((x - 1.3, 2.25 - 0.55 * j), 2.6, 0.4,
                                    boxstyle="round,pad=0.01,rounding_size=0.05", fc="white", ec=c, lw=1.3))
        ax.text(x, 2.45 - 0.55 * j, comp, ha="center", va="center", fontsize=9)
    ax.text(x, 1.15, "BEHAVIOUR IN THE MODEL (Fig 2)", ha="center", fontsize=8, weight="bold", color="#444444")
    ax.text(x, 0.55, risk, ha="center", va="center", fontsize=9, color=c, weight="bold")
fig.savefig(OUT / "Fig3.png", bbox_inches="tight")
fig.savefig(OUT / "Fig3.tif", bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
print("ok")
