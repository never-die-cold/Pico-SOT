"""Replica of the thermal model of Jhuria et al. (NE 2020).

Solves the 1D heat-diffusion equation across the 16 nm metallic stack,

    C dT/dt = Lambda d2T/dz2 + q(t),      q(t) = rho_e J(t)^2

with an adiabatic top surface and an interfacial thermal conductance G_int
at the film/substrate boundary (heat flux G_int*T).  This is the physical
model the paper used to produce the temperatures that feed their macrospin
LLG simulation (Ms(T), Kz(T)).  Here we compute T(t) at the Co layer and
calibrate an equivalent 0D low-pass channel (used by the .mx3 scripts)
against the FD solution.

Parameters (paper):
    C      = 2.6e6 J m-3 K-1   (weighted average of the stack)
    Lambda = 9 W m-1 K-1       (Wiedemann-Franz)
    G_int  = 170e6 W m-2 K-1   (sapphire; 100e6 for glass)
    rho_e  = 81e-8 Ohm m
    d      = 16 nm

Outputs:
    runs/heat_model.png        FD T_Co(t) for several Jp + 0D channel comparison
    stdout                     calibration numbers (peak, tau, ODE error)

Usage:
    python heat_model.py
"""
import math
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ------------------------------------------------------------------- constants
C_VOL = 2.6e6        # J/m3/K
LAMBDA = 9.0         # W/m/K
G_INT = 170e6        # W/m2/K  (sapphire substrate)
RHO_E = 81e-8        # Ohm m
D_STACK = 16e-9      # m
TC = 800.0           # K
T_AMB = 300.0
CO_Z_FROM_TOP = 6.5e-9   # Co layer centre: Pt(1)+Ta(4)+Cu(1)+Co(1)/2
TP = 6e-12               # sech^2 FWHM used by the macrospin switching runs

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")


def sech2(t, t0, tp):
    x = 1.763 * (t - t0) / tp
    e = np.exp(np.clip(x, -300, 300))
    return 4.0 / (e + 1.0 / e) ** 2


def thomas(a, b, c, d):
    """Solve tridiagonal a[i] x[i-1] + b[i] x[i] + c[i] x[i+1] = d[i]."""
    n = len(b)
    cp = np.empty(n)
    dp = np.empty(n)
    cp[0] = c[0] / b[0]
    dp[0] = d[0] / b[0]
    for i in range(1, n):
        m = b[i] - a[i] * cp[i - 1]
        cp[i] = c[i] / m
        dp[i] = (d[i] - a[i] * dp[i - 1]) / m
    x = np.empty(n)
    x[-1] = dp[-1]
    for i in range(n - 2, -1, -1):
        x[i] = dp[i] - cp[i] * x[i + 1]
    return x


def solve_fd(q_shape, dt, nt, nz=33, d=D_STACK, collect=None):
    """Implicit-Euler 1D FD.  q_shape[i] is the source at step i in W/m3.

    Returns (z, T[nt, nz]) with T the deviation from ambient.
    """
    z = np.linspace(0.0, d, nz)
    dz = d / (nz - 1)
    # implicit Euler: (C/dt) T - Lambda d2T/dz2 = q + (C/dt) T_old
    k = LAMBDA / dz**2
    a = np.zeros(nz)          # sub-diagonal
    b = np.full(nz, C_VOL / dt + 2.0 * k)   # diagonal
    c = np.zeros(nz)          # super-diagonal
    a[1:] = -k
    c[:-1] = -k
    c[0] = -2.0 * k           # adiabatic (mirror) top node
    b[-1] = C_VOL / dt + k + G_INT / dz    # Robin substrate node
    T = np.zeros(nz)
    if collect is None:
        collect = np.arange(0, nt)
    out = np.zeros((len(collect), nz))
    k = 0
    for n in range(nt):
        d = q_shape[n] + (C_VOL / dt) * T
        T = thomas(a, b, c, d)
        if k < len(collect) and collect[k] == n:
            out[k] = T
            k += 1
    return z, out


