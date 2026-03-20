use clap::Parser;
use serde_json::{Value, json};
use std::path::PathBuf;

// ---------------------------------------------------------------------------
// Input validation helpers (defined before any handler)
// ---------------------------------------------------------------------------

const VALID_MODES: &[&str] = &["full", "collect", "analyze"];
const MAX_URL_LEN: usize = 2048;
const MAX_TOKEN_LEN: usize = 256;
const MAX_PATH_LEN: usize = 500;
const MAX_RESPONSE_SIZE: usize = 50 * 1024 * 1024; // 50MB

fn validate_mode(mode: &str) -> anyhow::Result<&str> {
    anyhow::ensure!(
        VALID_MODES.contains(&mode),
        "Invalid mode '{}': must be one of {:?}",
        mode,
        VALID_MODES
    );
    Ok(mode)
}

fn validate_url(url: &str) -> anyhow::Result<()> {
    anyhow::ensure!(!url.is_empty(), "URL must not be empty");
    anyhow::ensure!(url.len() <= MAX_URL_LEN, "URL too long");
    anyhow::ensure!(
        url.starts_with("https://") || url.starts_with("http://"),
        "URL must start with http:// or https://"
    );
    Ok(())
}

fn validate_token(token: &str) -> anyhow::Result<()> {
    anyhow::ensure!(!token.is_empty(), "Token must not be empty");
    anyhow::ensure!(token.len() <= MAX_TOKEN_LEN, "Token too long");
    anyhow::ensure!(
        token.chars().all(|c| c.is_ascii_graphic()),
        "Token contains invalid characters"
    );
    Ok(())
}

fn validate_output_path(path: &PathBuf) -> anyhow::Result<()> {
    let s = path.to_string_lossy();
    anyhow::ensure!(s.len() <= MAX_PATH_LEN, "Output path too long");
    anyhow::ensure!(
        !s.contains(".."),
        "Path traversal not allowed in output path"
    );
    Ok(())
}

fn sanitize_api_response(value: Value) -> Value {
    // Ensure response is not excessively large
    let serialized = serde_json::to_string(&value).unwrap_or_default();
    if serialized.len() > MAX_RESPONSE_SIZE {
        return json!({"error": "Response too large"});
    }
    value
}

// ---------------------------------------------------------------------------
// CLI argument parsing
// ---------------------------------------------------------------------------

#[derive(Parser)]
#[command(
    name = "narrative-tracker",
    about = "Solana ecosystem narrative detection"
)]
struct Args {
    #[arg(long, default_value = "full")]
    mode: String,
    #[arg(long, default_value = "data")]
    output: PathBuf,
    #[arg(long, default_value = "site")]
    site: PathBuf,
}

// ---------------------------------------------------------------------------
// HTTP helpers with error handling
// ---------------------------------------------------------------------------

async fn get_json(client: &reqwest::Client, url: &str) -> Value {
    if validate_url(url).is_err() {
        return json!(null);
    }
    match client.get(url).send().await {
        Ok(r) if r.status().is_success() => {
            sanitize_api_response(r.json().await.unwrap_or(json!(null)))
        }
        _ => json!(null),
    }
}

async fn get_json_auth(client: &reqwest::Client, url: &str, token: Option<&str>) -> Value {
    if validate_url(url).is_err() {
        return json!(null);
    }
    let mut req = client.get(url);
    if let Some(t) = token {
        if validate_token(t).is_ok() {
            req = req.header("Authorization", format!("Bearer {t}"));
        }
    }
    match req.send().await {
        Ok(r) if r.status().is_success() => {
            sanitize_api_response(r.json().await.unwrap_or(json!(null)))
        }
        _ => json!(null),
    }
}

async fn post_json(client: &reqwest::Client, url: &str, body: &Value) -> Value {
    if validate_url(url).is_err() {
        return json!(null);
    }
    match client.post(url).json(body).send().await {
        Ok(r) if r.status().is_success() => {
            sanitize_api_response(r.json().await.unwrap_or(json!(null)))
        }
        _ => json!(null),
    }
}

fn enc(s: &str) -> String {
    s.bytes()
        .map(|b| match b {
            b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => {
                (b as char).to_string()
            }
            _ => format!("%{:02X}", b),
        })
        .collect()
}

