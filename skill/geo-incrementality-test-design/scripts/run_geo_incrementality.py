#!/usr/bin/env python3
"""
run_geo_incrementality.py — Geo-incrementality analysis on real panel data.

Input: long-format CSV with one row per (unit, period), e.g.
    country,week,sales
    US,1,120000
    DE,1,41000
    ...

Usage:
    python run_geo_incrementality.py --data panel.csv \
        --unit-col country --period-col week --outcome-col sales \
        --treated US --intervention 22 \
        [--exclude IN DE] [--no-placebo] [--out-prefix results/us_test]

Notes:
- One treated unit per run. If several units were treated, analyze one at a
  time and pass the others via --exclude so they never enter the donor pool.
- --intervention is the first period AFTER the campaign started (pre-period
  is strictly before this value).
- Periods can be integers (e.g. a week index) or dates (YYYY-MM-DD).
Dependencies: pandas, numpy, scipy, matplotlib.
"""

import argparse
import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---------------------------------------------------------------- core math
def fit_weights(y_pre: np.ndarray, X_pre: np.ndarray):
    """Constrained least squares: w >= 0, sum(w) = 1 (Abadie-style SCM).

    Data is rescaled and an analytic gradient supplied — without both, SLSQP
    can silently fail to move on large-magnitude outcomes.
    """
    scale = y_pre.mean()
    ys, Xs = y_pre / scale, X_pre / scale
    n = Xs.shape[1]

    def loss(w):
        r = ys - Xs @ w
        return r @ r

    def grad(w):
        r = ys - Xs @ w
        return -2.0 * Xs.T @ r

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0,
             "jac": lambda w: np.ones(n)}]
    res = minimize(loss, np.full(n, 1.0 / n), jac=grad, method="SLSQP",
                   bounds=[(0.0, 1.0)] * n, constraints=cons,
                   options={"maxiter": 500, "ftol": 1e-12})
    return res.x, bool(res.success)


def synth_analysis(pivot: pd.DataFrame, target: str, donors: list, pre: np.ndarray):
    y = pivot[target].to_numpy(dtype=float)
    X = pivot[donors].to_numpy(dtype=float)
    w, ok = fit_weights(y[pre], X[pre])
    synth = X @ w
    resid_pre = y[pre] - synth[pre]
    resid_post = y[~pre] - synth[~pre]
    pre_rmspe = float(np.sqrt(np.mean(resid_pre ** 2)))
    post_rmspe = float(np.sqrt(np.mean(resid_post ** 2)))
    effect_series = (y[~pre] - synth[~pre]) / synth[~pre]
    return {
        "weights": pd.Series(w, index=donors).sort_values(ascending=False),
        "y": y, "synth": synth, "converged": ok,
        "pre_mape": float(np.mean(np.abs(resid_pre / y[pre]))),
        "pre_rmspe": pre_rmspe,
        "rmspe_ratio": post_rmspe / pre_rmspe if pre_rmspe > 0 else np.inf,
        "avg_effect": float(effect_series.mean()),
    }


# ---------------------------------------------------------------- helpers
def parse_periods(series: pd.Series):
    """Return a sortable representation of the period column."""
    try:
        return pd.to_numeric(series)
    except (ValueError, TypeError):
        pass
    try:
        return pd.to_datetime(series)
    except (ValueError, TypeError):
        print("[warn] period column is neither numeric nor datetime; "
              "falling back to lexicographic order.")
        return series.astype(str)


