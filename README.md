# Solana Narrative Tracker

Detects emerging narratives and early signals within the Solana ecosystem, refreshed fortnightly. Analyzes onchain and offchain data to surface trends early and translate them into actionable build ideas.

**Live Dashboard:** [https://solana-narrative-tracker.pages.dev](https://solana-narrative-tracker.pages.dev)

Built autonomously by an AI agent ([Claude Code](https://claude.com/claude-code)) for the [Superteam Earn](https://earn.superteam.fun) bounty.

---

## Current Detected Narratives (Feb 9, 2026)

| # | Narrative | Signal | Category |
|---|-----------|--------|----------|
| 1 | **Agentic Capital: AI Agents as On-Chain Economic Actors** | 9/10 | AI |
| 2 | **Institutional RWA Tokenization Surge** | 8/10 | Infrastructure |
| 3 | **Stablecoin Micropayments via x402** | 8/10 | Payments |
| 4 | **Privacy-First Solana Infrastructure** | 7/10 | Infrastructure |
| 5 | **Bear Market Builder Accumulation** | 7/10 | DeFi |
| 6 | **On-Chain NASDAQ: Solana as Internet Capital Markets** | 7/10 | DeFi |
| 7 | **Post-Quantum Protocol Hardening** | 6/10 | Infrastructure |

### Narrative 1: Agentic Capital (Signal: 9/10)

The Solana ecosystem is witnessing the emergence of "Agentic Capital" — autonomous AI agents that don't just execute trades but manage entire venture funds, hire other agents, and participate in governance. ai16z crossed $2B market cap as the first fully autonomous AI-managed venture fund. The ElizaOS framework enables multi-agent swarms, and the ongoing Solana Agent Hackathon ($100K pool) is producing production-ready agent infrastructure.

**Build Ideas:**
- **Agent Reputation Protocol** — On-chain reputation system for AI agents tracking trade performance and reliability
- **Agent Treasury Dashboard** — Real-time monitoring for autonomous agent wallets (Dune Analytics for AI agents)
- **ElizaOS Plugin Marketplace** — Curated marketplace for agent plugins with SOL monetization
- **Agent-to-Agent Payment Rails** — Machine-to-machine micropayment protocol complementing x402

### Narrative 2: Institutional RWA Tokenization (Signal: 8/10)

Real-world asset tokenization on Solana has crossed $1.3B, with WisdomTree deploying its full suite of regulated tokenized funds and Ondo enabling access to 200+ U.S. stocks and ETFs. Fireblocks provides institutional-grade treasury infrastructure.

**Build Ideas:**
- **RWA Yield Aggregator** — Aggregate yields from tokenized treasuries across WisdomTree, Ondo
- **Tokenized Stock Portfolio Tracker** — Unified dashboard for tokenized equity positions
- **RWA Collateral Bridge** — Use tokenized RWAs as DeFi collateral on Solana

### Narrative 3: Stablecoin Micropayments via x402 (Signal: 8/10)

Coinbase's x402 protocol enables HTTP-native stablecoin micropayments — average transaction $0.06. Stablecoin turnover on Solana runs 2-3x faster than Ethereum. Standard Chartered has called the shift from "memecoins to micropayments" as Solana's defining 2026 transition.

**Build Ideas:**
- **x402-Powered API Monetization Platform** — Let developers monetize APIs with stablecoin payments
- **Micropayment Content Wall** — Pay-per-article with instant Solana settlement
- **Cross-Stablecoin Payment Router** — Accept any stablecoin, settle in merchant's preference

### Narrative 4: Privacy-First Infrastructure (Signal: 7/10)

GhostWareOS provides full-stack privacy (payments, swaps, messaging) with GHOST token rallying 60%. A $70K Solana privacy hackathon just concluded. Enterprise pilots are live — Zebec running private payroll.

**Build Ideas:**
- **Privacy-Preserving DeFi Aggregator** — Route through shielded pools without exposing wallet history
- **Confidential DAO Voting** — ZK voting for Solana DAOs
- **Selective Disclosure Identity Layer** — Prove attributes without revealing personal data

### Narrative 5: Bear Market Builder Accumulation (Signal: 7/10)

SOL down 39% in 30 days, TVL -27%, yet 15 new trending repos, 5 active SIMDs, and protocols like Sentora growing 85.9% in 7 days. Classic builder season.

**Build Ideas:**
- **Solana Builder Activity Index** — Quantified "builder confidence" metric
- **Bear Market Grant Aggregator** — Curated listing of active grants and bounties
- **Protocol Risk Dashboard** — Real-time risk monitoring for Solana DeFi

### Narrative 6: On-Chain NASDAQ (Signal: 7/10)

Convergence of tokenized stocks, prediction markets (DFlow/Kalshi), proprietary AMMs, and staking ETFs positions Solana as an on-chain NASDAQ.

**Build Ideas:**
- **Unified Trading Terminal** — Single interface for stocks, crypto, prediction markets on Solana
- **On-Chain Payment for Order Flow** — PFOF economics for DEX aggregators
- **Prediction Market Builder Kit** — SDK for custom prediction markets with oracle integration

### Narrative 7: Post-Quantum Protocol Hardening (Signal: 6/10)

SIMD-0461 proposes Falcon signature verification (post-quantum cryptography) as a precompile. Forward-looking governance that few L1s are pursuing.

**Build Ideas:**
- **Quantum-Ready Wallet** — Support both Ed25519 and post-quantum Falcon signatures
- **SIMD Governance Tracker** — Dashboard for all Solana Improvement Documents

---

## Data Sources

| Source | Type | Data Collected | Auth Required |
|--------|------|----------------|---------------|
| [DeFiLlama](https://defillama.com) | Onchain | TVL history, protocol metrics, yield pools, stablecoin flows | No |
| [Solana RPC](https://api.mainnet-beta.solana.com) | Onchain | Network TPS, performance samples | No |
| [GitHub API](https://api.github.com) | Developer | Trending repos, commit activity, topic analysis | Optional |
| [CoinGecko](https://coingecko.com) | Market | Token prices, market caps, volume, category data | No |
| [Solana Foundation Blog](https://solana.com/news) | Social | Ecosystem announcements, partnerships, technical updates | No |
| [Helius Blog](https://helius.dev/blog) | Social | Developer-focused ecosystem analysis | No |
| [Jupiter Research](https://jupresear.ch) | Social | DeFi research, community proposals | No |
| [SIMD GitHub](https://github.com/solana-foundation/solana-improvement-documents) | Governance | Protocol improvement proposals | No |

## How Signals Are Detected and Ranked

### Collection Phase
1. **Onchain signals** are collected from DeFiLlama (TVL trends, protocol growth rates, yield shifts, stablecoin circulation) and the Solana RPC (network performance)
2. **Developer signals** are collected from GitHub — new repo creation, star velocity, commit frequency, and topic distribution across the Solana ecosystem
3. **Market signals** come from CoinGecko — token price movements, volume changes, category rotation, and trending assets
4. **Social signals** are collected from RSS feeds (ecosystem blogs, governance proposals) and supplemented with web news monitoring

### Analysis Phase
Signals are synthesized using AI analysis (Claude) that:
- **Cross-correlates** signals across all four categories (a narrative supported by onchain + developer + social data ranks higher than one from a single source)
- **Prioritizes novelty** — emerging trends that aren't yet mainstream consensus receive higher signal strength scores
- **Scores signal strength 1-10** based on: evidence breadth, data recency, cross-source correlation, and magnitude of change
- **Generates build ideas** that are concrete, actionable, and tied to specific signals — not generic "build a DeFi protocol" suggestions

### Ranking Criteria
- **Signal Strength 8-10:** Strong cross-source evidence, significant magnitude, novel narrative
- **Signal Strength 5-7:** Emerging trend with supporting evidence from 2+ sources
- **Signal Strength 1-4:** Early signal, limited evidence (not included in output)

## How to Run

### Prerequisites
- Python 3.9+
- `pip install -r requirements.txt`

### Quick Start
```bash
# Full run: collect signals + analyze + generate site
python main.py

# Collect signals only (no API key needed)
python main.py --collect-only

# Analyze only (requires existing signals.json and ANTHROPIC_API_KEY)
python main.py --analyze-only
```

### Environment Variables
```bash
# Required for AI-powered analysis
export ANTHROPIC_API_KEY=sk-ant-...

# Optional: increases GitHub API rate limits (60/hr -> 5000/hr)
export GITHUB_TOKEN=ghp_...
```

### Automated Updates (GitHub Actions)
The included workflow runs fortnightly via GitHub Actions:
1. Collects fresh signals from all data sources
2. Analyzes signals with Claude API
3. Commits updated data to the repo
4. Deploys the updated dashboard to GitHub Pages

To enable: add `ANTHROPIC_API_KEY` as a GitHub repository secret.

## Architecture

```
solana-narrative-tracker/
├── main.py                    # Orchestrator: collect → analyze → generate
├── collectors/
│   ├── onchain.py             # DeFiLlama + Solana RPC
│   ├── github_signals.py      # GitHub Search API
│   ├── market.py              # CoinGecko
│   └── social.py              # RSS feeds + SIMD governance
├── analyzer.py                # Claude API narrative synthesis
├── site/
│   ├── index.html             # Dashboard UI
│   ├── style.css              # Solana-themed styling
│   ├── app.js                 # Data rendering
│   └── data.json              # Generated narrative data
├── data/
│   ├── signals.json           # Raw collected signals (gitignored)
│   └── analysis.json          # Structured narrative analysis
└── .github/workflows/
    └── update.yml             # Fortnightly automation
```

## License

MIT
