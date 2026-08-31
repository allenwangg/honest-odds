#!/usr/bin/env python3
"""Which Claude backend can this machine use? Run before deciding to pay."""
import shutil, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pythia.config import Config

cfg = Config.load()
print(f"config says llm_backend: {cfg.llm_backend}\n")

cli = shutil.which("claude")
if cli:
    print(f"✓ Claude Code CLI found: {cli}")
    try:
        r = subprocess.run(["claude", "-p", "--output-format", "json", "--max-turns", "1",
                            "Reply with exactly: OK"],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print("✓ `claude -p` WORKS — set llm_backend: cli and pay nothing extra")
        else:
            print(f"✗ `claude -p` failed ({r.returncode}): {r.stderr[:200]}")
            print("  (if it says login required: run `claude` once, or `claude setup-token`)")
    except Exception as e:
        print(f"✗ `claude -p` errored: {e}")
else:
    print("✗ Claude Code CLI not installed")
    print("  install:  npm install -g @anthropic-ai/claude-code")

print()
if cfg.anthropic_key:
    print("✓ ANTHROPIC_API_KEY is set in .env (api backend available)")
else:
    print("✗ no ANTHROPIC_API_KEY in .env (api backend unavailable)")
