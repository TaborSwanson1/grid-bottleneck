# The Grid Bottleneck: AI Demand vs the Transformer Shortage

AI companies are spending record amounts on data centers, but some of that hardware can't be switched on. This project asks how much of the holdup is a transformer problem, and whether trade policy is making it worse.

Status: in progress. Day 1 of 14.

## Product codes

US imports of liquid-dielectric transformers fall under three six-digit HTS codes, split by power handling capacity. Each one breaks into ten-digit statistical codes. Every code reports quantity in units ("No.") and weight (kg).

| Code | Size | Ten-digit codes | General duty |
|---|---|---|---|
| 8504.21 | Up to 650 kVA | .0020 (to 50), .0040 (50 to 100), .0060 (100 to 500), .0080 (500 to 650) | Free |
| 8504.22 | 650 to 10,000 kVA | .0040 (650 to 2,500), .0080 (2,500 to 10,000) | Free |
| 8504.23 | Over 10,000 kVA | .0041 (10,000 to 59,999), .0045 (59,999 to 100,000), .0080 (over 100,000) | 1.6% |

In this project, 8504.21 is "small," 8504.22 is "medium" and 8504.23 is "large." The large units are where the shortage is worst. The full table is in `data/reference/hts_codes.csv`.

Source: USITC Harmonized Tariff Schedule, checked October 30, 2026. The general duty column doesn't include extra tariffs like Section 232 or Section 301.

## Data

| What | Source | Status |
|---|---|---|
| Transformer producer prices | FRED: WPU11740999, PCU335311335311 | Day 2 |
| Imports by country, value and quantity | US Census international trade API (free key needed) | Day 3 |
| Hyperscaler capex | SEC EDGAR XBRL API | Day 6 |
| Grid interconnection queues | LBNL "Queued Up" | Day 8 |
| Electricity demand and prices | EIA | Day 9 |

## Layout

- `data/raw`: downloads, never edited by hand
- `data/clean`: cleaned tables built from raw
- `data/reference`: lookup tables like the HTS codes
- `notebooks`: analysis, meant to run top to bottom
- `charts`: final charts
- `log.md`: one line per work session
