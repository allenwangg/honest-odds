# PLAYBOOK — every non-code artifact of the week, pre-written

Trading code is frozen. This file is the other half of winning: the video you
record Wednesday, the 12 posts you publish, the submission copy you paste, and
the Discord messages you send. Fill the {braces} with live numbers and ship.

---

## 1. Demo video script (2:30, word for word)

**Shot list:** (1) cover image 3s → (2) implied-curve PNG → (3) dashboard full
→ (4) zoom on one ledger rail → (5) log line of a gate block → (6) Claude
window with MCP prompt → (7) a fund letter → (8) terminal: snapshot.py +
calibrate.py → (9) end card: cover + repo link. Record with QuickTime/Loom,
voice over screen. One take is fine; honest beats polished.

**[0:00 — cover]** "Every option price is a probability in disguise. Line up
the calls on SPY, take the slope of price against strike, and you get this —
the market's live probability distribution for where SPY closes on Friday.
Which means the options chain is a prediction market. I built an agent that
reads it."

**[0:15 — curve]** "This curve is P of SPY closing above each strike, computed
straight from call prices. No model, just no-arbitrage. A tight call spread
around a strike *is* a binary bet on that event, and its price over its width
is the market's quote — under the risk-neutral measure this is exact; it's
Breeden–Litzenberger, 1978. My agent, Pythia, computes its own probability for the
same events — Claude, prompted as a calibrated superforecaster that treats the
market's number as its prior — and trades only when they disagree by enough."

**[0:40 — dashboard]** "This is the divergence ledger. Slate diamond: the
market's probability. Gold dot: Pythia's. The gold bar between them is the
edge. Here — the market said {X}% above {K} by Friday. Pythia said {Y}% with
{C}% confidence, so it bought the {K1}/{K2} call spread, sized Kelly-lite,
max loss defined to the dollar before entry."

**[1:20 — gate block]** "Every trade passes eight dumb gates: defined-risk
only, budget caps, a daily circuit breaker, liquidity checks, a kill file.
Dumb on purpose — the LLM can be wrong; the gates can't be argued with.
Here's one blocking a trade where the fill price would have eaten the edge."

**[1:45 — MCP]** "Execution runs on the Alpaca Trading API — atomic multi-leg
limit orders. Supervision runs on Alpaca's MCP server: same account, and I
can interrogate or override the agent in plain language. 'Close the SPY
spread — I disagree with today's thesis.'"

**[2:05 — receipts]** "Every decision is journaled. Every night Claude writes
the fund letter. And every forecast gets graded when it resolves — across {N}
resolved events this week, Pythia's Brier score was {B1} against the market's
{B2}. Final P&L: {Z}. The chain talks. Pythia listens, disagrees carefully,
and writes everything down."

---

## 2. Social calendar — 12 posts, pre-drafted (X primary; mirror to LinkedIn)

Rules: one image per post, native video for clips, links in the FIRST REPLY
(not the post). Master thread: every post replies to the teaser. Tag
@AlpacaHQ @lablabai on the teaser, the video, and the finale only — reply to
*their* threads for the rest (your proven 72K-impression move).

**T0 — Tonight (teaser, becomes your pinned post):**
"Every option price is a probability in disguise. This is SPY's probability
distribution for Friday — read straight off the options chain. This week I'm
entering the @AlpacaHQ × @lablabai AI Trading Agents Hackathon with Pythia:
an agent that computes this curve, forms its own view, and trades only the
disagreements. Daily letters start Monday. Everything public, win or lose. 🧵"
[image: cover]

**Mon AM:** "Day 1. The market's curve this morning: {curve img}. Pythia's
biggest disagreement: market says {X}% that {SYM} closes above {K} Friday.
Pythia says {Y}%. Position: {structure}, max loss ${L} — known before entry."

**Mon PM:** "Day 1 letter. {2-line excerpt}. Equity: ${E} ({±%}). Every
decision journaled — grading this call tomorrow, publicly." [image: ledger]

