# ==============================================================================
# Script: style.py
# Project: Grid Bottleneck - Shared chart style
# Objective: One place for text colors, the three series colors, and the axis
#            styling every chart uses. Importing it also turns off matplotlib's
#            math parsing, so labels like "$69B to $376B" print as written.
# ==============================================================================

import matplotlib.pyplot as plt

plt.rcParams["text.parse_math"] = False

INK, INK_2, MUTED, GRID = "#111111", "#555555", "#777777", "#e6e6e6"
US_GRAY = "#999999"  # comparison lines (the US, a 2019 = 100 baseline)
# These three pass the colorblind check against each other in any combination.
# A fourth series goes in its own panel instead of getting a fourth color.
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
# Same thing, same color in every chart
CAPEX = BLUE                # Big Tech capex
PPI = "#4a4a4a"             # US transformer producer price index (benchmark line)
SMALL_UNITS = AQUA          # imported small transformers
LARGE_UNITS = ORANGE        # imported large transformers


def clean_axes(ax, grid_axis: str = "y", labelsize: float = 8) -> None:
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(colors=INK_2, labelsize=labelsize)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.6)
        ax.set_axisbelow(True)


def source_note(fig, text: str, y: float = 0.01) -> None:
    fig.text(0.01, y, text, fontsize=7, color=MUTED)
