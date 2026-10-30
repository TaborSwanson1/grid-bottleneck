# ==============================================================================
# Script: check_capex.py
# Project: Grid Bottleneck - Check SEC XBRL capex against the filings themselves
# Objective: For each cached 10-Q and 10-K, find the capex line in the cash flow
#            statement and confirm the XBRL year-to-date value appears in it.
# Inputs:  data/raw/sec/<company>.json, data/raw/sec/filings/*.txt
#          (run lease_notes.py first to download the filings)
# Outputs: data/clean/capex_check.csv
# ==============================================================================

from pathlib import Path
import glob
import json
import re

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
# company: (cash flow label, XBRL tag, unit the statement uses)
LINES = {
    "amazon": (r"Purchases of property and equipment", "PaymentsToAcquireProductiveAssets", 1e6),
    "microsoft": (r"Additions to property and equipment", "PaymentsToAcquirePropertyPlantAndEquipment", 1e6),
    "alphabet": (r"Purchases of property and equipment", "PaymentsToAcquirePropertyPlantAndEquipment", 1e6),
    "meta": (r"Purchases of property and equipment", "PaymentsToAcquirePropertyPlantAndEquipment", 1e6),
    "oracle": (r"Capital expenditures", "PaymentsToAcquirePropertyPlantAndEquipment", 1e6),
    "coreweave": (r"Purchase of property and equipment", "PaymentsToAcquirePropertyPlantAndEquipment", 1e6),
    "iren": (r"Payments for property, plant and equipment", "PaymentsToAcquirePropertyPlantAndEquipment", 1e3),
}


def ytd_value(facts: pd.DataFrame, period: str, form: str) -> float | None:
    """The filing's own year-to-date (10-Q) or full-year (10-K) value. Skips Amazon's trailing 12 months."""
    f = facts[(facts.end == period) & (facts.form == form)].copy()
    f["days"] = (pd.to_datetime(f.end) - pd.to_datetime(f.start)).dt.days
    f = f[f.days.between(350, 380)] if form == "10-K" else f[f.days < 300]
    return None if f.empty else f.sort_values("days").iloc[-1].val


def row_numbers(text: str, label: str) -> list[int]:
    nums = []
    for m in re.finditer(label, text, re.I):
        window = re.sub(r"^[^$(\d]{0,80}", "", text[m.end(): m.end() + 200])  # skip trailing words in the label
        window = re.split(r"[A-Za-z]{4,}", window, maxsplit=1)[0]  # stop at the next line's label
        nums += [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]{2,}", window)]
    return nums


if __name__ == "__main__":
    rows = []
    for co, (label, tag, unit) in LINES.items():
        facts = pd.DataFrame(json.load(open(ROOT / f"data/raw/sec/{co}.json"))["facts"]["us-gaap"][tag]["units"]["USD"])
        for path in sorted(glob.glob(str(ROOT / f"data/raw/sec/filings/{co}_*.txt"))):
            _, period, form = Path(path).stem.split("_")
            xbrl = ytd_value(facts, period, form)
            nums = row_numbers(Path(path).read_text(), label)
            # CoreWeave switched from thousands to millions after its first three 10-Qs
            found = xbrl is not None and any(abs(n * u - xbrl) <= max(u, 0.001 * xbrl) for n in nums for u in (unit, 1e3))
            rows.append({"company": co, "period": period, "form": form,
                         "xbrl_usd_m": None if xbrl is None else round(xbrl / 1e6),
                         "in_filing": found, "row_numbers": nums[:6]})
    r = pd.DataFrame(rows)
    r.to_csv(ROOT / "data/clean/capex_check.csv", index=False)
    print(r.groupby("company").in_filing.agg(["sum", "count"]).to_string())
    bad = r[~r.in_filing]
    # Meta's three early-2023 10-Qs: the XBRL value is Meta's later revision, off by under 1%
    print("\nNot matched:" if len(bad) else "\nAll matched.")
    if len(bad):
        print(bad.to_string(index=False))
