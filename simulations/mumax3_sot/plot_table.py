"""Plot mumax3 table.txt files (Fig. 4 / Fig. 3 comparison helper).

Usage:
    python plot_table.py runs/fig4_Hxp_Ip/table.txt [more tables ...]
                         [--tref 1.0] [--out fig4_sim.png]

Left panel : observable  dMz/Ms = Ms(t)*mz(t)/Ms(tref) - mz(tref)
             (the paper's Fig. 4 signal; if the table has no Ms column,
              falls back to mz(t) - mz(tref))
Right panel: temperature rise T-T_room [K] and current pulse J(t).

Column names are read from the '#' header line of table.txt.
"""
import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_table(path):
    names = None
    with open(path, "r") as f:
        for line in f:
            if line.startswith("#"):
                parts = [c.strip() for c in line[1:].strip().split("\t") if c.strip()]
                names = [p.split()[0] for p in parts]
            else:
                break
    data = np.loadtxt(path, comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return {n: data[:, k] for k, n in enumerate(names)}


def observable(cols, tref_ps):
    t = cols["t"]
    mz = cols["mz"]
    kref = int(np.argmin(np.abs(t - tref_ps * 1e-12)))
    if "Ms" in cols:
        ms = cols["Ms"]
        return ms * mz / ms[kref] - mz[kref], kref
    return mz - mz[kref], kref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tables", nargs="+")
    ap.add_argument("--tref", type=float, default=1.0, help="reference time [ps] before the pulse")
    ap.add_argument("--out", default="fig_sim.png")
    args = ap.parse_args()

    fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.6), constrained_layout=True)

    for path in args.tables:
        if not os.path.isfile(path):
            print("skip (missing):", path)
            continue
        cols = load_table(path)
        t_ps = cols["t"] * 1e12
        dmz, kref = observable(cols, args.tref)
        d = os.path.dirname(os.path.abspath(path))
        if os.path.basename(d) == "out":
            d = os.path.dirname(d)
        label = os.path.basename(d) or os.path.basename(path)

        ax[0].plot(t_ps, dmz, label=label, lw=1.2)
        if "T" in cols:
            ax[1].plot(t_ps, cols["T"] - 300.0, label=label, lw=1.2)

        i_min = kref + int(np.argmin(dmz[kref:]))
        print("%-40s  min dMz/Ms = %+.4f at %6.1f ps   final = %+.4f"
              % (label, dmz[i_min], t_ps[i_min], dmz[-1]))

    ax[0].axhline(0, color="k", lw=0.5, alpha=0.4)
    ax[0].set_xlabel("delay (ps)")
    ax[0].set_ylabel(r"$\Delta M_z\,/\,M_s$")
    ax[0].legend(fontsize=7)
    ax[1].set_xlabel("delay (ps)")
    ax[1].set_ylabel(r"$\Delta T$ (K)   /   J (arb.)")
    ax[1].legend(fontsize=7)

    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)


if __name__ == "__main__":
    sys.exit(main())
