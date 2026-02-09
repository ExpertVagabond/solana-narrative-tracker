"""Social and news signal collector — RSS feeds + ecosystem blogs."""
from __future__ import annotations

import httpx
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

TIMEOUT = 20

RSS_FEEDS = [
    ("Solana Foundation", "https://solana.com/news/rss.xml"),
    ("Helius Blog", "https://www.helius.dev/blog/rss.xml"),
    ("Jito Blog", "https://www.jito.network/blog/rss.xml"),
    ("Marinade", "https://blog.marinade.finance/rss/"),
    ("Jupiter", "https://www.jupresear.ch/latest.rss"),
]

NEWS_FEEDS = [
    ("CoinDesk Solana", "https://www.coindesk.com/tag/solana/feed/"),
    ("TheBlock", "https://www.theblock.co/rss/all"),
]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()[:500]


def _parse_rss(source: str, url: str) -> list[dict]:
    """Parse an RSS feed and extract articles."""
    try:
        resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            pub_date = item.findtext("pubDate", "")
            description = _strip_html(item.findtext("description", ""))
            if title:
                items.append({
                    "source": source,
                    "title": title.strip(),
                    "url": link.strip(),
                    "published": pub_date.strip(),
                    "summary": description,
                })
        return items[:10]
    except Exception as e:
        print(f"  [social] RSS failed for {source}: {e}")
        return []


def _parse_atom(source: str, url: str) -> list[dict]:
    """Parse an Atom feed."""
    try:
        resp = httpx.get(url, timeout=TIMEOUT, follow_redirects=True)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = []
        for entry in root.findall("atom:entry", ns):
            title = entry.findtext("atom:title", "", ns)
            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            updated = entry.findtext("atom:updated", "", ns)
            summary = _strip_html(entry.findtext("atom:summary", "", ns))
            if title:
                items.append({
                    "source": source,
                    "title": title.strip(),
                    "url": link.strip(),
                    "published": updated.strip(),
                    "summary": summary,
                })
        return items[:10]
    except Exception:
        return _parse_rss(source, url)


def get_ecosystem_articles() -> list[dict]:
    """Collect articles from Solana ecosystem blogs."""
    all_articles = []
    for source, url in RSS_FEEDS:
        articles = _parse_rss(source, url)
        if not articles:
            articles = _parse_atom(source, url)
        all_articles.extend(articles)
    return all_articles


def get_news_articles() -> list[dict]:
    """Collect Solana-related news from crypto media."""
    all_articles = []
    for source, url in NEWS_FEEDS:
        articles = _parse_rss(source, url)
        # Filter for Solana-related articles from general feeds
        if source != "CoinDesk Solana":
            articles = [
                a for a in articles
                if any(
                    kw in (a["title"] + " " + a["summary"]).lower()
                    for kw in ["solana", "sol", "jupiter", "jito", "raydium", "phantom", "marinade"]
                )
            ]
        all_articles.extend(articles)
    return all_articles


def get_governance_proposals() -> list[dict]:
    """Check for recent Solana governance/SIMD proposals."""
    try:
        resp = httpx.get(
            "https://api.github.com/repos/solana-foundation/solana-improvement-documents/pulls",
            params={"state": "open", "sort": "created", "direction": "desc", "per_page": 10},
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        prs = resp.json()
        return [
            {
                "title": pr["title"],
                "url": pr["html_url"],
                "created_at": pr["created_at"],
                "user": pr["user"]["login"],
                "labels": [l["name"] for l in pr.get("labels", [])],
            }
            for pr in prs
        ]
    except Exception as e:
        print(f"  [social] SIMD fetch failed: {e}")
        return []


def collect() -> dict:
    """Collect all social signals."""
    print("[social] Collecting signals...")
    signals = {
        "ecosystem_articles": get_ecosystem_articles(),
        "news_articles": get_news_articles(),
        "governance": get_governance_proposals(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
    eco_count = len(signals["ecosystem_articles"])
    news_count = len(signals["news_articles"])
    gov_count = len(signals["governance"])
    print(f"  [social] Got {eco_count} ecosystem articles, {news_count} news, {gov_count} governance proposals")
    return signals
