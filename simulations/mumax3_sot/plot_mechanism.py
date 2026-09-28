"""Final figure: mechanism control panels (paper-parameter replica), 2x3 layout.

Top row    average mz(t):
    (a) heating off (--) vs on (-) at the same Jp, theta_DL = 0.2
    (b) theta_DL ~ 0: thermal-anisotropy torque only (full model as reference)
    (c) Kz(T) frozen (--) / Ms(T) frozen (:) vs full model (-)
Bottom row the same runs' temperature T(t) (0D heat channel, Tc marked),
resampled off the 10 ps free-evolution hold with figstyle.destair.

2026-09-28 restyled with figstyle (D5): readable fonts, unified palette,
single-quantity panels (the original 3-panel twin-axis version was replaced
long ago; this version replaces the 12.6x3.8 in / 5.5 pt layout).

Usage:
    python plot_mechanism.py [--runs runs] [--out runs/mechanism_compare.png]
"""
import argparse
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import figstyle as fs


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


def plot_run(ax, runs, tag, color, ls="-", lw=1.6, label=None):
    """Draw mz(t) on ax; return the heat trace (t, T) de-staircased for the
    T row below (the free-evolution loop holds T for 10 ps at a time)."""
    path = os.path.join(runs, tag, "out", "table.txt")
    if not os.path.isfile(path):
        raise SystemExit("missing: %s" % path)
    c = load_table(path)
    t = c["t"] * 1e12
    ax.plot(t, c["mz"], color=color, ls=ls, lw=lw, label=label)
    return fs.destair(t, c["T"])


def style_mz(ax):
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(0, color="k", lw=0.5, alpha=0.4)
    ax.set_xlim(0, 160)
    ax.set_ylim(-1.08, 1.08)
    ax.set_xlabel("延迟 t (ps)")
    ax.set_ylabel("平均 $m_z$")


def style_T(ax, mark_tc=False):
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(800, color="gray", ls=":", lw=0.9)
    ax.set_xlim(0, 160)
    ax.set_ylim(290, 900)
    ax.set_xlabel("延迟 t (ps)")
    ax.set_ylabel("$T$ (K)")
    if mark_tc:
        ax.text(4, 815, "$T_c$", fontsize=10, color="gray")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "mechanism_compare.png"))
    args = ap.parse_args()

    fs.apply()
    fig, axs = plt.subplots(2, 3, figsize=(13.5, 6.8), constrained_layout=True)

    # ---- (a) heating off -> on at the same Jp (theta_DL = 0.2) ----
    ax, axt = axs[0][0], axs[1][0]
    pairs = [(6e12, "si_noh_t20_Jp6", "si_h_t20_Jp6"),
             (8e12, "si_noh_t20_Jp8", "si_h_t20_Jp8"),
             (10e12, "si_noh_t20_Jp10", "si_h_t20_Jp10"),
             (20e12, "si_noh_t20_Jp20", "si_h_t20_Jp20")]
    cols = plt.cm.viridis(np.linspace(0.15, 0.85, len(pairs)))
    for (jp, off, on), col in zip(pairs, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.3,
                 label="$J_p$=%.0f" % (jp / 1e12))
        t, T = plot_run(ax, args.runs, on, col, lw=1.7)
        axt.plot(t, T, color=col, lw=1.4)
    ax.set_title("(a) 加热降阈值\n虚线=无加热，实线=加热（$\\theta_{DL}$=0.2）")
    ax.legend(fontsize=9, loc="lower left", title="$J_p$（10¹² A/m²）",
              title_fontsize=9)

    # ---- (b) theta_DL ~ 0: thermal-anisotropy torque only ----
    ax, axt = axs[0][1], axs[1][1]
    b2 = [(8e12, "si_b2t0_Jp8", "不翻"),
          (10e12, "si_b2t0_Jp10", "不翻"),
          (12e12, "si_b2t0_Jp12", "122.5 ps"),
          (14e12, "si_b2t0_Jp14", "80.2 ps")]
    cols = plt.cm.inferno(np.linspace(0.25, 0.9, len(b2)))
    for (jp, tag, tc), col in zip(b2, cols):
        t, T = plot_run(ax, args.runs, tag, col, lw=1.6,
                        label="$J_p$=%.0f（%s）" % (jp / 1e12, tc))
        axt.plot(t, T, color=col, lw=1.4)
    plot_run(ax, args.runs, "si_h_t20_Jp10", "gray", ls=":", lw=1.5,
             label="完整模型 10（68.3 ps）")
    ax.set_title("(b) $\\theta_{DL}\\approx$0：纯热各向异性力矩\n（更慢、需更强加热）")
    ax.legend(fontsize=9, loc="lower left", title="$J_p$（10¹² A/m²），括号内为翻转时间",
              title_fontsize=9, frameon=True, framealpha=0.9, edgecolor="none")

    # ---- (c) Kz(T) frozen / Ms(T) frozen ----
    ax, axt = axs[0][2], axs[1][2]
    b3 = [(10e12, "si_Kzfr_Jp10", "si_h_t20_Jp10"),
          (12e12, "si_Kzfr_Jp12", "si_h_t20_Jp12")]
    cols = plt.cm.plasma(np.linspace(0.12, 0.55, len(b3)))
    for (jp, off, on), col in zip(b3, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.3)
        t, T = plot_run(ax, args.runs, on, col, lw=1.7,
                        label="$J_p$=%.0f" % (jp / 1e12))
        axt.plot(t, T, color=col, lw=1.4)
    for jp, tag, col in [(10e12, "si_Msfr_Jp10", "tab:cyan"),
                         (12e12, "si_Msfr_Jp12", "tab:green")]:
        plot_run(ax, args.runs, tag, col, ls=":", lw=1.6,
                 label="$M_s$(T) 冻结，%.0f" % (jp / 1e12))
    ax.set_title("(c) Kz(T) 冻结（--）不翻；$M_s$(T) 冻结（:）边缘态\n→ 两通道都必要")
    ax.legend(fontsize=9, loc="lower left", title="$J_p$（10¹² A/m²）",
              title_fontsize=9)

    for j, axt in enumerate(axs[1]):
        style_T(axt, mark_tc=(j == 0))
    for ax in axs[0]:
        style_mz(ax)

    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
