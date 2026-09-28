"""Final switching-threshold plots from runs/summary.csv (paper-parameter model).

With the paper heat channel the peak temperature is fixed by the current,
Tmax = 300 + 50.4 K (Jp/6e12)^2, so the old 2D (Jp, Tmax) phase map
collapses into 1D threshold curves.  This script plots:

    phase_map.png    mz_final vs Jp, all four series in one axes (overview)
    phase_heated.png 2 panels (theta = 0.2 | 0.3), heating on   <- deck P7
    phase_noheat.png 2 panels (theta = 0.2 | 0.3), heating off  <- deck P7
    phase_traces.png mz(t) and T(t) around the theta=0.2 heated boundary
    phase_speed.png  crossing time vs Jp (switched cases)

For each (theta, heating, Jp) the `si_*_lr<ps>` re-run (long free relaxation,
e.g. 1500 ps, T back to ~300 K) overrides the base 0.4 ns snapshot.  Points
whose m_final.ovf is not a uniform state (|average m| < 0.9, i.e. the 64x64
pseudo-macrospin broke into domains near the boundary) are **not drawn at
all** — they carry no single-domain information, so plotting them (as the old
grey crosses did) misleads about both the outcome and the series they belong
to.  The polylines simply connect the surviving points with straight lines,
and the excluded Jp values are listed in docs/RESULTS.md §3 and on deck
page 7.

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

import figstyle as fs

SERIES = {  # tag pattern -> (label, color, linestyle)  [fs palette, D5]
    # all series drawn with solid lines: colour alone separates the four series
    ("0.2", "1"): ("$\\theta_{DL}$=0.2，加热", fs.C["heat020"], "-"),
    ("0.2", "0"): ("$\\theta_{DL}$=0.2，无加热", fs.C["noheat020"], "-"),
    ("0.3", "1"): ("$\\theta_{DL}$=0.3，加热", fs.C["heat030"], "-"),
    ("0.3", "0"): ("$\\theta_{DL}$=0.3，无加热", fs.C["noheat030"], "-"),
}

TRACE_ORDER = ["si_h_t20_Jp8", "si_h_t20_Jp9", "si_h_t20_Jp10",
               "si_h_t20_Jp11", "si_h_t20_Jp12", "si_h_t20_Jp15"]

TRACE_STYLE = {  # tag -> (color, outcome at the end of the 0.4 ns table)
    "si_h_t20_Jp8": ("#1f77b4", "不翻"),
    "si_h_t20_Jp9": ("#ff7f0e", "不翻"),
    "si_h_t20_Jp10": ("#2ca02c", "翻转"),
    "si_h_t20_Jp11": ("#d62728", "翻转"),
    "si_h_t20_Jp12": ("#9467bd", "翻转"),
    "si_h_t20_Jp15": ("#8c564b", "回翻"),
}

# precessional recapture windows (Jp in 1e12 units) verified on the 0.5e12 grid;
# bounds are inclusive of the verified no-switch points (masked points excluded)
WINDOWS = {("0.2", "1"): (14.5, 17.0), ("0.3", "1"): (15.0, 17.0)}


def series_points(pts, theta, heat):
    """(valid, masked) for one series, sorted by Jp; masked = |<m>| < 0.9."""
    sel = [p for p in pts if p["theta"] == theta and p["heat"] == heat]
    valid = sorted([p for p in sel if p["uni"] >= 0.9], key=lambda p: p["Jp"])
    masked = sorted([p for p in sel if p["uni"] < 0.9], key=lambda p: p["Jp"])
    return valid, masked


def series_xy(valid):
    """x (1e12 units), y of the surviving points, joined by straight lines.

    Masked (multidomain) points are simply absent from the arrays; the polyline
    connects the neighbouring measured points directly — no gap markers and no
    line breaks (a broken line reads as a plotting glitch, the connected line
    is the intended look).
    """
    return [p["Jp"] / 1e12 for p in valid], [p["mz"] for p in valid]


def threshold(valid):
    """(lo, hi) in 1e12 units bracketing the first switch (last + -> first -)."""
    for a, b in zip(valid, valid[1:]):
        if a["mz"] > 0 > b["mz"]:
            return a["Jp"] / 1e12, b["Jp"] / 1e12
    return None, None


def plot_series(ax, pts, theta, heat, lw=1.7, ms=4.5, annotate=True):
    """One series = one panel: no excluded markers, straight-line connected."""
    label, color, ls = SERIES[(theta, str(heat))]
    valid, masked = series_points(pts, theta, heat)
    xs, ys = series_xy(valid)
    ax.plot(xs, ys, ls, color=color, lw=lw, marker="o", ms=ms)
    ax.axhline(0, color="k", lw=0.6, alpha=0.4)
    ax.axhline(-0.5, color="k", ls="--", lw=0.9, alpha=0.55)
    ax.set_xlim(5.6, 30.4)
    ax.set_ylim(-1.12, 1.16)
    style(ax)
    if annotate:
        lo, hi = threshold(valid)
        if lo is not None:
            jc = 0.5 * (lo + hi)
            ax.axvline(jc, color="0.35", ls=":", lw=1.3)
            ax.annotate("$J_c$ ≈ %.1f" % jc, xy=(jc, 0.80), ha="center",
                        fontsize=10.5, color="0.2",
                        bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
        win = WINDOWS.get((theta, str(heat)))
        if win:
            ax.axvspan(win[0], win[1], color="0.92", zorder=0)
            ax.annotate("回翻窗口", xy=(0.5 * (win[0] + win[1]), -0.80),
                        ha="center", va="center", fontsize=10, color="0.3",
                        bbox=dict(fc="white", ec="none", alpha=0.8, pad=1.5))
    return valid, masked


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
    pat = re.compile(r"^si_(h|noh)_t(\d+)_Jp(\d+)(?:p(\d+))?(?:_lr(\d+))?$")
    best = {}
    with open(summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = pat.match(row.get("tag", ""))
            if not m:
                continue
            lr = int(m.group(5) or 0)
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
    """Overview: all four series in one axes (docs/README thumbnail)."""
    fig, ax = plt.subplots(figsize=(7.4, 4.9), constrained_layout=True)
    for key, (label, color, ls) in SERIES.items():
        th, heat = key
        valid, masked = series_points(pts, th, int(heat))
        if not valid:
            continue
        xs, ys = series_xy(valid)
        ax.plot(xs, ys, ls, color=color, lw=1.6, marker="o", ms=4,
                label=label)
    ax.axhline(0, color="k", lw=0.6, alpha=0.5)
    ax.axhline(-0.5, color="k", ls="--", lw=0.8, alpha=0.5)
    ax.text(20.5, -0.40, "判定线 mz=−0.5", fontsize=8.5, color="0.35")
    # empty top strip for the provenance note (data rows sit at +-0.98)
    ax.set_ylim(-1.12, 1.42)
    ax.text(5.85, 1.40, "点优先取 1.5 ns 长弛豫复跑值（无复跑处为 0.4 ns 快照）\n"
            "多畴伪影点不绘制（清单见 RESULTS.md §3）",
            fontsize=8.5, color="0.4", ha="left", va="top", linespacing=1.4)
    ax.set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
    ax.set_ylabel("末态 $m_z$")
    ax.set_title("开关阈值（6 ps sech² 脉冲，Hx=160 mT）\n"
                 "加热模型：$T_{max}$ = 300 + 50.4 K ($J_p$/6×10¹²)$^2$")
    ax.legend(fontsize=9, loc="upper right", bbox_to_anchor=(0.995, 0.64))
    style(ax)
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_split(pts, outdir):
    """Deck P7: threshold curves split by heating state, one series per panel.

    phase_heated.png / phase_noheat.png, each 1x2 panels (theta 0.2 | 0.3) so
    that no two series share an axes (the old single-axes map overplotted four
    curves plus the excluded-point crosses).
    """
    for heat, name in ((1, "phase_heated.png"), (0, "phase_noheat.png")):
        fig, axs = plt.subplots(1, 2, figsize=(10.8, 4.43),
                                constrained_layout=True)
        for j, theta in enumerate(("0.2", "0.3")):
            ax = axs[j]
            plot_series(ax, pts, theta, heat)
            ax.set_title("$\\theta_{DL}$=%s，%s" % (
                theta, "加热开" if heat else "加热关（T = 300 K）"))
            ax.set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
            if j == 0:
                ax.set_ylabel("末态 $m_z$")
        out = os.path.join(outdir, name)
        fig.savefig(out, dpi=200)
        print("saved:", out)


def fig_traces(out):
    fig, ax = plt.subplots(1, 2, figsize=(10.6, 4.2), constrained_layout=True)
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
        ax[0].plot(t, mz, lw=1.5, color=col,
                   label="$J_p$=%s：%s" % (jp, outcome))
        tT, T = fs.destair(t, c["T"])
        ax[1].plot(tT, T, lw=1.5, color=col)
    ax[0].axhline(0, color="k", lw=0.6, alpha=0.5)
    ax[0].axvspan(0, 48, color="0.92", label="脉冲窗口")
    ax[0].set_xlim(0, 160)
    ax[0].set_xlabel("时间 t (ps)")
    ax[0].set_ylabel("平均 $m_z$")
    ax[0].set_title("边界案例 $m_z$(t)（加热 θ=0.2）")
    ax[0].legend(fontsize=9, loc="lower left", ncol=2)
    style(ax[0])
    ax[1].axhline(800, color="gray", ls=":", lw=0.9)
    ax[1].set_xlim(0, 160)
    ax[1].set_ylim(280, 820)
    ax[1].set_xlabel("时间 t (ps)")
    ax[1].set_ylabel("$T$ (K)")
    ax[1].set_title("温度轨迹（热通道，点线 = $T_c$）")
    style(ax[1])
    fig.savefig(out, dpi=200)
    print("saved:", out)


def fig_speed(pts, out):
    fig, ax = plt.subplots(1, 2, figsize=(10.6, 4.2), constrained_layout=True)
    for key, (label, color, ls) in SERIES.items():
        th, heat = key
        g = sorted([p for p in pts if p["theta"] == th and p["heat"] == int(heat)
                    and p["uni"] >= 0.9
                    and p["t_cross"] == p["t_cross"] and p["mz"] < -0.5
                    and p["Tmax"] <= 800.0], key=lambda p: p["Jp"])
        if not g:
            continue
        ax[0].plot([p["Jp"] / 1e12 for p in g], [p["t_cross"] for p in g],
                   ls, marker="o", ms=4.5, lw=1.4, color=color, label=label)
    hot = sorted([p for p in pts if p["uni"] >= 0.9
                  and p["t_cross"] == p["t_cross"] and p["mz"] < -0.5
                  and p["Tmax"] > 800.0], key=lambda p: p["Jp"])
    if hot:  # T > Tc: film demagnetizes (Msat = 0); t_cross is the cooling time
        ax[0].plot([p["Jp"] / 1e12 for p in hot], [p["t_cross"] for p in hot], "x",
                   color="0.45", ms=7, mew=1.5, ls="none",
                   label="$T_{max}>T_c$（剔除）")
    ax[0].set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
    ax[0].set_ylabel("$t_{cross}$ (ps)")
    ax[0].set_title("过零时间（仅翻转成功且 $T_{max}\\leq T_c$）")
    ax[0].legend(fontsize=9)
    style(ax[0])
    for p in pts:
        if p["uni"] < 0.9:  # multidomain: no valid single-domain mz, never plot
            continue
        ax[1].scatter(p["Jp"] / 1e12, p["mz"], s=34, c=[p["Tmax"]], cmap="inferno",
                      vmin=300, vmax=900, edgecolor="none")
    sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(300, 900))
    fig.colorbar(sm, ax=ax[1], label="$T_{max}$ (K)")
    ax[1].axhline(-0.5, color="k", ls="--", lw=0.9)
    ax[1].set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
    ax[1].set_ylabel("末态 $m_z$")
    ax[1].set_title("末态 $m_z$（颜色 = $T_{max}$）")
    style(ax[1])
    fig.savefig(out, dpi=200)
    print("saved:", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="runs/summary.csv")
    ap.add_argument("--outdir", default="runs")
    args = ap.parse_args()

    fs.apply()
    pts = load_points(args.summary)
    for p in sorted(pts, key=lambda p: (p["theta"], p["heat"], p["Jp"])):
        print("%-28s th=%s heat=%d  Jp=%4.0fe12  Tmax=%4.0f K  mz=%+.4f  "
              "t_cross=%-5s |avg|=%s"
              % (p["tag"], p["theta"], p["heat"], p["Jp"] / 1e12, p["Tmax"], p["mz"],
                 "%.1f" % p["t_cross"] if p["t_cross"] == p["t_cross"] else "-",
                 "%.3f%s" % (p["uni"], "" if p["uni"] >= 0.9 else " <- multidomain")))

    fig_map(pts, os.path.join(args.outdir, "phase_map.png"))
    fig_split(pts, args.outdir)
    fig_traces(os.path.join(args.outdir, "phase_traces.png"))
    fig_speed(pts, os.path.join(args.outdir, "phase_speed.png"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
