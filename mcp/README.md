# MCP layer — Claude as Honest Odds's supervisor

The hackathon requires Alpaca's Trading API **plus** the MCP server or CLI. Honest Odds's
execution path is the Trading API (`alpaca-py`, atomic multi-leg limit orders). The MCP
server is the *supervision* path: Claude, connected to the same dedicated paper account
through **Alpaca's official MCP server**, is how the operator interrogates and overrides
the agent in plain language. Both are demoed in the video.

## Setup — verified working, Sep 2026

The upstream repo moved to a `src/` layout and installs a console script, so the old
`python server.py` invocation no longer resolves. This is the command that works:

```bash
git clone https://github.com/alpacahq/alpaca-mcp-server
pip install -e ./alpaca-mcp-server

claude mcp add alpaca \
  -e ALPACA_API_KEY=your_paper_key \
  -e ALPACA_SECRET_KEY=your_paper_secret \
  -e ALPACA_PAPER_TRADE=true \
  -- "$(which alpaca-mcp-server)"
```

Verify:

```bash
$ claude mcp list
Checking MCP server health...

alpaca: /opt/anaconda3/bin/alpaca-mcp-server  - ✔ Connected
```

Claude Desktop works the same way via `claude_desktop_config.json` with the same
command and env block.

## Supervision prompts (the ones in the demo)

- "What's the account's P&L today and what option positions are open?"
- "Show open orders. Cancel anything unfilled older than 30 minutes."
- "Close the QQQ put spread — I disagree with the thesis in today's journal."
- "What did the last trade cost and what's its max loss?"

## Why this split is the right architecture

The autonomous loop needs determinism, idempotent order ids, and gates that cannot be
argued with — that is code against the Trading API. The human needs judgment and
language — that is Claude over MCP. One brokerage account, two interfaces, each doing
what it is best at. The loop never asks the model for permission; the human never
places an order by hand.
