#!/usr/bin/env python3
"""Pythia — reads the options chain like a prediction market. Paper trading only.

Usage:
  python run.py --once --dry-run          # one cycle, decisions logged, no orders
  python run.py --once                    # one live paper cycle
  python run.py --loop                    # trade the day (config: cycle_minutes)
  python run.py --loop --config config.contest.yaml
  python run.py --flatten                 # close everything, cancel open orders
  python run.py --letter                  # write today's fund letter
"""
from __future__ import annotations

import argparse
import logging
import sys

from pythia.config import ROOT, Config


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=None, help="YAML config path (default config.yaml)")
    ap.add_argument("--once", action="store_true", help="run a single cycle")
    ap.add_argument("--loop", action="store_true", help="run continuously during market hours")
    ap.add_argument("--dry-run", action="store_true", help="evaluate and journal, submit nothing")
    ap.add_argument("--flatten", action="store_true", help="close all positions, cancel orders")
    ap.add_argument("--letter", action="store_true", help="write today's fund letter")
    ap.add_argument("--selftest", action="store_true",
                    help="offline end-to-end rehearsal, no keys needed")
    args = ap.parse_args()

    (ROOT / "journal").mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(),
                  logging.FileHandler(ROOT / "journal" / "pythia.log")],
    )
    cfg = Config.load(args.config)

    if args.selftest:
        from pythia.selftest import run_selftest
        return run_selftest(cfg)

    if args.flatten:
        cfg.require_keys(need_anthropic=False)
        from pythia.execution import Executor
        from pythia.market_data import MarketData
        Executor(cfg, MarketData(cfg).trading).flatten_all()
        return 0

    if args.letter:
        cfg.require_keys()
        from pythia.journal import Journal
        from pythia.market_data import MarketData
        account = MarketData(cfg).trading.get_account()
        Journal(cfg).fund_letter(account_summary={
            "equity": float(account.equity),
            "pnl_vs_100k": round(float(account.equity) - 100_000, 2),
        })
        return 0

    if not (args.once or args.loop):
        print(__doc__)
        return 2

    cfg.require_keys()
    from pythia.scheduler import Pythia
    bot = Pythia(cfg, dry_run=args.dry_run)
    if args.once:
        bot.cycle()
    else:
        bot.loop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
