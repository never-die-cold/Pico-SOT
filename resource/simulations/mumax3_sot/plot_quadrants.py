"""Final figure: q1-q4 final states tiled into a 2x2 panel (Fig. 3 quadrants).

Reads the OVF2_BINARY snapshots (m_final.ovf) of the four polarity/field
combinations directly and renders the out-of-plane component mz, so the
uniform (domain-wall-free) coherent reversal is visible in the colour map.

Quadrants (paper convention, parallel -> -Mz, antiparallel -> +Mz):
    q1  Hx>0, I>0   parallel       -> -Mz
    q2  Hx<0, I>0   antiparallel   -> +Mz
    q3  Hx>0, I<0   antiparallel   -> +Mz
    q4  Hx<0, I<0   parallel       -> -Mz

Usage:
    python plot_quadrants.py [--runs runs] [--out runs/q_quadrants.png]
"""
import argparse
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

CASES = [
    ("q1_Hxp_Ip",  "(a) q1  Hx>0, I>0  (平行)"),
    ("q2_Hxm_Ip",  "(b) q2  Hx<0, I>0  (反平行)"),
    ("q3_Hxp_Im",  "(c) q3  Hx>0, I<0  (反平行)"),
    ("q4_Hxm_Im",  "(d) q4  Hx<0, I<0  (平行)"),
]


def read_ovf(path):
    """Return m as an (ny, nx, valdim) array from an OVF2_BINARY file."""
    raw = open(path, "rb").read()
    i = raw.find(b"# Begin: Data Binary 4")
    if i < 0:
        raise ValueError("not an OVF2 binary file: %s" % path)
    head = raw[:i].decode("ascii", "replace")

    def key(name):
        m = re.search(r"^# %s:\s*(\S+)" % name, head, re.M)
        if m is None:
            raise ValueError("missing %s in %s" % (name, path))
        return m.group(1)

    nx, ny, nz = (int(key(k)) for k in ("xnodes", "ynodes", "znodes"))
    dim = int(key("valuedim"))
    xstep, ystep = float(key("xstepsize")), float(key("ystepsize"))
    j = raw.find(b"\n", i) + 1
    n = nx * ny * nz * dim
    data = np.frombuffer(raw, dtype="<f4", count=n, offset=j + 4)
    return data.reshape(nz, ny, nx, dim)[0], (nx * xstep, ny * ystep)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "q_quadrants.png"))
    args = ap.parse_args()

    fig, axes = plt.subplots(2, 2, figsize=(8.6, 7.4), constrained_layout=True)
    im = None
    ext = None
    for ax, (tag, title) in zip(axes.ravel(), CASES):
        path = os.path.join(args.runs, tag, "out", "m_final.ovf")
        if not os.path.isfile(path):
            raise SystemExit("missing: %s" % path)
        m, (lx, ly) = read_ovf(path)
        mz = m[:, :, 2]
        ext = [0, lx * 1e6, 0, ly * 1e6]
        im = ax.imshow(mz, origin="lower", extent=ext, cmap="RdBu_r",
                       vmin=-1, vmax=1, interpolation="nearest", aspect="equal")
        ax.set_title("%s\n$\\langle m_z \\rangle$ = %+.3f" % (title, mz.mean()),
                     fontsize=10)
        ax.set_xlabel(r"$x$ ($\mu$m)")
        ax.set_ylabel(r"$y$ ($\mu$m)")
        ax.set_xticks([0, 1, 2, 3, 4, 5])
        ax.set_yticks([0, 1, 2, 3, 4])

    cb = fig.colorbar(im, ax=axes, shrink=0.82, pad=0.02)
    cb.set_label(r"$m_z$")
    fig.suptitle(
        "Final states after one 6 ps pulse: uniform single domains, no domain walls\n"
        "(q1/q4 reverse to $-M_z$; only the open-boundary edge column stays pinned; "
        "5$\\times$4 $\\mu$m device)", fontsize=11)
    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)


if __name__ == "__main__":
    sys.exit(main())
