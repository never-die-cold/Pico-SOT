"""Final figure: mechanism control panels (SI-parameter replica).

Three flat panels dissect the switching mechanism of the 6 ps pulse with the
SI heat channel (Tmax = 300 + 50.4 K (Jp/6e12)^2):
  (a) heating off vs on at the same Jp (theta_DL = 0.2):
      pure LLG needs ~2e13; with the SI heating ~1e13 switches.
  (b) theta_DL ~ 0: only the thermal-anisotropy torque survives
      (switching from ~1.2e13, slower - SI Fig. 5 behaviour).
  (c) Kz(T) frozen at 300 K (SI scaling off): no switching up to 1.4e13,
      while freezing Ms(T) alone still nearly switches -> the Kz(T) collapse
      is the necessary channel.

Solid = full SI model, dashed = control arm.  Thin dash-dotted curves on the
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


def style(ax):
    ax.grid(alpha=0.25, lw=0.5)
    ax.axhline(0, color="k", lw=0.5, alpha=0.4)
    ax.set_xlim(0, 160)
    ax.set_ylim(-1.08, 1.08)
    ax.set_xlabel("delay (ps)")
    ax.set_ylabel("average mz")


def twin(ax):
    axt = ax.twinx()
    axt.set_ylim(290, 900)
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

    # ---- (a) heating off -> on at the same Jp (theta_DL = 0.2) ----
    ax = axes[0]
    axt = twin(ax)
    pairs = [(6e12, "si_noh_t20_Jp6", "si_h_t20_Jp6"),
             (8e12, "si_noh_t20_Jp8", "si_h_t20_Jp8"),
             (10e12, "si_noh_t20_Jp10", "si_h_t20_Jp10"),
             (20e12, "si_noh_t20_Jp20", "si_h_t20_Jp20")]
    cols = plt.cm.viridis(np.linspace(0.15, 0.85, len(pairs)))
    for (jp, off, on), col in zip(pairs, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.2,
                 label="$J_p$=%.0fe12" % (jp / 1e12))
        t, c = plot_run(ax, args.runs, on, col, ls="-", lw=1.6)
        axt.plot(t, c["T"], color=col, ls="-.", lw=0.9, alpha=0.55)
    ax.set_title("(a) SI heat off (---) vs on (-), same $J_p$, $\\theta_{DL}$=0.2\n"
                 "heating lowers $J_c$: ~20e12 -> ~10e12 (ratio 2, SI: 9$\\to$6e12)",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="lower left", title="solid: heating on, dashed: off",
              title_fontsize=7)
    style(ax)

    # ---- (b) theta_DL ~ 0: thermal-anisotropy torque only ----
    ax = axes[1]
    axt = twin(ax)
    b2 = [(8e12, "si_b2t0_Jp8", "no flip"),
          (10e12, "si_b2t0_Jp10", "no flip"),
          (12e12, "si_b2t0_Jp12", "122.5 ps"),
          (14e12, "si_b2t0_Jp14", "80.2 ps")]
    cols = plt.cm.inferno(np.linspace(0.25, 0.9, len(b2)))
    for (jp, tag, tc), col in zip(b2, cols):
        t, c = plot_run(ax, args.runs, tag, col, lw=1.5,
                        label="$J_p$=%.0fe12  (%s)" % (jp / 1e12, tc))
        axt.plot(t, c["T"], color=col, ls="-.", lw=0.9, alpha=0.55)
    t, c = plot_run(ax, args.runs, "si_h_t20_Jp10", "gray", ls=":", lw=1.4,
                    label=r"full model $\theta_{DL}$=0.2 (68.3 ps)")
    ax.set_title(r"(b) $\theta_{DL}\approx$0: thermal-anisotropy torque only"
                 "\n(SI Fig. 5; needs stronger heating, slower)", fontsize=10)
    ax.legend(fontsize=7, loc="lower left")
    style(ax)

    # ---- (c) Kz(T) frozen / Ms(T) frozen ----
    ax = axes[2]
    axt = twin(ax)
    b3 = [(10e12, "si_Kzfr_Jp10", "si_h_t20_Jp10"),
          (12e12, "si_Kzfr_Jp12", "si_h_t20_Jp12")]
    cols = plt.cm.plasma(np.linspace(0.12, 0.55, len(b3)))
    for (jp, off, on), col in zip(b3, cols):
        plot_run(ax, args.runs, off, col, ls="--", lw=1.2)
        t, c = plot_run(ax, args.runs, on, col, lw=1.6,
                        label="$J_p$=%.0fe12" % (jp / 1e12))
        axt.plot(t, c["T"], color=col, ls="-.", lw=0.9, alpha=0.55)
    for jp, tag, col in [(10e12, "si_Msfr_Jp10", "tab:cyan"),
                         (12e12, "si_Msfr_Jp12", "tab:green")]:
        plot_run(ax, args.runs, tag, col, ls=":", lw=1.5,
                 label="$M_s$(T) frozen, %.0fe12" % (jp / 1e12))
    ax.set_title("(c) Kz(T) frozen (---) vs full SI (-): no flip to 1.4e13\n"
                 "Ms(T) frozen only (:): Kz(T) collapse drives the switch",
                 fontsize=10)
    ax.legend(fontsize=7, loc="lower left")
    style(ax)

    fig.savefig(args.out, dpi=200)
    print("saved:", args.out)


if __name__ == "__main__":
    sys.exit(main())
