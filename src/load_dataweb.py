# ==============================================================================
# Script: load_dataweb.py
# Project: Grid Bottleneck - Transformer imports
# Objective: Turn a USITC DataWeb export (one sheet per measure, years as
#            columns) into one long table: year, country, hts, value, duties,
#            quantity, plus unit value and effective tariff rate.
# Adapted from load_and_merge in ~/Trade_research/01_data_cleanup.py.
# ==============================================================================

from pathlib import Path
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MEASURES = {
    "Customs Value": "customs_value_usd",
    "Calculated Duties": "calculated_duties_usd",
    "First Unit of Quantity": "quantity",
}


def read_measure(path: Path, sheet: str, value_name: str) -> pd.DataFrame:
    # Row 3 of each sheet holds the headers; the first two rows are metadata
    df = pd.read_excel(path, sheet_name=sheet, header=2)
    df.columns = [str(c).strip().removesuffix(".0") for c in df.columns]
    df = df[df["Country"].notna()]  # drops the "Total:" row

    # The quantity sheet adds "<year>_Suppressed" flag columns; keep them apart
    years = [c for c in df.columns if c.isdigit()]
    ids = [c for c in df.columns if c in ("Country", "HTS Number", "Description")]

    long = df.melt(id_vars=ids, value_vars=years, var_name="year", value_name=value_name)
    long[value_name] = pd.to_numeric(
        long[value_name].astype(str).str.replace(",", ""), errors="coerce"
    ).fillna(0)
    long["year"] = long["year"].astype(int)
    return long.rename(columns={"Country": "country", "HTS Number": "hts", "Description": "description"})


def load(path: Path) -> pd.DataFrame:
    keys = None
    merged = None
    for sheet, name in MEASURES.items():
        m = read_measure(path, sheet, name)
        if merged is None:
            merged = m
            keys = [c for c in ("year", "country", "hts") if c in m.columns]
        else:
            merged = merged.merge(m[keys + [name]], on=keys, how="outer")

    if "hts" in merged.columns:
        # Excel stores the codes as floats (8.50423e+09), so go through int first
        merged["hts"] = pd.to_numeric(merged["hts"]).astype("int64").astype(str).str.zfill(10)
        merged["hts6"] = merged["hts"].str[:6]
        ref = pd.read_csv(ROOT / "data/reference/hts_codes.csv", dtype=str)
        sizes = ref.drop_duplicates("hts6").set_index("hts6")["size_group"]
        merged["size_group"] = merged["hts6"].map(sizes)

    # Unit value and effective tariff are only defined when there was trade
    has_trade = merged["customs_value_usd"] > 0
    merged["unit_value_usd"] = (merged["customs_value_usd"] / merged["quantity"]).where(
        has_trade & (merged["quantity"] > 0)
    )
    merged["effective_tariff"] = (merged["calculated_duties_usd"] / merged["customs_value_usd"]).where(has_trade)
    return merged


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/raw/dataweb_hts10.xlsx"
    out = load(src)
    dest = ROOT / "data/clean/transformer_imports.csv"
    out.to_csv(dest, index=False)
    print(f"Wrote {len(out):,} rows to {dest.relative_to(ROOT)}")
    print(f"Has HTS breakout: {'hts' in out.columns}")
