# Choosing a measurement design

A geo test needs markets that ran the campaign and comparable markets that did not. This note covers where that holds, what to do when it doesn't, and how to report the result to people who think in year-over-year numbers.

## Where a geo test fits

| Situation | Fit | Why |
|---|---|---|
| A campaign funded in some markets but not others | Strong | The split already exists, but it is rarely random, so pre-period fit matters. This repo simulates this case. |
| A new ad product or platform piloted in a few markets first | Strong | The staged rollout creates the comparison group. Observe long enough to get past novelty effects. |
| Checking a marketing mix model in specific markets | Partial | A test informs only the markets, channels and spend levels it covers. Test where the model looks doubtful, then use the results to calibrate it there. |
| A product launched everywhere on the same day | Weak | Every market is treated at once, so there is no comparison group. See the options below. |

## When there is no comparison group

1. **Staggered rollout:** start some markets days or weeks later, by design, so they serve as the comparison.
2. **Deliberate holdout:** keep some markets out on purpose, or, within one ad platform, run a lift study that randomly holds out people instead of markets.
3. **Compare each market with its own history** instead of with other markets (next section).

The time to raise this is while the launch is being planned. Building measurement into the plan costs little then; after launch it is often impossible.

## Comparing a market with its own history

**Year over year.** Easy to understand, partly controls for seasonality, and it is the standard language of boards and investors. But it cannot separate category growth (if the category grows 10% a year, year over year credits that growth to the campaign), one-off events from last year leak in, and it gives no measure of uncertainty.

**Before vs after.** Fast and intuitive. But it cannot tell seasonality from the campaign (if September is normally stronger than August, the seasonal rise looks like campaign lift), and it is the most exposed to anything else that changed at the same time.

**Trend and seasonality projection.** Decompose the history into trend, seasonality and remainder (STL, for example), project trend and seasonality forward as the "no campaign" line, and compare it with actuals. CausalImpact without control markets does much the same, with a Bayesian structural time-series model instead of STL.

**Earlier launches as a benchmark.** Compare the new launch with earlier ones aligned by weeks since launch, as console sales are often compared with the previous generation's; weighting several earlier launches applies the synthetic-control idea over time. Two cautions: this compares the campaign with past campaigns, not with no campaign, and pre-launch signals such as pre-orders or search interest are themselves moved by launch advertising, so matching on them hides part of the effect.

| Method | Quantifies uncertainty | Controls for seasonality and trend | Controls for other events at the same time |
|---|---|---|---|
| Year over year | No | Partly | No |
| Before vs after | No | No | No |
| Trend and seasonality projection | Yes (prediction interval) | Yes | No |

The limit is structural. Comparing markets cancels shocks that hit all of them at once; comparing a market with its own past cannot. It also assumes past patterns would have continued, which breaks when the market is changing (a new competitor, a maturing category). A holdout in even a few markets is stronger, and time-based methods are the fallback when that is impossible.

## Reporting to finance and executives

Show both numbers and reconcile them. Executives hear year over year first; it is their working language, and skipping it costs trust. Then bridge to the test result, for example: "Sales rose 15% year over year while the category grew 8%, so we outgrew the category by about 6.5% (1.15 / 1.08 − 1). The geo test attributes about 4 points of that to the campaign; the rest came from other changes, such as price or distribution." (Illustrative numbers.)

That bridge does most of the work: it explains the gap between the number people already know and the number they should act on.

## Effect patterns seen in practice

The three shapes in this repo's simulation were injected by design, to check that the method recovers effects of different shapes. They are inputs to the simulation, not evidence about real campaigns. Patterns commonly described in practice:

| Pattern | Typical context | Timing implication |
|---|---|---|
| A. Spike, then fast decay | Promotions, price-led offers, direct response, deadline-driven purchases | Concentrate spend just before the moment that matters |
| B. Slow build, then sustained | High-consideration purchases with long decision journeys: cars, appliances, insurance | Needs lead time: start earlier than the target date |
| C. Small but persistent | Brand and awareness campaigns; Binet & Field describe brand effects that build slowly and last for months or years | Sustain spend and judge it over months; a short post-period understates it |
| D. Pull-forward, then dip | Pantry loading in packaged-goods promotions; upgrades bought earlier than planned | The dip is borrowed demand being repaid, not ad wear-out (wear-out fades toward zero, not below it). Net lift = area above zero minus area below. Observe for at least one purchase cycle after the spike (weeks for groceries, months or more for durables), or lift is overstated |
| E. Delayed | Categories with long search and comparison | A short post-period misses the effect |

Why markets differ: media mix (TV-heavy markets often show longer carryover than digital-first ones), retail structure (a high e-commerce share means faster, easier-to-measure response; store-led retail spreads and delays it), and the length of the decision journey (longer journeys look more like B or E). Regional groupings are a starting point, not a conclusion: markets within one region can differ widely, so verify market by market.
