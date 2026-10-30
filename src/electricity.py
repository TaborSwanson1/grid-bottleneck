# ==============================================================================
# Script: electricity.py
# Project: Grid Bottleneck - Electricity demand and prices near data center hubs
# Objective: Retail electricity sales and average prices for Virginia, Texas,
#            Arizona and Oregon vs the US, 2015 to 2025, plus 2026 so far.
# Inputs:  data/raw/eia_sales_revenue.xlsx (EIA-861M monthly sales and revenue
#          by state and sector; 2026 months are preliminary)
# Outputs: data/clean/electricity_annual.csv, data/clean/electricity_2026_ytd.csv,
#          charts/electricity_demand_prices.png
#
# Uses commercial + industrial combined. Data centers are billed as commercial
# in some places and industrial in others, and Oregon moved a big block of load
# from industrial to commercial in 2023. Adding the two cancels that out.
# Prices are nominal (not adjusted for inflation).
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from style import INK, INK_2, MUTED, GRID

ROOT = Path(__file__).resolve().parent.parent
STATES = {"VA": "Virginia", "TX": "Texas", "AZ": "Arizona", "OR": "Oregon"}
YEARS = range(2015, 2026)
BASE = 2019
SECTORS = ["res", "com", "ind", "trn", "tot"]


def load_monthly() -> pd.DataFrame:
    t = pd.read_excel(ROOT / "data/raw/eia_sales_revenue.xlsx", "Monthly-States", header=None, skiprows=3).iloc[:, :24]
    t.columns = ["year", "month", "state", "status"] + [f"{s}_{m}" for s in SECTORS for m in ("rev", "mwh", "cust", "price")]
    t = t[pd.to_numeric(t.year, errors="coerce").notna()].copy()  # drops the footnote rows
    for c in t.columns[4:]:
        t[c] = pd.to_numeric(t[c], errors="coerce")
    t[["year", "month"]] = t[["year", "month"]].astype(int)
    t["ci_mwh"] = t.com_mwh + t.ind_mwh
    t["ci_rev"] = t.com_rev + t.ind_rev  # thousand dollars
    return t


def summarize(t: pd.DataFrame) -> pd.DataFrame:
    """Sales (TWh) and average price (cents/kWh) for each state and the US."""
    def agg(g):
        return pd.Series({"ci_twh": g.ci_mwh.sum() / 1e6, "ci_price": 100 * g.ci_rev.sum() / g.ci_mwh.sum(),
                          "com_twh": g.com_mwh.sum() / 1e6})
    states = t[t.state.isin(STATES)].groupby(["state", "year"]).apply(agg).reset_index()
    us = t.groupby("year").apply(agg).reset_index().assign(state="US")
    return pd.concat([states, us])


def chart(a: pd.DataFrame, dest: Path) -> None:
    fig, axes = plt.subplots(2, 4, figsize=(11, 6.4), dpi=150, sharey="row")
    us = a[a.state == "US"].set_index("year")
    us_idx = 100 * us.ci_twh / us.ci_twh[BASE]
    for col, (st, name) in enumerate(STATES.items()):
        s = a[a.state == st].set_index("year")
        idx = 100 * s.ci_twh / s.ci_twh[BASE]
        for row, (y, y_us, fmt) in enumerate([(idx, us_idx, "{:.0f}"), (s.ci_price, us.ci_price, "{:.1f}¢")]):
            ax = axes[row, col]
            ax.plot(y_us.index, y_us.values, color="#999999", linewidth=1.6, linestyle="--")
            ax.plot(y.index, y.values, color="#2a78d6", linewidth=2.2, marker="o", markersize=3)
            ax.annotate(fmt.format(y.iloc[-1]), (y.index[-1], y.iloc[-1]), xytext=(0, 7), textcoords="offset points",
                        ha="center", fontsize=8.5, color=INK)
            if col == 0:
                ax.annotate("US", (y_us.index[-1], y_us.iloc[-1]), xytext=(0, -12), textcoords="offset points",
                            ha="center", fontsize=8, color=INK_2)
            ax.set_xticks([2015, 2020, 2025])
            ax.grid(axis="y", color=GRID, linewidth=0.6)
            ax.tick_params(colors=INK_2, labelsize=8)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            if row == 0:
                ax.set_title(name, loc="left", fontsize=10.5, color=INK)
    axes[0, 0].set_ylabel(f"Sales, {BASE} = 100", color=INK_2, fontsize=9)
    axes[1, 0].set_ylabel("Average price, cents/kWh", color=INK_2, fontsize=9)
    fig.suptitle("Power use grew 4 to 5 times faster than the US in Virginia, Texas and Oregon. Prices tracked the US through 2025.",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.915, "Commercial + industrial retail electricity, blue = state, dashed gray = US. "
             "Top: sales indexed to 2019. Bottom: average price (nominal).", fontsize=8.5, color=INK_2)
    fig.text(0.01, 0.01, "Source: EIA-861M monthly sales and revenue by state. Commercial and industrial combined "
             "because utilities classify data centers differently.", fontsize=7, color=MUTED)
    fig.subplots_adjust(left=0.07, right=0.98, top=0.83, bottom=0.08, hspace=0.3, wspace=0.12)
    fig.savefig(dest)


def ytd_2026(t: pd.DataFrame) -> pd.DataFrame:
    """2026 so far vs the same months of 2025. 2026 data is preliminary."""
    last = t[t.year == 2026].month.max()
    sub = t[t.year.isin([2025, 2026]) & (t.month <= last)]
    sub = pd.concat([sub[sub.state.isin(STATES)], sub.assign(state="US")])
    g = sub.groupby(["state", "year"])[["ci_mwh", "ci_rev"]].sum().unstack("year")
    out = pd.DataFrame({
        "sales_growth": g.ci_mwh[2026] / g.ci_mwh[2025] - 1,
        "price_2025": 100 * g.ci_rev[2025] / g.ci_mwh[2025],
        "price_2026": 100 * g.ci_rev[2026] / g.ci_mwh[2026],
    })
    out["price_growth"] = out.price_2026 / out.price_2025 - 1
    out.attrs["months"] = f"Jan to {pd.Timestamp(2026, last, 1):%b}"
    return out


if __name__ == "__main__":
    t = load_monthly()
    full = t[t.year.isin(YEARS)]
    a = summarize(full)
    a.round(3).to_csv(ROOT / "data/clean/electricity_annual.csv", index=False)
    chart(a, ROOT / "charts/electricity_demand_prices.png")
    y = ytd_2026(t)
    y.round(4).to_csv(ROOT / "data/clean/electricity_2026_ytd.csv")

    p = a.pivot_table(index="state", columns="year", values=["ci_twh", "ci_price", "com_twh"])
    show = pd.DataFrame({
        "ci_sales_change_2019_25": p.ci_twh[2025] / p.ci_twh[BASE] - 1,
        "com_sales_change_2019_25": p.com_twh[2025] / p.com_twh[BASE] - 1,
        "price_2019": p.ci_price[BASE], "price_2025": p.ci_price[2025],
        "price_change": p.ci_price[2025] / p.ci_price[BASE] - 1,
    })
    print(show.round(3).to_string(), "\n")
    print(y.attrs["months"], "2026 vs 2025:")
    print(y.round(3).to_string())
