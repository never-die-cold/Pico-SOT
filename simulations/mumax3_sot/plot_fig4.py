"""Final Fig. 4 dynamics figure (time-resolved delta-Mz under a 3.7 ps pulse).

Loads the six a_f4 runs (3 field/current combinations x 2 current signs) and
plots the paper's observable

    dMz/Ms (t) = Ms(T(t)) * mz(t) / Ms(t_ref) - mz(t_ref)

grouped by the SOT symmetry:
    平行  Hx*I > 0 : (Hx+, I+) and (Hx-, I-)   -> mz precesses towards -z
    反平行 Hx*I < 0 : (Hx+, I-) and (Hx-, I+)   -> opposite phase
    无 Hx          : (Hx=0, I+) and (Hx=0, I-)  -> no precession
Within each group the two mirror cases coincide (solid = Hx>0, dashed = Hx<0),
so the legend only carries the three groups.

Usage:
    python plot_fig4.py [--runs runs] [--out runs/fig4_full.png]
"""
import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

GROUPS = [
    ("平行  (Hx$\\cdot$I > 0)", "crimson",
     [("a_f4_Hxp160_Ip", "-"), ("a_f4_Hxm160_Im", "--")]),
    ("反平行  (Hx$\\cdot$I < 0)", "tab:blue",
     [("a_f4_Hxp160_Im", "-"), ("a_f4_Hxm160_Ip", "--")]),
    ("无 Hx", "0.25",
     [("a_f4_Hx0_Ip", "-"), ("a_f4_Hx0_Im", "--")]),
]


def load_table(path):
    names = None
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                names = [c.strip().split()[0]
                         for c in line[1:].strip().split("\t") if c.strip()]
            else:
                rows.append([float(x) for x in line.split()])
    idx = {n: i for i, n in enumerate(names)}
    data = np.array(rows)
    return {n: data[:, i] for n, i in idx.items()}


def observable(cols, tref_ps=1.0):
    t = cols["t"]
    mz = cols["mz"]
    ms = cols["Ms"]
    kref = int(np.argmin(np.abs(t - tref_ps * 1e-12)))
    return ms * mz / ms[kref] - mz[kref], kref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "fig4_full.png"))
    args = ap.parse_args()

    fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.6), constrained_layout=True)

    t_ref = None
    for label, color, cases in GROUPS:
        for i, (tag, ls) in enumerate(cases):
            path = os.path.join(args.runs, tag, "out", "table.txt")
            if not os.path.isfile(path):
                raise SystemExit("missing: %s" % path)
            c = load_table(path)
            t = c["t"] * 1e12
            t_ref = t
            dmz, kref = observable(c)
            # the first table row (t=0) is the un-relaxed m=+z state; masking it
            # removes the spurious +1.3% spike present in every Hx != 0 run
            dmz[np.isclose(t, 0.0)] = np.nan
            ax[0].plot(t, dmz, color=color, ls=ls, lw=1.3,
                       label=label if i == 0 else None)

    ax[0].axhline(0, color="k", lw=0.5, alpha=0.4)
    ax[0].set_xlabel("delay (ps)")
    ax[0].set_ylabel(r"$\Delta M_z\,/\,M_s$")
    ax[0].set_xlim(0, 425)
    ax[0].legend(fontsize=8, loc="lower right", title="实线: Hx>0, 虚线: Hx<0",
                 title_fontsize=7.5)

    # right panel: heating and current pulse (identical for all six runs)
    c = load_table(os.path.join(args.runs, "a_f4_Hx0_Ip", "out", "table.txt"))
    ax[1].plot(t_ref, c["T"] - 300.0, color="crimson", lw=1.4, label=r"$\Delta T$ (K)")
    ax[1].set_xlabel("delay (ps)")
    ax[1].set_ylabel(r"$\Delta T$ (K)", color="crimson")
    ax[1].tick_params(axis="y", colors="crimson")
    ax[1].set_xlim(0, 425)
    ax[1].set_ylim(-2, 25)
    axt = ax[1].twinx()
    axt.plot(t_ref, c["J"] / 4e12, color="0.35", lw=1.0, ls=":",
             label=r"$J/J_p$")
    axt.set_ylabel(r"$J\,/\,J_p$", color="0.35")
    axt.tick_params(axis="y", colors="0.35")
    axt.set_ylim(-0.05, 1.45)
    h1, l1 = ax[1].get_legend_handles_labels()
    h2, l2 = axt.get_legend_handles_labels()
    ax[1].legend(h1 + h2, l1 + l2, fontsize=8, loc="upper right")
    ax[1].annotate("echo at 29 ps (t0+ted)", xy=(29, 19), xytext=(75, 15),
                   fontsize=8, color="0.35",
                   arrowprops=dict(arrowstyle="->", color="0.35", lw=0.8))

    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)


if __name__ == "__main__":
    sys.exit(main())
