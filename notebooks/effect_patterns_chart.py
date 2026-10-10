"""
effect_patterns_chart.py
------------------------
Illustrates the three effect shapes injected into the synthetic panel, plus
one reference shape that is NOT in the simulation but matters in practice:
pull-forward demand followed by a post-campaign dip.

Usage:
    python notebooks/effect_patterns_chart.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent

t = np.linspace(0, 30, 300)

# The three shapes used in the simulation (same functions as the data generator)
spike = 0.22 * np.exp(-t / 6.0)
slow_build = 0.12 * (1 - np.exp(-t / 10.0)) * np.exp(-np.maximum(t - 10.0, 0) / 18.0)
persistent = 0.06 * (1 - np.exp(-t / 14.0))

# Reference only: an early spike, then a dip below baseline (borrowed demand)
pull_forward = 0.20 * np.exp(-t / 4.0) - 0.06 * np.exp(-((t - 10.0) ** 2) / 30.0)

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(t, spike * 100, linewidth=2.2, label="A. Spike & fast decay")
ax.plot(t, slow_build * 100, linewidth=2.2, label="B. Slow build, sustained")
ax.plot(t, persistent * 100, linewidth=2.2, label="C. Small but persistent")
ax.plot(t, pull_forward * 100, linewidth=1.6, linestyle="--", color="gray",
        label="(ref) D. Pull-forward & post-dip")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xlabel("Weeks since campaign start")
ax.set_ylabel("Incremental effect (%)")
ax.set_title("Incremental effect patterns and what they imply for timing")
ax.legend(loc="upper right")
# Each note uses its curve's color so it is clear which shape it refers to.
ax.annotate("invest close to the moment\nyou need impact", xy=(2.5, 16), fontsize=8.5, color="C0")
ax.annotate("needs lead time:\nstart earlier", xy=(11, 8.2), fontsize=8.5, color="C1")
ax.annotate("sustain; judge over months", xy=(20, 3.0), fontsize=8.5, color="C2")
ax.annotate("watch for borrowed demand\n(post-period must be long enough)",
            xy=(15.5, -5.0), fontsize=8.5, color="gray")
fig.tight_layout()
out = HERE / "effect_patterns.png"
fig.savefig(out, dpi=150)
print(f"Chart saved: {out.name}")
