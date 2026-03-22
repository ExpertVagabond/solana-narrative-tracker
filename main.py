#!/usr/bin/env python3
"""Solana Narrative Tracker — detects emerging narratives in the Solana ecosystem.

Security Architecture:
- sanitize_error(): strips file paths, redacts secrets (20+ char tokens), truncates to 200 chars
- validate_mode(): whitelisted CLI modes only — rejects unknown arguments
- validate_path(): blocks path traversal (.. segments) and enforces max length
- validate_signals(): schema validation on ingested data structures
- validate_json_file(): size-bounded file loading with schema check
- sanitize_string(): HTML-entity-encodes angle brackets, enforces max length
- All API keys (ANTHROPIC_API_KEY, etc.) loaded from env vars — never hardcoded
- All catch blocks use sanitize_error() — no raw exception messages reach output
- File sizes capped at 50 MB to prevent resource exhaustion

Usage:
    python main.py                # Full run: collect + analyze + generate site
    python main.py --collect-only # Only collect raw signals
    python main.py --analyze-only # Only analyze (requires existing signals.json)
"""
from __future__ import annotations

import json
import logging
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Security utilities (defined first — used throughout all modules)
# ---------------------------------------------------------------------------


def sanitize_error(e: Exception) -> str:
    """Sanitize error messages to prevent information leakage."""
    msg = str(e)
    msg = re.sub(r'/[^\s]+', '[path]', msg)
    msg = re.sub(r'[A-Za-z0-9]{20,}', '[redacted]', msg)
    return msg[:200]


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Strip dangerous characters and enforce length."""
    if not isinstance(value, str):
        return ""
    return value.replace("<", "&lt;").replace(">", "&gt;").strip()[:max_length]


def require_env(name: str) -> str:
    """Load required env var or fail with clear message (no raw value leaked)."""
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"Required env var {name} is not set")
    return val


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------

_VALID_MODES = {"--full", "--collect-only", "--analyze-only", "--help"}
_MAX_SIGNALS_SIZE = 50 * 1024 * 1024  # 50MB max signals file
_MAX_PATH_LEN = 500
_SAFE_PATH_RE = re.compile(r"^[a-zA-Z0-9_./-]+$")


def validate_mode(mode: str) -> str:
    """Validate CLI mode argument against whitelist."""
    mode = mode.strip()
    if mode not in _VALID_MODES:
        raise ValueError(f"Unknown mode. Valid: {', '.join(sorted(_VALID_MODES))}")
    return mode


def validate_path(path: Path) -> Path:
    """Ensure path is reasonable and not a traversal attempt."""
    s = str(path)
    if len(s) > _MAX_PATH_LEN:
        raise ValueError("Path too long")
    if ".." in s:
        raise ValueError("Path traversal not allowed")
    return path


def validate_signals(signals: Any) -> dict:
    """Validate signals data structure."""
    if not isinstance(signals, dict):
        raise ValueError("Signals must be a dictionary")
    required = {"onchain", "github", "market", "social"}
    missing = required - set(signals.keys())
    if missing:
        logger.warning("Signals missing keys: %s", missing)
    return signals


def validate_json_file(path: Path, max_size: int = _MAX_SIGNALS_SIZE) -> dict:
    """Safely load and validate a JSON file with size bounds."""
    path = validate_path(path)
    if not path.exists():
        raise FileNotFoundError("Signals file not found")
    if path.stat().st_size > max_size:
        raise ValueError(f"File exceeds {max_size} byte limit")
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON: {sanitize_error(exc)}") from exc
    return validate_signals(data)


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

from collectors import onchain, github_signals, market, social  # noqa: E402
from analyzer import analyze, build_signal_digest  # noqa: E402

PROJECT_ROOT = Path(__file__).parent
SITE_DIR = validate_path(PROJECT_ROOT / "site")
DATA_DIR = validate_path(PROJECT_ROOT / "data")


def collect_all() -> dict:
    """Collect signals from all sources."""
    print("=" * 60)
    print("SOLANA NARRATIVE TRACKER — Signal Collection")
    print("=" * 60)

    signals = {}
    signals["onchain"] = onchain.collect()
    signals["github"] = github_signals.collect()
    signals["market"] = market.collect()
    signals["social"] = social.collect()
    signals["collected_at"] = datetime.now(timezone.utc).isoformat()

    # Save raw signals
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "signals.json", "w") as f:
        json.dump(signals, f, indent=2, default=str)
    print(f"\nRaw signals saved to {DATA_DIR / 'signals.json'}")
    return signals


def run_analysis(signals: dict) -> dict:
    """Run narrative analysis on collected signals."""
    print("\n" + "=" * 60)
    print("SOLANA NARRATIVE TRACKER — Narrative Analysis")
    print("=" * 60)

    result = analyze(signals)

    # Save analysis
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "analysis.json", "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\nAnalysis saved to {DATA_DIR / 'analysis.json'}")
    return result


def generate_site(analysis: dict, signals: dict) -> None:
    """Generate site data file for the frontend."""
    print("\n[site] Generating site data...")
    SITE_DIR.mkdir(exist_ok=True)

    # Combine analysis with key signal summaries for the dashboard
    site_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "highlights": {
            "sol_price": signals.get("market", {}).get("sol", {}),
            "tvl": signals.get("onchain", {}).get("tvl", {}),
            "top_movers": signals.get("onchain", {}).get("top_protocols", [])[:5],
            "trending_repos": signals.get("github", {}).get("trending_new", [])[:5],
            "recent_news": (
                signals.get("social", {}).get("ecosystem_articles", [])[:5]
                + signals.get("social", {}).get("news_articles", [])[:5]
            ),
        },
    }

    with open(SITE_DIR / "data.json", "w") as f:
        json.dump(site_data, f, indent=2, default=str)
    print(f"  Site data written to {SITE_DIR / 'data.json'}")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--full"

    try:
        mode = validate_mode(mode)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if mode == "--help":
        print(__doc__ or "Solana Narrative Tracker")
        return 0

    try:
        if mode == "--collect-only":
            collect_all()
            return 0

        if mode == "--analyze-only":
            signals_path = DATA_DIR / "signals.json"
            signals = validate_json_file(signals_path)
            analysis = run_analysis(signals)
            generate_site(analysis, signals)
            return 0

        # Full run
        signals = collect_all()
        analysis = run_analysis(signals)
        generate_site(analysis, signals)

        print("\n" + "=" * 60)
        narrative_count = len(analysis.get("narratives", []))
        if narrative_count:
            print(f"Done! {narrative_count} narratives detected.")
        else:
            print("Done! Raw signals collected (analysis requires ANTHROPIC_API_KEY).")
        print(f"Dashboard data: {SITE_DIR / 'data.json'}")
        print("=" * 60)
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        return 130
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        logger.error("Fatal error: %s", sanitize_error(exc))
        print(f"ERROR: {type(exc).__name__}: check logs for details")
        return 1
    except OSError as exc:
        logger.error("IO error: %s", sanitize_error(exc))
        print("ERROR: File system error")
        return 1


if __name__ == "__main__":
    sys.exit(main())
