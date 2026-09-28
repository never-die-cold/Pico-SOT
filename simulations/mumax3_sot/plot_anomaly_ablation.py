"""Ablation-summary figure for the recapture-window attribution study.

Reads ab_* rows from runs/summary.csv (Hx / G_int / Tc scans around the
heated theta_DL=0.2 recapture window) and the si_h_t20 reference series:

    anomaly_ablation.png   (a) outcome map in the (Jp, Hx) plane
                           (b) outcome map in the (Jp, G_int) plane
                           (c) outcome map in the (Jp, Tc) plane

Each point: switch (crimson), no switch / recaptured (white), marginal
(|mz|<0.5 but not switched, yellow), T>Tc (open, HAMR-like regime).

Usage:
    python plot_anomaly_ablation.py [--summary runs/summary.csv] [--outdir runs]
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

REF_HX = 160  # reference series bias field


def load_rows(summary):
    rows = []
    with open(summary, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = row.get("tag", "")
            if not row.get("Jp"):
                continue
            jp = float(row["Jp"]) / 1e12
            mz = float(row["mz_final"])
            tmax = float(row["Tmax_K"])
            sw = int(row["switched"]) if row["switched"] else 0
            m = re.match(r"^ab_hx(\d+)_Jp", tag)
            if m:
                rows.append({"fam": "hx", "x": float(m.group(1)) / 1000.0, "jp": jp,
                             "mz": mz, "sw": sw, "tmax": tmax})
                continue
            m = re.match(r"^ab_G(\d+)_Jp", tag)
            if m:
                rows.append({"fam": "G", "x": float(m.group(1)), "jp": jp,
                             "mz": mz, "sw": sw, "tmax": tmax})
                continue
            m = re.match(r"^ab_Tc(\d+)_Jp", tag)
            if m:
                rows.append({"fam": "Tc", "x": float(m.group(1)), "jp": jp,
                             "mz": mz, "sw": sw, "tmax": tmax})
                continue
            if re.match(r"^si_h_t20_Jp\d+(?:p\d+)?(_lr\d+)?(_dt\d+)?$", tag):
                rows.append({"fam": "hx", "x": REF_HX / 1000.0, "jp": jp,
                             "mz": mz, "sw": sw, "tmax": tmax, "ref": True})
    return rows


def outcome_color(r):
    if r["tmax"] > 800.0:
        return "darkorange"
    if r["sw"]:
        return "crimson"
    if abs(r["mz"]) < 0.5:
        return "gold"  # hovered near the equator
    return "white"


def panel(ax, rows, xlabel, title, xlim=None):
    xs = sorted({r["x"] for r in rows})
    for x in xs:
        band = sorted([r for r in rows if r["x"] == x], key=lambda r: r["jp"])
        for r in band:
            face = outcome_color(r)
            edge = "0.15"
            if r["tmax"] > 800.0:
                ax.scatter(r["jp"], x, marker="s", s=210, facecolor="none",
                           edgecolor="darkorange", linewidth=1.6, zorder=3)
            ax.scatter(r["jp"], x, marker="o", s=170, facecolor=face,
                       edgecolor=edge, linewidth=1.0, zorder=4)
    ax.set_xlabel(r"$J_p$（10$^{12}$ A/m$^2$）")
    ax.set_ylabel(xlabel)
    ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.3, lw=0.5)
    if xlim:
        ax.set_xlim(*xlim)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="runs/summary.csv")
    ap.add_argument("--outdir", default="runs")
    args = ap.parse_args()

    rows = load_rows(args.summary)
    fams = {f: [r for r in rows if r["fam"] == f] for f in ("hx", "G", "Tc")}
    if not fams["hx"]:
        raise SystemExit("no ab_* rows found; run ablation_plan.json first")

    fs.apply()
    fig, axs = plt.subplots(1, 3, figsize=(14.5, 4.6), constrained_layout=True,
                            sharey=False)
    panel(axs[0], fams["hx"], "(a) 改变面内偏置场 $H_x$：窗口随 $H_x$ 移动/分裂",
          "$H_x$ (T)", xlim=(11.4, 20.6))
    axs[0].set_xscale("linear")
    if fams["G"]:
        panel(axs[1], fams["G"], "(b) 改变界面热导 $G$（降温快慢）：窗口边界随 $\\tau$ 移动",
              "$G_{int}$（10$^6$ W/m²K）")
    else:
        axs[1].text(0.5, 0.5, "G_int 扫描未运行", ha="center", va="center",
                    transform=axs[1].transAxes)
    if fams["Tc"]:
        panel(axs[2], fams["Tc"], "(c) 改变 $T_c$（温标）：窗口边界随 $T_c$ 移动",
              "$T_c$ (K)")
    else:
        axs[2].text(0.5, 0.5, "Tc 扫描未运行", ha="center", va="center",
                    transform=axs[2].transAxes)

    handles = [
        plt.scatter([], [], s=150, facecolor="crimson", edgecolor="0.15", label="翻转"),
        plt.scatter([], [], s=150, facecolor="white", edgecolor="0.15", label="不翻（回翻/未翻）"),
        plt.scatter([], [], s=150, facecolor="gold", edgecolor="0.15", label="边缘态（|mz|<0.5）"),
        plt.scatter([], [], s=150, marker="s", facecolor="none", edgecolor="darkorange",
                    linewidth=1.6, label="$T_{max}>T_c$（HAMR 区）"),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=4, fontsize=9.5,
               frameon=False)
    path = os.path.join(args.outdir, "anomaly_ablation.png")
    fig.savefig(path, dpi=200)
    print("saved:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
