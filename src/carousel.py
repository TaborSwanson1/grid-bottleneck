# ==============================================================================
# Script: carousel.py
# Project: Grid Bottleneck - LinkedIn carousel for Post 1 (the overbuild risk)
# Objective: Six 4:5 slides (1080 x 1350) that carry the post's argument on a
#            phone screen: how big the signed backlog is, how fast it's growing
#            next to deliveries, who it depends on, and why timing matters.
#            Saved as one PDF (LinkedIn's document post) and as single PNGs.
# Inputs:  data/clean/leases_not_commenced.csv, data/clean/lease_backlog_ratio.csv
# Outputs: charts/post1/post1_carousel.pdf, charts/post1/slide_1.png ... slide_6.png
# ==============================================================================

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from style import INK, INK_2, MUTED, GRID, US_GRAY, BLUE, clean_axes

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "charts/post1"
BIG_FOUR = ["Microsoft", "Meta", "Alphabet", "Amazon"]
LIGHT_BLUE = "#a9c9ef"  # BLUE at a lighter tint, for the same series in a later phase
plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]


def slide(n: int, title: str):
    fig = plt.figure(figsize=(7.2, 9), dpi=150)
    fig.text(0.07, 0.95, f"{n} / 6", fontsize=10, color=MUTED)
    fig.text(0.07, 0.905, title, fontsize=21, color=INK, va="top", weight="bold", linespacing=1.15)
    return fig


def footer(fig, text: str) -> None:
    fig.text(0.07, 0.035, text, fontsize=8.5, color=MUTED, va="bottom", linespacing=1.4)


def cover(waiting: pd.Series) -> plt.Figure:
    fig = plt.figure(figsize=(7.2, 9), dpi=150)
    fig.text(0.07, 0.72, f"${waiting.iloc[-1] / 1000:.1f} trillion", fontsize=54, color=BLUE, weight="bold")
    fig.text(0.07, 0.655, "of data center leases that Microsoft, Meta,\nAlphabet and Amazon have signed but\nhaven't started yet.",
             fontsize=19, color=INK, va="top", linespacing=1.3)
    fig.text(0.07, 0.43, f"Two years ago it was ${waiting.loc['2024-06-30']:.0f} billion.", fontsize=19, color=INK)
    fig.text(0.07, 0.3, "Is that demand, or a pile-up?\nWhat 4 years of 10-Q and 10-K lease notes show.",
             fontsize=14, color=INK_2, linespacing=1.4)
    footer(fig, "Tabor Swanson  |  github.com/TaborSwanson1/grid-bottleneck")
    return fig


def growth(waiting: pd.Series) -> plt.Figure:
    fig = slide(2, "The signed backlog went from $414B\nto $1T in nine months")
    ax = fig.add_axes([0.1, 0.17, 0.84, 0.58])
    s = waiting.copy()
    s.index = pd.to_datetime(s.index)
    ax.plot(s.index, s.values, color=BLUE, linewidth=3, marker="o", markersize=4)
    for date, label in [("2024-06-30", "$168B\nJun 2024"), ("2025-12-31", "$414B\nDec 2025"), ("2026-09-30", "$1,016B\nSep 2026")]:
        v = s.loc[date]
        ax.annotate(label, (pd.Timestamp(date), v), xytext=(-8, 8), textcoords="offset points",
                    ha="right", fontsize=11, color=INK, linespacing=1.2)
    ax.yaxis.set_major_formatter(lambda v, _: f"${v:,.0f}B")
    ax.set_ylim(0, 1150)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    clean_axes(ax, labelsize=10)
    fig.text(0.07, 0.79, "Future payments on leases signed but not started, Microsoft, Meta,\nAlphabet and Amazon combined. Mostly data centers.",
             fontsize=11, color=INK_2, va="top", linespacing=1.35)
    footer(fig, "Source: lease and commitment notes in each company's 10-Q and 10-K, 2022 to Sep 2026.\n"
                "Totals over terms of up to 20 years, not one year of spending. Amazon includes warehouses.")
    return fig


