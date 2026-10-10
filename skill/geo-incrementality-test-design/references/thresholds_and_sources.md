# Thresholds and Standards — with source labels

Every value below is tagged [SOURCED] (peer-reviewed or original
methodological source) or [HEURISTIC] (industry practice / rule of thumb).
When advising users, always disclose which kind a threshold is.

| Item | Value / rule | Label & source |
|---|---|---|
| Placebo rank inference | p = rank/(J+1); smallest attainable p = 1/(J+1) | [SOURCED] Abadie, Diamond & Hainmueller (2010, JASA); Abadie (2021, JEL review) |
| Placebo pre-fit filter | Drop placebos whose pre-period fit is more than 5x worse than the treated unit's | [SOURCED] Abadie et al. (2010) use pre-period MSPE at 20x, 5x and 2x; this skill filters on pre-MAPE at 5x instead — a [HEURISTIC] adaptation for panels with heterogeneous unit scales (the original outcome, per-capita cigarette sales, shares one scale across states). 5x on a linear error is looser than 5x on MSPE (about 2.2x linear) |
| Convex-hull requirement | Treated unit must be reproducible as a convex (0–1, sum-1) combination of donors — inside their range | [SOURCED] Abadie & Gardeazabal (2003, AER); Abadie (2021) |
| Pre-period fit bar | MAPE ≲ 5% "reasonable"; 2–3% good | [HEURISTIC] industry practice; no canonical published cutoff |
| Statistical power target | ≥80% | [SOURCED as convention] Cohen (1988); universal experimental-design convention |
| Test length | 4–6 weeks + 2–4 weeks post-observation (delayed & pulled-forward conversions) | [HEURISTIC] measurement-vendor practice (e.g. Haus public materials) |
| Corner-solution warning | One donor weight ≥0.8 → donor pool likely inadequate | [HEURISTIC] |
| Pre-period length | 20+ periods minimum, 52+ (one seasonal cycle) preferred | [HEURISTIC] grounded in overfitting logic; original studies used 10–20 yearly points |
| Why measurement is hard at all | Individual-level ad ROI experiments need enormous samples; CI widths >100pp common | [SOURCED] Lewis & Rao (2015, QJE), "The Unfavorable Economics of Measuring the Returns to Advertising" |
| Cross-validation option | Bayesian structural time series as an alternative counterfactual (unconstrained-weights family) | [SOURCED] Brodersen et al. (2015, Annals of Applied Statistics) — the CausalImpact paper; its flagship example is an online advertising campaign |
| Synthetic vs matched markets | Weighted synthetic controls can be several times more precise than single matched-market designs | [HEURISTIC/vendor] Haus methodology analysis (vendor material, not peer-reviewed — cite as such) |
| Brand vs activation budget split | ~60:40 brand:activation on average | [SOURCED with caveats] Binet & Field (IPA databank); category-dependent average, selection-bias critiques exist — never present as law |

## Production tooling

For production use, prefer maintained packages over hand-rolled fits:
- Python: `pysyncon` (Abadie-style SCM incl. placebo tooling)
- R: `CausalImpact` (original Google implementation; the Python TF port has
  recurring dependency issues — known practical constraint)
- Meta `GeoLift` (R): purpose-built for marketing geo experiments
The bundled script is a validated reference implementation for
transparency and environments where installs are restricted.
