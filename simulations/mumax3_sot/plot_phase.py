"""Final switching-threshold plots from runs/summary.csv (paper-parameter model).

With the paper heat channel the peak temperature is fixed by the current,
Tmax = 300 + 50.4 K (Jp/6e12)^2, so the old 2D (Jp, Tmax) phase map
collapses into 1D threshold curves.  This script plots:

    phase_map.png    mz_final vs Jp for the four series
                     (theta_DL = 0.2/0.3 x heating on/off)
    phase_traces.png mz(t) and T(t) around the theta=0.2 heated boundary
    phase_speed.png  crossing time vs Jp (switched cases)

For each (theta, heating, Jp) the `si_*_lr<ps>` re-run (long free relaxation,
e.g. 1500 ps, T back to ~300 K) overrides the base 0.4 ns snapshot.  Points
whose m_final.ovf is not a uniform state (|average m| < 0.9, i.e. the 64x64
pseudo-macrospin broke into domains near the boundary) are excluded from the
lines and drawn as grey crosses.

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

TRACE_ORDER = ["si_h_t20_Jp8", "si_h_t20_Jp9", "si_h_t20_Jp10",
               "si_h_t20_Jp11", "si_h_t20_Jp12", "si_h_t20_Jp15"]

TRACE_STYLE = {  # tag -> (color, outcome at the end of the 0.4 ns table)
    "si_h_t20_Jp8": ("#1f77b4", "no switch"),
    "si_h_t20_Jp9": ("#ff7f0e", "no switch"),
    "si_h_t20_Jp10": ("#2ca02c", "switches"),
    "si_h_t20_Jp11": ("#d62728", "switches"),
    "si_h_t20_Jp12": ("#9467bd", "switches"),
    "si_h_t20_Jp15": ("#8c564b", "recovers"),
}


def ovf_uniformity(runs_root, tag):
    """|average m| from m_final.ovf: 1 for a uniform state, <<1 for multidomain."""
    path = os.path.join(runs_root, tag, "out", "m_final.ovf")
    if not os.path.isfile(path):
        return 1.0
    raw = open(path, "rb").read()
    i = raw.find(b"# Begin: Data Binary 4")
    j = raw.find(b"\n", i) + 1
    head = raw[:i].decode("ascii", "replace")
    nx = int(re.search(r"xnodes:\s*(\d+)", head).group(1))
    ny = int(re.search(r"ynodes:\s*(\d+)", head).group(1))
    nz = int(re.search(r"znodes:\s*(\d+)", head).group(1))
    vd = int(re.search(r"valuedim:\s*(\d+)", head).group(1))
    data = np.frombuffer(raw[j + 4:], dtype="<f4")
    nc = nx * ny * nz
    v = data[: nc * vd].reshape(nc, vd)
    return float(np.linalg.norm(v[:, :3].mean(axis=0)))


def load_points(summary):
    """One point per (theta, heat, Jp); *_lr<ps> re-runs win over the base case."""
    runs_root = os.path.dirname(os.path.abspath(summary))
    pat = re.compile(r"^si_(h|noh)_t(\d+)_Jp(\d+)(?:_lr(\d+))?$")
    best = {}
    with open(summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = pat.match(row.get("tag", ""))
            if not m:
                continue
            lr = int(m.group(4) or 0)
            key = ("0." + m.group(2)[0], 1 if m.group(1) == "h" else 0,  # 20 -> 0.2
                   float(row["Jp"]))
            if key in best and best[key]["lr"] > lr:
                continue
            best[key] = {
                "tag": row["tag"],
                "heat": key[1],
                "theta": key[0],
                "Jp": float(row["Jp"]),
                "Tmax": float(row["Tmax_K"]),
                "mz": float(row["mz_final"]),
                "t_cross": float(row["t_cross_ps"]) if row["t_cross_ps"] else np.nan,
                "lr": lr,
                "uni": ovf_uniformity(runs_root, row["tag"]),
            }
    pts = sorted(best.values(), key=lambda p: (p["theta"], p["heat"], p["Jp"]))
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
        g = sorted([p for p in pts if p["theta"] == th and p["heat"] == int(heat)
                    and p["uni"] >= 0.9], key=lambda p: p["Jp"])
        if not g:
            continue
        x = [p["Jp"] / 1e12 for p in g]
        y = [p["mz"] for p in g]
        ax.plot(x, y, ls, color=color, lw=1.4, marker="o", ms=3.5,
                label=label)
    bad = [p for p in pts if p["uni"] < 0.9]
    if bad:
        ax.plot([p["Jp"] / 1e12 for p in bad], [p["mz"] for p in bad], "x",
                color="0.35", ms=6, mew=1.4, ls="none",
                label="multidomain (excluded)")
    ax.axhline(0, color="k", lw=0.6, alpha=0.5)
    ax.axhline(-0.5, color="k", ls="--", lw=0.7, alpha=0.5)
    ax.text(20.5, -0.42, "switch criterion", fontsize=7, color="0.35")
    ax.text(0.985, 0.98, "$\\theta_{DL}$=0.2 series: $t_{free}$=1.5 ns$^{*}$\n"
            "$^{*}$1.5 ns where available; else 0.4 ns snapshot",
            transform=ax.transAxes, fontsize=6, color="0.4", ha="right", va="top")
    ax.set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax.set_ylabel("final $m_z$")
    ax.set_title("Switching threshold, 6 ps sech$^2$ pulse, Hx=160 mT\n"
                 "heating model: $T_{max}$ = 300 + 50.4 K ($J_p$/6×10¹²)$^2$")
    ax.legend(fontsize=7, loc="lower left")
    style(ax)
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_traces(out):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.3), constrained_layout=True)
    for tag in TRACE_ORDER:
        path = os.path.join(os.path.dirname(out), tag, "out", "table.txt")
        if not os.path.isfile(path):
            print("skip (missing):", path)
            continue
        c = load_table(path)
        t = c["t"] * 1e12
        mz = c["mz"]
        col, outcome = TRACE_STYLE[tag]
        jp = re.search(r"Jp(\d+)", tag).group(1)
        ax[0].plot(t, mz, lw=1.2, color=col,
                   label="$J_p$=%s: %s" % (jp, outcome))
        ax[1].plot(t, c["T"], lw=1.2, color=col)
    ax[0].axhline(0, color="k", lw=0.5, alpha=0.5)
    ax[0].axvline(24, color="k", lw=0.5, alpha=0.2)
    ax[0].set_xlim(0, 160)
    ax[0].set_xlabel("time (ps)")
    ax[0].set_ylabel("average mz")
    ax[0].set_title("Boundary cases: mz(t)")
    style(ax[0])
    ax[1].axhline(800, color="gray", ls=":", lw=0.8)
    ax[1].set_xlim(0, 160)
    ax[1].set_ylim(280, 820)
    ax[1].set_xlabel("time (ps)")
    ax[1].set_ylabel("T (K)")
    ax[1].set_title("T(t)  (heat channel)")
    style(ax[1])
    h, lab = ax[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="outside upper center", ncol=6, fontsize=7.5,
               frameon=False, columnspacing=1.2, handlelength=1.8)
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_speed(pts, out):
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.4), constrained_layout=True)
    for key, (label, color, ls) in SERIES.items():
        th, heat = key
        g = sorted([p for p in pts if p["theta"] == th and p["heat"] == int(heat)
                    and p["t_cross"] == p["t_cross"] and p["mz"] < -0.5
                    and p["Tmax"] <= 800.0], key=lambda p: p["Jp"])
        if not g:
            continue
        ax[0].plot([p["Jp"] / 1e12 for p in g], [p["t_cross"] for p in g],
                   ls, marker="o", ms=4, lw=1.1, color=color, label=label)
    hot = sorted([p for p in pts if p["t_cross"] == p["t_cross"] and p["mz"] < -0.5
                  and p["Tmax"] > 800.0], key=lambda p: p["Jp"])
    if hot:  # T > Tc: film demagnetizes (Msat = 0); t_cross is the cooling time
        ax[0].plot([p["Jp"] / 1e12 for p in hot], [p["t_cross"] for p in hot], "x",
                   color="0.45", ms=6, mew=1.3, ls="none",
                   label="$T_{max}>T_c$ (excluded)")
    ax[0].set_xlabel(r"$J_p$ ($10^{12}$ A/m$^2$)")
    ax[0].set_ylabel(r"$t_{cross}$ (ps)")
    ax[0].set_title("Crossing time (switched cases, $T_{max}\\,\\leq\\,T_c$)")
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
        print("%-28s th=%s heat=%d  Jp=%4.0fe12  Tmax=%4.0f K  mz=%+.4f  "
              "t_cross=%-5s |avg|=%s"
              % (p["tag"], p["theta"], p["heat"], p["Jp"] / 1e12, p["Tmax"], p["mz"],
                 "%.1f" % p["t_cross"] if p["t_cross"] == p["t_cross"] else "-",
                 "%.3f%s" % (p["uni"], "" if p["uni"] >= 0.9 else " <- multidomain")))

    fig_map(pts, os.path.join(args.outdir, "phase_map.png"))
    fig_traces(os.path.join(args.outdir, "phase_traces.png"))
    fig_speed(pts, os.path.join(args.outdir, "phase_speed.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
