# VIDEO SCRIPTS — four versions, all narration-ready

Record with **Cmd + Shift + 5** (Mac screen recorder). No camera, no editing.
Read the bold-free text aloud while doing what the [brackets] say. Numbers in
{braces} come from `scripts/morning.py` or `scripts/snapshot.py`.

Pace: about 150 words per minute. Don't rush the pauses — silence while a
chart is on screen reads as confidence.

Before recording: close Slack/Mail, hide your bookmarks bar, set Terminal
font to 18pt (Terminal → Settings → Profiles → Font), and put the dashboard
and a Terminal window side by side.

---
---

# VERSION 1 — THE SUBMISSION (2:30)
*For the lablab judges. This is the one that matters most.*

**[0:00 — cover image full screen]**

Every option price is a probability in disguise.

If a contract pays one dollar when SPY closes above 505, and it trades at
31 cents, the market just told you it thinks there's a 31 percent chance.
Nobody publishes that number. It's hidden inside the price.

**[0:18 — the curve chart]**

Do that across every strike and you get this — the market's full probability
distribution for where SPY closes on Friday. Read straight off the chain, no
model required. It's Breeden-Litzenberger, 1978.

Which means the options chain is a prediction market that's been quoting
probabilities all along. I built an agent that reads it.

**[0:40 — dashboard, full window]**

This is Pythia. Every fifteen minutes it computes that curve, then asks
Claude for an independent estimate of the same probabilities — prompted as a
calibrated forecaster that treats the market's number as its prior and has to
argue before deviating.

**[0:58 — zoom into one divergence rail]**

This is the divergence ledger. Slate diamond, the market. Gold dot, Pythia.
The bar between them is the disagreement.

Here the market said {X} percent that {SYM} closes above {K}. Pythia said
{Y} percent. That's a {E}-point gap, so it bought the {K1}/{K2} debit
spread — a defined-risk structure whose maximum loss, {L} dollars, was known
before the order went out.

**[1:25 — Terminal, scroll the log to a blocked trade]**

Every trade passes eight gates before it exists. Defined risk only. Budget
caps. A daily circuit breaker. Liquidity checks. A kill file. Here's one
blocking a trade because the fill price would have eaten the edge.

The gates contain no model and no LLM. That's deliberate — the intelligence
upstream can be wrong. The gates can't be argued with.

**[1:50 — Claude window with the Alpaca MCP server]**

Execution runs on the Alpaca Trading API — atomic multi-leg limit orders.
Supervision runs on Alpaca's MCP server, same account, so I can interrogate
or override the agent in plain language.

[type] "Close the SPY spread — I disagree with today's thesis."

**[2:10 — a fund letter, then the calibration output]**

Every decision is journaled with its reasoning. Every night Claude writes the
fund letter. And every forecast gets graded when it resolves — across {N}
resolved events this week, Pythia's Brier score was {B1} against the market's
{B2}.

**[2:25 — end card]**

Final result: {Z}. Built solo. The chain talks. Pythia listens, disagrees
carefully, and writes everything down.

---
---

# VERSION 2 — THE YOUTUBE EXPLAINER (6:00)
*For your channel and for X. This is the one that can travel.*
*Title: "The options market has been telling you the odds this whole time"*

**[0:00 — cover]**

I'm going to show you something hiding in plain sight in financial markets,
and by the end of this video you'll be able to read it yourself.

**[0:10 — blank/curve]**

Here's the setup. An option is a contract that pays off if a stock ends up
past a certain price by a certain date. They trade all day, publicly, on
every major stock.

Now imagine a very specific bet: I'll pay you one dollar if SPY closes above
505 dollars this Friday, and nothing otherwise. What's that bet worth today?

Obviously it depends on the odds. If it's nearly certain, it's worth almost a
dollar. If it's nearly impossible, almost nothing. If it's a coin flip, about
fifty cents.

So the price *is* the probability. That's not an analogy — it's the same
number wearing a different hat.

**[0:50 — show two option quotes side by side]**

Here's the part that surprises people. That bet already exists. If you buy
the 505 call and sell the 506 call, you've built something that pays about a
dollar if SPY finishes above 505, and nothing if it finishes below. Costs you
31 cents today. The market is quoting 31 percent.

Do that at every strike, and you don't just get one probability — you get all
of them.

**[1:25 — the curve, drawn]**

That's this. The market's complete probability distribution for Friday's
close. It's free. It updates every second. Almost nobody looks at it.

The formal version: the derivative of the call price with respect to strike
gives you the probability of finishing above that strike. Breeden and
Litzenberger published it in 1978. It's not exotic — it's plumbing.

**[1:55 — dashboard]**

So here's what I built with it, for a trading agent hackathon.

The agent computes that curve every fifteen minutes. Then it asks Claude the
same question independently: what's the probability SPY closes above 505 on
Friday? With one rule — the market's number is your starting point, and you
have to justify moving away from it.

Most of the time they roughly agree, and nothing happens. That's the correct
outcome and it's most of the day.

**[2:35 — a divergence rail]**

Sometimes they don't. Market says 31, Claude says 44. That thirteen-point gap
is the entire strategy. Buy the thing that pays if Claude's right, in a size
where being wrong costs a known, small amount.

**[3:00 — risk gates in the log]**

Which brings up the part people skip, and it's the part that actually matters.

