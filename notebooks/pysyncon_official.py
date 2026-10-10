"""
pysyncon_official.py
--------------------
Cross-check with the maintained `pysyncon` package (pip install pysyncon).

The direct scipy implementation in synthetic_control_analysis.py should give
a similar result: if two independent implementations agree, the hand-built
one is less likely to hide a bug.

Usage:
    python notebooks/pysyncon_official.py
"""

from pysyncon import Dataprep, Synth

from synthetic_control_analysis import INTERVENTION_WEEK, load_panel

TARGET_COUNTRY = "US"

panel = load_panel()
donors = sorted(panel.loc[~panel["is_treated"], "country"].unique().tolist())

dataprep = Dataprep(
    foo=panel,
    predictors=["search_spend", "social_spend"],
    predictors_op="mean",
    dependent="installs",
    unit_variable="country",
    time_variable="week",
    treatment_identifier=TARGET_COUNTRY,
    controls_identifier=donors,
    time_predictors_prior=range(0, INTERVENTION_WEEK),
    time_optimize_ssr=range(0, INTERVENTION_WEEK),
)

synth = Synth()
synth.fit(dataprep=dataprep)

print("=== pysyncon result ===\n")
print("Donor weights:")
print(synth.weights().sort_values(ascending=False).round(3))

att_result = synth.att(time_period=range(INTERVENTION_WEEK, 104))
print(f"\nPost-period ATT (absolute installs): {att_result['att']:,.0f}")
print(f"Standard error: {att_result['se']:,.0f}")

# Convert to a relative effect to compare with the scipy implementation.
post_actual_mean = panel[
    (panel.country == TARGET_COUNTRY) & (panel.week >= INTERVENTION_WEEK)
]["installs"].mean()
synthetic_level_post = post_actual_mean - att_result["att"]
att_pct = att_result["att"] / synthetic_level_post
print(f"Relative effect: {att_pct:.2%}  (scipy implementation: 4.01%, true: 4.20%)")
