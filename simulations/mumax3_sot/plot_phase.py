"""Final switching-threshold plots from runs/summary.csv (SI-parameter model).

With the SI heat channel the peak temperature is fixed by the current,
Tmax = 300 + 50.4 K (Jp/6e12)^2, so the old 2D (Jp, Tmax) phase map
collapses into 1D threshold curves.  This script plots:

    phase_map.png    mz_final vs Jp for the four series
                     (theta_DL = 0.2/0.3 x heating on/off)
    phase_traces.png mz(t) and T(t) around the theta=0.2 heated boundary
    phase_speed.png  crossing time vs Jp (switched cases)

B2/B3-style controls (theta~0, Kz frozen) and Hx=0 symmetry checks are
excluded; they live in mechanism_compare.png.

Usage:
    python plot_phase.py [--summary runs/summary.csv] [--outdir runs]
"""
import argparse
import csv
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

SERIES = {  # tag pattern -> (label, color, linestyle)
    ("0.2", "1"): ("$\\theta_{DL}$=0.2, heating on", "crimson", "-"),
    ("0.2", "0"): ("$\\theta_{DL}$=0.2, heating off", "tab:blue", "-"),
    ("0.3", "1"): ("$\\theta_{DL}$=0.3, heating on", "darkorange", "--"),
    ("0.3", "0"): ("$\\theta_{DL}$=0.3, heating off", "tab:green", "--"),
}


def load_points(summary):
    pts = []
    pat = re.compile(r"^si_(h|noh)_t(\d+)_Jp(\d+)$")
    with open(summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("model") != "si":
                continue
            m = pat.match(row["tag"])
            if not m:
                continue
            pts.append({
                "tag": row["tag"],
                "heat": 1 if m.group(1) == "h" else 0,
                "theta": "0." + m.group(2)[0],  # 20 -> 0.2, 30 -> 0.3
                "Jp": float(row["Jp"]),
                "Tmax": float(row["Tmax_K"]),
                "mz": float(row["mz_final"]),
                "t_cross": float(row["t_cross_ps"]) if row["t_cross_ps"] else np.nan,
            })
    assert pts, "no si_ threshold points found"
    return pts


def load_table(path):
    names = None
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                names = [c.strip().split()[0] for c in line[1:].strip().split("\t") if c.strip()]
            else:
                rows.append([float(x) for x in line.split()])
    idx = {n: i for i, n in enumerate(names)}
    data = np.array(rows)
    return {n: data[:, i] for n, i in idx.items()}


def style(ax):
    ax.grid(alpha=0.25, lw=0.5)


def fig_map(pts, out):
    fig, ax = plt.subplots(figsize=(6.4, 4.2), constrained_layout=True)
    # Tmax scale as a secondary y-axis for the heated series
    for key, (label, color, ls) in SERIES.items():
        th, heat = key
        g = sorted([p for p in pts if p["theta"] == th and p["heat"] == int(heat)],
                   key=lambda p: p["Jp"])
        if not g:
            continue
        x = [p["Jp"] / 1e12 for p in g]
        y = [p["mz"] for p in g]
        ax.plot(x, y, ls, color=color, lw=1.4, marker="o", ms=3.5,
                label=label)
    ax.axhline(0, color="k", lw=0.6, alpha=0.5)
    ax.axhline(-0.5, color="k", ls="--", lw=0.7, alpha=0.5)
    ax.text(6.1, -0.42, "switch criterion", fontsize=7, color="0.35")
    ax.set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax.set_ylabel("final $m_z$")
    ax.set_title("Switching threshold, 6 ps sech$^2$ pulse, Hx=160 mT\n"
                 "SI model: $T_{max}$ = 300 + 50.4 K ($J_p$/6e12)$^2$")
    ax.legend(fontsize=7.5, loc="lower left")
    style(ax)
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_traces(tags, out):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.3), constrained_layout=True)
    refs = ["si_h_t20_Jp9", "si_h_t20_Jp10"]
    for tag in tags + refs:
        path = os.path.join(os.path.dirname(out), tag, "out", "table.txt")
        if not os.path.isfile(path):
            print("skip (missing):", path)
            continue
        c = load_table(path)
        t = c["t"] * 1e12
        mz = c["mz"]
        col = "tab:blue" if mz[-1] > 0 else "crimson"
        if tag in refs:
            col = "gray"
        ax[0].plot(t, mz, lw=1.1, color=col, label=tag)
        ax[1].plot(t, c["T"], lw=1.1, color=col)
    ax[0].axhline(0, color="k", lw=0.5, alpha=0.5)
    ax[0].axvline(24, color="k", lw=0.5, alpha=0.2)
    ax[0].set_xlim(0, 160)
    ax[0].set_xlabel("time (ps)")
    ax[0].set_ylabel("average mz")
    ax[0].set_title("Boundary cases: mz(t)")
    ax[0].legend(fontsize=6.5, loc="lower right")
    style(ax[0])
    ax[1].axhline(800, color="gray", ls=":", lw=0.8)
    ax[1].set_xlim(0, 160)
    ax[1].set_ylim(280, 820)
    ax[1].set_xlabel("time (ps)")
    ax[1].set_ylabel("T (K)")
    ax[1].set_title("T(t)  (SI heat channel)")
    style(ax[1])
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_speed(pts, out):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4), constrained_layout=True)
    for key, (label, color, ls) in SERIES.items():
        th, heat = key
        g = sorted([p for p in pts if p["theta"] == th and p["heat"] == int(heat)
                    and p["t_cross"] == p["t_cross"] and p["mz"] < -0.5],
                   key=lambda p: p["Jp"])
        if not g:
            continue
        ax[0].plot([p["Jp"] / 1e12 for p in g], [p["t_cross"] for p in g],
                   ls, marker="o", ms=4, lw=1.1, color=color, label=label)
    ax[0].set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax[0].set_ylabel(r"$t_{cross}$ (ps)")
    ax[0].set_title("Crossing time (switched cases)")
    ax[0].legend(fontsize=7)
    style(ax[0])
    for p in pts:
        ax[1].scatter(p["Jp"] / 1e12, p["mz"], s=30, c=[p["Tmax"]], cmap="inferno",
                      vmin=300, vmax=900)
    sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(300, 900))
    fig.colorbar(sm, ax=ax[1], label=r"$T_{max}$ (K)")
    ax[1].axhline(-0.5, color="k", ls="--", lw=0.8)
    ax[1].set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax[1].set_ylabel("final mz")
    ax[1].set_title("Final mz (color = $T_{max}$)")
    style(ax[1])
    fig.savefig(out, dpi=200)
    print("saved:", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="runs/summary.csv")
    ap.add_argument("--outdir", default="runs")
    args = ap.parse_args()

    pts = load_points(args.summary)
    for p in sorted(pts, key=lambda p: (p["theta"], p["heat"], p["Jp"])):
        print("%-22s th=%s heat=%d  Jp=%.0fe12  Tmax=%4.0f K  mz=%+.4f  t_cross=%s"
              % (p["tag"], p["theta"], p["heat"], p["Jp"] / 1e12, p["Tmax"], p["mz"],
                 "%.1f" % p["t_cross"] if p["t_cross"] == p["t_cross"] else "-"))

    fig_map(pts, os.path.join(args.outdir, "phase_map.png"))
    fig_traces(["si_h_t20_Jp8", "si_h_t20_Jp11", "si_h_t20_Jp12", "si_h_t20_Jp15"],
               os.path.join(args.outdir, "phase_traces.png"))
    fig_speed(pts, os.path.join(args.outdir, "phase_speed.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
