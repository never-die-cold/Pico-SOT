"""Noise-ensemble statistics: P_sw(Jp) around the precessional recapture window.

Reads the ns_h_t20_* ensemble (Noise=1, independent Langevin realisations via
FixDt jitter, see docs/MODEL.md S2.4) and the deterministic reference outcomes:

    noise_stats.png   (a) P_sw(Jp) with Wilson 95% interval, deterministic
                          outcome as diamonds
                      (b) mz_final per-replicate strip per Jp

Requires ab_dt*_Jp15 deterministic dt-jitter controls in summary.csv (they must
reproduce the deterministic outcome; without noise the jitter changes nothing).

Usage:
    python plot_noise.py [--summary runs/summary.csv] [--outdir runs]
"""
import argparse
import csv
import math
import os
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import figstyle as fs


def wilson(k, n, z=1.96):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    e = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - e) / d, (c + e) / d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="runs/summary.csv")
    ap.add_argument("--outdir", default="runs")
    args = ap.parse_args()

    pat = re.compile(r"^ns_h_t20_Jp(\d+)(?:p(\d+))?_r(\d+)$")
    ens = {}
    with open(args.summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            m = pat.match(row.get("tag", ""))
            if not m:
                continue
            jp = int(m.group(1)) + (int(m.group(2) or 0) / 10)
            ens.setdefault(jp, []).append(row)

    if not ens:
        raise SystemExit("no ns_h_t20_* rows found; run noise_plan.json first")

    det = {}
    with open(args.summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if re.match(r"^si_h_t20_Jp\d+(?:p\d+)?(_lr\d+)?$", row.get("tag", "")) and row.get("Jp"):
                jp = round(float(row["Jp"]) / 1e12, 2)
                det[jp] = int(row["switched"])

    fs.apply()
    fig, ax = plt.subplots(1, 2, figsize=(11.0, 4.3), constrained_layout=True)

    jps = sorted(ens)
    psw, lo, hi, n_arr = [], [], [], []
    for jp in jps:
        rows = ens[jp]
        n = len(rows)
        k = sum(int(r["switched"]) for r in rows)
        psw.append(k / n)
        a, b = wilson(k, n)
        lo.append(k / n - a)
        hi.append(b - k / n)
        n_arr.append(n)
    ax[0].errorbar(jps, psw, yerr=[lo, hi], fmt="o-", color=fs.C["heat020"],
                   lw=1.6, ms=5, capsize=3, label="噪声系综（8 个独立样本）")
    dj = sorted(j for j in det if 13.0 <= j <= 19.0)
    ax[0].plot(dj, [det[j] for j in dj], "D", color="0.25", ms=7,
               label="确定性（Noise=0）")
    ax[0].axvspan(15, 17, color="0.92", zorder=0)
    ax[0].text(16, 0.5, "回翻窗口\n(15–17)", ha="center", va="center",
               fontsize=9.5, color="0.3")
    ax[0].set_ylim(-0.06, 1.06)
    ax[0].set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
    ax[0].set_ylabel("$P_{sw}$")
    ax[0].set_title("(a) 开关概率：窗口在噪声下是否稳健")
    ax[0].legend(fontsize=9, loc="center left")

    rng = np.random.default_rng(0)
    for jp in jps:
        mzs = [float(r["mz_final"]) for r in ens[jp]]
        x = np.full(len(mzs), jp) + rng.uniform(-0.12, 0.12, len(mzs))
        ax[1].scatter(x, mzs, s=26, color=fs.C["heat020"], alpha=0.75,
                      edgecolor="none")
    for jp, v in det.items():
        if 13.0 <= jp <= 19.0:
            ax[1].scatter(jp, [-0.98 if v else 0.98], marker="D", s=46,
                          color="0.25", zorder=4)
    ax[1].axvspan(15, 17, color="0.92", zorder=0)
    ax[1].set_ylim(-1.08, 1.08)
    ax[1].set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
    ax[1].set_ylabel("末态 $m_z$")
    ax[1].set_title("(b) 每个样本的末态（菱形 = 确定性）")

    path = os.path.join(args.outdir, "noise_stats.png")
    fig.savefig(path, dpi=200)
    print("saved:", path)

    for jp, p, n in zip(jps, psw, n_arr):
        print("Jp=%4.1f  P_sw=%.2f  (%d/%d)" % (jp, p, round(p * n), n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