def ratio(r: pd.DataFrame) -> plt.Figure:
    fig = slide(3, "At four of six, signed leases are\npiling up faster than they open")
    latest = r.sort_values("period").groupby("company").tail(1).set_index("company")
    first = r[r.period < "2023-01-01"].sort_values("period").groupby("company").tail(1).set_index("company").ratio
    order = ["Oracle", "Alphabet", "Meta", "Microsoft", "Amazon", "CoreWeave"]
    falling = {"Oracle", "CoreWeave"}
    ax = fig.add_axes([0.25, 0.2, 0.68, 0.52])
    y = range(len(order))[::-1]
    vals = [latest.loc[c, "ratio"] for c in order]
    ax.barh(list(y), vals, color=[US_GRAY if c in falling else BLUE for c in order], height=0.6)
    ax.axvline(1, color=INK_2, linewidth=1, linestyle="--")
    for yi, c, v in zip(y, order, vals):
        when = pd.Timestamp(latest.loc[c, "period"]).strftime("%b %Y")
        note = f"from {first[c]:.1f}x at end of 2022" if c in first else "falling as sites open"
        ax.text(v + 0.08, yi, f"{v:.1f}x  ({when})\n{note}", va="center", fontsize=9.5, color=INK, linespacing=1.25)
    ax.set_yticks(list(y), order, fontsize=12, color=INK)
    ax.set_xlim(0, 7.2)
    ax.set_xticks([0, 1, 2, 3, 4, 5])
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}x")
    clean_axes(ax, grid_axis="x", labelsize=10)
    ax.tick_params(axis="y", length=0)
    ax.text(1.05, len(order) - 0.45, "more waiting than running", fontsize=9, color=INK_2)
    fig.text(0.07, 0.79, "Payments on leases signed but not started, divided by payments\non leases already running. Gray bars are falling.",
             fontsize=11, color=INK_2, va="top", linespacing=1.35)
    footer(fig, "Source: lease notes and lease maturity tables, 10-Q and 10-K. Both sides are undiscounted.\n"
                "Meta reports the running side only once a year. Its waiting leases have since tripled.")
    return fig


def concentration() -> plt.Figure:
    fig = slide(4, "A few AI labs carry\na lot of it")
    tiles = [
        ("~40%", "of Amazon's $578B contracted backlog\ncomes from OpenAI and Anthropic deals"),
        ("$417B", "of new compute and lease commitments\nat Anthropic, about 9x its yearly revenue,\nowed \"regardless of actual usage\""),
        ("11%", "of Microsoft's quarterly revenue\ncame from OpenAI"),
        ("72%", "of CoreWeave's revenue came from\nits three largest customers"),
    ]
    for i, (big, text) in enumerate(tiles):
        top = 0.74 - i * 0.165
        fig.text(0.07, top, big, fontsize=34, color=BLUE, weight="bold", va="top")
        fig.text(0.42, top - 0.005, text, fontsize=11.5, color=INK, va="top", linespacing=1.35)
        if i:
            fig.add_artist(plt.Line2D([0.07, 0.93], [top + 0.025, top + 0.025], color=GRID, linewidth=1))
    fig.text(0.07, 0.115, "If one of them slows down, the commitments don't vanish.\nThey become a credit problem for whoever is owed.",
             fontsize=12, color=INK, linespacing=1.4)
    footer(fig, "Sources: Amazon and Microsoft 10-Qs (Sep 2026), CoreWeave 10-Q (Jun 2026), Anthropic S-1.\n"
                "The 40% adds announced deal sizes against the backlog, so it's rough.")
    return fig


