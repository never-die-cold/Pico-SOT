"""Anomaly evidence figure: why does switching fail at Jp = 15-17 (x10^12 A/m^2)?

Reads the long-relaxation (lr1500) heated theta_DL=0.2 runs and shows, for
Jp = 14..18, that the recaptured cases (15-17) follow one damped precessional
revolution around the +x bias field while the anisotropy well is still too
shallow to capture them:

    anomaly_evidence.png   2x2: mz(t), T(t), H_k(t) vs Hx, and the my-mz orbit

H_k(T) = BK300 * fr(T)^2 with fr = 1-(T/Tc)^1.7 (paper model, see
docs/paper_replica.md); H_k(T*) = Hx defines the well-recovery temperature T*.

Panel (b)/(c) resample T with figstyle.destair: the lr1500 runs recompute T
only once per 10 ps free-evolution step, so the stored column is a staircase
whose nodes are exact samples of the exp(-t/245 ps) decay (see figstyle).

Usage:
    python plot_anomaly.py [--outdir runs] [--docsfig ../../docs/figures]
"""
import argparse
import os

import numpy as np
import matplotlib.pyplot as plt

import figstyle as fs

HERE = os.path.dirname(os.path.abspath(__file__))

# paper parameters (macrospin_switch.mx3)
TC = 800.0
BK300 = 0.8          # T
HX = 0.160           # T  (Hx_mT = 160)
TP_PS = 6.0

CASES = [  # (Jp in 1e12 A/m2, tag, outcome)
    (14, "si_h_t20_Jp14_lr1500", "sw"),
    (15, "si_h_t20_Jp15_lr1500", "recap"),
    (16, "si_h_t20_Jp16_lr1500", "recap"),
    (17, "si_h_t20_Jp17_lr1500", "recap"),
    (18, "si_h_t20_Jp18_lr1500", "sw"),
]


def load(rundir, tag):
    path = os.path.join(rundir, tag, "out", "table.txt")
    cols = np.loadtxt(path, comments="#")  # t, mx, my, mz, E_total, J, T
    t_ps = cols[:, 0] * 1e12
    return {"t": t_ps, "mx": cols[:, 1], "my": cols[:, 2], "mz": cols[:, 3],
            "J": cols[:, 5], "T": cols[:, 6]}


def fr_of_T(T):
    fr = 1.0 - (T / TC) ** 1.7
    return np.clip(fr, 0.0, None)


def T_star(hx=HX):
    """Temperature where H_k(T) = Hx (well reappears during cooling)."""
    fr = np.sqrt(hx / BK300)
    return TC * (1.0 - fr) ** (1.0 / 1.7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(HERE, "runs"))
    ap.add_argument("--docsfig", default=os.path.join(HERE, "..", "..", "docs", "figures"))
    args = ap.parse_args()

    fs.apply()
    runs = {jp: load(args.outdir, tag) for jp, tag, _ in CASES}
    outcome = {jp: o for jp, _, o in CASES}

    tstar = T_star()
    colors = {jp: plt.cm.viridis(i / (len(CASES) - 1)) for i, (jp, _, _) in enumerate(CASES)}
    # semantic: switched = blue family, recaptured = warm family
    colors = {jp: ("tab:blue" if outcome[jp] == "sw" else "crimson") for jp, _, _ in CASES}

    fig, axes = plt.subplots(2, 2, figsize=(11.0, 7.0))

    # ---------------- (a) mz(t) ----------------
    ax = axes[0, 0]
    for jp, run in runs.items():
        m = run["t"] <= 400.0
        ax.plot(run["t"][m], run["mz"][m], color=colors[jp],
                label=f"$J_p$={jp}×10$^{{12}}$ A/m²" + ("（翻转）" if outcome[jp] == "sw" else "（回翻）"))
        tc = run["t"][np.where(np.sign(run["mz"]) != np.sign(run["mz"][0]))[0]]
        if len(tc):
            ax.plot(tc[0], 0, marker="v", ms=5, color=colors[jp], clip_on=False)
    ax.axvspan(0, 8 * TP_PS, color=fs.C["pulse"], label=fs.T["pulse"])
    ax.axhline(0, color="0.7", lw=0.6)
    ax.set_xlabel(fs.T["time"])
    ax.set_ylabel(fs.T["mz"])
    ax.set_title("(a) 磁矩轨迹：15–17 过零后翻回 +z")
    ax.legend(fontsize=8.5, ncol=1)

    # ---------------- (b) T(t) ----------------
    ax = axes[0, 1]
    for jp, run in runs.items():
        t, T = fs.destair(run["t"], run["T"])   # 10 ps free-evolution hold
        m = t <= 400.0
        ax.plot(t[m], T[m], color=colors[jp])
    ax.axhline(tstar, color=fs.C["refline"], lw=1.0, ls="--",
               label=f"$T^*$={tstar:.0f} K ($H_k$=$H_x$)")
    ax.axvspan(0, 8 * TP_PS, color=fs.C["pulse"])
    ax.set_xlabel(fs.T["time"])
    ax.set_ylabel(fs.T["temp"])
    ax.set_title("(b) 温度：降温穿过 $T^*$ 的时间决定捕获相位")
    ax.legend(fontsize=9)

    # ---------------- (c) H_k(t) vs Hx ----------------
    ax = axes[1, 0]
    for jp, run in runs.items():
        tb, T = fs.destair(run["t"], run["T"])  # H_k inherits the T staircase
        m = tb <= 400.0
        hk = BK300 * fr_of_T(T[m]) ** 2
        ax.plot(tb[m], hk, color=colors[jp])
    ax.axhline(HX, color=fs.C["refline"], lw=1.0, ls="--", label=fs.T["hx"])
    ax.axvspan(0, 8 * TP_PS, color=fs.C["pulse"])
    ax.set_xlabel(fs.T["time"])
    ax.set_ylabel(fs.T["hk"])
    ax.set_ylim(0, None)
    ax.set_title("(c) $H_k(T)$ 恢复 vs $H_x$：$H_k\\lesssim H_x$ 期间势阱过浅")
    ax.legend(fontsize=9)

    # ---------------- (d) my-mz orbit ----------------
    ax = axes[1, 1]
    for jp in (15, 18):
        run = runs[jp]
        m = (run["t"] <= 400.0) & (run["t"] >= 40.0)
        ax.plot(run["my"][m], run["mz"][m], color=colors[jp], lw=1.4,
                label=f"$J_p$={jp}×10$^{{12}}$ " + ("（翻转）" if outcome[jp] == "sw" else "（回翻）"))
        for tt in (48, 92, 160, 280):
            i = np.argmin(np.abs(run["t"] - tt))
            ax.plot(run["my"][i], run["mz"][i], marker="o", ms=3.5, color=colors[jp])
            ax.annotate(f"{tt} ps", (run["my"][i], run["mz"][i]),
                        textcoords="offset points", xytext=(5, 4), fontsize=8, color=colors[jp])
    ax.axhline(0, color="0.7", lw=0.6)
    ax.axvline(0, color="0.7", lw=0.6)
    ax.set_xlabel("$m_y$")
    ax.set_ylabel(fs.T["mz"])
    ax.set_title("(d) 绕 +$x$ 轴的阻尼进动一圈：落在哪侧被捕获")
    ax.legend(fontsize=9, loc="lower left")

    path = fs.save(fig, args.outdir, "anomaly_evidence.png")
    if os.path.isdir(args.docsfig):
        import shutil
        shutil.copy(path, os.path.join(args.docsfig, "anomaly_evidence.png"))
        print("copied to", args.docsfig)


if __name__ == "__main__":
    main()
