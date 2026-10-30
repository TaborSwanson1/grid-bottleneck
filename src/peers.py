# ==============================================================================
# Script: peers.py
# Project: Grid Bottleneck - Hyperscalers vs Oracle and the neoclouds
# Objective: Compare cash capex and new lease assets over each company's last
#            twelve reported months, so companies with different fiscal years
#            line up.
# Inputs:  SEC companyfacts (via capex.company_facts)
# Outputs: data/clean/peers_ttm.csv, charts/peers_ttm.png
# Nebius is left out: it files as a foreign company and its XBRL stops at 2023.
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

import style  # noqa: F401  (turns off math parsing so "$" prints as written)
from capex import company_facts, LEASE_TAGS

ROOT = Path(__file__).resolve().parent.parent
CASH = "PaymentsToAcquirePropertyPlantAndEquipment"
PEERS = {
    # name: (cik, cash capex tag, group)
    "Amazon": ("0001018724", "PaymentsToAcquireProductiveAssets", "Hyperscaler"),
    "Microsoft": ("0000789019", CASH, "Hyperscaler"),
    "Alphabet": ("0001652044", CASH, "Hyperscaler"),
    "Meta": ("0001326801", CASH, "Hyperscaler"),
    "Oracle": ("0001341439", CASH, "Cloud challenger"),
    "CoreWeave": ("0001769628", CASH, "Neocloud"),
    "IREN": ("0001878848", CASH, "Neocloud"),
}

# IREN splits capex into "property, plant and equipment" and "computer hardware" (GPUs).
# Only the first is tagged in XBRL, so add the second from the 10-K cash flow statement.
EXTRA_CASH_CAPEX = {("IREN", "2026-06-30"): 1_335_081_000}  # FY2026 10-K, "Payments for computer hardware"


def facts_frame(facts: dict, tag: str) -> pd.DataFrame:
    r = pd.DataFrame(facts["facts"]["us-gaap"][tag]["units"]["USD"])
    r = r[r.form.str.match(r"10-[QK]")]
    r["start"] = pd.to_datetime(r.start)
    r["end"] = pd.to_datetime(r.end)
    r = r.sort_values("filed").drop_duplicates(["start", "end"], keep="last")
    r["days"] = (r.end - r.start).dt.days
    return r


def ttm_by_end(r: pd.DataFrame) -> pd.Series:
    """Twelve months ending on each report date we can build it for.

    A full-year row is its own TTM. Otherwise:
    TTM = this year-to-date + last full year - last year's same year-to-date.
    """
    out = {}
    for _, row in r[r.days.between(350, 380)].iterrows():
        out[row.end] = row.val
    for _, ytd in r[r.days.between(80, 290)].iterrows():
        if ytd.end in out:
            continue
        fy = r[r.days.between(350, 380) & ((ytd.start - r.end).dt.days.between(0, 3))]
        if fy.empty:
            continue
        fy = fy.iloc[-1]
        prior = r[((r.start - fy.start).dt.days.abs() <= 3)
                  & ((r.end - (ytd.end - pd.DateOffset(years=1))).dt.days.abs() <= 7)]
        if prior.empty:
            continue
        out[ytd.end] = ytd.val + fy.val - prior.iloc[-1].val
    return pd.Series(out).sort_index()


def peer_table() -> pd.DataFrame:
    rows = []
    for name, (cik, cash_tag, group) in PEERS.items():
        facts = company_facts(name, cik)
        series = {"cash_capex": ttm_by_end(facts_frame(facts, cash_tag))}
        for k, t in LEASE_TAGS.items():
            try:
                series[k] = ttm_by_end(facts_frame(facts, t))
            except KeyError:
                series[k] = pd.Series(dtype=float)
        # Latest date where cash capex and operating leases both have a TTM.
        # Finance leases are small for most; treat a missing one as zero, and say so.
        common = series["cash_capex"].index.intersection(series["operating_leases"].index)
        end = common.max()
        fin = series["finance_leases"]
        fin_val = fin.get(end)
        rows.append({
            "company": name, "group": group, "ttm_end": end.date(),
            "cash_capex": series["cash_capex"][end] + EXTRA_CASH_CAPEX.get((name, str(end.date())), 0),
            "finance_leases": 0.0 if fin_val is None else fin_val,
            "finance_missing": fin_val is None,
            "operating_leases": series["operating_leases"][end],
        })
    t = pd.DataFrame(rows)
    t["total"] = t[["cash_capex", "finance_leases", "operating_leases"]].sum(axis=1)
    t["lease_share"] = (t.finance_leases + t.operating_leases) / t.total
    return t


def chart(t: pd.DataFrame, dest: Path) -> None:
    t = t.sort_values("lease_share")
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    parts = [("cash_capex", "Cash capex", "#2a78d6"), ("finance_leases", "Finance leases", "#eb6834"),
             ("operating_leases", "Operating leases", "#1baf7a")]
    left = pd.Series(0.0, index=t.index)
    for col, label, color in parts:
        share = 100 * t[col] / t.total
        ax.barh(t.company, share, left=left, color=color, height=0.62, edgecolor="white",
                linewidth=1.2, label=label)
        left += share
    for i, (_, r) in enumerate(t.iterrows()):
        note = "*" if r.finance_missing else ""
        ax.annotate(f"{r.lease_share:.0%} leased{note}   ${r.total / 1e9:.0f}B total, 12 mo. to {r.ttm_end:%b %Y}",
                    (100, i), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color="#111111")
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.tick_params(colors="#555555", labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="lower left", bbox_to_anchor=(0, 1.0))
    ax.set_title("CoreWeave and Oracle lease far more of what they add than the big four",
                 loc="left", fontsize=11, color="#111111", pad=26)
    fig.text(0.01, 0.01, "Source: SEC XBRL company facts. Share of new spending: cash purchases of property and "
             "equipment vs right-of-use assets\nfrom new leases, last 12 reported months. "
             "* Finance leases not reported for that period. Nebius left out (no recent XBRL data).",
             fontsize=6.5, color="#777777")
    fig.subplots_adjust(left=0.13, right=0.62, top=0.84, bottom=0.14)
    fig.savefig(dest)


if __name__ == "__main__":
    t = peer_table()
    t.to_csv(ROOT / "data/clean/peers_ttm.csv", index=False)
    chart(t, ROOT / "charts/peers_ttm.png")
    show = t.set_index("company")
    print((show[["cash_capex", "finance_leases", "operating_leases", "total"]] / 1e9).round(1)
          .join(show[["ttm_end", "lease_share", "finance_missing"]]).to_string())