def timing() -> plt.Figure:
    fig = slide(5, "Signed on today's demand,\ndelivered into a later market")
    ax = fig.add_axes([0.07, 0.42, 0.86, 0.3])
    rows = [("Signed", 2024, 2026.8, US_GRAY), ("Start dates", 2026, 2034, BLUE), ("Lease terms run", 2026, 2054, LIGHT_BLUE)]
    for i, (label, a, b, color) in enumerate(rows):
        yi = len(rows) - 1 - i
        ax.barh(yi, b - a, left=a, color=color, height=0.55)
        ax.text(a, yi + 0.42, f"{label}: {a}" + (f" to {int(b)}" if b != 2026.8 else " to now"), fontsize=10.5, color=INK)
    ax.set_xlim(2023, 2055)
    ax.set_ylim(-0.5, len(rows) - 0.1)
    ax.set_yticks([])
    ax.set_xticks(range(2025, 2056, 5))
    clean_axes(ax, grid_axis="x", labelsize=10)
    ax.spines["left"].set_visible(False)
    fig.text(0.07, 0.79, "These leases begin between 2026 and 2034 and many run 15 to 20\nyears. The demand case gets made once, at signing.",
             fontsize=11, color=INK_2, va="top", linespacing=1.35)
    fig.text(0.07, 0.33, "The market has already moved once inside this cycle.", fontsize=13, color=INK, weight="bold")
    fig.text(0.07, 0.295, "Early 2025: Microsoft reportedly dropped about 200 MW of US leases\nand let over 1 GW of agreements lapse as OpenAI moved work to Oracle.\n\n"
             "Sep 2026: Microsoft had $365B of leases signed and waiting.",
             fontsize=11, color=INK, va="top", linespacing=1.4)
    footer(fig, "Sources: lease notes (Microsoft FY2027 to FY2034, Oracle 15 to 19 year terms); TD Cowen via\n"
                "Bloomberg, Feb 2025. Microsoft didn't comment. Bars are ranges across companies.")
    return fig


def close() -> plt.Figure:
    fig = slide(6, "What would change my mind")
    points = [
        "The ratio falls everywhere, the way it already has\nat Oracle and CoreWeave. That means buildings are\nopening and the backlog isn't stuck.",
        "Contract GPU prices keep rising for another year.\nOne-year H100 contracts rose about 40% from\nOct 2025 to Mar 2026.",
        "Texas and other grids audit their large-load\nrequests down, and most of what's left gets built.",
    ]
    for i, p in enumerate(points):
        top = 0.76 - i * 0.15
        fig.text(0.07, top, str(i + 1), fontsize=26, color=BLUE, weight="bold", va="top")
        fig.text(0.15, top - 0.004, p, fontsize=12.5, color=INK, va="top", linespacing=1.35)
    fig.text(0.07, 0.25, "Demand is strong today. Northern Virginia is 0.2% vacant.\nThat's also what the start of a build cycle looks like.",
             fontsize=12, color=INK_2, linespacing=1.4)
    fig.text(0.07, 0.13, "Code, data and every source:\ngithub.com/TaborSwanson1/grid-bottleneck", fontsize=13, color=INK, linespacing=1.4)
    footer(fig, "Tabor Swanson  |  Economics, University of Oregon")
    return fig


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    nc = pd.read_csv(ROOT / "data/clean/leases_not_commenced.csv")
    waiting = nc[nc.company.isin(BIG_FOUR)].pivot_table(index="period", columns="company", values="not_commenced_usd")
    waiting = waiting.dropna().sum(axis=1) / 1e9  # quarters where all four reported
    r = pd.read_csv(ROOT / "data/clean/lease_backlog_ratio.csv")
    figs = [cover(waiting), growth(waiting), ratio(r), concentration(), timing(), close()]
    with PdfPages(OUT / "post1_carousel.pdf") as pdf:
        for i, fig in enumerate(figs, 1):
            fig.savefig(OUT / f"slide_{i}.png")
            pdf.savefig(fig)
            plt.close(fig)
    print(f"Saved {len(figs)} slides to {OUT.relative_to(ROOT)}")
