# Solana Narrative Tracker

**AI-powered signal detection for emerging Solana ecosystem narratives. Collects onchain, developer, market, and social signals, then uses Claude to synthesize actionable narratives with build ideas.**

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Solana](https://img.shields.io/badge/Solana-Ecosystem-9945FF?logo=solana&logoColor=white)](https://solana.com)
[![Claude](https://img.shields.io/badge/Claude-AI_Analysis-D4A574?logo=anthropic&logoColor=white)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Live Dashboard:** [solana-narrative-tracker.pages.dev](https://solana-narrative-tracker.pages.dev)

## How It Works

```
DeFiLlama + Solana RPC  ──>  Onchain Signals    \
GitHub Search API        ──>  Developer Signals    \
CoinGecko               ──>  Market Signals       ──>  Claude  ──>  Narratives
RSS Feeds + SIMDs        ──>  Social Signals      /
```

Every fortnight:
1. **Collect** raw signals from 8+ data sources (all free, no API keys for collection)
2. **Synthesize** with Claude to identify 5-8 emerging narratives
3. **Score** each narrative 1-10 based on evidence breadth and novelty
4. **Generate** concrete build ideas tied to specific signals
5. **Deploy** updated dashboard via GitHub Actions

## Data Sources

| Source | Type | Auth |
|--------|------|------|
| DeFiLlama | TVL, protocol growth, yield pools, stablecoin flows | None |
| Solana RPC | Network TPS, performance samples | None |
| GitHub API | Trending repos, commit activity, topics | Optional |
| CoinGecko | Prices, market caps, volume, categories | None |
| Solana Foundation Blog | Ecosystem announcements | None |
| Helius Blog | Developer analysis | None |
| Jupiter Research | DeFi proposals | None |
| SIMD GitHub | Protocol improvement proposals | None |

## Quick Start

```bash
git clone https://github.com/ExpertVagabond/solana-narrative-tracker.git
cd solana-narrative-tracker
pip install -r requirements.txt

# Full run: collect + analyze + generate
python main.py

# Collect only (no API key needed)
python main.py --collect-only

# Analyze only (requires ANTHROPIC_API_KEY)
python main.py --analyze-only
```

### Environment

```bash
export ANTHROPIC_API_KEY=sk-ant-...     # Required for analysis
export GITHUB_TOKEN=ghp_...             # Optional (increases rate limit)
```

## Scoring

| Score | Meaning |
|-------|---------|
| 8-10 | Strong cross-source evidence, novel narrative |
| 5-7 | Emerging trend with 2+ supporting sources |
| 1-4 | Early signal, limited evidence (excluded) |

## Architecture

```
main.py                      Orchestrator
analyzer.py                  Claude API narrative synthesis
collectors/
  onchain.py                 DeFiLlama + Solana RPC
  github_signals.py          GitHub trending repos
  market.py                  CoinGecko prices/categories
  social.py                  RSS feeds + SIMD governance
site/
  index.html                 Dashboard UI
  app.js                     Data rendering
  data.json                  Generated narratives
```

## Automated Updates

GitHub Actions workflow runs fortnightly — collects signals, analyzes with Claude, deploys to Cloudflare Pages. Add `ANTHROPIC_API_KEY` as a repository secret to enable.

## License

[MIT](LICENSE)

## Author

Built by [Purple Squirrel Media](https://purplesquirrelmedia.io)
