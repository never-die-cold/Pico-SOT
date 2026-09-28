"""Shared matplotlib style for all PicoSOT figures.

Import and call `apply()` (or just `import figstyle as fs; fs.apply()`) before
building any figure.  Replaces the per-script rcParams that previously allowed
5.5-7 pt fonts on oversized canvases (ROADMAP D5).

Language: labels default to Chinese; set env LANG=en for English
(same keys, both dictionaries must stay in sync).
"""
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# palette: one semantic colour per series family, reused across every figure
# ---------------------------------------------------------------------------
C = {
    "heat020": "crimson",      # theta_DL = 0.2, heating on
    "noheat020": "tab:blue",   # theta_DL = 0.2, heating off
    "heat030": "tab:orange",   # theta_DL = 0.3, heating on
    "noheat030": "tab:green",  # theta_DL = 0.3, heating off
    "control": "0.35",         # ablations / symmetry checks
    "refline": "k",
    "pulse": "0.85",           # pulse-window shading
}

_JP = {"14": "C0", "15": "C1", "16": "C2", "17": "C3", "18": "C4"}  # per-Jp curves

_TEXT = {
    "zh": {
        "time": "时间 t (ps)",
        "mz": "$m_z$",
        "temp": "温度 T (K)",
        "pulse": "脉冲窗口 (8$t_p$)",
        "hk": "各向异性场 $H_k(T)$ (T)",
        "hx": "面内场 $H_x$",
    },
    "en": {
        "time": "time t (ps)",
        "mz": "$m_z$",
        "temp": "temperature T (K)",
        "pulse": "pulse window (8$t_p$)",
        "hk": "anisotropy field $H_k(T)$ (T)",
        "hx": "in-plane field $H_x$",
    },
}
LANG = os.environ.get("LANG", "zh") if os.environ.get("LANG") in ("zh", "en") else "zh"
T = _TEXT[LANG]


def apply():
    """Set the global rcParams; call once at the top of every plot script."""
    plt.rcParams.update({
        # ~2x the old sizes (legends were 5.5-7 pt, ticks 7, titles 8.5)
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 11,
        "axes.labelsize": 11.5,
        "axes.titlesize": 12,
        "legend.fontsize": 9.5,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        # readable lines on 200 dpi output
        "lines.linewidth": 1.6,
        "axes.linewidth": 0.9,
        "legend.frameon": False,
        "figure.constrained_layout.use": True,
    })


def save(fig, outdir, name):
    """Save at dpi 200 and print the path (old scripts copied files by hand)."""
    path = os.path.join(outdir, name)
    fig.savefig(path, dpi=200)
    print("wrote", path)
    return path


def jp_color(jp):
    return _JP.get(str(jp), None)


def destair(t, y, dt=None):
    """Draw a zero-order-hold trace as the continuous curve it samples.

    The .mx3 loops recompute T (and through it Ms, Kz) once per loop step --
    0.2 ps while the pulse is on, 10 ps during the free-evolution stage -- and
    the table stores that held value.  Plotting the raw column therefore draws
    plateaus whose width is the loop step, which reads as a staircase.

    Between two hold nodes the stored value is an exact sample of the ODE the
    model solved: the 10 ps tail nodes of the lr1500 runs fit exp(-t/tau) with
    tau = 244.7 ps against the analytic C*d/G = 245 ps, residual < 0.04 K.
    Resampling those nodes on the table's own time grid restores the curve the
    model actually integrated, instead of the staircase the writer emitted.

    Returns (t, y) interpolated on a uniform grid, or the input unchanged when
    the trace shows no holds (fewer than three distinct values).
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)
    if t.size < 3:
        return t, y
    node = np.concatenate(([0], np.nonzero(np.diff(y) != 0)[0] + 1))
    if node.size < 3:
        return t, y
    if dt is None:
        dt = float(np.median(np.diff(t)))
    fine = np.arange(t[node[0]], t[node[-1]] + 0.5 * dt, dt)
    return fine, np.interp(fine, t[node], y[node])