def parse_intervention(raw: str, periods: pd.Series):
    if pd.api.types.is_numeric_dtype(periods):
        return float(raw)
    if pd.api.types.is_datetime64_any_dtype(periods):
        return pd.to_datetime(raw)
    return str(raw)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--unit-col", required=True)
    ap.add_argument("--period-col", required=True)
    ap.add_argument("--outcome-col", required=True)
    ap.add_argument("--treated", required=True)
    ap.add_argument("--intervention", required=True,
                    help="first period AFTER campaign start (pre < this)")
    ap.add_argument("--exclude", nargs="*", default=[],
                    help="units to drop from donor pool (e.g. other treated units)")
    ap.add_argument("--no-placebo", action="store_true")
    ap.add_argument("--power", action="store_true",
                    help="simulate power curve / MDE from placebo noise")
    ap.add_argument("--alpha", type=float, default=0.10,
                    help="rank-p threshold counted as 'detected' (default 0.10)")
    ap.add_argument("--power-target", type=float, default=0.80)
    ap.add_argument("--out-prefix", default="geo_incrementality")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    for c in (args.unit_col, args.period_col, args.outcome_col):
        if c not in df.columns:
            sys.exit(f"[error] column '{c}' not found. Available: {list(df.columns)}")

    df = df[[args.unit_col, args.period_col, args.outcome_col]].copy()
    df[args.period_col] = parse_periods(df[args.period_col])
    if df[args.outcome_col].isna().any():
        sys.exit("[error] outcome column contains missing values — fix upstream.")

    pivot = df.pivot_table(index=args.period_col, columns=args.unit_col,
                           values=args.outcome_col).sort_index()
    if pivot.isna().any().any():
        bad = pivot.columns[pivot.isna().any()].tolist()
        sys.exit(f"[error] unbalanced panel — units with missing periods: {bad}")

    if args.treated not in pivot.columns:
        sys.exit(f"[error] treated unit '{args.treated}' not in data.")
    donors = [u for u in pivot.columns
              if u != args.treated and u not in set(args.exclude)]
    if len(donors) < 4:
        sys.exit(f"[error] only {len(donors)} donors — too few for a credible "
                 "comparison or placebo inference.")

    cutoff = parse_intervention(args.intervention, pivot.index.to_series())
    pre = np.asarray(pivot.index < cutoff)
    n_pre, n_post = int(pre.sum()), int((~pre).sum())
    if n_post == 0:
        sys.exit("[error] no post-intervention periods found.")
    if n_pre < 20:
        print(f"[warn] only {n_pre} pre-periods — weights may overfit; "
              "interpret with caution (aim for 20+, ideally 52+).")

    # convex-hull proxy check on pre-period means
    t_mean = pivot[args.treated][pre].mean()
    d_means = pivot[donors][pre].mean()
    if not (d_means.min() <= t_mean <= d_means.max()):
        print(f"[warn] treated pre-period mean ({t_mean:,.0f}) lies OUTSIDE the "
              f"donor range ({d_means.min():,.0f}–{d_means.max():,.0f}). "
              "A convex combination cannot reproduce it — expect poor fit. "
              "Add comparably-sized donors or rescale (e.g. per-capita).")

    res = synth_analysis(pivot, args.treated, donors, pre)

    print(f"\n=== Geo-incrementality: {args.treated} "
          f"(pre={n_pre}, post={n_post}, donors={len(donors)}) ===")
    if not res["converged"]:
        print("[warn] optimizer did not converge — results unreliable.")
    print(f"Pre-period fit MAPE : {res['pre_mape']:.2%}"
          + ("   [warn: >5% — post-period numbers are NOT interpretable; "
             "fix the comparison group first]" if res["pre_mape"] > 0.05 else ""))
    top_w = res["weights"].iloc[0]
    print(f"Top donor weights   : "
          + ", ".join(f"{u}={w:.2f}" for u, w in res["weights"].head(5).items())
          + ("   [warn: corner solution — donor pool likely inadequate]"
             if top_w > 0.8 else ""))
    print(f"Avg post effect     : {res['avg_effect']:+.2%}  (estimate, not truth)")

    # ---------------- placebo inference (Abadie-style rank test) ----------
    if not args.no_placebo:
        ratios, effects, pre_fits = {}, {}, {}
        for d in donors:
            pool = [x for x in donors if x != d]
            r = synth_analysis(pivot, d, pool, pre)
            ratios[d], effects[d], pre_fits[d] = (
                r["rmspe_ratio"], r["avg_effect"], r["pre_mape"])

        j = len(donors)
        rank_all = 1 + sum(v >= res["rmspe_ratio"] for v in ratios.values())
        p_all = rank_all / (j + 1)
        # Adaptation of Abadie et al. (2010)'s pre-fit filter: the original
        # drops placebos whose pre-period MSPE exceeds 20x, 5x or 2x the
        # treated unit's (fine when all units share one scale, e.g. per-capita
        # sales). With heterogeneous unit sizes we filter on pre-MAPE
        # (scale-free) at 5x instead, which is looser than 5x MSPE (about 2.2x
        # on a linear error).
        kept = {d: v for d, v in ratios.items()
                if pre_fits[d] <= 5 * res["pre_mape"]}
        rank_f = 1 + sum(v >= res["rmspe_ratio"] for v in kept.values())
        p_filt = rank_f / (len(kept) + 1)
        dropped = sorted(set(donors) - set(kept))
        if dropped:
            print(f"\n[note] placebo units dropped by 5x pre-MAPE filter "
                  f"(poor fit, would distort noise dist): {dropped}")

        print(f"\nPlacebo test (post/pre RMSPE ratio, higher = more unusual)")
        print(f"  treated ratio     : {res['rmspe_ratio']:.2f}")
        print(f"  rank among all    : {rank_all}/{j + 1}  ->  p ~ {p_all:.3f}")
        print(f"  rank (5x pre-fit filter, n={len(kept)}) ->  p ~ {p_filt:.3f}")
        print(f"  note: with {j} donors the smallest attainable p is "
              f"{1 / (j + 1):.3f} — agree on this resolution limit up front.")
        print(f"  placebo avg effects range: "
              f"{min(effects.values()):+.2%} … {max(effects.values()):+.2%}")

        # ---------------- power / MDE simulation --------------------------
        if args.power:
            rng = np.random.default_rng(0)
            # use the same 5x pre-fit filter as inference: badly-fit placebos
            # produce absurd pseudo-effects that would wreck the noise dist.
            noise = np.array([effects[d] for d in kept])
            abs_noise = np.abs(noise)
            jj = len(kept)
            floor = 1.0 / (jj + 1)
            if args.alpha < floor:
                print(f"[warn] alpha={args.alpha} is below the attainable "
                      f"floor {floor:.3f} with {jj} usable donors — power "
                      "will be 0. Raise alpha or add donors.")
            grid = np.arange(0.01, 0.21, 0.01)
            n_sim = 2000
            print(f"\nPower simulation (alpha={args.alpha}, "
                  f"{n_sim} draws per effect size, filtered placebo noise, "
                  f"n={jj})")
            mde = None
            for e in grid:
                obs = np.abs(rng.choice(noise, n_sim) + e)
                ranks = 1 + (abs_noise[None, :] >= obs[:, None]).sum(axis=1)
                power = float(np.mean(ranks / (jj + 1) <= args.alpha))
                marker = ""
                if mde is None and power >= args.power_target:
                    mde, marker = e, f"   <-- MDE at {args.power_target:.0%} power"
                if round(e, 2) in (0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.20) or marker:
                    print(f"  effect {e:>5.0%}: power {power:5.1%}{marker}")
            if mde is None:
                print(f"  [warn] no effect size up to 20% reaches "
                      f"{args.power_target:.0%} power — this design cannot "
                      "reliably detect realistic effects; redesign needed.")

    # ---------------- chart ----------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(pivot.index, res["y"], label=f"{args.treated} (actual)", lw=2)
    ax.plot(pivot.index, res["synth"], "--", label="synthetic control")
    ax.axvline(cutoff, color="gray", ls=":", label="intervention")
    ax.set_title(f"{args.treated}: actual vs synthetic control")
    ax.set_xlabel(args.period_col); ax.set_ylabel(args.outcome_col)
    ax.legend(); fig.tight_layout()
    out_png = f"{args.out_prefix}_{args.treated}.png"
    fig.savefig(out_png, dpi=150)
    print(f"\nChart saved: {out_png}")


if __name__ == "__main__":
    main()
