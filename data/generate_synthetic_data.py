"""
generate_synthetic_data.py
--------------------------
Builds a synthetic panel for a geo-incrementality test: 16 countries x 104
weeks of weekly app installs for a fictional product.

Design choices
1. 3 treated countries + 13 untreated donor countries. Synthetic control needs
   a donor pool large enough to reproduce the treated unit; Abadie's classic
   studies use many comparison units for the same reason.
2. From week 70, each treated country gets a different effect shape:
     - US: fast spike that fades within weeks
     - IN: slow build that peaks around week 10, then fades
     - DE: small but persistent
3. The true weekly lift is stored in `_true_lift_pct_GROUND_TRUTH_ONLY`.
   Real data never has this column. It is here so a method can be graded
   against a known answer before anyone trusts it.

All values are fictional and unrelated to any real company, product or campaign.
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=42)

N_WEEKS = 104  # two years
INTERVENTION_START_WEEK = 70

COUNTRIES = [
    # (country_code, baseline_weekly_installs, effect_shape, is_treated)
    # Treated baselines sit inside the donors' range (7,000-32,000). A treated
    # unit larger than every donor cannot be matched by weights in [0, 1] that
    # sum to 1 (failure mode 2 in the README).
    ("US", 22000, "fast_spike", True),
    ("IN", 20000, "slow_build", True),
    ("DE", 14000, "persistent", True),
    # untreated donor pool
    ("UK", 24000, "none", False),
    ("FR", 23000, "none", False),
    ("CA", 18000, "none", False),
    ("AU", 12000, "none", False),
    ("JP", 32000, "none", False),
    ("BR", 29000, "none", False),
    ("MX", 16000, "none", False),
    ("IT", 19000, "none", False),
    ("ES", 17000, "none", False),
    ("NL", 9000, "none", False),
    ("SE", 7000, "none", False),
    ("PL", 11000, "none", False),
    ("KR", 15000, "none", False),
]


def true_effect_curve(weeks_since_start: np.ndarray, shape: str) -> np.ndarray:
    """True incremental lift (as a fraction) by week; zero before the campaign."""
    effect = np.zeros_like(weeks_since_start, dtype=float)
    active = weeks_since_start >= 0
    t = weeks_since_start[active]

    if shape == "fast_spike":
        # fast spike that fades within about six weeks
        peak, decay = 0.22, 6.0
        effect[active] = peak * np.exp(-t / decay)
    elif shape == "slow_build":
        # slow build that peaks around week 10, then fades (long consideration)
        peak, rise, decay = 0.12, 10.0, 18.0
        effect[active] = peak * (1 - np.exp(-t / rise)) * np.exp(-np.maximum(t - rise, 0) / decay)
    elif shape == "persistent":
        # small but steady and long-lasting (brand-type effect)
        plateau, rise = 0.06, 14.0
        effect[active] = plateau * (1 - np.exp(-t / rise))
    return effect


def generate() -> pd.DataFrame:
    weeks = np.arange(N_WEEKS)
    seasonal = 1 + 0.08 * np.sin(2 * np.pi * weeks / 52)  # yearly seasonality
    trend = 1 + 0.0015 * weeks  # slow category growth

    rows = []
    for code, base, shape, is_treated in COUNTRIES:
        # Media spend: baseline search and social budgets plus noise.
        # Donor countries advertise too.
        search_spend = base * 0.18 * (1 + RNG.normal(0, 0.05, N_WEEKS))
        social_spend = base * 0.12 * (1 + RNG.normal(0, 0.07, N_WEEKS))

        # Spend is recorded as a covariate only; it is NOT part of the installs
        # equation. An earlier version multiplied a spend term into installs.
        # Because spend scales with market size, large markets were inflated
        # several-fold and fell outside the donors' range.

        weeks_since_start = weeks - INTERVENTION_START_WEEK
        true_lift_pct = true_effect_curve(weeks_since_start, shape) if is_treated else np.zeros(N_WEEKS)

        # Treated countries add campaign spend from the intervention week (recorded only).
        incremental_spend = np.where(
            (weeks >= INTERVENTION_START_WEEK) & is_treated, base * 0.10, 0.0
        )
        search_spend = search_spend + incremental_spend * 0.6
        social_spend = social_spend + incremental_spend * 0.4

        noise = RNG.normal(0, 0.025, N_WEEKS)  # measurement noise
        installs = base * trend * seasonal * (1 + true_lift_pct + noise)

        for w in range(N_WEEKS):
            rows.append(
                {
                    "country": code,
                    "effect_shape": shape,
                    "is_treated": is_treated,
                    "week": w,
                    "installs": round(installs[w]),
                    "search_spend": round(search_spend[w], 1),
                    "social_spend": round(social_spend[w], 1),
                    "intervention_week": INTERVENTION_START_WEEK,
                    # Answer key: never present in real data. Use it only to
                    # grade the method, never as an input to the analysis.
                    "_true_lift_pct_GROUND_TRUTH_ONLY": round(true_lift_pct[w], 4),
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate()
    out_path = Path(__file__).resolve().parent / "synthetic_geo_panel.csv"
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} rows to {out_path}")
    print("\nMean weekly installs by country:")
    print(df.groupby(["country", "effect_shape", "is_treated"])["installs"].mean().round(0))
    print("\nTrue average post-campaign lift by effect shape (answer key, for validation only):")
    treated = df[df["is_treated"] & (df["week"] >= df["intervention_week"])]
    print(treated.groupby("effect_shape")["_true_lift_pct_GROUND_TRUTH_ONLY"].mean().round(4))
