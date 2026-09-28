"""Batch runner: execute a JSON plan of run_case.py cases sequentially.

Plan format (list of case objects):

    [
      {"template": "macrospin_switch.mx3", "tag": "ab_hx040_Jp14",
       "set": {"Jp": "14e12", "Hx_mT": "40"}},
      ...
    ]

Paths are relative to this script's directory (the mumax3 working dir).

Behaviour:
  * skips cases whose runs/<tag> directory already exists (resume-safe);
    --force re-runs everything
  * --dry-run only lists what would run
  * each case is delegated to `python run_case.py <template> <tag> --set ...`
    so summary.csv handling stays in one place
  * a case that fails is logged and the batch continues (mumax3 GPU hiccups
    should not kill a 90-case overnight run); exit code 1 if any failed

Usage:
    python run_batch.py ablation_plan.json [--force] [--dry-run] [--limit N]
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="run only the first N cases")
    args = ap.parse_args()

    with open(os.path.join(HERE, args.plan), encoding="utf-8") as f:
        cases = json.load(f)
    if args.limit:
        cases = cases[:args.limit]

    todo = []
    for c in cases:
        tag = c["tag"]
        case_dir = os.path.join(HERE, "runs", tag)
        if os.path.isdir(case_dir) and not args.force:
            print("skip (exists):", tag)
            continue
        todo.append(c)

    print("%d cases in plan, %d to run" % (len(cases), len(todo)))
    if args.dry_run:
        for c in todo:
            print("  would run:", c["tag"], c.get("set", {}))
        return 0

    failed = []
    t_start = time.time()
    for i, c in enumerate(todo, 1):
        cmd = [sys.executable, os.path.join(HERE, "run_case.py"), c["template"], c["tag"]]
        # ONE --set with all pairs: argparse nargs='*' makes repeated --set
        # flags last-wins, which would silently drop every parameter but the last
        sets = ["%s=%s" % (k, v) for k, v in c.get("set", {}).items()]
        if sets:
            cmd += ["--set"] + sets
        t0 = time.time()
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True,
                           errors="replace")
        dt = time.time() - t0
        status = "ok" if r.returncode == 0 else "FAILED(%d)" % r.returncode
        print("[%d/%d] %s %s (%.0f s)" % (i, len(todo), c["tag"], status, dt), flush=True)
        if r.returncode != 0:
            failed.append(c["tag"])
            print(r.stdout[-800:], r.stderr[-800:])
    total = time.time() - t_start
    print("done: %d ok, %d failed, %.1f min total" % (len(todo) - len(failed), len(failed), total / 60))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
