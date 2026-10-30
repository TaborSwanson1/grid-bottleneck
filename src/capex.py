# ==============================================================================
# Script: capex.py
# Project: Grid Bottleneck - Hyperscaler capital spending
# Objective: Quarterly capex for Amazon, Microsoft, Alphabet and Meta from SEC
#            XBRL company facts, 2022 to now.
# Inputs:  SEC companyfacts API (cached to data/raw/sec/<company>.json)
#          SEC_USER_AGENT in .env, e.g. "Your Name you@example.com"; the SEC
#          blocks requests that don't include contact info
# Outputs: data/clean/capex_quarterly.csv, charts/capex_quarterly.png
# ==============================================================================

from pathlib import Path
import json
import os
import ssl
import urllib.request
import certifi
import pandas as pd
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from style import INK, INK_2, BLUE, clean_axes, source_note

ROOT = Path(__file__).resolve().parent.parent
START = "2022-01-01"
# Cash flow line "purchases of property and equipment". Amazon tags it differently.
COMPANIES = {
    "Amazon": ("0001018724", "PaymentsToAcquireProductiveAssets"),
    "Microsoft": ("0000789019", "PaymentsToAcquirePropertyPlantAndEquipment"),
    "Alphabet": ("0001652044", "PaymentsToAcquirePropertyPlantAndEquipment"),
    "Meta": ("0001326801", "PaymentsToAcquirePropertyPlantAndEquipment"),
}


def user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT")
    env = ROOT / ".env"
    if not ua and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("SEC_USER_AGENT="):
                ua = line.split("=", 1)[1].strip().strip('"')
    if not ua:
        raise SystemExit("Set SEC_USER_AGENT in .env (name and email) before pulling SEC data.")
    return ua


def company_facts(name: str, cik: str) -> dict:
    cache = ROOT / f"data/raw/sec/{name.lower()}.json"
    if not cache.exists():
        req = urllib.request.Request(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            headers={"User-Agent": user_agent()},
        )
        ctx = ssl.create_default_context(cafile=certifi.where())
        cache.write_bytes(urllib.request.urlopen(req, context=ctx).read())
    return json.loads(cache.read_text())


def quarterly(facts: dict, tag: str, start: str = START) -> pd.Series:
    """Quarterly values from a mix of 3-month, year-to-date and full-year facts.

    10-Q cash flow statements are year-to-date: the Q2 filing reports six
    months. A quarter is the YTD value minus the prior YTD value with the same
    start date. Q4 comes from the 10-K's full year minus nine months.
    """
    rows = pd.DataFrame(facts["facts"]["us-gaap"][tag]["units"]["USD"])
    rows = rows[rows.form.isin(["10-Q", "10-K", "10-Q/A", "10-K/A"])]
    rows["start"] = pd.to_datetime(rows.start)
    rows["end"] = pd.to_datetime(rows.end)
    # The same period shows up in later filings too; keep the latest filed value
    rows = rows.sort_values("filed").drop_duplicates(["start", "end"], keep="last")
    rows["days"] = (rows.end - rows.start).dt.days

    out = {}
    for _, r in rows[rows.days.between(80, 100)].iterrows():
        out[r.end] = r.val
    for fy_start, grp in rows[rows.days > 100].groupby("start"):
        grp = grp.sort_values("end")
        prev = rows[(rows.start == fy_start) & rows.days.between(80, 100)]
        prev_end, prev_val = (prev.end.iloc[0], prev.val.iloc[0]) if len(prev) else (None, None)
        for _, r in grp.iterrows():
            # Only difference adjacent periods; a skipped quarter would make a 6-month "quarter"
            adjacent = prev_end is not None and 80 <= (r.end - prev_end).days <= 100
            if adjacent and r.end not in out:
                out[r.end] = r.val - prev_val
            prev_end, prev_val = r.end, r.val
    s = pd.Series(out).sort_index()
    return s[s.index >= start]


def chart(q: pd.DataFrame, dest: Path) -> None:
    """One panel per company on a shared scale. Four colored lines fail the colorblind check."""
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.4), dpi=150, sharey=True)
    for ax, name in zip(axes, COMPANIES):
        y = q[name] / 1e9
        ax.plot(y.index, y.values, color=BLUE, linewidth=2, marker="o", markersize=3)
        ax.annotate(f"${y.iloc[-1]:.0f}B", (y.index[-1], y.iloc[-1]), xytext=(-4, 6),
                    textcoords="offset points", ha="right", fontsize=9, color=INK)
        ax.set_title(name, loc="left", fontsize=10, color=INK)
        ax.set_xticks(pd.to_datetime(["2022-06-30", "2024-06-30", "2026-06-30"]))
        ax.xaxis.set_major_formatter(lambda v, _: f"{mdates.num2date(v).year}")
        clean_axes(ax)
    axes[0].set_ylim(bottom=0)
    axes[0].yaxis.set_major_formatter(lambda v, _: f"${v:.0f}B")
    total, first = q.iloc[-1].sum() / 1e9, q.iloc[0].sum() / 1e9
    fig.suptitle(f"The four biggest cloud companies spent ${total:.0f}B on capex last quarter, vs ${first:.0f}B in early 2022",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.9, "Quarterly cash purchases of property and equipment, same scale in every panel.",
             fontsize=8.5, color=INK_2)
    source_note(fig, "Source: SEC XBRL company facts, cash flow statements. Quarters derived from year-to-date "
                "filings. Excludes leases. Amazon's figure is gross of equipment-sale proceeds.")
    fig.subplots_adjust(left=0.06, right=0.99, top=0.8, bottom=0.12, wspace=0.12)
    fig.savefig(dest)


