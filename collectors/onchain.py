"""Onchain signal collector — DeFiLlama + Solana RPC."""
from __future__ import annotations

import httpx
from datetime import datetime, timedelta, timezone

DEFILLAMA_BASE = "https://api.llama.fi"
SOLANA_RPC = "https://api.mainnet-beta.solana.com"
TIMEOUT = 30


def _get(url: str, params: dict | None = None) -> dict | list | None:
    try:
        resp = httpx.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [onchain] Failed to fetch {url}: {e}")
        return None


def get_solana_tvl_history() -> dict:
    """Get Solana chain TVL over last 30 days."""
    data = _get(f"{DEFILLAMA_BASE}/v2/historicalChainTvl/Solana")
    if not data:
        return {"error": "Failed to fetch TVL"}
    recent = data[-30:]
    current = recent[-1]["tvl"]
    tvl_14d = recent[-14]["tvl"] if len(recent) >= 14 else recent[0]["tvl"]
    tvl_30d = recent[0]["tvl"]
    return {
        "current_tvl": current,
        "tvl_14d_ago": tvl_14d,
        "tvl_30d_ago": tvl_30d,
        "change_14d_pct": round(((current - tvl_14d) / tvl_14d) * 100, 2),
        "change_30d_pct": round(((current - tvl_30d) / tvl_30d) * 100, 2),
        "data_points": [{"date": d["date"], "tvl": d["tvl"]} for d in recent],
    }


def get_top_protocols(limit: int = 30) -> list[dict]:
    """Get top Solana protocols sorted by 7d TVL change."""
    data = _get(f"{DEFILLAMA_BASE}/protocols")
    if not data:
        return []
    solana = [
        p for p in data
        if "Solana" in (p.get("chains") or []) and (p.get("tvl") or 0) > 1_000_000
    ]
    for p in solana:
        p["_change_7d"] = p.get("change_7d") or 0
    solana.sort(key=lambda x: abs(x["_change_7d"]), reverse=True)
    return [
        {
            "name": p["name"],
            "category": p.get("category", "Unknown"),
            "tvl": round(p.get("tvl", 0)),
            "change_1d": round(p.get("change_1d") or 0, 2),
            "change_7d": round(p.get("change_7d") or 0, 2),
            "chains": p.get("chains", []),
            "url": p.get("url", ""),
        }
        for p in solana[:limit]
    ]


def get_yield_opportunities(limit: int = 20) -> list[dict]:
    """Get top Solana DeFi yield opportunities."""
    data = _get("https://yields.llama.fi/pools")
    if not data or not isinstance(data, dict):
        return []
    pools = data.get("data", [])
    solana_pools = [
        p for p in pools
        if p.get("chain") == "Solana" and (p.get("tvlUsd") or 0) > 500_000
    ]
    solana_pools.sort(key=lambda x: abs(x.get("apyMean30d") or 0), reverse=True)
    return [
        {
            "pool": p.get("pool", ""),
            "project": p.get("project", ""),
            "symbol": p.get("symbol", ""),
            "tvl_usd": round(p.get("tvlUsd", 0)),
            "apy": round(p.get("apy") or 0, 2),
            "apy_mean_30d": round(p.get("apyMean30d") or 0, 2),
            "apy_change_7d": round((p.get("apy") or 0) - (p.get("apyMean30d") or 0), 2),
        }
        for p in solana_pools[:limit]
    ]


def get_stablecoin_flows() -> dict:
    """Get stablecoin activity on Solana."""
    data = _get("https://stablecoins.llama.fi/stablecoins?includePrices=true")
    if not data:
        return {"error": "Failed to fetch stablecoin data"}
    stables = data.get("peggedAssets", [])
    solana_stables = []
    for s in stables:
        chains = s.get("chainCirculating", {})
        if "Solana" in chains:
            sol_data = chains["Solana"]
            current = sum(v.get("current", {}).get("peggedUSD", 0) for v in [sol_data] if isinstance(sol_data, dict))
            solana_stables.append({
                "name": s.get("name", ""),
                "symbol": s.get("symbol", ""),
                "circulating_on_solana": current,
            })
    solana_stables.sort(key=lambda x: x["circulating_on_solana"], reverse=True)
    return {"stablecoins": solana_stables[:10]}


def get_network_performance() -> dict:
    """Get Solana network performance metrics via RPC."""
    try:
        resp = httpx.post(
            SOLANA_RPC,
            json={"jsonrpc": "2.0", "id": 1, "method": "getRecentPerformanceSamples", "params": [10]},
            timeout=TIMEOUT,
        )
        samples = resp.json().get("result", [])
        if not samples:
            return {"error": "No performance data"}
        avg_tps = sum(s["numTransactions"] / s["samplePeriodSecs"] for s in samples) / len(samples)
        return {
            "avg_tps": round(avg_tps),
            "samples": len(samples),
        }
    except Exception as e:
        return {"error": str(e)}


def collect() -> dict:
    """Collect all onchain signals."""
    print("[onchain] Collecting signals...")
    signals = {
        "tvl": get_solana_tvl_history(),
        "top_protocols": get_top_protocols(),
        "yields": get_yield_opportunities(),
        "stablecoins": get_stablecoin_flows(),
        "network": get_network_performance(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    proto_count = len(signals["top_protocols"])
    yield_count = len(signals["yields"])
    print(f"  [onchain] Got TVL data, {proto_count} protocols, {yield_count} yield pools")
    return signals
