# FRIDAY — the last day. One card. Every decision already made.

Deadline **10:00am CT, Fri Sep 4**. Account PA3C8Y75G64Y. Week closed ~+6.8%.

## THE TRADING DECISION IS MADE: SIT.

Do NOT run `config.event.yaml`. Do NOT trade the open. Do NOT restart the loop.
Above +2% equity the Monte Carlo (40k sims, 120-entry field, scored on all four
judging criteria) puts flat at ~77% podium and trading at ~40%. You are
defending a number, not hunting one. Payrolls prints at 7:30 — you will want to
have an opinion about it. Having one is fine. Acting on it is the one move that
can still cost you the week.

If the urge is strong: `touch KILL` and read journal/letters/. That is what the
kill switch is for, and using it is not an admission of anything.

## LAST NIGHT (do first if `pythia_afternoon.sh report` never ran)

    cd ~/Downloads/pythia && bash pythia_afternoon.sh report

Letter, snapshot, calibration, Friday verdict, and both posts pre-filled.
Nothing below can be finished without its output.

## THE MORNING

  7:30  payrolls prints. Watch it or don't. Trade nothing either way.
  9:00  fix the two soft spots in WRITEUP.md (see below), commit, push.
  9:45  `python3 scripts/snapshot.py`  -> the FINAL number
  9:50  paste finals into the lablab form. Submit. Screenshot the confirmation.
 10:00  DEADLINE. Post the finale, quote the pinned teaser, tag the hosts.

## TWO THINGS IN WRITEUP.md THAT ARE STILL WRONG

1. **Line ~79** cites `Thu 9:42am CT: $107,132, +7.1%`. That is an INTRADAY MARK,
   not a close. This is the same error already caught once for Wednesday
   ($109,333 was a 2:45pm mark, never a close). Replace it with Thursday's
   actual close from the snapshot, and say "close" explicitly.
2. **Line ~94** still reads `demo video: [YouTube link]`. Paste the real URL.

Then the bracketed Results line fills from `snapshot.py` + `calibrate.py`:
final equity, round-trips, hit rate, max drawdown, gate blocks, Brier vs market.

## SUBMISSION CHECKLIST (the only thing that can still change the result)

- [ ] title, short description (255), long description (2000)
- [ ] cover image
- [ ] video presentation (YouTube link — also into WRITEUP.md line 94)
- [ ] slide presentation
- [ ] public repo: github.com/allenwangg/pythia
- [ ] demo app URL — **verify GitHub Pages is actually ON**: repo Settings ->
      Pages -> Source: `master` branch, `/docs` folder. Committing docs/ does
      NOT enable Pages. Open the URL in a private window before submitting it.
- [ ] Alpaca paper account ID: PA3C8Y75G64Y
- [ ] 1-page write-up: WRITEUP.md (AI logic, risk gates, Alpaca infra)
- [ ] up to 5 social links tagging @lablabai + @AlpacaHQ

## WHAT THE ENTRY IS ACTUALLY SELLING

Not the number. Two monopolies found in the competitor research: a real audited
P&L (no other entry publishes one) and real Alpaca MCP compliance. Both come
from the same habit — calling it before it resolves and grading it after, win
or lose. The QQQ miss disclosed in the write-up is not damage. It is the proof.

## IF SOMETHING BREAKS

Submit anyway, with whatever is true at 9:50. An entry filed with an honest
gap beats a perfect entry filed at 10:01.