async fn github_signals(client: &reqwest::Client, token: Option<&str>) -> Value {
    let d30 = (chrono::Utc::now() - chrono::Duration::days(30))
        .format("%Y-%m-%d")
        .to_string();
    let d14 = (chrono::Utc::now() - chrono::Duration::days(14))
        .format("%Y-%m-%d")
        .to_string();

    let trending = get_json_auth(
        client,
        &format!(
            "https://api.github.com/search/repositories?q={}&sort=stars&per_page=15",
            enc(&format!("solana created:>{d30}"))
        ),
        token,
    )
    .await;
    let active = get_json_auth(
        client,
        &format!(
            "https://api.github.com/search/repositories?q={}&sort=updated&per_page=15",
            enc(&format!("solana pushed:>{d14}"))
        ),
        token,
    )
    .await;
    let top = get_json_auth(
        client,
        &format!(
            "https://api.github.com/search/repositories?q={}&sort=stars&per_page=10",
            enc("solana stars:>500")
        ),
        token,
    )
    .await;

    let topics = [
        "defi",
        "nft",
        "ai-agents",
        "depin",
        "rwa",
        "liquid-staking",
        "payments",
        "gaming",
        "dao",
        "privacy",
    ];
    let mut topic_data = json!({});
    for topic in topics {
        let r = get_json_auth(
            client,
            &format!(
                "https://api.github.com/search/repositories?q={}&sort=stars&per_page=5",
                enc(&format!("solana topic:{topic}"))
            ),
            token,
        )
        .await;
        topic_data[topic] = json!({"total": r["total_count"], "repos": r["items"]});
    }

    json!({"trending_new": trending["items"], "most_active": active["items"], "high_star": top["items"], "ecosystem_topics": topic_data})
}

async fn market_signals(client: &reqwest::Client) -> Value {
    let sol = get_json(client, "https://api.coingecko.com/api/v3/coins/solana").await;
    let tokens = get_json(client, "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category=solana-ecosystem&order=market_cap_desc&per_page=30").await;
    let trending = get_json(client, "https://api.coingecko.com/api/v3/search/trending").await;

    json!({
        "sol_price": sol["market_data"]["current_price"]["usd"],
        "sol_market_cap": sol["market_data"]["market_cap"]["usd"],
        "sol_24h_change": sol["market_data"]["price_change_percentage_24h"],
        "sol_7d_change": sol["market_data"]["price_change_percentage_7d"],
        "sol_30d_change": sol["market_data"]["price_change_percentage_30d"],
        "ecosystem_tokens": tokens, "trending": trending["coins"]
    })
}

async fn onchain_signals(client: &reqwest::Client) -> Value {
    let tvl = get_json(client, "https://api.llama.fi/v2/historicalChainTvl/Solana").await;
    let protocols = get_json(client, "https://api.llama.fi/protocols").await;

    let sol_protocol_count = protocols
        .as_array()
        .map(|a| {
            a.iter()
                .filter(|p| {
                    p["chains"]
                        .as_array()
                        .map(|c| c.iter().any(|ch| ch.as_str() == Some("Solana")))
                        .unwrap_or(false)
                        && p["tvl"].as_f64().unwrap_or(0.0) > 1_000_000.0
                })
                .count()
        })
        .unwrap_or(0);

    let tps = post_json(
        client,
        "https://api.mainnet-beta.solana.com",
        &json!({"jsonrpc":"2.0","id":1,"method":"getRecentPerformanceSamples","params":[5]}),
    )
    .await;

    json!({
        "tvl_history_30d": tvl.as_array().map(|a| a.len()).unwrap_or(0),
        "current_tvl": tvl.as_array().and_then(|a| a.last()).and_then(|v| v["tvl"].as_f64()),
        "top_protocols": sol_protocol_count,
        "performance_samples": tps["result"]
    })
}

async fn social_signals(client: &reqwest::Client) -> Value {
    let simds = get_json(client,
        "https://api.github.com/repos/solana-foundation/solana-improvement-documents/pulls?state=open&per_page=10").await;
    json!({
        "governance_proposals": simds.as_array().map(|a| a.iter().map(|pr| json!({
            "title": pr["title"], "user": pr["user"]["login"],
            "created_at": pr["created_at"], "url": pr["html_url"]
        })).collect::<Vec<_>>()).unwrap_or_default()
    })
}

