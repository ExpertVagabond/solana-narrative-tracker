"""Market signal collector — CoinGecko + Jupiter."""
from __future__ import annotations

import httpx
from datetime import datetime, timezone

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
TIMEOUT = 30


def _get(url: str, params: dict | None = None) -> dict | list | None:
    try:
        resp = httpx.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [market] Failed to fetch {url}: {e}")
        return None


def get_solana_ecosystem_tokens(limit: int = 30) -> list[dict]:
    """Get top Solana ecosystem tokens by market cap."""
    data = _get(
        f"{COINGECKO_BASE}/coins/markets",
        params={
            "vs_currency": "usd",
            "category": "solana-ecosystem",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "7d,14d,30d",
        },
    )
    if not data:
        return []
    return [
        {
            "id": t["id"],
            "symbol": t["symbol"].upper(),
            "name": t["name"],
            "price": t.get("current_price"),
            "market_cap": t.get("market_cap"),
            "market_cap_rank": t.get("market_cap_rank"),
            "volume_24h": t.get("total_volume"),
            "change_24h": round(t.get("price_change_percentage_24h") or 0, 2),
            "change_7d": round(t.get("price_change_percentage_7d_in_currency") or 0, 2),
            "change_14d": round(t.get("price_change_percentage_14d_in_currency") or 0, 2),
            "change_30d": round(t.get("price_change_percentage_30d_in_currency") or 0, 2),
        }
        for t in data
    ]


def get_sol_price_data() -> dict:
    """Get SOL price and market data."""
    data = _get(
        f"{COINGECKO_BASE}/coins/solana",
        params={"localization": "false", "tickers": "false", "community_data": "false"},
    )
    if not data:
        return {"error": "Failed to fetch SOL data"}
    market = data.get("market_data", {})
    return {
        "price_usd": market.get("current_price", {}).get("usd"),
        "market_cap": market.get("market_cap", {}).get("usd"),
        "volume_24h": market.get("total_volume", {}).get("usd"),
        "change_24h": round(market.get("price_change_percentage_24h") or 0, 2),
        "change_7d": round(market.get("price_change_percentage_7d") or 0, 2),
        "change_14d": round(market.get("price_change_percentage_14d") or 0, 2),
        "change_30d": round(market.get("price_change_percentage_30d") or 0, 2),
        "ath": market.get("ath", {}).get("usd"),
        "ath_change_pct": round(market.get("ath_change_percentage", {}).get("usd") or 0, 2),
    }


def get_trending_tokens() -> list[dict]:
    """Get currently trending tokens on CoinGecko."""
    data = _get(f"{COINGECKO_BASE}/search/trending")
    if not data:
        return []
    coins = data.get("coins", [])
    solana_trending = []
    for c in coins:
        item = c.get("item", {})
        platforms = item.get("platforms", {})
        if "solana" in platforms or any("solana" in str(v).lower() for v in platforms.values()):
            solana_trending.append({
                "name": item.get("name"),
                "symbol": item.get("symbol"),
                "market_cap_rank": item.get("market_cap_rank"),
                "score": item.get("score"),
            })
    return solana_trending


def get_defi_categories() -> list[dict]:
    """Get DeFi category performance data."""
    data = _get(f"{COINGECKO_BASE}/coins/categories")
    if not data:
        return []
    relevant = [
        c for c in data
        if any(
            kw in (c.get("name") or "").lower()
            for kw in ["solana", "defi", "liquid staking", "dex", "lending", "yield", "meme", "ai", "depin", "rwa"]
        )
    ]
    return [
        {
            "name": c["name"],
            "market_cap": c.get("market_cap"),
            "market_cap_change_24h": round(c.get("market_cap_change_24h") or 0, 2),
            "volume_24h": c.get("volume_24h"),
            "top_3_coins": c.get("top_3_coins", [])[:3],
        }
        for c in relevant[:15]
    ]


def collect() -> dict:
    """Collect all market signals."""
    print("[market] Collecting signals...")
    signals = {
        "sol": get_sol_price_data(),
        "ecosystem_tokens": get_solana_ecosystem_tokens(),
        "trending": get_trending_tokens(),
        "categories": get_defi_categories(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    token_count = len(signals["ecosystem_tokens"])
    trending_count = len(signals["trending"])
    print(f"  [market] Got SOL data, {token_count} ecosystem tokens, {trending_count} trending")
    return signals
