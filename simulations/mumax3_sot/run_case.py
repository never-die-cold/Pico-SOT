"""Run one mumax3 case with parameter substitutions, keeping results organized.

Layout created (next to the template script):

    runs/
      summary.csv          one row per case (params + final state)
      <tag>/
        <tag>.mx3          exact script that was run
        out/               mumax3 output (table.txt, log.txt, ovf, png, ...)

Usage:
    python run_case.py fig3_switching.mx3 q1_Hxp_Ip --set Hx=0.160 Isign=1
    python run_case.py fig4_dynamics.mx3 f4_lowJ --set Jpk=2e12 dTpk=15 --no-run
"""
import argparse
import csv
import datetime
import os
import re
import subprocess
import sys

MUMAX = os.environ.get("MUMAX3_BIN", r"E:\mumax3.12_windows_cuda12.9\mumax3.exe")
SUMMARY = "summary.csv"


def substitute(text, sets):
    for var, val in sets.items():
        pat = re.compile(r"^(\s*%s\s*:?=\s*)(\S+)(.*)$" % re.escape(var), re.M)
        new_text, n = pat.subn(lambda m: m.group(1) + str(val) + m.group(3), text)
        if n == 0:
            raise SystemExit("parameter %r not found in template" % var)
        text = new_text
    return text


def read_table(path):
    names = None
    rows = []
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                names = [c.strip().split()[0] for c in line[1:].strip().split("\t") if c.strip()]
            else:
                rows.append([float(x) for x in line.split()])
    idx = {n: i for i, n in enumerate(names)}
    t = rows[-1][idx["t"]]
    mz = rows[-1][idx["mz"]]
    tmax = max(r[idx["T"]] for r in rows) if "T" in idx else float("nan")

    mz0 = rows[0][idx["mz"]]
    s0 = 1.0 if mz0 >= 0 else -1.0
    t_cross = float("nan")
    recov = float("nan")
    for r in rows:
        if r[idx["mz"]] * s0 < 0:
            t_cross = r[idx["t"]]
            break
    if t_cross == t_cross:  # not NaN
        for r in rows:
            if r[idx["t"]] >= t_cross + 50e-12:
                if abs(mz) > 1e-9:
                    recov = abs(r[idx["mz"]]) / abs(mz)
                break
    mz0 = rows[0][idx["mz"]]  # first table row = initial state (sign only)
    return t, mz, tmax, t_cross, recov, mz0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template")
    ap.add_argument("tag")
    ap.add_argument("--set", nargs="*", default=[], metavar="VAR=VALUE")
    ap.add_argument("--mumax", default=MUMAX)
    ap.add_argument("--force", action="store_true", help="overwrite existing case dir")
    ap.add_argument("--no-run", action="store_true", help="only write the script")
    args = ap.parse_args()

    root = os.path.dirname(os.path.abspath(args.template))
    sets = {}
    for kv in args.set:
        k, v = kv.split("=", 1)
        sets[k] = v

    case_dir = os.path.join(root, "runs", args.tag)
    out_dir = os.path.join(case_dir, "out")
    if os.path.exists(case_dir):
        if not args.force:
            raise SystemExit("case dir exists (use --force): %s" % case_dir)
        import shutil
        shutil.rmtree(case_dir)
    os.makedirs(case_dir)

    text = open(args.template, encoding="utf-8").read()
    text = substitute(text, sets)
    script = os.path.join(case_dir, args.tag + ".mx3")
    with open(script, "w", encoding="utf-8") as f:
        f.write(text)
    print("script:", script)

    if args.no_run:
        return 0

    cmd = [args.mumax, "-f", "-o", out_dir, script]
    print("run:", " ".join(cmd))
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        raise SystemExit("mumax3 failed with code %d" % r.returncode)

    table = os.path.join(out_dir, "table.txt")
    if not os.path.isfile(table):
        raise SystemExit("no table.txt produced")
    t_end, mz, tmax, t_cross, recov, mz0 = read_table(table)

    row = {"tag": args.tag, "time": datetime.datetime.now().isoformat(timespec="seconds"),
           "t_end_ps": "%.1f" % (t_end * 1e12), "mz_final": "%.4f" % mz,
           "switched": int(mz * mz0 < -0.5), "Tmax_K": "%.0f" % tmax,
           "t_cross_ps": "" if t_cross != t_cross else "%.1f" % (t_cross * 1e12),
           "recov_50ps": "" if recov != recov else "%.2f" % recov}
    row.update(sets)
    summary = os.path.join(root, "runs", SUMMARY)
    rows, fields = [], []
    if os.path.isfile(summary):
        with open(summary, newline="", encoding="utf-8") as f:
            r = csv.DictReader(f)
            fields = list(r.fieldnames or [])
            rows = list(r)
    for k in row:
        if k not in fields:
            fields.append(k)
    rows.append(row)
    with open(summary, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("mz_final = %+.4f  Tmax = %.0f K  ->  %s" % (mz, tmax, summary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