**Tue AM:** "Grading yesterday: said {Y}%, market said {X}% — {SYM} closed
{above/below} {K}. {✓/✗}. Today's disagreement: {new call}." 

**Tue PM:** "Day 2 letter. ISM printed {..}; Pythia's read going in was {..}.
{result}. Equity ${E}." 

**Wed AM:** "Scoreboard so far: {n} calls, {w} right. Brier: Pythia {B1} vs
market {B2}. Today's disagreement: {call}."

**Wed PM:** "I recorded 2½ minutes of the agent working — the probability
curve, the divergence ledger, a risk gate blocking a bad trade, and Claude
overriding it by voice^H^Hchat. Video: ⬇️" [native video] (tag hosts)

**Thu AM:** "Grading + today's card: {call}. This afternoon Pythia builds its
NFP book — the whole week comes down to 90 minutes tomorrow morning."

**Thu PM:** "Submitted. Equity ${E} ({±%}), {n} trades, {g} orders blocked by
its own gates. Tomorrow 8:30am ET: nonfarm payrolls, then judgment at 10.
The book going in: {positions}." [image: dashboard]

**Fri (the finale, quote-tweet the teaser, tag hosts):** "NFP: {number}.
Pythia's final print: ${E} ({±%}) — {one honest sentence, win or lose}.
Every trade, every letter, every graded forecast: {repo}. The options chain
is a prediction market. Now you can read it too."

**Wed AM alternative (the educational thread — these travel farthest):**
"How to read a probability off an options chain, in 3 posts:
1/ A call spread that pays $1 if SPY closes above K costs some fraction of
$1. That fraction IS the market's probability. No model required.
2/ Formally: −∂C/∂K = Q(S_T > K). Breeden–Litzenberger, 1978. Every chain,
every day, is a full probability distribution hiding in plain sight.
3/ My hackathon agent computes this curve, asks Claude for an independent
estimate, and trades only the disagreements — behind 8 risk gates. Curve as
of this morning: {img}" 

**Anytime spare:** reply to lablab's hackathon thread with the day's curve.

---

## 3. lablab submission copy (paste-ready)

**Title:** Pythia — the options chain is a prediction market
**Tagline:** An AI agent that reads market-implied probabilities off the
options chain, forms its own with Claude, and trades the disagreement —
behind eight risk gates.
**Description:** Under no-arbitrage, P(S closes above K) is the negative
slope of the call-price curve — so every options chain is a live prediction
market. Pythia computes that curve each cycle, has Claude form independent,
calibrated probabilities for the same events (market prior first, deviation
must be argued), and expresses only the large disagreements as defined-risk
debit spreads, Kelly-lite sized. Eight non-negotiable gates sit between every
plan and the exchange; every decision — traded, skipped, or blocked — is
journaled with its thesis; Claude writes the nightly fund letter; and every
forecast is Brier-scored against the market when it resolves. Execution:
Alpaca Trading API (atomic MLEG orders). Supervision: Alpaca MCP server, so
a human can interrogate or override the agent in plain language. Built solo
in a week; `python run.py --selftest` runs the entire pipeline offline in
one command.

---

## 4. Discord messages

**Intro (build channel):** "Solo entry: Pythia — it treats the options chain
as a prediction market (P(S>K) = −dC/dK from call mids), has Claude form its
own probabilities, and trades the disagreements as debit spreads behind 8
risk gates. Daily fund letters + graded forecasts all week here + on X:
{handle}. Curve as of tonight: {image}"

**Questions for organizers:** "Two quick rule checks: (1) can one team win a
podium prize *and* a Social Engagement Award, or one prize max per team?
(2) is there an official hashtag you're tracking for the engagement awards?"

---

## 5. Daily 15-minute ops loop (so nothing gets dropped)

Morning (8:25 CT): glance dashboard → post AM card → check tmux alive.
Close (3:05 CT): `--letter` → post PM letter → mirror to LinkedIn/blog →
share in Discord → `calibrate.py` (from Tue) → update macro.md for tomorrow.
That's the whole engagement machine: 15 min, twice a day, six days.
