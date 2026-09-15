"""Final figure: mechanism control panels - c0/b0, b2, b3.

Three flat panels compare the switching mechanism of the 6 ps pulse:
  (a) c0/b0 : Joule heating off vs on at the same Jp (heating is required)
  (b) b2    : theta_DL ~ 0, only the thermal-anisotropy torque survives
              (switching still possible but slower / hotter)
  (c) b3    : Ku(T) frozen (KuExp=0), i.e. thermal-anisotropy torque removed
              (no switching up to 1.4e13 A/m^2)

Solid = heating on, dashed = heating off.  Thin dash-dotted curves on the
right axis are T(t) of the same run.

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
                names = [c.strip().split()[0]
                         for c in line[1:].strip().split("\t") if c.strip()]
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


def style(ax):
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(0, color="k", lw=0.5, alpha=0.4)
    ax.set_xlim(0, 160)
    ax.set_ylim(-1.08, 1.08)
    ax.set_xlabel("delay (ps)")
    ax.set_ylabel("average mz")


def twin(ax):
    axt = ax.twinx()
    axt.set_ylim(290, 1120)
    axt.set_ylabel("T (K)", fontsize=8, color="gray")
    axt.tick_params(axis="y", labelsize=7, colors="gray")
    axt.spines["right"].set_color("gray")
    return axt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--out", default=os.path.join("runs", "mechanism_compare.png"))
    args = ap.parse_args()

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 3.8), constrained_layout=True)

    # ---- (a) c0/b0: heating off -> on at the same Jp ----
    ax = axes[0]
    axt = twin(ax)
    pairs = [(6e12, "c0_noh_6e12", "b0_6e12"),
             (8e12, "c0_noh_8e12", "b0_8e12"),
             (10e12, "c0_noh_10e12", "b1_Jp10_dT300")]
    cols = plt.cm.viridis(np.linspace(0.15, 0.8, len(pairs)))
    for (jp, off, on), col in zip(pairs, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.2, label="$J_p$=%.0fe12" % (jp / 1e12))
        t, c = plot_run(ax, args.runs, on, col, ls="-", lw=1.6)
        axt.plot(t, c["T"], color=col, ls="-.", lw=0.9, alpha=0.55)
    ax.set_title("(a) c0/b0: heating off (---) vs on (-), same $J_p$\n"
                 "8e12: only the Joule-heated run switches", fontsize=10)
    ax.legend(fontsize=7.5, loc="lower left", title="solid: heating on, dashed: off",
              title_fontsize=7)
    style(ax)

    # ---- (b) b2: theta_DL ~ 0 ----
    ax = axes[1]
    axt = twin(ax)
    b2 = [(300, "b2_theta0_dT300"), (450, "b2_theta0_dT450"),
          (600, "b2_theta0_dT600"), (800, "b2_theta0_dT800")]
    cols = plt.cm.inferno(np.linspace(0.25, 0.9, len(b2)))
    crosses = ["no flip", "85.9 ps", "92.3 ps", "122.4 ps"]
    for (dt, tag), col, tc in zip(b2, cols, crosses):
        t, c = plot_run(ax, args.runs, tag, col, lw=1.5,
                        label=r"$\Delta T_{pk}$=%d K  (%s)" % (dt, tc))
        axt.plot(t, c["T"], color=col, ls="-.", lw=0.9, alpha=0.55)
    t, c = plot_run(ax, args.runs, "b1_Jp8_dT450", "gray", ls=":", lw=1.4,
                    label=r"b1 $\theta_{DL}$=0.2  (58.6 ps)")
    ax.set_title(r"(b) b2: $\theta_{DL}\approx$0, thermal-anisotropy torque only"
                 "\n$J_p$=8e12, $T_c$ clamped at 800 K", fontsize=10)
    ax.legend(fontsize=7, loc="lower left")
    style(ax)

    # ---- (c) b3: Ku(T) frozen ----
    ax = axes[2]
    axt = twin(ax)
    b3 = [(8e12, "b3_noKuT_Jp8", "b1_Jp8_dT300"),
          (10e12, "b3_noKuT_Jp10", "b1_Jp10_dT300"),
          (12e12, "b3_noKuT_Jp12", "b1_Jp12_dT300"),
          (14e12, "b3_noKuT_Jp14", "b1_Jp14_dT300")]
    cols = plt.cm.plasma(np.linspace(0.12, 0.8, len(b3)))
    for (jp, off, on), col in zip(b3, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.2)
        t, c = plot_run(ax, args.runs, on, col, lw=1.6,
                        label="$J_p$=%.0fe12" % (jp / 1e12))
        axt.plot(t, c["T"], color=col, ls="-.", lw=0.9, alpha=0.55)
    ax.set_title("(c) b3: Ku(T) frozen (---) vs Ku(T) on (-), $J_{ref}=J_p$\n"
                 "no flip up to 1.4e13 -> Ku(T) channel is necessary", fontsize=10)
    ax.legend(fontsize=7.5, loc="lower left", title="solid: Ku(T) on, dashed: KuExp=0",
              title_fontsize=7)
    style(ax)

    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)


if __name__ == "__main__":
    sys.exit(main())
