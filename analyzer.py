"""Narrative analyzer — uses Claude API to synthesize signals into narratives."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

SYSTEM_PROMPT = """You are an expert Solana ecosystem analyst. You analyze raw data signals from
onchain metrics, developer activity, market data, and social/news sources to identify emerging
narratives in the Solana ecosystem.

Your job is to identify 5-8 emerging or accelerating narratives for the current fortnight.
Prioritize NOVELTY and SIGNAL QUALITY over volume. Focus on trends that are:
- Genuinely emerging (not already obvious/mainstream)
- Supported by multiple signal types (onchain + dev + social)
- Actionable for builders

For each narrative, provide:
1. A clear, concise title
2. A signal strength score (1-10)
3. A 2-3 sentence explanation of WHY this is emerging
4. The key evidence/signals that support it
5. 3-5 concrete product ideas that could be built around this narrative
6. Which signal types support it (onchain/developer/market/social)

Output valid JSON matching this schema:
{
  "analysis_date": "ISO date",
  "period": "Feb 1-14, 2026",
  "executive_summary": "2-3 sentence overview of the Solana ecosystem state",
  "narratives": [
    {
      "id": 1,
      "title": "Narrative Title",
      "signal_strength": 8,
      "category": "DeFi|Infrastructure|Consumer|AI|DePIN|Gaming|Payments|Social",
      "summary": "2-3 sentences explaining the narrative",
      "evidence": ["signal 1", "signal 2", "signal 3"],
      "signal_types": ["onchain", "developer", "market"],
      "build_ideas": [
        {
          "title": "Product Idea",
          "description": "1-2 sentence description",
          "complexity": "low|medium|high",
          "potential_impact": "low|medium|high"
        }
      ],
      "key_projects": ["project1", "project2"],
      "risk_factors": ["risk 1"]
    }
  ],
  "meta": {
    "signals_analyzed": 0,
    "data_sources": ["DeFiLlama", "GitHub", "CoinGecko", "RSS Feeds", "Solana RPC"]
  }
}"""


def build_signal_digest(signals: dict) -> str:
    """Build a text digest of all collected signals for LLM analysis."""
    parts = []

    # Onchain signals
    onchain = signals.get("onchain", {})
    tvl = onchain.get("tvl", {})
    parts.append("## ONCHAIN SIGNALS")
    parts.append(f"Solana TVL: ${tvl.get('current_tvl', 0):,.0f}")
    parts.append(f"  14d change: {tvl.get('change_14d_pct', 0):+.1f}%")
    parts.append(f"  30d change: {tvl.get('change_30d_pct', 0):+.1f}%")

    parts.append("\nTop protocols by TVL movement (7d):")
    for p in onchain.get("top_protocols", [])[:15]:
        parts.append(f"  {p['name']} ({p['category']}): TVL ${p['tvl']:,.0f}, 7d: {p['change_7d']:+.1f}%, 1d: {p['change_1d']:+.1f}%")

    parts.append("\nTop yield opportunities:")
    for y in onchain.get("yields", [])[:10]:
        parts.append(f"  {y['project']} {y['symbol']}: APY {y['apy']:.1f}% (30d avg: {y['apy_mean_30d']:.1f}%), TVL ${y['tvl_usd']:,.0f}")

    net = onchain.get("network", {})
    if "avg_tps" in net:
        parts.append(f"\nNetwork TPS (avg): {net['avg_tps']}")

    # GitHub signals
    github = signals.get("github", {})
    parts.append("\n## DEVELOPER SIGNALS")
    parts.append("Trending new Solana repos (last 30 days):")
    for r in github.get("trending_new", [])[:10]:
        parts.append(f"  {r['name']}: ★{r['stars']} | {r['language'] or 'N/A'} | {r['description'][:100]}")
        if r.get("topics"):
            parts.append(f"    topics: {', '.join(r['topics'][:5])}")

    parts.append("\nMost active repos (last 14 days):")
    for r in github.get("most_active", [])[:10]:
        parts.append(f"  {r['name']}: ★{r['stars']} | pushed: {r['pushed_at'][:10]}")

    parts.append("\nEcosystem topic breakdown:")
    for t in github.get("ecosystem_topics", []):
        parts.append(f"  {t['topic']}: {t['repo_count']} repos, {t['total_stars']} total stars")

    # Market signals
    market = signals.get("market", {})
    sol = market.get("sol", {})
    parts.append("\n## MARKET SIGNALS")
    parts.append(f"SOL: ${sol.get('price_usd', 0):,.2f}")
    parts.append(f"  24h: {sol.get('change_24h', 0):+.1f}%, 7d: {sol.get('change_7d', 0):+.1f}%, 14d: {sol.get('change_14d', 0):+.1f}%, 30d: {sol.get('change_30d', 0):+.1f}%")

    parts.append("\nTop Solana ecosystem tokens (by market cap):")
    for t in market.get("ecosystem_tokens", [])[:15]:
        parts.append(f"  {t['symbol']}: ${t['price']:.4f}, 7d: {t['change_7d']:+.1f}%, 14d: {t['change_14d']:+.1f}%")

    if market.get("trending"):
        parts.append("\nTrending Solana tokens on CoinGecko:")
        for t in market["trending"]:
            parts.append(f"  {t['name']} ({t['symbol']})")

    parts.append("\nRelevant categories:")
    for c in market.get("categories", [])[:10]:
        parts.append(f"  {c['name']}: mcap change 24h: {c['market_cap_change_24h']:+.1f}%")

    # Social signals
    social = signals.get("social", {})
    parts.append("\n## SOCIAL & NEWS SIGNALS")
    parts.append("Recent ecosystem articles:")
    for a in social.get("ecosystem_articles", [])[:15]:
        parts.append(f"  [{a['source']}] {a['title']}")
        if a.get("summary"):
            parts.append(f"    {a['summary'][:150]}")

    parts.append("\nCrypto news mentioning Solana:")
    for a in social.get("news_articles", [])[:10]:
        parts.append(f"  [{a['source']}] {a['title']}")

    parts.append("\nGovernance (open SIMDs):")
    for g in social.get("governance", [])[:5]:
        parts.append(f"  {g['title']} (by {g['user']})")

    return "\n".join(parts)


def analyze_with_claude(signals: dict) -> dict:
    """Use Claude API to analyze signals and generate narratives."""
    try:
        import anthropic
    except ImportError:
        print("  [analyzer] anthropic package not installed, skipping API analysis")
        return {}

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [analyzer] ANTHROPIC_API_KEY not set, skipping API analysis")
        return {}

    digest = build_signal_digest(signals)
    client = anthropic.Anthropic(api_key=api_key)
    print("  [analyzer] Sending signals to Claude for analysis...")

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Analyze these Solana ecosystem signals from the past fortnight and identify emerging narratives. Today's date is {datetime.now(timezone.utc).strftime('%Y-%m-%d')}.\n\n{digest}",
            }
        ],
    )

    text = response.content[0].text
    # Extract JSON from response
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except json.JSONDecodeError:
        print("  [analyzer] Failed to parse Claude response as JSON")
        return {"raw_response": text}


def analyze(signals: dict) -> dict:
    """Main analysis entry point."""
    print("[analyzer] Analyzing signals...")
    digest = build_signal_digest(signals)

    # Count total signals
    total = 0
    for category in signals.values():
        if isinstance(category, dict):
            for v in category.values():
                if isinstance(v, list):
                    total += len(v)

    result = analyze_with_claude(signals)
    if result and "narratives" in result:
        result["meta"] = result.get("meta", {})
        result["meta"]["signals_analyzed"] = total
        print(f"  [analyzer] Generated {len(result['narratives'])} narratives from {total} signals")
        return result

    # If API analysis failed, return the raw digest for manual analysis
    print("  [analyzer] API analysis not available — returning raw signal digest")
    return {
        "analysis_date": datetime.now(timezone.utc).isoformat(),
        "period": "Current fortnight",
        "executive_summary": "Analysis pending — raw signals collected successfully.",
        "narratives": [],
        "raw_digest": digest,
        "meta": {
            "signals_analyzed": total,
            "data_sources": ["DeFiLlama", "GitHub", "CoinGecko", "RSS Feeds", "Solana RPC"],
            "status": "raw_signals_only",
        },
    }
