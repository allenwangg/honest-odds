#!/usr/bin/env bash
# One command for the whole afternoon. Run from ~/Downloads/pythia (or wherever the repo is).
#   bash pythia_afternoon.sh flatten     # 2:15pm — stop the loop, close everything
#   bash pythia_afternoon.sh report      # 3:05pm — letter, snapshot, calibrate, post text
#   bash pythia_afternoon.sh             # does both, in order
set -uo pipefail
cd "$(dirname "$0")" 2>/dev/null || true
[ -f run.py ] || { echo "!! run.py not here. cd into the pythia repo first."; exit 1; }
PY=$(command -v python3 || command -v python)
STAMP=$(date +%H:%M)
line(){ printf '\n\033[1m%s\033[0m\n' "$*"; }

do_flatten(){
  line "[$STAMP] 1/3  stopping the loop"
  pkill -f "run.py --loop" 2>/dev/null && echo "   loop stopped" || echo "   no loop running (fine)"
  sleep 2
  line "[$STAMP] 2/3  closing every position"
  $PY run.py --flatten
  line "[$STAMP] 3/3  confirming flat"
  $PY - <<'EOF'
import os,sys
sys.path.insert(0,'.')
try:
    from dotenv import load_dotenv; load_dotenv('.env')
    from alpaca.trading.client import TradingClient
    c=TradingClient(os.getenv("ALPACA_API_KEY"),os.getenv("ALPACA_SECRET_KEY"),paper=True)
    pos=c.get_all_positions(); acct=c.get_account()
    print(f"   equity ${float(acct.equity):,.2f}   open positions: {len(pos)}")
    for p in pos: print(f"   STILL OPEN -> {p.symbol} x{p.qty}")
    print("   FLAT. Nothing rides into payrolls." if not pos else "   !! not flat — rerun --flatten")
except Exception as e:
    print("   (couldn't verify via API:",e,")")
EOF
}

do_report(){
  line "[$STAMP] nightly letter"
  $PY run.py --letter || echo "   (letter failed, not fatal)"
  line "snapshot"
  $PY scripts/snapshot.py | tee /tmp/pythia_snap.txt
  line "calibration (Brier vs the market)"
  $PY scripts/calibrate.py 2>&1 | tee /tmp/pythia_cal.txt | tail -20
  line "DECISION FOR FRIDAY"
  $PY - <<'EOF'
import re,os
try: s=open('/tmp/pythia_snap.txt').read()
except: s=""
m=re.search(r"equity\s+\$([\d,]+\.\d\d)",s)
eq=float(m.group(1).replace(",","")) if m else None
if eq is None:
    print("   couldn't read equity from snapshot — read it off the dashboard")
else:
    r=(eq/100000-1)*100
    print(f"   equity ${eq:,.2f}   return {r:+.2f}%")
    if r >= 2.0:
        print("   -> SIT. Do not run config.event.yaml Friday. Do not trade the open.")
        print("      Monte-Carlo (40k sims, 120-entry field): trading from here cuts")
        print("      podium odds from ~77% to ~40%. You are defending, not chasing.")
    else:
        print("   -> GAMBLE IS NOW CORRECT. Below ~+2% the median outcome is worthless;")
        print("      only the right tail changes your rank. Friday 8:30-9:45:")
        print("      python run.py --loop --config config.event.yaml   then --flatten 9:45.")
    print()
    print("   ---- DAY 4 POST (fill the two blanks, then post) ----")
    print(f"   Day 4 grade, @lablabai x @AlpacaHQ. Yesterday: market said 60% QQQ")
    print(f"   finishes above 708, Pythia said 52%. It closed at ____.")
    print(f"   [Pythia's lean was right / market was right]. Week: {r:+.1f}%.")
    print(f"   Flat into payrolls on purpose - the number is banked, not bet.")
    print()
    print("   ---- FRIDAY FINAL POST ----")
    print(f"   Final, @lablabai x @AlpacaHQ: ${eq:,.0f} on $100,000 ({r:+.1f}%) after")
    print(f"   five sessions. __ agent trades, __ vetoed by gates, two winners banked")
    print(f"   by rule, zero manual entries. Called before it resolved, graded after")
    print(f"   - every day. Code: github.com/allenwangg/pythia")
EOF
  line "NEXT"
  echo "   1. paste the snapshot + calibrate output to Claude -> deck Brier boxes + write-up"
  echo "   2. post the Day 4 grade"
  echo "   3. tomorrow 9:45  python scripts/snapshot.py  -> final post -> deadline 10:00"
}

case "${1:-both}" in
  flatten) do_flatten ;;
  report)  do_report ;;
  *)       do_flatten; do_report ;;
esac
