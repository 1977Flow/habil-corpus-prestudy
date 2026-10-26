"""PDIG R1: summary tables (S2, S3) and Figure 2 from learning_agent_loop.json.
Outputs: ../results/sim_summary.json, ../results/S2_Table.md, ../results/S3_Table.md,
         ../figures/Fig2_threshold.tif (+ .png preview)"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent.parent
R = json.loads((HERE / "results" / "learning_agent_loop.json").read_text())
runs, meta = R["runs"], R["meta"]
W = sorted({float(k.split("|")[3]) for k in runs if k.startswith("grid|")})
RHO = sorted({float(k.split("|")[2]) for k in runs if k.startswith("grid|")})


def last(k):
    return runs[k]["traj"][-1]


def g(mode, rho, w):
    return runs[f"grid|{mode}|{rho}|{w}"]


summary = {"meta": meta, "true_mcc_share": runs[f"grid|anchored|0.5|0.0"]["true_mcc_share"]}
# Threshold per rho: smallest w at which final JSD exceeds the w=0 value by > 0.01 bits
thr = {}
for mode in ("anchored", "reified"):
    for rho in RHO:
        base = g(mode, rho, 0.0)["traj"][-1][0]
        crit = next((w for w in W if g(mode, rho, w)["traj"][-1][0] - base > 0.01), None)
        thr[f"{mode}|{rho}"] = {"empirical_w_crit": crit,
                                "analytic_mcc_step": round(rho / (1 + rho), 3),
                                "analytic_cc_step": round(2 * rho / (1 + 2 * rho), 3)}
summary["thresholds"] = thr
summary["architectures"] = {}
for mode in ("anchored", "reified"):
    for rho in RHO:
        for w, name in ((0.2, "clinical_first"), (0.5, "equilibrium"), (0.8, "business_first")):
            t = g(mode, rho, w)["traj"]
            summary["architectures"][f"{mode}|{rho}|{name}"] = {
                "jsd_c1": t[0][0], "jsd_c5": t[4][0], "jsd_c20": t[-1][0],
                "mcc_share_c20": t[-1][1], "accuracy_c1": t[0][2], "accuracy_c20": t[-1][2]}
boot = {}
for mode in ("anchored", "reified"):
    for w in (0.2, 0.5, 0.8):
        vals = np.array([runs[k]["traj"][-1] for k in runs if k.startswith("boot|") and k.endswith(f"|{mode}|0.5|{w}")])
        boot[f"{mode}|0.5|{w}"] = {"n": len(vals),
                                   "jsd_c20_p2.5_p50_p97.5": [round(float(np.percentile(vals[:, 0], p)), 4) for p in (2.5, 50, 97.5)],
                                   "acc_c20_p2.5_p50_p97.5": [round(float(np.percentile(vals[:, 2], p)), 4) for p in (2.5, 50, 97.5)]}
summary["bootstrap"] = boot
sens = {}
for k, v in runs.items():
    if k.startswith("sens|"):
        _, name, mode, rho, w = k.split("|")
        sens[f"{name}|{mode}|{w}"] = {"jsd_end": v["traj"][-1][0], "mcc_end": v["traj"][-1][1], "acc_end": v["traj"][-1][2]}
summary["sensitivity"] = sens
(HERE / "results" / "sim_summary.json").write_text(json.dumps(summary, indent=2))

# S2 Table: final JSD / MCC share / accuracy for the full grid
lines = ["# S2 Table. Learning coding agent, full grid (cycle 20)", "",
         f"Model population: {meta['categories']} ICD-10-CM categories, {meta['codes_in_model']} codes, "
         f"{meta['instances']:,} coded instances (true MCC share {summary['true_mcc_share']:.4f}).", ""]
for mode in ("anchored", "reified"):
    lines += [f"## {mode.capitalize()} reference", "",
              "| w_admin | " + " | ".join(f"rho={r}: JSD / MCC share / accuracy" for r in RHO) + " |",
              "|---|" + "---|" * len(RHO)]
    for w in W:
        cells = []
        for rho in RHO:
            j, m, a = g(mode, rho, w)["traj"][-1]
            cells.append(f"{j:.4f} / {m:.3f} / {a:.3f}")
        lines.append(f"| {w:.2f} | " + " | ".join(cells) + " |")
    lines.append("")
(HERE / "results" / "S2_Table.md").write_text("\n".join(lines), encoding="utf-8")

lines = ["# S3 Table. Sensitivity (rho = 0.5) and category bootstrap (30 resamples)", "",
         "| Variant | Reference | w_admin | JSD (cycle end) | MCC share | Accuracy |", "|---|---|---|---|---|---|"]
for k in sorted(sens):
    name, mode, w = k.split("|")
    s = sens[k]
    lines.append(f"| {name} | {mode} | {w} | {s['jsd_end']:.4f} | {s['mcc_end']:.3f} | {s['acc_end']:.3f} |")
lines += ["", "| Bootstrap | Reference | w_admin | JSD cycle 20 (2.5%, 50%, 97.5%) | Accuracy cycle 20 (2.5%, 50%, 97.5%) |",
          "|---|---|---|---|---|"]
for k, v in boot.items():
    mode, rho, w = k.split("|")
    lines.append(f"| categories | {mode} | {w} | {v['jsd_c20_p2.5_p50_p97.5']} | {v['acc_c20_p2.5_p50_p97.5']} |")
(HERE / "results" / "S3_Table.md").write_text("\n".join(lines), encoding="utf-8")

# Figure 2
fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), dpi=300)
cols = {0.1: "#9e3d22", 0.25: "#d9822b", 0.5: "#3b75af", 1.0: "#2a9d8f"}
for rho in RHO:
    axes[0].plot(W, [g("anchored", rho, w)["traj"][-1][0] for w in W], color=cols[rho], label=f"rho = {rho}")
    axes[0].plot(W, [g("reified", rho, w)["traj"][-1][0] for w in W], color=cols[rho], ls="--")
    axes[0].axvline(rho / (1 + rho), color=cols[rho], lw=0.6, ls=":")
axes[0].set(xlabel="administrative weight w_admin", ylabel="JSD to true codes, cycle 20 (bits)",
            title="A  Final divergence")
axes[0].legend(frameon=False, fontsize=7)
for rho in RHO:
    axes[1].plot(W, [g("anchored", rho, w)["traj"][-1][2] for w in W], color=cols[rho])
    axes[1].plot(W, [g("reified", rho, w)["traj"][-1][2] for w in W], color=cols[rho], ls="--")
axes[1].axhline(0.95, color="grey", lw=0.6, ls=":")
axes[1].set(xlabel="administrative weight w_admin", ylabel="coding accuracy, cycle 20",
            title="B  Accuracy (dotted: start 0.95)")
for w, c in ((0.2, "#2a9d8f"), (0.5, "#3b75af"), (0.8, "#d9822b")):
    for mode, ls in (("anchored", "-"), ("reified", "--")):
        axes[2].plot(range(1, 21), [x[0] for x in g(mode, 0.5, w)["traj"]], color=c, ls=ls,
                     label=f"w_admin {w}" if mode == "anchored" else None)
axes[2].set(xlabel="cycle", ylabel="JSD to true codes (bits)", title="C  Trajectories at rho = 0.5")
axes[2].legend(frameon=False, fontsize=7)
for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)
fig.text(0.01, -0.02, "Solid: anchored reference. Dashed: reified reference. Dotted verticals in A: analytic threshold rho/(1+rho).",
         fontsize=7)
fig.tight_layout()
out = HERE / "figures"
out.mkdir(exist_ok=True)
fig.savefig(out / "Fig2_threshold.png", bbox_inches="tight")
fig.savefig(out / "Fig2_threshold.tif", bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
print(json.dumps({"thresholds": thr, "bootstrap": boot}, indent=1))
for k, v in summary["architectures"].items():
    print(k, v)
