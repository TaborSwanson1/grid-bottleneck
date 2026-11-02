# ==============================================================================
# Script: where_and_who.py
# Project: Grid Bottleneck - Where power demand is growing, and who pays
# Objective: (1) Rank states by how much business electricity use grew,
#            2019 to 2025. (2) Show PJM's capacity price jump and how household
#            prices moved in PJM states vs the rest of the US.
# Inputs:  data/raw/eia_sales_revenue.xlsx (via electricity.py),
#          data/reference/pjm_capacity_prices.csv (from PJM auction reports)
# Outputs: data/clean/state_power_growth.csv, data/clean/household_prices.csv,
#          charts/where_power_demand_grew.png, charts/who_pays.png
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from style import INK, INK_2, BLUE, US_GRAY, clean_axes, source_note
from electricity import load_monthly

ROOT = Path(__file__).resolve().parent.parent
# States fully or mostly inside PJM (Illinois: the ComEd area in the north).
# How fast capacity costs reach household bills depends on each state's rules.
PJM_STATES = {"VA": "Virginia", "MD": "Maryland", "PA": "Pennsylvania", "NJ": "New Jersey",
              "OH": "Ohio", "DC": "Washington, DC", "IL": "Illinois", "DE": "Delaware"}
OTHER_HUBS = {"TX": "Texas", "GA": "Georgia", "AZ": "Arizona", "OR": "Oregon"}  # big data center states outside PJM
NAMES = {**PJM_STATES, **OTHER_HUBS, "ND": "North Dakota", "OK": "Oklahoma", "IA": "Iowa",
         "NE": "Nebraska", "NM": "New Mexico", "FL": "Florida"}


def state_growth(t: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    g = t[t.year.isin([2019, 2025])].groupby(["state", "year"]).ci_mwh.sum().unstack() / 1e6
    g["added_twh"] = g[2025] - g[2019]
    g["growth"] = g[2025] / g[2019] - 1
    return g.sort_values("added_twh", ascending=False).head(top)


def household_prices(t: pd.DataFrame) -> pd.DataFrame:
    """Average residential price, Jan to the latest 2026 month, in 2024 and 2026.

    2024 is the base because PJM's first big capacity price took effect in June 2025.
    """
    last = t[t.year == 2026].month.max()
    s = t[t.year.isin([2024, 2026]) & (t.month <= last)]
    s = pd.concat([s[s.state.isin(PJM_STATES | OTHER_HUBS)], s.assign(state="US")])
    g = s.groupby(["state", "year"])[["res_rev", "res_mwh"]].sum()
    p = (100 * g.res_rev / g.res_mwh).unstack()
    p["change"] = p[2026] / p[2024] - 1
    p["group"] = ["PJM" if st in PJM_STATES else "US" if st == "US" else "Other data center state" for st in p.index]
    p.attrs["months"] = f"Jan to {pd.Timestamp(2026, last, 1):%b}"
    return p


def chart_where(g: pd.DataFrame, dest: Path) -> None:
    g = g.iloc[::-1]
    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=150)
    ax.barh([NAMES.get(s, s) for s in g.index], g.added_twh, color=BLUE, height=0.62)
    for i, (_, r) in enumerate(g.iterrows()):
        ax.annotate(f"+{r.added_twh:.0f} TWh  (+{r.growth:.0%})", (r.added_twh, i), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, g.added_twh.max() * 1.3)
    ax.set_xlabel("Business electricity use added, 2019 to 2025 (TWh)", color=INK_2)
    clean_axes(ax, grid_axis="x", labelsize=9)
    ax.set_title("Texas and Virginia added the most business power demand since 2019",
                 loc="left", fontsize=11, color=INK, pad=30)
    ax.text(0, 1.02, "Data center hubs lead the list. Northern Virginia is the largest data center market, and Atlanta\n"
            "now has the most under construction (CBRE). Virginia is the only state where data centers use over 20% of power (EPRI).",
            transform=ax.transAxes, fontsize=8, color=INK_2)
    source_note(fig, "Source: EIA-861M, commercial + industrial retail sales. Not all growth is data centers: Texas and North Dakota\n"
                "also include crypto mining and oil field electrification. CBRE North America Data Center Trends H1 2026; EPRI Powering Intelligence update.")
    fig.subplots_adjust(left=0.16, right=0.97, top=0.82, bottom=0.17)
    fig.savefig(dest)


