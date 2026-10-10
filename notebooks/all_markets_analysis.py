"""
all_markets_analysis.py
-----------------------
Runs the same synthetic control on all three treated countries, US, IN and
DE, each with a different effect shape.

The donor pool is always "every untreated country", so treated countries
never act as donors for each other.

Usage:
    python notebooks/all_markets_analysis.py
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from synthetic_control_analysis import HERE, INTERVENTION_WEEK, fit_synthetic_control, load_panel

TARGETS = [
    ("US", "fast spike"),
    ("IN", "slow build"),
    ("DE", "small but persistent"),
]


def main():
    panel = load_panel()

    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharex=True)
    summary_rows = []

    for ax, (target, label) in zip(axes, TARGETS):
        weeks, actual, synthetic, weights, pre_rmse, pre_mape = fit_synthetic_control(panel, target)
        post = weeks >= INTERVENTION_WEEK
        est_lift = (actual[post] - synthetic[post]) / synthetic[post]

        truth = panel[panel.country == target].sort_values("week")[
            "_true_lift_pct_GROUND_TRUTH_ONLY"
        ].values
        true_lift = truth[post].mean()

        summary_rows.append(
            {
                "country": target,
                "pattern": label,
                "pre_mape": pre_mape,
                "estimated_lift": est_lift.mean(),
                "true_lift": true_lift,
                "gap_pp": (est_lift.mean() - true_lift) * 100,
                "top_donor": weights.index[0],
                "top_donor_weight": weights.iloc[0],
            }
        )

        ax.plot(weeks, actual, label="actual", linewidth=2)
        ax.plot(weeks, synthetic, label="synthetic", linestyle="--")
        ax.axvline(INTERVENTION_WEEK, color="gray", linestyle=":")
        ax.set_title(f"{target} ({label})")
        ax.set_xlabel("Week")
        if target == "US":
            ax.set_ylabel("Weekly installs")
            ax.legend()

    fig.tight_layout()
    out = HERE / "all_markets_result.png"
    fig.savefig(out, dpi=150)
    print(f"Chart saved: {out.name}\n")

    summary = pd.DataFrame(summary_rows)
    pd.set_option("display.float_format", lambda x: f"{x:.4f}")
    print(summary.to_string(index=False))
    return summary


if __name__ == "__main__":
    main()
