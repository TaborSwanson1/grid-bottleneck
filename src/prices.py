# ==============================================================================
# Script: prices.py
# Project: Grid Bottleneck - Transformer prices
# Objective: Compare US producer prices for transformers (FRED PPI) with the
#            price per unit of imported transformers, all indexed to 2019 = 100.
# Inputs:  data/raw/fred_*.csv, data/clean/transformer_imports.csv
# Outputs: data/clean/price_index.csv, charts/price_index_2019.png
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
BASE = 2019
YEARS = range(2015, 2026)  # 2026 import data isn't a full year yet
FRED = {
    "WPU11740999": "US producer price (PPI)",
    "PCU335311335311": "US industry PPI",
}


def fred_annual(series: str) -> pd.Series:
    raw = pd.read_csv(ROOT / f"data/raw/fred_{series}.csv", parse_dates=["observation_date"])
    s = pd.to_numeric(raw.set_index("observation_date")[series], errors="coerce")
    # FRED has gaps for some months; report how many so the annual mean isn't trusted blindly
    by_year = s.groupby(s.index.year)
    missing = by_year.apply(lambda x: x.isna().sum())
    if missing.loc[list(YEARS)].any():
        print(f"{series} missing months:", missing.loc[list(YEARS)][lambda m: m > 0].to_dict())
    return by_year.mean().loc[list(YEARS)].rename(series)


def import_indexes(d: pd.DataFrame) -> pd.DataFrame:
    """Two import price measures per size group, 2019 = 100.

    raw: total value / total units. Moves when the mix of codes shifts.
    fixed_mix: each 10-digit code's price per unit, weighted by its 2019
    units. Holds the mix at 2019, so it shows price change alone.
    """
    g = d.groupby(["size_group", "hts", "year"])[["customs_value_usd", "quantity"]].sum()
    g["unit_value"] = g.customs_value_usd / g.quantity
    out = {}
    for size, s in g.groupby(level="size_group"):
        s = s.droplevel("size_group")
        tot = s.groupby(level="year")[["customs_value_usd", "quantity"]].sum()
        raw = tot.customs_value_usd / tot.quantity
        w = s.xs(BASE, level="year").quantity
        p = s.unit_value.unstack("year")
        fixed = p.mul(w, axis=0).sum() / (p[BASE] * w).sum()
        out[f"import_{size}_raw"] = 100 * raw / raw.loc[BASE]
        out[f"import_{size}_fixed_mix"] = 100 * fixed
    return pd.DataFrame(out)


def chart(idx: pd.DataFrame, dest: Path) -> None:
    # The industry PPI is complete; the commodity PPI is missing most of 2023-24
    lines = [
        ("PCU335311335311", "US producer price index", "#2a78d6"),
        ("import_small_fixed_mix", "Imported small units (≤650 kVA)", "#1baf7a"),
        ("import_large_fixed_mix", "Imported large units (>10,000 kVA)", "#eb6834"),
    ]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=150)
    for col, label, color in lines:
        y = idx[col]
        ax.plot(y.index, y.values, color=color, linewidth=2, marker="o", markersize=4)
        ax.annotate(f"{label}  {y.iloc[-1]:.0f}", (y.index[-1], y.iloc[-1]),
                    xytext=(8, 0), textcoords="offset points", va="center",
                    fontsize=9, color="#333333")
    ax.axhline(100, color="#999999", linewidth=0.8, linestyle="--")
    ax.set_xticks(list(YEARS))
    ax.set_ylabel(f"Index, {BASE} = 100", color="#555555")
    ppi_rise = idx["PCU335311335311"].iloc[-1] - 100
    ax.set_title(f"US transformer prices rose {ppi_rise:.0f}% since {BASE}. Imported large units barely moved.",
                 loc="left", fontsize=11, color="#111111")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.6)
    ax.tick_params(colors="#555555", labelsize=9)
    fig.text(0.01, 0.01, "Sources: BLS PPI via FRED (PCU335311335311); USITC DataWeb imports for consumption, "
             "HTS 8504.21 and 8504.23. Import prices hold the 2019 mix of 10-digit codes fixed.",
             fontsize=7, color="#777777")
    fig.subplots_adjust(right=0.72, bottom=0.12)
    fig.savefig(dest)


if __name__ == "__main__":
    fred = pd.concat([fred_annual(s) for s in FRED], axis=1)
    fred = 100 * fred / fred.loc[BASE]
    d = pd.read_csv(ROOT / "data/clean/transformer_imports.csv", dtype={"hts": str})
    d = d[d.year.isin(YEARS) & (d.quantity > 0)]
    idx = fred.join(import_indexes(d)).round(1)
    idx.index.name = "year"
    idx.to_csv(ROOT / "data/clean/price_index.csv")
    chart(idx, ROOT / "charts/price_index_2019.png")
    print(idx.to_string())
