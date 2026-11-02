# ==============================================================================
# Script: backlog.py
# Project: Grid Bottleneck - Signed leases waiting vs leases already running
# Objective: For each filing, compare future payments on leases signed but not
#            started (lease_notes.py) with future payments on leases already
#            running (the lease maturity table). Both are undiscounted totals,
#            so the ratio is like for like. A rising ratio means commitments
#            are piling up faster than buildings are being handed over.
# Inputs:  data/raw/sec/filings/*.txt (from lease_notes.py),
#          data/clean/leases_not_commenced.csv
# Outputs: data/clean/lease_backlog_ratio.csv, charts/lease_backlog_ratio.png
# ==============================================================================

from pathlib import Path
import glob
import re

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from style import INK, INK_2, BLUE, clean_axes, source_note

ROOT = Path(__file__).resolve().parent.parent
NUM = r"\d[\d,]*(?:\.\d+)?"


def nums(text: str) -> list[float]:
    return [float(x.replace(",", "")) for x in re.findall(NUM, text)]


def running_total(company: str, text: str) -> tuple[float, str] | None:
    """Undiscounted future payments on leases already running, in dollars, plus the matched text."""
    if company == "amazon":
        # Commitments table, in millions; the last number in each row is the total
        op = re.search(r"Operating lease liabilities ((?:[\d,]+ ){5,8})", text)
        fin = re.search(r"Finance lease liabilities, including interest ((?:[\d,]+ ){5,8})", text)
        if op and fin:
            return (nums(op.group(1))[-1] + nums(fin.group(1))[-1]) * 1e6, op.group(0)[:80]
        return None
    if company == "meta":
        # Only in the 10-K: "Total undiscounted cash flows <operating> <finance>"
        m = re.search(r"Total undiscounted cash flows ((?:[\d,]+ ){2})", text)
        return (sum(nums(m.group(1))) * 1e6, m.group(0)) if m else None
    if company == "alphabet":
        # 10-Qs state it in a sentence, in billions
        m = re.search(r"undiscounted future lease payments under operating and finance leases was \$\s?(" + NUM
                      + r") billion and \$\s?(" + NUM + r") billion", text)
        if m:
            return (float(m.group(1)) + float(m.group(2))) * 1e9, m.group(0)
    # Microsoft, Oracle, Alphabet 10-Ks, CoreWeave: maturity table total row
    m = re.search(r"Total (?:future |undiscounted )*lease payments ((?:\$?\s?[\d,]+ ){1,2})", text, re.I)
    if not m:
        return None
    vals = nums(m.group(1))
    unit = 1e3 if company == "coreweave" and max(vals) > 1e5 else 1e6  # CoreWeave's early 10-Qs are in thousands
    return sum(vals) * unit, m.group(0)


def build() -> pd.DataFrame:
    nc = pd.read_csv(ROOT / "data/clean/leases_not_commenced.csv")
    nc["key"] = nc.company.str.lower()
    rows = []
    for path in sorted(glob.glob(str(ROOT / "data/raw/sec/filings/*_*_10-*.txt"))):
        co, period, form = Path(path).stem.split("_")
        waiting = nc[(nc.key == co) & (nc.period == period)].not_commenced_usd
        if waiting.empty:
            continue
        hit = running_total(co, Path(path).read_text())
        if hit:
            rows.append({"company": co.capitalize() if co != "coreweave" else "CoreWeave", "period": period,
                         "form": form, "waiting_usd": waiting.iloc[0], "running_usd": hit[0], "matched": hit[1]})
    d = pd.DataFrame(rows)
    d["ratio"] = d.waiting_usd / d.running_usd
    return d


def chart(d: pd.DataFrame, dest: Path) -> None:
    order = ["Oracle", "Alphabet", "Microsoft", "Meta", "Amazon", "CoreWeave"]
    d = d.assign(period=pd.to_datetime(d.period))
    fig, axes = plt.subplots(2, 3, figsize=(11, 6), dpi=150, sharey=True, sharex=True)
    for ax, name in zip(axes.flat, order):
        s = d[d.company == name].set_index("period").ratio.sort_index()
        ax.axhline(1, color="#999999", linewidth=0.8, linestyle="--")
        if len(s):
            ax.plot(s.index, s.values, color=BLUE, linewidth=2, marker="o", markersize=3)
            ax.text(0.03, 0.93, f"Latest {s.iloc[-1]:.1f}x", transform=ax.transAxes, ha="left", va="top",
                    fontsize=9, color=INK)
        ax.set_title(name, loc="left", fontsize=10, color=INK)
        clean_axes(ax)
        ax.tick_params(labelbottom=True)
    axes[0, 0].xaxis.set_major_locator(mdates.YearLocator())
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for ax in axes[:, 0]:
        ax.set_ylabel("Signed and waiting ÷ running", color=INK_2, fontsize=8.5)
    fig.suptitle("Signed data center leases waiting to start now outweigh leases already running, by up to 4.6 to 1",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.885, "Future payments on leases signed but not started, divided by future payments on leases already "
             "running. Above the dashed line, more is waiting than running.\nRising at Alphabet, Meta, Amazon and Microsoft. Falling at Oracle and CoreWeave as buildings get handed over.", fontsize=8.5, color=INK_2)
    source_note(fig, "Source: lease notes and lease maturity tables in each 10-Q and 10-K. Both sides are undiscounted totals. "
                "Meta reports its table only in 10-Ks. Amazon's include warehouses and stores.")
    fig.subplots_adjust(left=0.07, right=0.98, top=0.81, bottom=0.08, hspace=0.35, wspace=0.12)
    fig.savefig(dest)


if __name__ == "__main__":
    d = build()
    d.drop(columns="matched").round(3).to_csv(ROOT / "data/clean/lease_backlog_ratio.csv", index=False)
    chart(d, ROOT / "charts/lease_backlog_ratio.png")
    show = d.pivot_table(index="period", columns="company", values="ratio").round(2)
    print(show.to_string())
