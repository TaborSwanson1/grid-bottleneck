# ==============================================================================
# Script: run_all.py
# Project: Grid Bottleneck - Rebuild every table and chart in order
# Usage:   cd src && ../.venv/bin/python run_all.py
# Needs:   data/raw/dataweb_hts10.xlsx (exported by hand, see README) and
#          SEC_USER_AGENT in .env. Everything else downloads or is in data/raw.
# ==============================================================================

from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
# Order matters: prices.py reads load_dataweb's output, main_chart reads prices'.
STEPS = [
    "load_dataweb.py",
    "prices.py",
    "suppliers_tariffs.py",
    "capex.py",
    "peers.py",
    "lease_notes.py",
    "check_capex.py",
    "queues.py",
    "electricity.py",
    "main_chart.py",
]

if __name__ == "__main__":
    for step in STEPS:
        print(f"\n=== {step}")
        result = subprocess.run([sys.executable, "-W", "ignore", step], cwd=HERE)
        if result.returncode != 0:
            sys.exit(f"{step} failed; stopping.")
    print("\nAll steps finished.")