def chart_who(cap: pd.DataFrame, p: pd.DataFrame, dest: Path) -> None:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.5, 5.4), dpi=150, gridspec_kw={"width_ratios": [1, 1.1]})

    # Left: PJM capacity price by delivery year
    years = [y.replace("/20", "/") for y in cap.delivery_year]
    ax1.bar(years, cap.rto_price_usd_per_mw_day, color=BLUE, width=0.65)
    for i, r in cap.reset_index(drop=True).iterrows():
        label = f"${r.rto_price_usd_per_mw_day:.0f}" + ("\ncap" if r.at_cap else "")
        ax1.annotate(label, (i, r.rto_price_usd_per_mw_day), xytext=(0, 3), textcoords="offset points",
                     ha="center", fontsize=8, color=INK)
    ax1.set_ylim(0, cap.rto_price_usd_per_mw_day.max() * 1.25)
    ax1.set_ylabel("$ per MW-day", color=INK_2)
    ax1.set_title("PJM capacity price, by delivery year", loc="left", fontsize=10, color=INK)
    ax1.tick_params(axis="x", rotation=0)
    clean_axes(ax1, labelsize=8)

    # Right: household price change, PJM states vs other data center states vs US
    p = p.sort_values("change")
    colors = [BLUE if g == "PJM" else ("#4a4a4a" if g == "US" else US_GRAY) for g in p.group]
    names = [NAMES.get(s, s) if s != "US" else "US average" for s in p.index]
    ax2.barh(names, 100 * p.change, color=colors, height=0.62)
    for i, v in enumerate(p.change):
        ax2.annotate(f"+{v:.0%}", (100 * v, i), xytext=(5, 0), textcoords="offset points", va="center", fontsize=8.5, color=INK)
    ax2.set_xlim(0, 100 * p.change.max() * 1.2)
    ax2.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax2.set_title(f"Household electricity price, {p.attrs['months']} 2026 vs 2024", loc="left", fontsize=10, color=INK)
    clean_axes(ax2, grid_axis="x", labelsize=8.5)
    ax2.text(0.98, 0.04, "Blue = PJM states\nLight gray = data center states outside PJM",
             transform=ax2.transAxes, ha="right", fontsize=8, color=INK_2)

    fig.suptitle("PJM's capacity price rose more than 10x. Household bills in PJM states rose about twice as fast as the US.",
                 x=0.01, ha="left", fontsize=11, color=INK)
    source_note(fig, "Sources: PJM Base Residual Auction reports (RTO clearing price; 2026/27 onward cleared at the price cap); EIA-861M residential\n"
                "revenue / sales. Capacity is one part of the bill, and state rules shape how fast it passes through. PJM's market monitor\n"
                "attributes 38% of the 2028/29 auction's $16.4B cost to data center load.")
    fig.subplots_adjust(left=0.06, right=0.98, top=0.86, bottom=0.18, wspace=0.35)
    fig.savefig(dest)


if __name__ == "__main__":
    t = load_monthly()
    g = state_growth(t[t.year <= 2025])
    g.round(3).to_csv(ROOT / "data/clean/state_power_growth.csv")
    chart_where(g, ROOT / "charts/where_power_demand_grew.png")

    cap = pd.read_csv(ROOT / "data/reference/pjm_capacity_prices.csv")
    p = household_prices(t)
    p.round(4).to_csv(ROOT / "data/clean/household_prices.csv")
    chart_who(cap, p, ROOT / "charts/who_pays.png")
    print(g.round(2).to_string(), "\n")
    print(p.attrs["months"]); print(p.round(3).sort_values("change", ascending=False).to_string())
