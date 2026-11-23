# POSTS — paste-ready. Nothing to invent at 8am.

Rules: image on every post · links go in the FIRST REPLY, never the post
body (X downranks outbound links) · every post is a reply to the pinned
teaser so the thread compounds · tag @AlpacaHQ @lablabai on teaser, video,
and finale only — elsewhere, reply to THEIR threads instead.

Card images: `python scripts/make_card.py --day N --symbol SPY --strike 505
--implied 31 --inferred 44 --equity 101200 --verdict "..." --line "..."`

---

## TEASER (post tonight, then PIN)

Every option price is a probability in disguise. This is what a probability
distribution read straight off an options chain looks like.

This week I'm entering the @AlpacaHQ × @lablabai AI Trading Agents Hackathon
with Pythia: an agent that computes this curve, forms its own view with
Claude, and trades only the disagreements — behind 8 risk gates.

Daily letters start tomorrow. Everything public, win or lose. 🧵

> reply 1: Repo (built solo, MIT): {github link}

---

## MON AM
Day 1. Pythia's biggest disagreement with the market this morning:

Market says {X}% that {SYM} closes above {K} on Friday. Pythia says {Y}%.

Position: {structure}. Max loss ${L} — known to the dollar before entry.
Grading this call publicly tomorrow.

## MON PM
Day 1 letter, written by the agent itself:

"{2-line excerpt}"

Equity ${E} ({±%}). {n} decisions journaled, {g} blocked by its own risk
gates. The blocked ones matter more than the taken ones.

## TUE AM
Grading yesterday: Pythia said {Y}%, market said {X}%. {SYM} closed
{above/below} {K}. {✓ / ✗ — and it costs nothing to say so.}

Today's disagreement: {new call}

## TUE PM
Day 2 letter. {catalyst} printed {..}; Pythia's read going in was {..}.
Equity ${E} ({±%}).

## WED AM — the educational thread (this one travels)
How to read a probability off an options chain, in 3 posts:

1/ A call spread that pays $1 if SPY closes above K costs some fraction of
$1. That fraction IS the market's probability. No model required.

2/ Formally: −∂C/∂K = Q(S_T > K). Breeden–Litzenberger, 1978. Every chain,
every day, is a full probability distribution hiding in plain sight.

3/ My hackathon agent computes this curve, asks Claude for an independent
estimate, and trades only the disagreements — behind 8 risk gates. This
morning's curve: {img}

## WED PM — the video
I recorded 2½ minutes of the agent working: the probability curve, the
divergence ledger, a risk gate blocking a bad trade, and me overriding it in
plain language through @AlpacaHQ's MCP server.

Built solo this week for the @lablabai hackathon. ⬇️
[native video upload]

## THU AM
{n} calls graded so far, {w} right. Brier score: Pythia {B1} vs market {B2}.
{One honest sentence about which is winning.}

This afternoon Pythia builds its payrolls book. The whole week comes down to
90 minutes tomorrow morning.

## THU PM
Submitted. Equity ${E} ({±%}), {n} trades, {g} orders blocked by its own
gates, {d} forecasts graded.

Going into tomorrow's payrolls print: {positions}. Deadline is 10am CT —
whatever the number is, it's the number.

## FRI — finale (quote-tweet the teaser, tag both hosts)
Payrolls: {number}. Pythia's final print: ${E} ({±%}).

{One honest sentence — win or lose. If it lost: "The gates did their job;
the forecast didn't. Both are in the journal."}

Every trade, every letter, every graded forecast, and the math:
{repo}

The options chain is a prediction market. Now you can read it too.

---

## REPLY-JACK TEMPLATE (your 72K-impression move — use daily)
On @lablabai / @AlpacaHQ hackathon threads:

"Solo entry here — Pythia reads the options chain as a prediction market
(−∂C/∂K = the market's probability), has Claude form an independent view,
and trades only the disagreements behind 8 risk gates. Today's curve: {img}"
