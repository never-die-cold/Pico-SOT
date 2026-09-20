"""Bar chart of the Joule energy per 6 ps pulse for the P9 slide.

Computes E = rho * V * integral J^2 dt with the same accounting as
energy_check.py for the six key cases, then draws the bars used on the
group-meeting slide.

Usage:
    python plot_energy.py [--runs runs] [--out runs/energy_bars.png]
"""
import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from energy_check import RHO, VSTACK, find_table, load_j

CASES = [
    ("si_noh_t20_Jp6",  "6×10¹²\nno heat", "no"),
    ("si_h_t20_Jp10",   "10×10¹²\nheat", "yes"),
    ("si_h_t20_Jp12",   "12×10¹²\nheat", "yes"),
    ("si_h_t20_Jp14",   "14×10¹²\nheat", "yes"),
    ("si_h_t20_Jp20",   "20×10¹²\nheat", "over_tc"),
    ("si_noh_t20_Jp20", "20×10¹²\nno heat", "yes"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "energy_bars.png"))
    args = ap.parse_args()

    labels, energies, kinds = [], [], []
    print("%-16s %10s" % ("case", "E [pJ]"))
    for tag, label, kind in CASES:
        table = find_table(os.path.join(args.runs, tag))
        t, j = load_j(table)
        e = float(np.trapezoid(j * j, t) * RHO * VSTACK)
        labels.append(label)
        energies.append(e * 1e12)
        kinds.append(kind)
        print("%-16s %10.2f" % (tag, e * 1e12))

    face = {"no": "white", "yes": "crimson", "over_tc": "darkorange"}
    edge = {"no": "tab:blue", "yes": "crimson", "over_tc": "darkorange"}
    hatch = {"no": "", "yes": "", "over_tc": "//"}

    fig, ax = plt.subplots(figsize=(6.8, 4.3), constrained_layout=True)
    x = np.arange(len(CASES))
    for xi, e, k in zip(x, energies, kinds):
        ax.bar(xi, e, width=0.62, color=face[k], edgecolor=edge[k],
               hatch=hatch[k], linewidth=1.6, zorder=3)
        ax.text(xi, e + 9, "%.1f" % e, ha="center", va="bottom", fontsize=9)

    ax.axhline(50, color="k", ls="--", lw=1.0, zorder=2)
    ax.text(len(CASES) - 0.45, 56, "paper budget < 50 pJ", ha="right", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("energy per 6 ps pulse (pJ)")
    ax.set_title("Joule energy  E = $\\int J^2 dt\\cdot\\rho V$"
                 "   ($\\rho$=81 $\\mu\\Omega$cm, V=5$\\times$4$\\times$0.015 $\\mu$m$^3$)",
                 fontsize=10.5)
    ax.set_ylim(0, max(energies) * 1.20)
    ax.grid(axis="y", alpha=0.25, lw=0.5, zorder=0)

    handles = [
        Patch(facecolor="white", edgecolor="tab:blue", label="no switch"),
        Patch(facecolor="darkorange", edgecolor="darkorange", hatch="//",
              label="switch, Tmax > Tc"),
        Patch(facecolor="crimson", edgecolor="crimson", label="switch"),
    ]
    ax.legend(handles=handles, fontsize=8.5, loc="upper left")
    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
