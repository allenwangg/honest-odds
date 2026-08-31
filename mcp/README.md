# MCP layer — Claude as Pythia's supervisor

The hackathon requires Alpaca's Trading API **plus** the MCP server or CLI.
Pythia's execution path is the Trading API (`alpaca-py`, multi-leg limit
orders). The MCP server is the *supervision* path: Claude, connected to the
same paper account through Alpaca's official MCP server, is how the human
interrogates and overrides the agent in plain language. Demo both in the video.

## Setup (Claude Code)

```bash
git clone https://github.com/alpacahq/alpaca-mcp-server
cd alpaca-mcp-server && pip install -r requirements.txt
claude mcp add alpaca -e ALPACA_API_KEY=xxx -e ALPACA_SECRET_KEY=xxx \
  -e ALPACA_PAPER_TRADE=true -- python /path/to/alpaca-mcp-server/server.py
```

(Check the alpaca-mcp-server README for its current entrypoint and env names —
the repo moves fast. Claude Desktop works too via `claude_desktop_config.json`
with the same command/env structure.)

## Supervision prompts that make good demo footage

- "What's the account's P&L today and what option positions are open?"
- "Show open orders. Cancel anything unfilled older than 30 minutes."
- "Close the SPY call spread — I disagree with the thesis in today's journal."
- "What did the last trade cost and what's its max loss?"

## Why this split is the right architecture

The autonomous loop needs determinism, idempotent order ids, and gates that
cannot be argued with — that's code against the Trading API. The human needs
judgment and language — that's Claude over MCP. One brokerage account, two
interfaces, each doing what it's best at.
