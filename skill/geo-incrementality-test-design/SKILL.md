---
name: geo-incrementality-test-design
description: Design, run, and interpret geo-based incrementality tests for marketing campaigns using region-level panel data. Use whenever the user wants to measure the true incremental impact of marketing or media spend — as opposed to platform-reported ROAS or attribution — including designing a geo holdout test, computing power/MDE for a planned test, building a synthetic control counterfactual, running placebo significance tests, or translating lift results into budget-allocation decisions. Trigger even if the user never says "incrementality" — e.g. "did our campaign actually work", "measure campaign lift by country/region", "was that ad spend wasted", "we can't trust the platform numbers", "design a holdout test".
---

# Geo-Incrementality Test Design

Measure the causal ("incremental") impact of a campaign run in some
regions/countries by constructing a synthetic control counterfactual from
untreated regions, testing significance with placebo runs, and translating
the result into budget decisions.

## Step 1 — Determine the mode

- **Analysis mode**: the user has panel data and a campaign that already ran
  → go to Step 2.
- **Design mode**: the campaign has not run yet → skip to "Design mode".
- **Validation mode**: the user is skeptical of the method or building a new
  pipeline → offer to first run the pipeline on simulated data with a known
  ground truth (generate a panel with an injected effect, verify the
  pipeline recovers it). Never generate the treated unit's outcome as a
  function of the donor units — that builds success into the data and makes
  the validation circular. Generate units independently with shared
  trend/seasonality only.

## Step 2 — Data intake (analysis mode)

Required: long-format data with one row per (unit, period):
unit column (country/region/DMA), period column (date or index), outcome
column (sales, installs, signups — a behavioral metric; explain that
awareness/consideration require separate survey-based designs).

Before running anything, confirm with the user:
1. Which unit(s) were treated, and the first period AFTER the campaign began.
2. Whether OTHER units were also treated — they must be passed via
   `--exclude`, never left in the donor pool.
3. SUTVA risks: could the campaign have reached untreated units (adjacent
   regions, online spillover, travelers)? Was campaign budget drawn from
   untreated units' budgets? If yes, exclude the contaminated units and say
   so in the output.
4. Anything unusual during the test window (competitor events, price
   changes, stockouts) — these confound the comparison.

## Step 3 — Run the analysis

```bash
python scripts/run_geo_incrementality.py \
  --data panel.csv --unit-col region --period-col week --outcome-col sales \
  --treated US --intervention 70 \
  [--exclude <other treated units>] [--power --alpha 0.15]
```

One treated unit per run. The script prints warnings — never suppress or
paraphrase them away; every `[warn]` must appear in your summary to the
user. Key automatic checks: balanced panel, ≥4 donors, ≥20 pre-periods
(warn), treated unit inside the donor range (convex-hull proxy), pre-period
MAPE, corner-solution weights, placebo rank p-value, attainable-p floor.

## Step 4 — Interpret (read references/thresholds_and_sources.md first)

Order of interpretation — do not skip ahead:
1. **Pre-period fit** (MAPE): if poor, STOP — the post-period number is
   uninterpretable, not "a weaker result". Diagnose the donor pool.
2. **Weights sanity**: corner solution (one donor ≥0.8) → donor pool
   inadequate. Also ask the user whether the top-weighted donors make
   business sense as comparators.
3. **Effect size**: always call it an estimate. Never say "measured X%".
4. **Significance**: placebo rank p. State the resolution floor
   1/(J+1) explicitly — with few donors, p<0.05 may be unattainable by
   construction; agree on the achievable threshold rather than fail it.
5. **Pull-forward check**: if the effect spikes then dips below zero, the
   campaign may have borrowed future demand; net effect = area above minus
   area below. Ensure the post-period extends past the dip.

When advising on thresholds, always distinguish sourced standards from
heuristics using the labels in references/thresholds_and_sources.md, and
tell the user which is which.

## Step 5 — Report in two layers

1. Technical: the script output, chart, and caveats.
2. Executive: fill assets/executive_summary_template.md — verdict first,
   ≤4 technical terms, numbers in a table, limitations phrased as scope
   ("what this covers + what needs a separate design"), and decisions
   separated into effectiveness (size, significance, pattern → where/when)
   vs efficiency (iROAS → how much, as ONE input alongside strategic
   priorities, never the sole decision rule).

## Design mode (campaign not yet run)

1. Donor pool: treated unit's scale/trend must lie INSIDE the donors' range
   (a convex combination cannot reach outside it); more donors → finer
   placebo p resolution (floor 1/(J+1)).
2. Pre-agree power/MDE with the stakeholders who will act on the result:
   run the script on historical (pre-campaign) data with a past pseudo-
   intervention date and `--power` to estimate the MDE of the planned
   design. If MDE exceeds the plausible effect size, redesign (more donors,
   longer test, bigger spend contrast) before launching.
3. Test length: typically 4–6 weeks plus 2–4 weeks post-observation for
   delayed and pulled-forward conversions [industry practice — label it as
   such].
4. Metric: primary = closest to money (sales/installs); secondary = upper
   funnel (brand search volume, share of search). Fix these BEFORE the test
   to avoid post-hoc metric shopping.

## Honesty rules (apply to every output)

- Simulated/public-data results validate the METHOD; only real treated data
  measures a campaign. Never blur this line.
- Report what was run, not what was discussed.
- Quote numbers only from produced outputs, never from memory.
- The power simulation uses effect-based ranks on the filtered placebo
  noise; the significance test uses RMSPE-ratio ranks. They are consistent
  in spirit but not identical — say "approximate" when reporting power.

## Bundled resources

- `scripts/run_geo_incrementality.py` — full pipeline (fit, placebo, power,
  chart). Read its `--help` before first use.
- `references/thresholds_and_sources.md` — every threshold with a
  [SOURCED] / [HEURISTIC] label. Read before interpreting results.
- `references/pitfalls.md` — failure modes and diagnostics. Read when any
  warning fires or results look implausible.
- `assets/executive_summary_template.md` — executive report skeleton.
