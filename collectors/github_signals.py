"""GitHub developer activity signal collector."""
from __future__ import annotations

import httpx
import os
from datetime import datetime, timedelta, timezone

GITHUB_API = "https://api.github.com"
TIMEOUT = 30


def _headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def _search_repos(query: str, sort: str = "stars", limit: int = 15) -> list[dict]:
    try:
        resp = httpx.get(
            f"{GITHUB_API}/search/repositories",
            params={"q": query, "sort": sort, "order": "desc", "per_page": limit},
            headers=_headers(),
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return [
            {
                "name": r["full_name"],
                "description": (r.get("description") or "")[:200],
                "stars": r["stargazers_count"],
                "forks": r["forks_count"],
                "language": r.get("language"),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
                "pushed_at": r["pushed_at"],
                "url": r["html_url"],
                "topics": r.get("topics", []),
                "open_issues": r["open_issues_count"],
            }
            for r in items
        ]
    except Exception as e:
        print(f"  [github] Search failed for '{query}': {e}")
        return []


def get_trending_new_repos() -> list[dict]:
    """Find recently created Solana repos gaining traction."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    return _search_repos(f"solana created:>{cutoff}", sort="stars")


def get_most_active_repos() -> list[dict]:
    """Find Solana repos with most recent push activity."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=14)).strftime("%Y-%m-%d")
    return _search_repos(f"solana pushed:>{cutoff}", sort="updated")


def get_high_star_repos() -> list[dict]:
    """Find top Solana repos by stars overall (ecosystem baseline)."""
    return _search_repos("solana stars:>500", sort="stars")


def get_topic_repos(topic: str, limit: int = 10) -> list[dict]:
    """Search repos for a specific Solana sub-topic."""
    return _search_repos(f"solana {topic}", sort="stars", limit=limit)


def get_ecosystem_topics() -> list[dict]:
    """Search for repos across key Solana ecosystem verticals."""
    topics = [
        "solana defi",
        "solana nft",
        "solana payments",
        "solana ai agent",
        "solana mobile",
        "solana depin",
        "solana gaming",
        "solana rwa",
        "solana blink",
        "solana token-extensions",
    ]
    results = []
    for topic in topics:
        repos = get_topic_repos(topic, limit=5)
        results.append({
            "topic": topic.replace("solana ", ""),
            "repo_count": len(repos),
            "top_repos": repos[:3],
            "total_stars": sum(r["stars"] for r in repos),
        })
    results.sort(key=lambda x: x["total_stars"], reverse=True)
    return results


def collect() -> dict:
    """Collect all GitHub signals."""
    print("[github] Collecting signals...")
    signals = {
        "trending_new": get_trending_new_repos(),
        "most_active": get_most_active_repos(),
        "high_star": get_high_star_repos(),
        "ecosystem_topics": get_ecosystem_topics(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    new_count = len(signals["trending_new"])
    active_count = len(signals["most_active"])
    print(f"  [github] Got {new_count} trending new, {active_count} most active repos")
    return signals
