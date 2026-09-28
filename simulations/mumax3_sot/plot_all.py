"""One-shot rebuild of every deliverable figure (ROADMAP T1).

Runs all plot scripts in dependency order and copies their outputs into
docs/figures/.  Skips scripts whose required run data is absent (e.g. the
noise ensemble before noise_plan.json has been executed) so a fresh checkout
with only docs/figures can still rebuild most figures once runs/ exists.

Usage:
    python plot_all.py            # rebuild all + copy to ../../docs/figures
    python plot_all.py --dry-run  # list what would run
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "..", "docs", "figures")

# script -> outputs it produces (copied to docs/figures when present in runs/)
JOBS = [
    ("heat_model.py", ["heat_model.png"]),
    ("plot_phase.py", ["phase_map.png", "phase_heated.png", "phase_noheat.png",
                       "phase_traces.png", "phase_speed.png"]),
    ("plot_mechanism.py", ["mechanism_compare.png"]),
    ("plot_fig4.py", ["fig4_full.png"]),
    ("plot_quadrants.py", ["q_quadrants.png"]),
    ("plot_energy.py", ["energy_bars.png"]),
    ("plot_energy_split.py", ["energy_bars_split.png"]),
    ("plot_anomaly.py", ["anomaly_evidence.png"]),
    ("plot_anomaly_ablation.py", ["anomaly_ablation.png"]),
    ("plot_noise.py", ["noise_stats.png"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    failed = []
    for script, outs in JOBS:
        if args.dry_run:
            print("would run:", script, "->", ", ".join(outs))
            continue
        r = subprocess.run([sys.executable, os.path.join(HERE, script)],
                           cwd=HERE, capture_output=True, text=True, errors="replace")
        ok = r.returncode == 0
        print(("ok  " if ok else "FAIL"), script)
        if not ok:
            failed.append(script)
            print(r.stdout[-600:], r.stderr[-600:])
            continue
        for name in outs:
            src = os.path.join(HERE, "runs", name)
            if os.path.isfile(src):
                shutil.copy(src, os.path.join(DOCS, name))
                print("     copied", name)
    if failed:
        print("failed scripts:", ", ".join(failed))
        return 1
    print("all figures rebuilt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
