# Research context — where Pythia sits, and what it would take to make it a result

*Written Nov 2026. Every paper below was read at the linked page; numbers are quoted from
those pages. Pythia's own numbers come from `scripts/robustness.py`.*

## The question

Can a language model produce probabilities about real, unresolved events that beat a
strong, liquid benchmark, and does it say what it actually believes when it does? That is a
capability question (forecasting) and an honesty question (calibration) at once.

## What the field has found, 2024–2026

| Work | Benchmark | Finding |
|---|---|---|
| Halawi, Zhang, Chen, Steinhardt — [*Approaching Human-Level Forecasting with Language Models*](https://arxiv.org/abs/2402.18563) (2024) | Competitive-forecaster crowd | A retrieval system "nears the crowd aggregate of competitive forecasters, and in some settings surpasses it." |
| Karger, Chen, Halawi et al. — [*ForecastBench*](https://arxiv.org/abs/2409.19839) (2024) | Superforecasters, live questions | Experts beat the best LLM (p < 0.001): median Brier 0.096 vs 0.122 for the top model. |
| Forecasting Research Institute — [*AI models have likely reached parity with superforecasters on ForecastBench*](https://forecastingresearch.substack.com/p/ai-models-have-likely-reached-parity) (Jul 2026) | Same | Several models are now statistically indistinguishable from superforecasters, though the superforecaster baseline is from 2024 and partly extrapolated. |
| Metaculus — [*AI Forecasting in 2026: What 11 Analyses Say*](https://forum.effectivealtruism.org/posts/Spyz3wESZu2eeqhDj/ai-forecasting-in-2026-what-11-analyses-say) (2026) | Pro forecasters, live tournament | "The Pro team has beaten the bot team in every comparison to date"; many parity claims rest on backtests with possible leakage. |
| Lu — [*Evaluating LLMs on Real-World Forecasting Against Expert Forecasters*](https://arxiv.org/abs/2507.04562) (2025) | Metaculus experts | o3 Brier 0.1352 vs expert median 0.0225 on 157 questions. |
| Nel — [*Do LLMs Know What They Don't Know? Epistemic Calibration via Prediction Markets*](https://arxiv.org/abs/2512.16030) (2025) | Kalshi, 300 questions | All five frontier models miscalibrated; ECE 0.120 (Claude Opus 4.5, best) to 0.395; only Claude Opus 4.5 had positive Brier skill. |
| Ye, Dineen, Zhu et al. — [*Hindcast: Replaying Prediction Markets to Evaluate LLM Forecasters*](https://arxiv.org/abs/2607.14051) (2026) | Polymarket price at matched time | Retrieval lowers Brier for 8 of 9 models; the paper's central problem is answer leakage in replayed tests. |
| Li, Li, Cong — [*Can LLMs Predict the Future? A Brier Score Analysis of Prediction Markets*](https://arxiv.org/abs/2609.32885) (2026) | Base-rate predictor | Post-cutoff, Claude models score 0.183–0.192; newer or larger tiers "do not consistently produce more accurate probabilities." |
| Bhaskara, Gupta, Yeon — [*Approximate Recall, Approximate Forecasts*](https://arxiv.org/abs/2611.10891) (2026) | — | The strongest predictor of worse forecasts is confident-but-wrong recall of relevant facts. |

Two Anthropic papers frame the honesty side: Kadavath et al., [*Language Models (Mostly)
Know What They Know*](https://arxiv.org/abs/2207.05221) (2022) on calibration of model
confidence, and Sharma et al., [*Towards Understanding Sycophancy in Language
Models*](https://arxiv.org/abs/2310.13548) (2023) on models shifting answers toward what
the user appears to want.

**Three open problems recur:** (1) leakage, because backtests let the model "know" the
answer; (2) weak or stale benchmarks, because a base rate or a thin market is easy to beat;
(3) sample size, because forecasts that resolve together are not independent.

## What Pythia adds

1. **Leakage-free by construction.** Every probability was written to
   `journal/decisions.jsonl` with a timestamp before the event resolved, about closes
   hours or a day away, which no training data can contain. No replay, no retrieval of
   future text.
2. **The strongest benchmark available on a 1-day horizon.** The comparison is the
   risk-neutral probability read off the SPY/QQQ option chains at the same minute,
   one of the most liquid markets there is, not a base rate or a forecasting crowd.
3. **A concrete case of benchmark quality manufacturing an edge.** Four stale 0DTE quotes
   moved the result from −44% to −72% Brier. The model flagged them as stale in its own
   rationale before the close, which is itself a small honesty result: it said it was
   disagreeing with bad data, not claiming to out-forecast the market. This is problem (2)
   above in a measurable form, and it is why CALIBRATION.md reports both numbers.
4. **A directional asymmetry worth testing.** Pythia scored 90% better than the chain when
   more bullish and 11% worse when more bearish (16 forecasts each side, one up week). If
   it holds, it is a systematic bias, and the trading filter was pointed at it.

## What it does not show yet

On the 6 independent symbol-day clusters left after cleaning, the unweighted mean
per-cluster Brier difference is −0.0025 with a standard deviation of 0.044. Most of the
pooled gap comes from far-from-the-money strikes, where chain mid-prices are noisy. The
current evidence is consistent with a modest edge and with none.

## Pre-registered next experiments

Each of these is a design, not a result. None has been run.

**E1. Enough clusters to answer the question.** Using the observed cluster s.d. of 0.044
(rough, from 6 clusters), detecting a true per-cluster improvement of 0.01 Brier at 80%
power and two-sided α = 0.05 needs about **150 symbol-days**, roughly 15 trading weeks of
SPY + QQQ. An improvement of 0.02 needs about 38. Run forward, no backtests.

**E2. Fix the benchmark before scoring.** Pre-register a quote-quality filter applied
before outcomes are known: drop strikes whose implied curve violates monotonicity or whose
bid–ask width exceeds a set fraction of the price. Score wing strikes against the bid and
ask (the price you could actually trade), not the mid.

**E3. Calibration under pushback.** For each logged forecast, re-ask the same question with
a user message that pushes back ("the options market says 60%, are you sure?") and with a
neutral control. Measure the shift in stated probability and the change in Brier. A model
that moves toward the pushback without new information, and gets worse for it, is showing
sycophancy in a setting with a proper scoring rule and a ground truth. This connects the
Pythia data directly to the Sharma et al. line of work.

**E4. Test the bearish asymmetry out of sample.** Fix the hypothesis now ("Pythia's bearish
disagreements score worse than the chain"), then test it on E1's data only.
