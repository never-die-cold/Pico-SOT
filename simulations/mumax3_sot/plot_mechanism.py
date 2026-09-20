"""Final figure: mechanism control panels (paper-parameter replica), 2x3 layout.

Top row    average mz(t):
    (a) heating off (--) vs on (-) at the same Jp, theta_DL = 0.2
    (b) theta_DL ~ 0: thermal-anisotropy torque only (full model as reference)
    (c) Kz(T) frozen (--) / Ms(T) frozen (:) vs full model (-)
Bottom row the same runs' temperature T(t) (0D heat channel, Tc marked).

This replaces the earlier 3-panel version whose twin y axes (mz + T) were
hard to read; each panel now carries a single quantity.

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

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


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


def plot_run(ax, runs, tag, color, ls="-", lw=1.5, label=None):
    path = os.path.join(runs, tag, "out", "table.txt")
    if not os.path.isfile(path):
        raise SystemExit("missing: %s" % path)
    c = load_table(path)
    t = c["t"] * 1e12
    ax.plot(t, c["mz"], color=color, ls=ls, lw=lw, label=label)
    return t, c


def style_mz(ax):
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(0, color="k", lw=0.5, alpha=0.4)
    ax.set_xlim(0, 160)
    ax.set_ylim(-1.08, 1.08)
    ax.set_xlabel("delay (ps)", fontsize=8)
    ax.set_ylabel("average $m_z$", fontsize=8)
    ax.tick_params(labelsize=7)


def style_T(ax, mark_tc=False):
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(800, color="gray", ls=":", lw=0.8)
    ax.set_xlim(0, 160)
    ax.set_ylim(290, 900)
    ax.set_xlabel("delay (ps)", fontsize=8)
    ax.set_ylabel("$T$ (K)", fontsize=8)
    ax.tick_params(labelsize=7)
    if mark_tc:
        ax.text(4, 812, "$T_c$", fontsize=6, color="gray")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "mechanism_compare.png"))
    args = ap.parse_args()

    fig, axs = plt.subplots(2, 3, figsize=(12.6, 3.8), constrained_layout=True)

    # ---- (a) heating off -> on at the same Jp (theta_DL = 0.2) ----
    ax, axt = axs[0][0], axs[1][0]
    pairs = [(6e12, "si_noh_t20_Jp6", "si_h_t20_Jp6"),
             (8e12, "si_noh_t20_Jp8", "si_h_t20_Jp8"),
             (10e12, "si_noh_t20_Jp10", "si_h_t20_Jp10"),
             (20e12, "si_noh_t20_Jp20", "si_h_t20_Jp20")]
    cols = plt.cm.viridis(np.linspace(0.15, 0.85, len(pairs)))
    for (jp, off, on), col in zip(pairs, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.1,
                 label="$J_p$=%.0f×10¹²" % (jp / 1e12))
        t, c = plot_run(ax, args.runs, on, col, lw=1.5)
        axt.plot(t, c["T"], color=col, lw=1.2)
    ax.set_title("(a) heating off (--) vs on (-), $\\theta_{DL}$=0.2\n"
                 "same $J_p$: heating lowers $J_c$", fontsize=8.5)
    ax.legend(fontsize=5.5, loc="lower left", title="dashed: off, solid: on",
              title_fontsize=5.5)

    # ---- (b) theta_DL ~ 0: thermal-anisotropy torque only ----
    ax, axt = axs[0][1], axs[1][1]
    b2 = [(8e12, "si_b2t0_Jp8", "no flip"),
          (10e12, "si_b2t0_Jp10", "no flip"),
          (12e12, "si_b2t0_Jp12", "122.5 ps"),
          (14e12, "si_b2t0_Jp14", "80.2 ps")]
    cols = plt.cm.inferno(np.linspace(0.25, 0.9, len(b2)))
    for (jp, tag, tc), col in zip(b2, cols):
        t, c = plot_run(ax, args.runs, tag, col, lw=1.4,
                        label="$J_p$=%.0f×10¹² (%s)" % (jp / 1e12, tc))
        axt.plot(t, c["T"], color=col, lw=1.2)
    plot_run(ax, args.runs, "si_h_t20_Jp10", "gray", ls=":", lw=1.3,
             label=r"full model $\theta_{DL}$=0.2 (68.3 ps)")
    ax.set_title(r"(b) $\theta_{DL}\approx$0: thermal-anisotropy torque"
                 "\n(paper: needs stronger heating, slower)", fontsize=8.5)
    ax.legend(fontsize=5.5, loc="lower left")

    # ---- (c) Kz(T) frozen / Ms(T) frozen ----
    ax, axt = axs[0][2], axs[1][2]
    b3 = [(10e12, "si_Kzfr_Jp10", "si_h_t20_Jp10"),
          (12e12, "si_Kzfr_Jp12", "si_h_t20_Jp12")]
    cols = plt.cm.plasma(np.linspace(0.12, 0.55, len(b3)))
    for (jp, off, on), col in zip(b3, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.1)
        t, c = plot_run(ax, args.runs, on, col, lw=1.5,
                        label="$J_p$=%.0f×10¹²" % (jp / 1e12))
        axt.plot(t, c["T"], color=col, lw=1.2)
    for jp, tag, col in [(10e12, "si_Msfr_Jp10", "tab:cyan"),
                         (12e12, "si_Msfr_Jp12", "tab:green")]:
        plot_run(ax, args.runs, tag, col, ls=":", lw=1.4,
                 label="$M_s$(T) frozen, %.0f×10¹²" % (jp / 1e12))
    ax.set_title("(c) Kz(T) frozen (--) vs full (-)\n"
                 "$M_s$(T) frozen only (:)", fontsize=8.5)
    ax.legend(fontsize=5.5, loc="lower left")

    for j, axt in enumerate(axs[1]):
        style_T(axt, mark_tc=(j == 0))
    for ax in axs[0]:
        style_mz(ax)

    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
