"""One place that talks to Claude, with two interchangeable backends.

  backend: "api"  -> Anthropic API, pay-as-you-go API credits
  backend: "cli"  -> shells out to `claude -p`, which authenticates with your
                     Claude subscription / Agent SDK credit instead

The CLI path exists so a Max/Pro subscriber doesn't have to buy separate API
credits for a week-long contest. Both return plain text; callers don't care
which one produced it.
"""
from __future__ import annotations

import json
import logging
import shutil
import subprocess

log = logging.getLogger("pythia.llm")


class LLMError(RuntimeError):
    pass


def cli_available() -> bool:
    return shutil.which("claude") is not None


def complete(system: str, prompt: str, cfg, max_tokens: int = 1500) -> str:
    backend = getattr(cfg, "llm_backend", "api")
    if backend == "cli":
        return _via_cli(system, prompt, cfg)
    return _via_api(system, prompt, cfg, max_tokens)


def _via_api(system: str, prompt: str, cfg, max_tokens: int) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=cfg.anthropic_key)
    resp = client.messages.create(
        model=cfg.model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def _via_cli(system: str, prompt: str, cfg) -> str:
    """`claude -p` in headless mode. No tools, bounded turns, JSON envelope."""
    if not cli_available():
        raise LLMError("`claude` CLI not found — install Claude Code or set llm_backend: api")
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--max-turns", "1",
        "--append-system-prompt", system,
    ]
    model = getattr(cfg, "cli_model", "") or ""
    if model:
        cmd += ["--model", model]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True,
                              text=True, timeout=180)
    except subprocess.TimeoutExpired as err:
        raise LLMError("claude CLI timed out after 180s") from err
    if proc.returncode != 0:
        raise LLMError(f"claude CLI exited {proc.returncode}: {proc.stderr[:300]}")
    out = proc.stdout.strip()
    try:                                    # envelope: {"result": "...", ...}
        data = json.loads(out)
        if isinstance(data, dict):
            for key in ("result", "text", "content"):
                if isinstance(data.get(key), str):
                    return data[key]
        return out
    except json.JSONDecodeError:
        return out                          # already plain text
