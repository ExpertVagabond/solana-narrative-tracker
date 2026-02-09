#!/usr/bin/env python3
"""Solana Narrative Tracker — detects emerging narratives in the Solana ecosystem.

Collects signals from onchain data, developer activity, market metrics,
and social/news sources, then uses AI to synthesize them into actionable
narratives with concrete build ideas.

Usage:
    python main.py                # Full run: collect + analyze + generate site
    python main.py --collect-only # Only collect raw signals
    python main.py --analyze-only # Only analyze (requires existing signals.json)
"""
from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

from collectors import onchain, github_signals, market, social
from analyzer import analyze, build_signal_digest

PROJECT_ROOT = Path(__file__).parent
SITE_DIR = PROJECT_ROOT / "site"
DATA_DIR = PROJECT_ROOT / "data"


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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--full"

    if mode == "--collect-only":
        collect_all()
        return

    if mode == "--analyze-only":
        signals_path = DATA_DIR / "signals.json"
        if not signals_path.exists():
            print("ERROR: No signals.json found. Run collection first.")
            sys.exit(1)
        with open(signals_path) as f:
            signals = json.load(f)
        analysis = run_analysis(signals)
        generate_site(analysis, signals)
        return

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


if __name__ == "__main__":
    main()
