"""Energy check for picosecond-pulse SOT switching (NE 2020 method).

The paper estimates the dissipated energy density as
    E = integral J(t)^2 rho dt = 0.75 * J^2 * rho * tau_p   [J/m^3]
and multiplies by the current-carrying stack volume to get < 50 pJ at the
switching threshold (Jc ~ 6e12 A/m^2, rho = 81 uOhm cm, tau_p = 6 ps,
volume = 5 um x 4 um x 15 nm).

Usage:
    python energy_check.py <table.txt | run_dir> [more ...]
"""
import argparse
import os
import sys

import numpy as np

RHO = 81e-8          # 81 uOhm cm  [Ohm m]
VSTACK = 5e-6 * 4e-6 * 15e-9   # 5 x 4 um^2 x 15 nm stack  [m^3]


def find_table(path):
    if os.path.isdir(path):
        for cand in (os.path.join(path, "out", "table.txt"), os.path.join(path, "table.txt")):
            if os.path.isfile(cand):
                return cand
        raise SystemExit("no table.txt in %s" % path)
    return path


def load_j(path):
    names, rows = None, []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                names = [c.strip().split()[0] for c in line[1:].strip().split("\t") if c.strip()]
            else:
                rows.append([float(x) for x in line.split()])
    i = {n: k for k, n in enumerate(names)}
    if "J" not in i:
        raise SystemExit("no J column in %s (add TableAddVar(Jcur,...))" % path)
    t = np.array([r[i["t"]] for r in rows])
    j = np.array([r[i["J"]] for r in rows])
    return t, j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    print("%-34s %10s %10s %10s" % ("case", "Jpk [A/m2]", "int J^2 dt", "E [pJ]"))
    for p in args.paths:
        table = find_table(p)
        t, j = load_j(table)
        integral = np.trapezoid(j * j, t)          # int J^2 dt  [A^2 s / m^4]
        e_joule = integral * RHO * VSTACK          # [J]
        name = os.path.basename(os.path.dirname(os.path.abspath(table)))
        if name == "out":
            name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(table))))
        print("%-34s %10.3g %10.3g %10.2f" % (name, np.max(np.abs(j)), integral, e_joule * 1e12))
    print("\npaper reference: J=6e12 gives ~40 pJ (their <50 pJ budget)")
    print("rho = %.3g Ohm m, V = %.3g m^3" % (RHO, VSTACK))


if __name__ == "__main__":
    sys.exit(main())