Being right about probability doesn't make you money if you size wrong. So
between the idea and the exchange sit eight rules. Loss must be capped
structurally. No trade risks more than a fixed slice of the account. Total
exposure has a ceiling. A bad enough day halts trading entirely. Illiquid
contracts are refused. And a file named KILL stops everything instantly.

None of those rules contain any AI. That's the point. The smart part can be
wrong; the dumb part can't be talked into anything.

**[3:50 — parity check / stale quote]**

One more, because it's my favorite. Free market data goes stale, and stale
prices create fake opportunities — the agent thinks it found an edge, but
it's really just looking at an old quote.

There's a relationship called put-call parity that has to hold on any live
chain. When it breaks by more than pennies, the data is lying. The agent
checks that every cycle and refuses to trade a chain that fails it.

**[4:25 — calibration output]**

And here's the honest part. Every prediction the agent makes gets written
down, and when the date arrives, it gets graded — against reality, and
against what the market thought at the same moment.

That's a Brier score. It's a scoring rule you can't game: the only way to
score well is to actually report what you believe. Across {N} predictions
this week: Pythia {B1}, the market {B2}. {Sentence about who won.}

Most trading content never shows you this. It shows the wins.

**[5:05 — dashboard wide]**

The whole thing runs on Alpaca's paper trading API — fake money, real prices.
Claude does the forecasting. Eight rules do the disciplining. And every night
it writes a letter explaining what it did and what it cost.

**[5:30 — end card]**

Result so far: {Z}. Every trade, every letter, and every graded forecast is
public — repo's linked below.

If you take one thing from this: the options market has been publishing
probabilities this entire time. You just have to know it's a chart.

---
---

# VERSION 3 — THE SHORT (55 seconds)
*Vertical. For Shorts, Reels, TikTok, and X video.*
*Hook must land in 3 seconds or it's dead.*

**[0:00 — curve, hard cut, no intro]**

This chart is free, updates every second, and almost nobody looks at it.

**[0:04]**

It's the stock market's own probability forecast — where the S&P ends up
this Friday, according to everyone trading it right now.

**[0:12]**

Here's where it comes from. Options are bets that pay off past a certain
price. Buy one, sell the next one up, and you've built a contract that pays a
dollar if the stock finishes above that level.

**[0:24]**

If that costs 31 cents — the market thinks there's a 31 percent chance.
Price is probability. Do it at every strike and you get the whole curve.

**[0:34 — dashboard]**

So I built an agent that reads this curve, asks an AI what *it* thinks the
odds are, and bets only when they disagree.

**[0:44 — divergence rail]**

Market said 31. My agent said 44. That gap is the trade — behind eight rules
that cap what it can lose before it's allowed to click buy.

**[0:52]**

Running it live this week. Everything public.

---
---

# VERSION 4 — THE DAILY BUILD LOG (90 seconds, reusable)
*Record one each evening. Same shape, new numbers. This is what wins the
engagement award — serial beats spectacular.*

**[0:00 — dashboard]**

Day {N} of running an AI options agent in public.

**[0:06]**

Yesterday it said {Y} percent that {SYM} would close above {K}. The market
said {X}. {SYM} closed at {CLOSE} — so that call was {right/wrong}.

{One sentence of honest reaction. If wrong: say what it missed. Do not
spin it.}

**[0:25 — today's curve]**

Today's biggest disagreement: {new call}. It's holding {structure}, and the
most it can lose on that is {L} dollars — decided before entry, not after.

**[0:45 — gates or journal]**

{One interesting thing that happened today: a gate that blocked something, a
position it banked, a chain it refused as stale.}

**[1:05]**

Balance: {E}. That's {±%} since Monday.

**[1:15 — end card]**

Grading today's call tomorrow. Repo and the full journal are public — link
below.

---
---

# TITLES & DESCRIPTIONS

**YouTube titles (pick by feel):**
- The options market has been telling you the odds this whole time
- I built an AI that trades against the market's own probabilities
- There's a free probability forecast hiding in the options chain
- Reading the market's mind with 1978 math and an AI

**Description block (paste under any version):**

> Options prices contain probabilities. The slope of the call-price curve
> across strikes gives you P(stock closes above K) — Breeden-Litzenberger,
> 1978. So the options chain is a prediction market that quotes odds all day.
>
> Pythia computes that curve, asks Claude for an independent estimate of the
> same probabilities, and trades only the disagreements — as defined-risk
> debit spreads, behind eight risk gates, with every forecast graded by Brier
> score when it resolves.
>
> Built solo for the Alpaca AI Trading Agents Hackathon. Paper trading only,
> not investment advice.
>
> Code: https://github.com/allenwangg/pythia
>
> 0:00 The hidden number
> 1:25 The whole curve
> 1:55 What I built
> 3:00 Why the boring rules matter
> 4:25 Grading the forecasts

**Tags:** options trading, prediction markets, quantitative finance, AI
agents, Claude, algorithmic trading, implied probability, Alpaca

---

# RECORDING CHECKLIST

- [ ] Dashboard open, market hours, real numbers on screen
- [ ] Terminal font 18pt, window clean
- [ ] Notifications off (Do Not Disturb)
- [ ] Cmd+Shift+5 → "Record Selected Portion" → drag over the window
- [ ] Read the script out loud once before recording (fixes 90% of stumbles)
- [ ] One take. Small stumbles are fine — they read as real.
- [ ] Upload to YouTube unlisted, test the link logged out, paste into lablab
