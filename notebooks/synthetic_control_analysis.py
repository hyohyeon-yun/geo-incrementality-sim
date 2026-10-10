"""
synthetic_control_analysis.py
-----------------------------
Abadie-style synthetic control on the synthetic panel, for the US
(fast-spike effect).

The weights solve a constrained least-squares problem on the pre-period:
minimize the gap between the treated unit and a weighted sum of donors,
with w >= 0 and sum(w) = 1. It is implemented directly with scipy so the
mechanics are visible. For production work, prefer a maintained package
such as `pysyncon` (see pysyncon_official.py for a cross-check).

Usage:
    python notebooks/synthetic_control_analysis.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE.parent / "data" / "synthetic_geo_panel.csv"

TARGET_COUNTRY = "US"  # fast spike
INTERVENTION_WEEK = 70


def load_panel() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


def fit_weights(y_pre: np.ndarray, X_pre: np.ndarray):
    """Donor weights with w >= 0 and sum(w) = 1, fitted on the pre-period.

    Outcomes are in the tens of thousands. Without rescaling, the problem is
    badly scaled and SLSQP stops with the weights near their starting
    values (failure mode 1 in the README). So the data is rescaled to
    around 1.0 and an analytic gradient is supplied.
    """
    scale = y_pre.mean()
    y_s, X_s = y_pre / scale, X_pre / scale
    n = X_s.shape[1]

    def loss(w):
        resid = y_s - X_s @ w
        return np.sum(resid ** 2)

    def grad(w):
        resid = y_s - X_s @ w
        return -2.0 * X_s.T @ resid

    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0, "jac": lambda w: np.ones(n)}]
    bounds = [(0.0, 1.0)] * n
    w0 = np.full(n, 1.0 / n)

    result = minimize(
        loss, w0, jac=grad, method="SLSQP", bounds=bounds, constraints=constraints,
        options={"maxiter": 500, "ftol": 1e-12},
    )
    if not result.success:
        print(f"[warning] optimizer did not converge: {result.message}")
    return result.x


def fit_synthetic_control(panel: pd.DataFrame, target: str):
    """Fit the target country against all untreated countries."""
    pivot = panel.pivot(index="week", columns="country", values="installs")
    donors = [c for c in pivot.columns if not panel[panel.country == c]["is_treated"].iloc[0]]

    y = pivot[target]
    X = pivot[donors]
    pre = pivot.index < INTERVENTION_WEEK

    w = fit_weights(y[pre].values, X[pre].values)
    weights = pd.Series(w, index=donors).sort_values(ascending=False)

    synthetic_full = X.values @ w
    y_arr = y.values
    pre_rmse = np.sqrt(np.mean((y_arr[pre] - synthetic_full[pre]) ** 2))
    pre_mape = np.mean(np.abs((y_arr[pre] - synthetic_full[pre]) / y_arr[pre]))

    return pivot.index.values, y_arr, synthetic_full, weights, pre_rmse, pre_mape


def main():
    panel = load_panel()
    weeks, actual, synthetic, weights, pre_rmse, pre_mape = fit_synthetic_control(
        panel, TARGET_COUNTRY
    )

    print(f"=== {TARGET_COUNTRY} (fast spike): synthetic control ===\n")
    print(f"Pre-period fit: RMSE={pre_rmse:,.0f}, MAPE={pre_mape:.2%}")
    print("  Lower MAPE = the synthetic twin tracked the real series better before the campaign.\n")

    print("Top 5 donor weights (which countries make up the twin):")
    print(weights.head(5).round(3).to_string())
    print()

    post = weeks >= INTERVENTION_WEEK
    estimated_lift = (actual[post] - synthetic[post]) / synthetic[post]
    print(f"Estimated average post-period lift: {estimated_lift.mean():.2%}")

    # Compare with the answer key (exists only in synthetic data).
    truth = panel[panel.country == TARGET_COUNTRY].sort_values("week")[
        "_true_lift_pct_GROUND_TRUTH_ONLY"
    ].values
    true_post_mean = truth[post].mean()
    print(f"True average lift (answer key): {true_post_mean:.2%}")
    print(f"Estimate minus truth: {(estimated_lift.mean() - true_post_mean) * 100:+.2f} pp\n")

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(weeks, actual, label=f"{TARGET_COUNTRY} (actual)", linewidth=2)
    ax.plot(weeks, synthetic, label="Synthetic control (counterfactual)", linestyle="--")
    ax.axvline(INTERVENTION_WEEK, color="gray", linestyle=":", label="Campaign start")
    ax.set_xlabel("Week")
    ax.set_ylabel("Weekly installs")
    ax.set_title(f"{TARGET_COUNTRY}: actual vs synthetic control")
    ax.legend()
    fig.tight_layout()
    out = HERE / "synthetic_control_result.png"
    fig.savefig(out, dpi=150)
    print(f"Chart saved: {out.name}")


if __name__ == "__main__":
    main()
