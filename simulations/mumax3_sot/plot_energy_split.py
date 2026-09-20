"""Split (heating on / heating off) bar chart of the Joule energy per pulse.

Same accounting as energy_check.py / plot_energy.py:

    E = rho * V * integral J(t)^2 dt,   rho = 81 uOhm cm,
    V = 5 um x 4 um x 15 nm,

one bar per (theta_DL=0.2, Jp = 6..20 x 10^12 A/m^2), full scan instead of
the six representative cases of energy_bars.png.  Left panel: paper heat
channel (Ms(T), Kz(T)); right panel: T frozen at 300 K (pure LLG/SOT).

Bar colours:  white/blue = no switch, crimson = switches, orange hatched =
switches but Tmax > Tc (HAMR-like, model outside its calibration), grey
hatched = multidomain artefact (|average m| < 0.9, excluded).

Usage:
    python plot_energy_split.py [--runs runs] [--out runs/energy_bars_split.png]
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
from plot_phase import load_points

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

JP_MIN, JP_MAX = 6, 20


def classify(p):
    if p["uni"] < 0.9:
        return "excluded"
    if p["mz"] < -0.5:
        return "over_tc" if p["Tmax"] > 800.0 else "switch"
    return "no"


def fig_split(pts, runs, out):
    face = {"no": "white", "switch": "crimson", "over_tc": "darkorange",
            "excluded": "0.75"}
    edge = {"no": "tab:blue", "switch": "crimson", "over_tc": "darkorange",
            "excluded": "0.35"}
    hatch = {"no": "", "switch": "", "over_tc": "//", "excluded": "xx"}

    fig, ax = plt.subplots(1, 2, figsize=(11.2, 4.5), sharey=True,
                           constrained_layout=True)
    emax = 0.0

    for panel, (axx, heat) in enumerate(zip(ax, (1, 0))):
        sel = sorted([p for p in pts if p["theta"] == "0.2"
                      and p["heat"] == heat
                      and JP_MIN * 1e12 <= p["Jp"] <= JP_MAX * 1e12],
                     key=lambda p: p["Jp"])
        jps, energies, kinds = [], [], []
        for p in sel:
            table = find_table(os.path.join(runs, p["tag"]))
            t, j = load_j(table)
            e = float(np.trapezoid(j * j, t) * RHO * VSTACK)
            jps.append(p["Jp"] / 1e12)
            energies.append(e * 1e12)
            kinds.append(classify(p))
            print("heat=%d %-24s Jp=%4.0fe12  E=%7.2f pJ  mz=%+.3f  |m|=%s  %s"
                  % (heat, p["tag"], p["Jp"] / 1e12, e * 1e12, p["mz"],
                     "%.3f" % p["uni"], kinds[-1]))
        x = np.array(jps) - JP_MIN
        for xi, e, k in zip(x, energies, kinds):
            axx.bar(xi, e, width=0.66, color=face[k], edgecolor=edge[k],
                    hatch=hatch[k], linewidth=0.9, zorder=3)
            axx.text(xi, e + 7, "%.0f" % e, ha="center", va="bottom",
                     fontsize=6, rotation=90, zorder=4)

        axx.axhline(50, color="k", ls="--", lw=1.0, zorder=2)
        axx.text(JP_MAX - JP_MIN + 0.42, 54, "paper budget < 50 pJ",
                 ha="right", fontsize=7.5)
        axx.set_xticks(np.arange(JP_MAX - JP_MIN + 1))
        axx.set_xticklabels([str(v) for v in range(JP_MIN, JP_MAX + 1)],
                            fontsize=7.5)
        axx.set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)", fontsize=10)
        axx.grid(axis="y", alpha=0.25, lw=0.5, zorder=0)
        axx.set_title("heating on ($M_s(T)$, $K_z(T)$)" if heat
                      else "heating off (T = 300 K)", fontsize=10.5)
        if heat:  # 15-17e12 precessional recapture window
            axx.axvspan(15 - 0.5 - JP_MIN, 17 + 0.5 - JP_MIN, color="0.92",
                        zorder=1)
            axx.text(16 - JP_MIN, 465, "recapture\nwindow", ha="center",
                     va="center", fontsize=7, color="0.35", zorder=4)
        if panel == 0:
            axx.set_ylabel("Joule energy per 6 ps pulse (pJ)", fontsize=10)
        emax = max(emax, max(energies))

    handles = [
        Patch(facecolor="white", edgecolor="tab:blue", label="no switch"),
        Patch(facecolor="crimson", edgecolor="crimson", label="switch"),
        Patch(facecolor="darkorange", edgecolor="darkorange", hatch="//",
              label="switch, $T_{max}>T_c$"),
        Patch(facecolor="0.75", edgecolor="0.35", hatch="xx",
              label="multidomain (excluded)"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=4,
               fontsize=8.5, frameon=False)
    fig.suptitle("Joule energy  E = $\\int J^2 dt\\cdot\\rho V$"
                 "   ($\\rho$=81 $\\mu\\Omega$cm, V=5$\\times$4$\\times$0.015 $\\mu$m$^3$,"
                 "  $\\theta_{DL}$=0.2, 6 ps sech$^2$)", fontsize=11)
    ax[0].set_ylim(0, emax * 1.13)
    fig.savefig(out, dpi=200)
    print("saved:", out)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="runs/summary.csv")
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "energy_bars_split.png"))
    args = ap.parse_args()

    pts = load_points(args.summary)
    return fig_split(pts, args.runs, args.out)


if __name__ == "__main__":
    sys.exit(main())
