"""Device schematic for the P1/P2 slides (no paper screenshot needed).

Draws the Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm stack cross-section with
the in-plane current pulse J(t), the bias field Hx and the spin
polarization sigma from the Pt/Ta layers.

Usage:
    python draw_device.py
Output:
    slides/assets/device_stack.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "slides", "assets", "device_stack.png")

LAYERS = [
    ("Ta 5 nm", 1.50, "#8c8c8c", "white"),
    ("Pt 4 nm", 1.25, "#a6bdd7", "#1f3864"),
    ("Co 1 nm (PMA)", 0.62, "#c00000", "white"),
    ("Cu 1 nm", 0.62, "#e8a33d", "#1f3864"),
    ("Ta 4 nm", 1.25, "#8c8c8c", "white"),
    ("Pt 1 nm", 0.55, "#a6bdd7", "#1f3864"),
]
X0, W = 1.6, 5.0


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    ax.set_xlim(0, 12)
    ax.set_ylim(-1.7, 8.6)
    ax.axis("off")

    y = 0.0
    for name, h, color, _ in LAYERS:
        ax.add_patch(Rectangle((X0, y), W, h, facecolor=color,
                               edgecolor="0.25", lw=1.0, zorder=3))
        ax.text(X0 + W + 0.25, y + h / 2.0, name, va="center", ha="left",
                fontsize=10.5, color="0.15",
                fontweight="bold" if "PMA" in name else "normal")
        y += h
    top = y
    yco = sum(h for _, h, _, _ in LAYERS[:2]) + LAYERS[2][1] / 2.0

    ax.text(X0 + W / 2.0, top + 2.05,
            "Ta(5)/Pt(4)/Co(1)/Cu(1)/Ta(4)/Pt(1) nm",
            ha="center", va="bottom", fontsize=12, fontweight="bold",
            color="#1f3864")

    # in-plane current pulse (x direction), drawn through the stack
    ax.add_patch(FancyArrow(X0 - 1.1, 0.9, W + 1.35, 0, width=0.075,
                            head_width=0.34, head_length=0.42,
                            length_includes_head=True, color="#c00000",
                            zorder=5))
    ax.text(X0 + W / 2.0, 0.9, r"$J(t)$: 6 ps sech$^2$  (in-plane $x$)",
            ha="center", va="center", fontsize=10, color="#c00000",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.9,
                      boxstyle="round,pad=0.15"), zorder=6)

    # bias field Hx (x direction, above the stack)
    ax.add_patch(FancyArrow(X0 - 0.4, top + 1.05, W + 0.8, 0, width=0.06,
                            head_width=0.30, head_length=0.36,
                            length_includes_head=True, color="#1f3864",
                            zorder=5))
    ax.text(X0 + W / 2.0, top + 1.35, r"$H_x$ = ±160 mT",
            ha="center", va="bottom", fontsize=10.5, color="#1f3864")

    # spin-polarization direction (sigma || y, out of the drawing plane)
    ax.annotate(r"$\sigma \parallel y$" + "\n(Pt/Ta)",
                xy=(X0, 2.45), xytext=(0.05, 4.9),
                fontsize=10.5, color="0.25", ha="left",
                arrowprops=dict(arrowstyle="-|>", color="0.25", lw=1.1,
                                connectionstyle="arc3,rad=-0.25"))

    # magnetization flip inside the Co layer (up -> down)
    ax.annotate("", xy=(X0 + 0.62 * W, yco + 0.24),
                xytext=(X0 + 0.62 * W, yco - 0.24),
                arrowprops=dict(arrowstyle="-|>", color="white", lw=2.0))
    ax.annotate("", xy=(X0 + 0.86 * W, yco - 0.24),
                xytext=(X0 + 0.86 * W, yco + 0.24),
                arrowprops=dict(arrowstyle="-|>", color="white", lw=2.0))

    ax.text(X0 + W / 2.0, -0.45, "5 × 4 µm² current window",
            ha="center", va="top", fontsize=10, color="0.35")
    ax.text(X0 + W / 2.0, -1.05,
            "one 6 ps pulse:  $m_z$: +z → −z   (SOT + Joule heating)",
            ha="center", va="top", fontsize=10, color="0.15")

    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    print("saved:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