async fn collect_all(client: &reqwest::Client, github_token: Option<&str>) -> Value {
    tracing::info!("Collecting GitHub signals...");
    let github = github_signals(client, github_token).await;
    tracing::info!("Collecting market signals...");
    let market = market_signals(client).await;
    tracing::info!("Collecting onchain signals...");
    let onchain = onchain_signals(client).await;
    tracing::info!("Collecting social signals...");
    let social = social_signals(client).await;
    json!({"collected_at": chrono::Utc::now().to_rfc3339(), "github": github, "market": market, "onchain": onchain, "social": social})
}

async fn analyze(client: &reqwest::Client, signals: &Value) -> Value {
    let api_key = std::env::var("ANTHROPIC_API_KEY").unwrap_or_default();
    if api_key.is_empty() {
        tracing::warn!("ANTHROPIC_API_KEY not set — skipping analysis");
        return json!({"narratives": [], "raw_signals": signals});
    }
    let digest = serde_json::to_string_pretty(signals).unwrap_or_default();
    let prompt = format!(
        "Analyze these Solana ecosystem signals and identify the top 5-7 emerging narratives.\n\
        For each: id, title, signal_strength (1-10), category, summary, evidence[], build_ideas[], key_projects[], risk_factors[].\n\
        Return valid JSON with a \"narratives\" array.\n\n{digest}"
    );
    let body = json!({"model":"claude-sonnet-4-5-20250929","max_tokens":8000,"messages":[{"role":"user","content":prompt}]});
    let resp = client
        .post("https://api.anthropic.com/v1/messages")
        .header("x-api-key", &api_key)
        .header("anthropic-version", "2023-06-01")
        .json(&body)
        .send()
        .await;
    match resp {
        Ok(r) if r.status().is_success() => {
            let data: Value = r.json().await.unwrap_or(json!({}));
            let text = data["content"][0]["text"].as_str().unwrap_or("{}");
            if let Some(start) = text.find('{')
                && let Some(end) = text.rfind('}')
                && let Ok(parsed) = serde_json::from_str::<Value>(&text[start..=end])
            {
                return parsed;
            }
            json!({"narratives": [], "raw_response": text})
        }
        _ => json!({"narratives": [], "error": "Claude API failed"}),
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_env_filter("info").init();
    let args = Args::parse();
    let _ = std::fs::create_dir_all(&args.output);
    let _ = std::fs::create_dir_all(&args.site);
    let client = reqwest::Client::builder()
        .user_agent("narrative-tracker/1.0")
        .build()
        .unwrap();
    let github_token = std::env::var("GITHUB_TOKEN").ok();
    let gt = github_token.as_deref();

    match args.mode.as_str() {
        "collect-only" => {
            let signals = collect_all(&client, gt).await;
            let p = args.output.join("signals.json");
            std::fs::write(&p, serde_json::to_string_pretty(&signals).unwrap()).unwrap();
            tracing::info!(path = %p.display(), "Signals saved");
        }
        "analyze-only" => {
            let sp = args.output.join("signals.json");
            let signals: Value = serde_json::from_str(
                &std::fs::read_to_string(&sp).expect("signals.json not found"),
            )
            .unwrap();
            let analysis = analyze(&client, &signals).await;
            let p = args.output.join("analysis.json");
            std::fs::write(&p, serde_json::to_string_pretty(&analysis).unwrap()).unwrap();
            tracing::info!(path = %p.display(), "Analysis saved");
        }
        _ => {
            tracing::info!("Phase 1: Collecting signals...");
            let signals = collect_all(&client, gt).await;
            std::fs::write(
                args.output.join("signals.json"),
                serde_json::to_string_pretty(&signals).unwrap(),
            )
            .unwrap();
            tracing::info!("Phase 2: Analyzing...");
            let analysis = analyze(&client, &signals).await;
            std::fs::write(
                args.output.join("analysis.json"),
                serde_json::to_string_pretty(&analysis).unwrap(),
            )
            .unwrap();
            tracing::info!("Phase 3: Generating site data...");
            let site_data = json!({
                "generated_at": chrono::Utc::now().to_rfc3339(),
                "narratives": analysis["narratives"],
                "signals_summary": {"github_trending": signals["github"]["trending_new"], "sol_price": signals["market"]["sol_price"],
                    "tvl": signals["onchain"]["current_tvl"], "governance": signals["social"]["governance_proposals"]}
            });
            std::fs::write(
                args.site.join("data.json"),
                serde_json::to_string_pretty(&site_data).unwrap(),
            )
            .unwrap();
            tracing::info!("Done");
        }
    }
}
