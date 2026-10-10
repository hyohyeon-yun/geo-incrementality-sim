"""
causalimpact_lite.py
--------------------
A simplified cross-check inspired by CausalImpact (Brodersen et al., 2015).

Limitation, stated plainly: real CausalImpact is a Bayesian structural
time-series model. This script keeps only the core idea (regress the treated
series on control series in the pre-period, predict the counterfactual, and
use residuals for uncertainty) with plain OLS and a normal approximation.
The band below is NOT a Bayesian posterior interval.

Why it is a useful cross-check: synthetic control constrains weights to
[0, 1] with sum 1, so it can only average donors. Regression weights are
unconstrained (negative or above 1 allowed): more flexible, but more prone
to overfitting. If two different methods land near the same answer, that
is evidence the answer is not an artifact of one method.

Usage:
    python notebooks/causalimpact_lite.py
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from synthetic_control_analysis import HERE, INTERVENTION_WEEK, load_panel

TARGET_COUNTRY = "US"


def fit_causalimpact_lite(panel: pd.DataFrame, target: str):
    pivot = panel.pivot(index="week", columns="country", values="installs")
    donors = [c for c in pivot.columns if not panel[panel.country == c]["is_treated"].iloc[0]]

    y = pivot[target].values
    X = pivot[donors].values
    pre = pivot.index.values < INTERVENTION_WEEK

    # Rescale for numerical stability (same lesson as the synthetic control fit).
    scale = y[pre].mean()
    y_s = y / scale
    X_s = X / scale

    # Intercept + unconstrained OLS: the key difference from synthetic control.
    X_design = np.column_stack([np.ones(len(X_s)), X_s])
    coef, *_ = np.linalg.lstsq(X_design[pre], y_s[pre], rcond=None)

    predicted = (X_design @ coef) * scale

    resid_pre = y[pre] - predicted[pre]
    resid_std = resid_pre.std(ddof=X_design.shape[1])

    return pivot.index.values, y, predicted, resid_std, coef


def main():
    panel = load_panel()
    weeks, actual, predicted, resid_std, coef = fit_causalimpact_lite(panel, TARGET_COUNTRY)
    post = weeks >= INTERVENTION_WEEK

    pre_mape = np.mean(np.abs((actual[~post] - predicted[~post]) / actual[~post]))
    print(f"=== {TARGET_COUNTRY}: CausalImpact-lite (OLS approximation) ===\n")
    print(f"Pre-period MAPE: {pre_mape:.2%}")

    rel_effect = (actual[post] - predicted[post]) / predicted[post]
    ci_halfwidth = 1.96 * resid_std  # pointwise, approximate

    print(f"Average relative effect: {rel_effect.mean():.2%}")
    print(f"Approximate pointwise 95% band (absolute): +/-{ci_halfwidth:,.0f}")
    print("  This is a normal approximation, not a Bayesian interval. For reference only.")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(weeks, actual, label="actual", linewidth=2)
    ax.plot(weeks, predicted, label="predicted (counterfactual)", linestyle="--")
    ax.fill_between(
        weeks, predicted - ci_halfwidth, predicted + ci_halfwidth,
        color="orange", alpha=0.15, label="approx. 95% band",
    )
    ax.axvline(INTERVENTION_WEEK, color="gray", linestyle=":")
    ax.set_xlabel("Week")
    ax.set_ylabel("Weekly installs")
    ax.set_title(f"{TARGET_COUNTRY}: CausalImpact-lite (OLS approximation)")
    ax.legend()
    fig.tight_layout()
    out = HERE / "causalimpact_lite_result.png"
    fig.savefig(out, dpi=150)
    print(f"\nChart saved: {out.name}")


if __name__ == "__main__":
    main()
