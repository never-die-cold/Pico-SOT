"""Draft phase-diagram plots from runs/summary.csv (Jp, Tmax) switching map.

Usage:
    python plot_phase.py [--summary runs/summary.csv] [--outdir runs]

Outputs (drafts, for review):
    runs/phase_map_draft.png      Jp vs Tmax scatter + boundary guide
    runs/phase_traces_draft.png   mz(t) and T(t) of the boundary cases
    runs/phase_speed_draft.png    crossing time vs Jp, final mz vs Tmax

Only heating-on, default-theta (Pol=0.20, KuExp>0) macrospin cases are
included; B2 (theta~0) and B3 (no Ku(T)) are excluded.
"""
import argparse
import csv
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_points(summary):
    pts = []
    with open(summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row.get("Jp") or not row.get("dT_ref"):
                continue
            if row["tag"].startswith("b0c_"):
                continue
            pol = row.get("Pol") or ""
            if pol and float(pol) < 0.05:
                continue
            kuexp = row.get("KuExp") or ""
            if kuexp and float(kuexp) == 0.0:
                continue
            mz = float(row["mz_final"])
            pts.append({
                "tag": row["tag"],
                "Jp": float(row["Jp"]),
                "dT": float(row["dT_ref"]),
                "Tmax": float(row["Tmax_K"]),
                "mz": mz,
                "t_cross": float(row["t_cross_ps"]) if row["t_cross_ps"] else np.nan,
                "heating": int(row.get("Heating") or 1),
            })
    assert pts, "no phase points found"
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
    fig, ax = plt.subplots(figsize=(5.6, 4.2), constrained_layout=True)
    for p in pts:
        c = "crimson" if p["mz"] <= -0.9 else ("darkorange" if p["mz"] < 0 else "tab:blue")
        m = "o" if p["mz"] <= -0.9 else ("^" if p["mz"] < 0 else "s")
        filled = p["mz"] < 0
        ax.scatter(p["Jp"] / 1e12, p["Tmax"], s=42, facecolors=c if filled else "none",
                   edgecolors=c, marker=m, lw=1.4, zorder=3)
    # eye-guide through the known boundary midpoints (draft only)
    gx = [10.5, 9.5, 8.0, 7.0, 6.0]
    gy = [583, 583, 619, 700, 810]
    ax.plot(gx, gy, "k--", lw=1.0, alpha=0.6, label="boundary guide (draft)")
    ax.axhline(800, color="gray", ls=":", lw=0.8)
    ax.text(6.05, 806, r"$T_c\approx800$ K", fontsize=8, color="gray")
    ax.scatter([], [], facecolors="none", edgecolors="crimson", marker="o", label="switched")
    ax.scatter([], [], color="darkorange", marker="^", label="partial")
    ax.scatter([], [], facecolors="none", edgecolors="tab:blue", marker="s", label="not switched")
    ax.set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax.set_ylabel(r"$T_{max}$ (K)")
    ax.set_title("Switching phase map (6 ps sech$^2$, draft)")
    ax.legend(fontsize=8, loc="lower right")
    style(ax)
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_traces(tags, out):
    refs = ["b1_Jp8_dT300", "b1_Jp8_dT450"]
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.3), constrained_layout=True)
    for tag in refs + tags:
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
    ax[1].set_xlabel("time (ps)")
    ax[1].set_ylabel("T (K)")
    ax[1].set_title("T(t)  (gray = reference 8e12 cases)")
    style(ax[1])
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_speed(pts, out):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4), constrained_layout=True)
    groups = {}
    for p in pts:
        groups.setdefault(p["dT"], []).append(p)
    for dT, g in sorted(groups.items()):
        g = sorted(g, key=lambda p: p["Jp"])
        jp = [p["Jp"] / 1e12 for p in g if p["t_cross"] == p["t_cross"]]
        tc = [p["t_cross"] for p in g if p["t_cross"] == p["t_cross"]]
        ax[0].plot(jp, tc, "o-", ms=4, lw=1.1, label="dT=%.0f K" % dT)
        jpn = [p["Jp"] / 1e12 for p in g if p["t_cross"] != p["t_cross"]]
        ax[0].scatter(jpn, [20] * len(jpn), marker="x", s=40)
    ax[0].set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax[0].set_ylabel(r"$t_{cross}$ (ps)")
    ax[0].set_title("Crossing time (x = no crossing)")
    ax[0].legend(fontsize=7)
    style(ax[0])
    for p in pts:
        ax[1].scatter(p["Jp"] / 1e12, p["mz"], s=36, c=[p["Tmax"]], cmap="inferno", vmin=300, vmax=900)
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
    for p in sorted(pts, key=lambda p: (p["Jp"], p["Tmax"])):
        print("%-18s Jp=%.2fe12  Tmax=%4.0f K  mz=%+.4f  t_cross=%s"
              % (p["tag"], p["Jp"] / 1e12, p["Tmax"], p["mz"],
                 "%.1f" % p["t_cross"] if p["t_cross"] == p["t_cross"] else "-"))

    fig_map(pts, os.path.join(args.outdir, "phase_map_draft.png"))
    fig_traces(["c1_Jp9_dT300", "c1_Jp8_dT375", "c1_Jp7_dT450", "c1_Jp6_dT600"],
               os.path.join(args.outdir, "phase_traces_draft.png"))
    fig_speed(pts, os.path.join(args.outdir, "phase_speed_draft.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