def ode_channel(q_shape, dt, tau):
    """Equivalent 0D channel used by the .mx3 scripts (exact exponential step).

    dT/dt = q/C - T/tau
    """
    n = len(q_shape)
    T = np.zeros(n)
    decay = math.exp(-dt / tau)
    for i in range(1, n):
        T[i] = T[i - 1] * decay + (q_shape[i - 1] / C_VOL) * tau * (1.0 - decay)
    return T


def main():
    # --- FD response to the normalised 6 ps sech^2 pulse (unit peak J=1) ---
    dt = 2e-14
    tmax = 450e-12
    nt = int(tmax / dt)
    t = np.arange(nt) * dt
    t0 = 4 * TP
    shape = sech2(t, t0, TP)
    q = RHO_E * shape**2          # W/m3 for Jp = 1 A/m2
    ico = int(CO_Z_FROM_TOP / D_STACK * 32 + 0.5)
    z, T_all = solve_fd(q, dt, nt)
    T_co = T_all[:, ico]

    # peak at the calibration current
    Jp = 6e12
    peak = T_co.max() * (Jp / 1.0) ** 2
    print("FD: peak T_Co rise at Jp=6e12: %.1f K" % peak)
    print("FD: T_amb+peak = %.1f K" % (T_AMB + peak))

    # after-pulse single-exponential fit (50-400 ps)
    mask = t > 50e-12
    A = np.polyfit(t[mask], np.log(np.maximum(T_co[mask] * Jp**2, 1e-30)), 1)
    tau_fit = -1.0 / A[0]
    print("FD: decay tau (50-400 ps fit) = %.1f ps" % (tau_fit * 1e12))

    # equivalent 0D channel with tau = C*d/G
    tau0 = C_VOL * D_STACK / G_INT
    T_ode = ode_channel(q, dt, tau0) * Jp**2
    err = np.max(np.abs(T_ode - T_co * Jp**2)) / peak
    print("ODE channel: tau = C*d/G = %.1f ps" % (tau0 * 1e12))
    print("ODE channel: max deviation vs FD (0-450 ps) = %.1f%%" % (100 * err))

    # --- figure ---
    fig, ax = plt.subplots(1, 2, figsize=(9.4, 3.6), constrained_layout=True)
    tt = t * 1e12
    for jp in (4e12, 6e12, 8e12, 1.2e13, 2e13):
        Tp = T_AMB + T_co * jp**2
        ax[0].plot(tt, Tp, lw=1.2, label=r"$J_p$=%.0f$\times10^{12}$ A/m$^2$" % (jp / 1e12))
    ax[0].axhline(TC, color="gray", ls=":", lw=0.8)
    ax[0].text(0.02, 0.03, r"$T_c=800$ K", transform=ax[0].transAxes,
               fontsize=8, color="gray")
    ax[0].set_xlim(0, 200)
    ax[0].set_xlabel("time (ps)")
    ax[0].set_ylabel(r"$T_{Co}$ (K)")
    ax[0].set_title("heat-diffusion model (1D FD, paper)")
    ax[0].legend(fontsize=7)
    ax[0].grid(alpha=0.25, lw=0.5)

    ax[1].plot(tt, T_AMB + T_co * (6e12) ** 2, "k-", lw=1.4,
               label="FD (paper model)")
    ax[1].plot(tt, T_AMB + T_ode[: nt], "--", lw=1.4, color="tab:red",
               label=r"0D ODE ($\tau$=C d/G)")
    ax[1].set_xlim(0, 200)
    ax[1].set_xlabel("time (ps)")
    ax[1].set_ylabel(r"$T_{Co}$ (K)")
    ax[1].set_title(r"$J_p$ = 6$\times10^{12}$ A/m$^2$, 6 ps sech$^2$")
    ax[1].legend(fontsize=7)
    ax[1].grid(alpha=0.25, lw=0.5)
    out = os.path.join(OUTDIR, "heat_model.png")
    fig.savefig(out, dpi=200)
    print("saved:", out)


if __name__ == "__main__":
    main()
