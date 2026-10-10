# Pitfalls and Diagnostics

Failure modes observed while building this pipeline. Read when a warning
fires or results look implausible.

| Symptom | Likely cause | Fix |
|---|---|---|
| Poor pre-fit + weights piled on one donor + absurd effect (e.g. +400%) | Treated unit lies outside the donors' range (convex hull violated) — a 0–1/sum-1 combination cannot reach it | Add comparably-scaled donors, or rescale outcomes (per-capita, per-store) so units share a scale |
| Optimizer barely moves from equal weights | Bad scaling: with outcomes in the tens of thousands the problem is badly scaled and the optimizer stops early | Normalize data before fitting and supply an analytic gradient (the bundled script does both) |
| One placebo shows a huge pseudo-effect and wrecks the noise distribution | That unit is at the edge of the panel (smallest/largest) — outside ITS OWN leave-one-out hull. A fit filter on absolute errors across very different unit sizes, or one applied on the wrong scale (5x on RMSPE is 25x on MSPE), can miss it | Filter placebos on a scale-free fit measure; report which units were dropped |
| Power curve non-monotonic or absurd MDE | Inequality direction flipped in the rank computation — the single most common coding error in rank/p-value logic | Hand-check a tiny example (5 numbers, count by hand) against the code |
| "No effect" conclusion after the test | Possibly true, possibly underpowered — indistinguishable without a pre-agreed MDE | Always pre-agree power/MDE before launch; report "no detectable effect above X%" instead of "no effect" |
| Spike then dip below zero post-campaign | Pulled-forward demand (pantry-loading, upgrade acceleration) — NOT ad fatigue (fatigue decays toward zero, not below) | Extend the post-period past the dip; net effect = area above minus area below zero |
| Reported ROAS healthy while true costs deteriorate | Platform attribution credits conversions that were not incremental | This is the problem the whole test exists to detect; compare reported ROAS with measured iROAS |
| Metric looks great on one KPI only | Post-hoc metric shopping (multiple comparisons) | Fix primary + secondary metrics before the test |
| Great result during launch week only | Novelty effect or seasonal coincidence | Test 4–6 weeks; check the window for external events in treated AND donor units |
| Validation on simulated data always succeeds | Treated outcome was generated FROM the donors (circular design) | Generate units independently; share only common trend/seasonality; hide the injected truth until scoring |
