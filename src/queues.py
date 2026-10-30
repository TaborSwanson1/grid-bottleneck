# ==============================================================================
# Script: queues.py
# Project: Grid Bottleneck - Interconnection queues near data center hubs
# Objective: How much new power is trying to connect in Virginia, Texas,
#            Arizona and Oregon, and how long projects wait to get online.
# Inputs:  data/raw/lbnl_ix_queue_data_file_thru2025.xlsx (LBNL "Queued Up",
#          2026 edition, data through 2025; CC BY 4.0, LBNL and GridTracker)
# Outputs: data/clean/queue_requests_by_state.csv, data/clean/queue_active_2025.csv,
#          data/clean/queue_wait_by_region.csv,
#          charts/queue_requests_by_state.png, charts/queue_wait_by_region.png
#
# These queues are power plants and batteries asking to connect, not data
# centers. They measure how hard it is to add new supply, not data center load.
# ==============================================================================

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/raw/lbnl_ix_queue_data_file_thru2025.xlsx"
plt.rcParams["text.parse_math"] = False
STATES = {"VA": "Virginia (PJM)", "TX": "Texas (mostly ERCOT)", "AZ": "Arizona (West)", "OR": "Oregon (West)"}
YEARS = range(2015, 2026)
TYPES = ["Solar", "Battery", "Wind", "Gas"]  # everything else is "Other"
INK, INK_2, MUTED, GRID = "#111111", "#555555", "#777777", "#e6e6e6"


def load_projects() -> pd.DataFrame:
    d = pd.read_excel(SRC, "03. Complete Queue Data", header=1)
    d["mw"] = d[["mw_1", "mw_2", "mw_3"]].apply(pd.to_numeric, errors="coerce").sum(axis=1)
    d["q_date"] = pd.to_datetime(d.q_date, errors="coerce")
    d["type"] = d.type_clean.where(d.type_clean.isin(TYPES), "Other / hybrid")
    return d[d.state.isin(STATES)]


def requests_by_year(d: pd.DataFrame) -> pd.DataFrame:
    """GW of new requests entering the queue each year. Request dates are complete, unlike exit dates."""
    r = d[d.q_date.dt.year.isin(YEARS)]
    return r.pivot_table(index=r.q_date.dt.year, columns="state", values="mw", aggfunc="sum").div(1e3).reindex(YEARS).fillna(0)


def active_2025(d: pd.DataFrame) -> pd.DataFrame:
    a = d[d.q_status == "active"]
    return a.pivot_table(index="state", columns="type", values="mw", aggfunc="sum").div(1e3).fillna(0)


def wait_by_region() -> pd.DataFrame:
    """LBNL's own median months from request to commercial operation, by year the project came online."""
    t = pd.read_excel(SRC, "38. IR to COD - region", header=26, usecols=range(7))
    t.columns = ["year", "region", "n", "mean", "p25", "median", "p75"]
    t = t[pd.to_numeric(t.year, errors="coerce").notna()]
    t["year"] = t.year.astype(int)
    return t[t.region.isin(["PJM", "ERCOT", "West", "All Regions"]) & t.year.isin(YEARS)]


def style(ax) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK_2, labelsize=8)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def chart_requests(req: pd.DataFrame, act: pd.DataFrame, dest: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.4), dpi=150)
    for ax, (st, label) in zip(axes, STATES.items()):
        ax.bar(req.index, req[st], color="#2a78d6", width=0.7)
        ax.set_title(label, loc="left", fontsize=10, color=INK)
        ax.annotate(f"{act.loc[st].sum():.0f} GW still waiting\nat end of 2025", (0.02, 0.97),
                    xycoords="axes fraction", va="top", fontsize=8, color=INK_2)
        ax.set_xticks([2015, 2020, 2025])
        ax.set_ylim(0, req[st].max() * 1.3)  # room for the label above the bars
        ax.yaxis.set_major_locator(plt.MaxNLocator(5, integer=True))
        ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f} GW")
        style(ax)
    fig.suptitle("New power projects asking to connect each year. Texas dwarfs the rest; Virginia's queue nearly shut in 2023-24.",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.text(0.01, 0.905, "GW of generation and storage entering the interconnection queue, by year of request. "
             "Each panel has its own scale.", fontsize=8.5, color=INK_2)
    fig.text(0.01, 0.01, "Source: Lawrence Berkeley National Laboratory and GridTracker, Queued Up 2026 edition "
             "(data through 2025), CC BY 4.0. Includes hybrid storage capacity.", fontsize=7, color=MUTED)
    fig.subplots_adjust(left=0.05, right=0.99, top=0.8, bottom=0.11, wspace=0.3)
    fig.savefig(dest)


def chart_wait(w: pd.DataFrame, dest: Path) -> None:
    lines = [("PJM", "PJM (Virginia)", "#2a78d6"), ("ERCOT", "ERCOT (Texas)", "#eb6834"),
             ("All Regions", "All US", "#555555")]
    # West (Arizona, Oregon) is left off: only 3 to 17 projects a year came online, too few for a median
    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    for region, label, color in lines:
        s = w[w.region == region].set_index("year")["median"] / 12
        ax.plot(s.index, s.values, color=color, linewidth=2.4 if region == "All Regions" else 2,
                linestyle="--" if region == "All Regions" else "-", marker="o", markersize=4)
        ax.annotate(f"{label}  {s.iloc[-1]:.1f} yrs", (s.index[-1], s.iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.set_xticks(list(YEARS))
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Median years from request to operation", color=INK_2)
    style(ax)
    ax.set_title("In PJM, which serves Virginia, the wait to connect new power has doubled since 2020",
                 loc="left", fontsize=11, color=INK)
    fig.text(0.01, 0.01, "Source: LBNL Queued Up 2026 edition, tab 38. Projects grouped by the year they came online. "
             "West (AZ, OR) left out: too few projects per year.",
             fontsize=7, color=MUTED)
    fig.subplots_adjust(right=0.7, bottom=0.12)
    fig.savefig(dest)


if __name__ == "__main__":
    d = load_projects()
    req, act, wait = requests_by_year(d), active_2025(d), wait_by_region()
    req.round(2).to_csv(ROOT / "data/clean/queue_requests_by_state.csv")
    act.round(2).to_csv(ROOT / "data/clean/queue_active_2025.csv")
    wait.to_csv(ROOT / "data/clean/queue_wait_by_region.csv", index=False)
    chart_requests(req, act, ROOT / "charts/queue_requests_by_state.png")
    chart_wait(wait, ROOT / "charts/queue_wait_by_region.png")
    print(req.round(1).to_string(), "\n")
    print(act.round(1).assign(total=act.sum(axis=1).round(1)).to_string(), "\n")
    print(wait.pivot_table(index="year", columns="region", values="median").div(12).round(1).to_string())
    print(wait.pivot_table(index="year", columns="region", values="n").to_string())
