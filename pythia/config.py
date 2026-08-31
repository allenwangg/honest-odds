"""Configuration: YAML file + environment variables. Fail loudly on missing keys."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class RiskConfig:
    per_trade_max_frac: float = 0.05      # G2: max risk per trade as fraction of equity
    portfolio_heat_frac: float = 0.25     # G3: total open max-loss cap
    daily_loss_halt_frac: float = 0.08    # G4: circuit breaker on drawdown from day start
    per_underlying_frac: float = 0.15     # G7: concentration cap per underlying
    max_spread_frac: float = 0.20         # G5: reject legs with (ask-bid)/mid above this
    min_bid: float = 0.01                 # G5: every leg must have a real bid
    stop_entries_min_before_close: int = 20


@dataclass
class Config:
    universe: list[str] = field(default_factory=lambda: ["SPY", "QQQ"])
    max_dte: int = 7
    min_dte: int = 0
    event_offsets: list[float] = field(default_factory=lambda: [-0.025, -0.01, 0.0, 0.01, 0.025])
    edge_threshold: float = 0.07
    edge_shrinkage: float = 1.0           # multiply raw edges by this (calibrate.py suggests it)
    max_parity_residual: float = 0.50     # $: skip symbol if put-call parity is this broken (stale quotes)
    min_confidence: float = 0.60
    max_trades_per_cycle: int = 2
    kelly_scalar: float = 0.5
    allow_spreads: bool = True
    convexity_mode: bool = False          # high conviction -> straight long option (uncapped upside)
    convexity_min_edge: float = 0.10
    convexity_min_conf: float = 0.70
    cancel_stale_after_min: int = 25      # cancel unfilled pythia orders older than this
    take_profit_close_plpc: float = 1.00  # close standalone long options up this fraction (1.0 = +100%)
    slippage_buffer: float = 0.05         # added to net-debit mid when pricing limits
    min_spread_width_frac: float = 0.005  # spread width >= 0.5% of strike (SPY ~$4, not $1)
    max_breakeven_prob: float = 0.85      # never pay more than 85c on the dollar
    cross_frac: float = 0.60              # concede this fraction of the bid-ask; work the rest
    cycle_minutes: int = 20
    options_feed: str = "indicative"      # free on paper accounts; "opra" needs a subscription
    llm_backend: str = "api"              # "api" = API credits · "cli" = `claude -p` (subscription)
    cli_model: str = ""                   # optional model override for the cli backend
    model: str = "claude-sonnet-5"        # any current model id works; see docs.claude.com
    analyst_max_tokens: int = 1500
    risk: RiskConfig = field(default_factory=RiskConfig)

    # populated from env
    alpaca_key: str = ""
    alpaca_secret: str = ""
    anthropic_key: str = ""

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Config":
        load_dotenv(ROOT / ".env")
        cfg = cls()
        cfg_path = Path(path) if path else ROOT / "config.yaml"
        if cfg_path.exists():
            raw = yaml.safe_load(cfg_path.read_text()) or {}
            risk_raw = raw.pop("risk", {}) or {}
            for k, v in raw.items():
                if hasattr(cfg, k):
                    setattr(cfg, k, v)
            for k, v in risk_raw.items():
                if hasattr(cfg.risk, k):
                    setattr(cfg.risk, k, v)
        cfg.alpaca_key = os.environ.get("ALPACA_API_KEY", "")
        cfg.alpaca_secret = os.environ.get("ALPACA_SECRET_KEY", "")
        cfg.anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        return cfg

    def require_keys(self, need_anthropic: bool = True) -> None:
        missing = [n for n, v in [("ALPACA_API_KEY", self.alpaca_key),
                                  ("ALPACA_SECRET_KEY", self.alpaca_secret)] if not v]
        # the cli backend authenticates through Claude Code, so no API key needed
        if need_anthropic and self.llm_backend == "api" and not self.anthropic_key:
            missing.append("ANTHROPIC_API_KEY")
        if self.llm_backend == "cli":
            from .llm import cli_available
            if not cli_available():
                raise SystemExit("llm_backend is 'cli' but the `claude` command "
                                 "was not found. Install Claude Code, or set "
                                 "llm_backend: api in config.yaml")
        if missing:
            raise SystemExit(f"Missing env vars: {', '.join(missing)} (copy .env.example to .env)")
