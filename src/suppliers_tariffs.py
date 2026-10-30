# ==============================================================================
# Script: suppliers_tariffs.py
# Project: Grid Bottleneck - Who supplies large transformers, and what they pay
# Objective: Supplier shares for large units (HTS 8504.23) over time, and the
#            effective tariff rate (calculated duties / customs value) by size
#            and by supplier.
# Inputs:  data/clean/transformer_imports.csv
# Outputs: data/clean/large_supplier_share.csv, data/clean/effective_tariff.csv,
#          charts/large_supplier_share.png, charts/effective_tariff_by_size.png,
#          charts/effective_tariff_large_2025.png
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from style import INK, INK_2, MUTED, GRID

ROOT = Path(__file__).resolve().parent.parent
YEARS = range(2015, 2026)

EUROPE = {
    "Austria", "Netherlands", "Germany", "Croatia", "Spain", "Poland", "Italy",
    "Sweden", "Portugal", "Finland", "France", "Belgium", "Czech Republic",
    "Hungary", "Romania", "Slovenia", "Slovakia", "Switzerland", "United Kingdom",
    "Denmark", "Norway", "Ireland", "Greece", "Bulgaria", "Serbia",
}
# Fixed order and colors; color follows the group, not its rank
GROUPS = [
    ("Mexico", "#2a78d6"),
    ("South Korea", "#eb6834"),
    ("Europe", "#1baf7a"),
    ("Brazil", "#eda100"),
    ("China", "#e87ba4"),
    ("Other", "#a3a3a3"),
]
# Same entity colors as charts/price_index_2019.png
SIZES = [("small", "Small (≤650 kVA)", "#1baf7a"),
         ("medium", "Medium (650 to 10,000 kVA)", "#2a78d6"),
         ("large", "Large (>10,000 kVA)", "#eb6834")]


def group_of(country: str) -> str:
    if country in ("Mexico", "South Korea", "Brazil", "China"):
        return country
    return "Europe" if country in EUROPE else "Other"


def style(ax, ylabel: str) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.set_ylabel(ylabel, color=INK_2)


def source(fig, text: str) -> None:
    fig.text(0.01, 0.01, text, fontsize=7, color=MUTED)


def supplier_share(d: pd.DataFrame) -> pd.DataFrame:
    large = d[d.size_group == "large"].assign(group=lambda x: x.country.map(group_of))
    v = large.pivot_table(index="year", columns="group", values="customs_value_usd", aggfunc="sum")
    return (100 * v.div(v.sum(axis=1), axis=0))[[g for g, _ in GROUPS]]


def chart_share(share: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=150)
    bottom = pd.Series(0.0, index=share.index)
    for g, color in GROUPS:
        ax.bar(share.index, share[g], bottom=bottom, color=color, width=0.72,
               edgecolor="white", linewidth=1.5)
        last = share.index[-1]
        ax.annotate(f"{g}  {share.loc[last, g]:.0f}%", (last + 0.45, bottom[last] + share.loc[last, g] / 2),
                    va="center", fontsize=9, color=INK)
        bottom += share[g]
    ax.set_xticks(list(share.index))
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    style(ax, "Share of import value")
    ax.set_title("China supplies about 2% of large US transformer imports. Mexico, Korea and Europe supply most.",
                 loc="left", fontsize=10.5, color=INK)
    ax.text(0, -0.2, "EO 14421 (signed August 26, 2026) lets DOE block grid equipment tied to countries under US\n"
            "arms embargoes, including China. This data ends in 2025.", transform=ax.transAxes, fontsize=8, color=INK_2)
    source(fig, "Source: USITC DataWeb, imports for consumption, HTS 8504.23 (liquid-dielectric transformers "
           "over 10,000 kVA), share of customs value.")
    fig.subplots_adjust(right=0.8, bottom=0.22)
    fig.savefig(dest)


