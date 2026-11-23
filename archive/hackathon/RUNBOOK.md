# RUNBOOK — the whole contest on one card. All decisions already made.

Times are CT (you). Market opens 8:30, closes 3:00. Deadline Fri 10:00 CT.

## SUNDAY
12:00  lablab enroll · fresh Alpaca paper acct ($100k exact) · options L3 · keys
 1:00  install → run 4 test files → `python run.py --selftest` → account_check
 2:00  `run.py --once --dry-run` → read journal → dashboard up → `show_curve.py`
 3:00  droplet: clone, .env, tmux, dry-run there
 4:00  GitHub push + LICENSE
 4:30  lablab draft: paste PLAYBOOK §3 copy + cover.png · note form fields
 5:30  eat
 6:00  Discord: PLAYBOOK §4 intro + the 2 rule questions · check leaderboard page
 6:45  fill teaser {braces} · 7:45 POST teaser (X+LinkedIn), pin it
 8:15  alpaca-mcp-server into Claude · test screen recorder
 9:00  macro.md verify · earnings calendar → add liquid weekly names
 9:30  alarms (8:15a, 2:55p daily) · SLEEP

## MON–THU DAILY LOOP
 8:25  AM post (PLAYBOOK §2) · tmux alive?
 8:45  Mon only: smoke trade — 1 contract, watch the fill
 loop  Mon: `--loop` (default cfg) · Tue–Thu: `--config config.contest.yaml`
 3:05  `--letter` → PM post → mirror LinkedIn/blog → Discord share
 3:30  Tue on: `calibrate.py` → set edge_shrinkage if λ<1 · macro.md tomorrow
 WED   after close: record video (PLAYBOOK §1) → post native, tag hosts
 THU   2:00–2:45 `--loop --config config.overnight.yaml` (NFP book) → stop
       after close: `friday_planner.py` → follow it → SUBMIT COMPLETE → PM post

## FRIDAY
 7:25  book + no KILL file · 7:30 NFP prints
 8:30  `--loop --config config.event.yaml` (as planner modified it)
 9:40  stop · 9:45 `--flatten` · 9:50 `snapshot.py` → paste finals into form
10:00  DEADLINE · post finale (quote the teaser, tag hosts)

## RULES ALREADY DECIDED — DO NOT RENEGOTIATE MID-WEEK
- Never override a gate. Never widen a cap intraday. Planner decides Friday.
- Analyst fails twice → trade nothing. That's correct, not broken.
- Anything feels wrong → `touch KILL`, breathe, read the journal.
- One account. One entry. Everything public, win or lose.

## IF IT BREAKS
- Order rejected on increment → it auto-retries at $0.05. Watch, don't touch.
- Symbol skipped on parity → the stale-quote gate working. Good.
- API/model down → agent fails closed; post the letter anyway, honestly.
