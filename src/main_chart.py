# ==============================================================================
# Script: main_chart.py
# Project: Grid Bottleneck - The headline chart
# Objective: Hyperscaler capex vs US transformer prices vs imported large
#            transformer prices, all indexed to 2019 = 100, annual 2019 to 2025.
# Inputs:  SEC companyfacts (via capex.py), data/clean/price_index.csv (prices.py)
# Outputs: data/clean/main_index.csv, charts/main_chart.png
#
# Annual on purpose: capex is quarterly, the PPI monthly and imports annual.
# Putting all three on calendar years is simpler and doesn't invent precision.
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

from style import INK, INK_2, MUTED, GRID, CAPEX, PPI, LARGE_UNITS

import capex

ROOT = Path(__file__).resolve().parent.parent
BASE = 2019
YEARS = range(2019, 2026)


def hyperscaler_capex() -> pd.Series:
    """Calendar-year cash capex for Amazon, Microsoft, Alphabet and Meta combined."""
    q = pd.DataFrame({n: capex.quarterly(capex.company_facts(n, cik), tag, start="2018-01-01")
                      for n, (cik, tag) in capex.COMPANIES.items()})
    full = q.groupby(q.index.year).count().eq(4).all(axis=1)  # only years with all 16 quarters
    annual = q.groupby(q.index.year).sum().sum(axis=1)
    return annual[full].reindex(YEARS)


def build() -> pd.DataFrame:
    prices = pd.read_csv(ROOT / "data/clean/price_index.csv", index_col="year")
    cap = hyperscaler_capex()
    out = pd.DataFrame({
        "capex_usd": cap,
        "capex_index": 100 * cap / cap[BASE],
        "ppi_index": prices.PCU335311335311,
        "import_large_index": prices.import_large_fixed_mix,
    }).loc[list(YEARS)]
    return out


def chart(d: pd.DataFrame, dest: Path) -> None:
    lines = [
        ("capex_index", "Big Tech capex", CAPEX),
        ("ppi_index", "US transformer prices (PPI)", PPI),
        ("import_large_index", "Imported large transformers,\nprice per unit", LARGE_UNITS),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 5.6), dpi=150)
    for col, label, color in lines:
        y = d[col]
        ax.plot(y.index, y.values, color=color, linewidth=2.4, marker="o", markersize=4.5)
        extra = f"  (${d.capex_usd[BASE] / 1e9:.0f}B to ${d.capex_usd.iloc[-1] / 1e9:.0f}B)" if col == "capex_index" else ""
        ax.annotate(f"{label}\n{y.iloc[-1] / 100:.1f}x{extra}", (y.index[-1], y.iloc[-1]), xytext=(10, 0),
                    textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.axhline(100, color="#999999", linewidth=0.8, linestyle="--")
    ax.set_xticks(list(YEARS))
    ax.set_ylim(0, d.capex_index.max() * 1.1)
    ax.set_ylabel(f"Index, {BASE} = 100", color=INK_2)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.tick_params(colors=INK_2, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title("Big Tech's capex is up 5.4x since 2019. US transformer prices are up 1.8x.",
                 loc="left", fontsize=11, color=INK, pad=24)
    ax.text(0, 1.02, "Imported large transformers barely moved in price, while the number shipped quadrupled.",
            transform=ax.transAxes, fontsize=9, color=INK_2)
    fig.text(0.01, 0.01,
             "Sources: SEC XBRL (cash purchases of property and equipment, Amazon + Microsoft + Alphabet + Meta, calendar "
             "years; Amazon's 2020-21 jump is mostly warehouses);\nBLS PPI via FRED (PCU335311335311); USITC DataWeb, "
             "HTS 8504.23, price per unit holding the 2019 mix of 10-digit codes fixed.", fontsize=7, color=MUTED)
    fig.subplots_adjust(left=0.08, right=0.72, top=0.86, bottom=0.14)
    fig.savefig(dest)


if __name__ == "__main__":
    d = build()
    d.index.name = "year"
    d.round(3).to_csv(ROOT / "data/clean/main_index.csv")
    chart(d, ROOT / "charts/main_chart.png")
    print(d.assign(capex_usd=(d.capex_usd / 1e9).round(1)).round(1).to_string())
