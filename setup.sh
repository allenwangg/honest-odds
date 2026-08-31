#!/usr/bin/env bash
# Pythia bootstrap — one command for the whole setup block.
#   bash setup.sh          install + offline proof (NO KEYS NEEDED)
#   bash setup.sh --live   the above, then account check + dry run (needs .env)
set -u
cd "$(dirname "$0")"
GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; DIM=$'\033[2m'; NC=$'\033[0m'
ok(){ echo "${GREEN}✓${NC} $1"; }
bad(){ echo "${RED}✗${NC} $1"; }

echo "── Pythia setup ──────────────────────────────"
python3 -c 'import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)' \
  && ok "python $(python3 -V | cut -d' ' -f2)" || { bad "need Python 3.10+"; exit 1; }

echo "${DIM}installing deps...${NC}"
python3 -m pip install -q -r requirements.txt 2>/dev/null \
  || python3 -m pip install -q --break-system-packages -r requirements.txt \
  || { bad "pip install failed"; exit 1; }
ok "dependencies installed"

[ -f .env ] || { cp .env.example .env; echo "${DIM}created .env — paste your keys into it${NC}"; }

echo "${DIM}running offline test suites...${NC}"
fail=0
for t in tests/test_implied.py tests/test_risk.py tests/test_structures.py tests/test_manager.py; do
  if python3 "$t" >/dev/null 2>&1; then ok "$(basename "$t")"; else bad "$(basename "$t")"; fail=1; fi
done
[ $fail -eq 0 ] || { bad "unit tests failed — stop and read the output: python3 tests/test_implied.py"; exit 1; }

echo "${DIM}running full offline rehearsal...${NC}"
if python3 run.py --selftest; then ok "END-TO-END PIPELINE WORKS (no keys used)"; else bad "selftest failed"; exit 1; fi
rm -f dashboard/state.json journal/decisions.jsonl journal/equity.jsonl journal/day_state.json

if [ "${1:-}" = "--live" ]; then
  echo; echo "── live checks (needs keys in .env) ──────────"
  python3 scripts/setup_account_check.py || bad "account check failed — fix .env / account"
  echo "${DIM}dry run against live chain data...${NC}"
  python3 run.py --once --dry-run || bad "dry run errored (stale weekend quotes are OK)"
fi

cat <<'EOF'

── next ──────────────────────────────────────
  1. paste keys into .env   (Alpaca PAPER + Anthropic)
  2. bash setup.sh --live   (account check + dry run)
  3. git init && git add -A && git commit -m "Pythia" && push public
  4. read RUNBOOK.md — the whole week is on that one card
EOF