# New lease assets, from the cash flow statement's supplemental disclosures.
# Booked when a lease starts (the building is handed over), not while it's
# being built, so these lag. Amazon's include warehouses and stores.
LEASE_TAGS = {
    "finance_leases": "RightOfUseAssetObtainedInExchangeForFinanceLeaseLiability",
    "operating_leases": "RightOfUseAssetObtainedInExchangeForOperatingLeaseLiability",
}
FULL_YEARS = range(2022, 2026)


def calendar_year(facts: dict, tag: str) -> pd.Series:
    """Calendar-year totals: four quarters if we have them, else the 10-K's Jan to Dec value.

    Meta only reports lease additions in its 10-K for recent years, so the
    quarterly route comes up empty there.
    """
    q = quarterly(facts, tag)
    by_year = q.groupby(q.index.year).agg(["sum", "count"])
    out = by_year.loc[by_year["count"] == 4, "sum"]
    rows = pd.DataFrame(facts["facts"]["us-gaap"][tag]["units"]["USD"])
    fy = rows[rows.form.str.startswith("10-K") & rows.start.str.endswith("-01-01") & rows.end.str.endswith("-12-31")]
    fy = fy.sort_values("filed").drop_duplicates("end", keep="last")
    for _, r in fy.iterrows():
        out.loc[int(r.end[:4])] = out.get(int(r.end[:4]), r.val)
    return out.reindex(FULL_YEARS)


def annual_with_leases() -> pd.DataFrame:
    rows = []
    for name, (cik, tag) in COMPANIES.items():
        facts = company_facts(name, cik)
        cols = {"cash_capex": calendar_year(facts, tag)}
        cols |= {k: calendar_year(facts, t) for k, t in LEASE_TAGS.items()}
        rows.append(pd.DataFrame(cols).assign(company=name))
    a = pd.concat(rows).rename_axis("year").reset_index()
    a["lease_share"] = (a.finance_leases + a.operating_leases) / a[["cash_capex", *LEASE_TAGS]].sum(axis=1)
    return a


def chart_leases(a: pd.DataFrame, dest: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.6), dpi=150, sharey=True)
    parts = [("cash_capex", "Cash capex", "#2a78d6"), ("finance_leases", "Finance leases", "#eb6834"),
             ("operating_leases", "Operating leases", "#1baf7a")]
    for ax, name in zip(axes, COMPANIES):
        c = a[a.company == name].set_index("year")
        bottom = pd.Series(0.0, index=c.index)
        for col, label, color in parts:
            v = c[col].fillna(0) / 1e9
            ax.bar(c.index, v, bottom=bottom, color=color, width=0.7, edgecolor="white", linewidth=1.2, label=label)
            bottom += v
        for yr, share in c.lease_share.items():
            ax.annotate(f"{share:.0%}", (yr, bottom[yr]), xytext=(0, 3), textcoords="offset points",
                        ha="center", fontsize=8, color="#555555")
        ax.set_title(name, fontsize=10, color="#111111", loc="left")
        ax.set_xticks(list(c.index))
        ax.tick_params(colors="#555555", labelsize=8)
        ax.grid(axis="y", color="#e6e6e6", linewidth=0.6)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].yaxis.set_major_formatter(lambda v, _: f"${v:.0f}B")
    axes[0].legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle("Leases are a big slice of new spending at Microsoft, a small one at Alphabet and Meta. "
                 "Label = lease share.", x=0.01, ha="left", fontsize=10.5, color="#111111")
    fig.text(0.01, 0.01, "Source: SEC XBRL company facts. Leases = right-of-use assets obtained for new lease "
             "liabilities, booked when a lease starts. Amazon's include warehouses and stores.",
             fontsize=7, color="#777777")
    fig.subplots_adjust(left=0.06, right=0.99, top=0.84, bottom=0.12, wspace=0.12)
    fig.savefig(dest)


if __name__ == "__main__":
    q = pd.DataFrame({name: quarterly(company_facts(name, cik), tag) for name, (cik, tag) in COMPANIES.items()})
    q.index.name = "quarter_end"
    q.to_csv(ROOT / "data/clean/capex_quarterly.csv")
    chart(q.dropna(), ROOT / "charts/capex_quarterly.png")
    print((q / 1e9).round(2).to_string(), "\n")

    a = annual_with_leases()
    a.to_csv(ROOT / "data/clean/capex_and_leases_annual.csv", index=False)
    chart_leases(a, ROOT / "charts/capex_and_leases_annual.png")
    show = a.set_index(["company", "year"])
    print((show[["cash_capex", *LEASE_TAGS]] / 1e9).round(1).join(show.lease_share.round(3)).to_string())