def effective_tariff(d: pd.DataFrame) -> pd.DataFrame:
    t = d.groupby(["size_group", "year"])[["calculated_duties_usd", "customs_value_usd"]].sum()
    return (100 * t.calculated_duties_usd / t.customs_value_usd).unstack("size_group")


def chart_tariff_by_size(rate: pd.DataFrame, dest: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    for size, label, color in SIZES:
        y = rate[size]
        ax.plot(y.index, y.values, color=color, linewidth=2, marker="o", markersize=4)
        ax.annotate(f"{label}  {y.iloc[-1]:.1f}%", (y.index[-1], y.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.set_xticks(list(rate.index))
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    style(ax, "Duties paid / import value")
    ax.set_title("Tariffs on imported transformers stayed near zero until 2025, then jumped.",
                 loc="left", fontsize=11, color=INK)
    source(fig, "Source: USITC DataWeb, imports for consumption, HTS 8504.21 to 8504.23. "
           "Effective rate = calculated duties / customs value.")
    fig.subplots_adjust(right=0.72, bottom=0.12)
    fig.savefig(dest)


def chart_tariff_large_2025(d: pd.DataFrame, dest: Path, top: int = 10) -> pd.DataFrame:
    large = d[(d.size_group == "large") & (d.year == 2025)]
    by = large.groupby("country")[["calculated_duties_usd", "customs_value_usd"]].sum()
    by["share"] = 100 * by.customs_value_usd / by.customs_value_usd.sum()
    by["rate"] = 100 * by.calculated_duties_usd / by.customs_value_usd
    by = by.nlargest(top, "customs_value_usd")
    # China is small by value; add it so the chart shows what it pays
    if "China" not in by.index:
        china = large[large.country == "China"][["calculated_duties_usd", "customs_value_usd"]].sum()
        by.loc["China"] = [*china, 100 * china.customs_value_usd / large.customs_value_usd.sum(),
                           100 * china.calculated_duties_usd / china.customs_value_usd]
    by = by.iloc[::-1]  # biggest supplier on top

    fig, ax = plt.subplots(figsize=(9, 5.4), dpi=150)
    ax.barh(by.index, by.rate, color="#eb6834", height=0.62)
    for i, (country, row) in enumerate(by.iterrows()):
        ax.annotate(f"{row.rate:.1f}%   ({row.share:.0f}% of imports)", (row.rate, i), xytext=(6, 0),
                    textcoords="offset points", va="center", fontsize=8.5, color=INK)
    ax.set_xlim(0, by.rate.max() * 1.35)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    style(ax, "")
    ax.set_xlabel("Effective tariff rate, 2025", color=INK_2)
    ax.set_title("What large-transformer suppliers paid in 2025, biggest suppliers first",
                 loc="left", fontsize=11, color=INK)
    source(fig, "Source: USITC DataWeb, HTS 8504.23, 2025. Effective rate = calculated duties / customs value. "
           "Base duty is 1.6% or free under trade deals.")
    fig.subplots_adjust(left=0.15, bottom=0.14)
    fig.savefig(dest)
    return by


if __name__ == "__main__":
    d = pd.read_csv(ROOT / "data/clean/transformer_imports.csv", dtype={"hts": str})
    d = d[d.year.isin(YEARS)]

    share = supplier_share(d)
    share.round(1).to_csv(ROOT / "data/clean/large_supplier_share.csv")
    chart_share(share, ROOT / "charts/large_supplier_share.png")

    rate = effective_tariff(d)
    rate.round(2).to_csv(ROOT / "data/clean/effective_tariff.csv")
    chart_tariff_by_size(rate, ROOT / "charts/effective_tariff_by_size.png")
    by = chart_tariff_large_2025(d, ROOT / "charts/effective_tariff_large_2025.png")

    print(share.round(1).to_string(), "\n")
    print(rate.round(2).to_string(), "\n")
    print(by[["share", "rate"]].iloc[::-1].round(1).to_string())
