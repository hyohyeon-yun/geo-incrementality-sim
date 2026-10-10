# Example: the result, written for a decision-maker

How the result in this repo would be reported to a non-technical stakeholder, following the template in [`skill/geo-incrementality-test-design/assets/executive_summary_template.md`](../skill/geo-incrementality-test-design/assets/executive_summary_template.md). The data are synthetic, with a known answer, so the memo reports a check of the method, not a real campaign.

---

## Conclusion

The geo test recovered the campaign's true incremental lift in all three campaign markets, within 0.7 percentage points of the hidden answer. Recommendation: pilot it on the next campaign that runs in some markets but not others, after agreeing with the budget owners on the smallest effect the test must be able to detect.

## What was measured and how

Three markets ran the campaign from week 70; thirteen did not. For each campaign market, "what would have happened without the campaign" was built as a weighted blend of the thirteen non-campaign markets (a synthetic control), matched on the 70 weeks before the campaign. The gap after that is the estimated lift. To check that the gap is not noise, the same analysis was run on each non-campaign market as if it had run the campaign (a placebo test).

## Results

| Output | Value | What it supports |
|---|---|---|
| Estimated lift, US | +4.0% (true +4.2%) | Whether and how much the campaign worked |
| Estimated lift, IN / DE | +4.7% / +4.3% (true +5.1% / +3.7%) | The same, per market |
| Significance, US (placebo rank) | Most unusual of 14 markets: chance alone would produce that 1 time in 14 (p ≈ 0.07), the best possible with 13 comparison markets | Confidence that the US gap is not noise |
| Effect pattern | US fast spike · IN slow build · DE small but persistent | When to schedule spend |
| Cost per incremental install | Not computed in this check (return on spend would also need revenue) | Efficiency across markets, one input among several |

## How to use it

- **Size and significance** answer whether the campaign worked in each market. Lift alone is not a basis for comparing markets, because their spend and size differ.
- **Pattern** suggests when to spend. Fast spike: concentrate just before the moment that matters. Slow build: start earlier. Small but persistent: sustain spend and judge it over months, not weeks.
- **Efficiency** (cost per incremental install, or incremental revenue per unit of incremental spend) informs how much each market gets, weighed with strategic priorities, never as the only rule.

## Scope

Measured on installs, a behavioral outcome. Changes in awareness or preference need a separate survey-based design. The result holds only if the campaign did not reach the comparison markets, for example through online spillover or budget moved out of them.

## Next steps

1. **Agree on power before the test.** The quick simulation here puts the smallest reliably detectable effect at about 11%, but it uses a simpler statistic than the significance test and overstates the threshold on this panel (see the [README](../README.md)). Redo it with the test's own statistic and agree on the result up front; that keeps "no effect" apart from "too small to detect".
2. **Choose holdout markets deliberately:** some larger and some smaller than each campaign market, enough of them to allow a stricter significance test, no spillover, and an explicit trade-off between the cost of holding markets out and the cost of repeating a wrong allocation.
3. **Feed results into the marketing mix model.** Lift from tests like this one can calibrate the model's estimates for the channels and markets tested.
