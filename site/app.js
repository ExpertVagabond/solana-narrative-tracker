(function () {
    "use strict";

    const $ = (s) => document.querySelector(s);
    const $$ = (s) => document.querySelectorAll(s);

    // Formatters
    function fmtUSD(n) {
        if (n == null) return "\u2014";
        if (n >= 1e9) return "$" + (n / 1e9).toFixed(2) + "B";
        if (n >= 1e6) return "$" + (n / 1e6).toFixed(1) + "M";
        if (n >= 1e3) return "$" + (n / 1e3).toFixed(1) + "K";
        return "$" + n.toFixed(2);
    }
    function fmtChange(n) {
        if (n == null) return "";
        const cls = n >= 0 ? "positive" : "negative";
        const sign = n >= 0 ? "+" : "";
        return `<span class="${cls}">${sign}${n.toFixed(1)}%</span>`;
    }
    function timeAgo(iso) {
        if (!iso) return "";
        const diff = Math.floor((Date.now() - new Date(iso)) / 1000);
        if (diff < 3600) return Math.floor(diff / 60) + "m ago";
        if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
        return Math.floor(diff / 86400) + "d ago";
    }

    // SVG Sparkline
    function renderSparkline(container, dataPoints) {
        if (!dataPoints || dataPoints.length < 2) return;
        const values = dataPoints.map((d) => d.tvl || d);
        const w = 200, h = 32, pad = 2;
        const min = Math.min(...values), max = Math.max(...values);
        const range = max - min || 1;
        const pts = values.map((v, i) => {
            const x = pad + (i / (values.length - 1)) * (w - 2 * pad);
            const y = h - pad - ((v - min) / range) * (h - 2 * pad);
            return `${x.toFixed(1)},${y.toFixed(1)}`;
        });
        const isUp = values[values.length - 1] >= values[0];
        const color = isUp ? "#22c55e" : "#ef4444";
        const fillPts = pts.join(" ") + ` ${w - pad},${h} ${pad},${h}`;
        container.innerHTML = `
            <svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
                <defs>
                    <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="${color}" stop-opacity="0.2"/>
                        <stop offset="100%" stop-color="${color}" stop-opacity="0"/>
                    </linearGradient>
                </defs>
                <polygon points="${fillPts}" fill="url(#sparkFill)"/>
                <polyline points="${pts.join(" ")}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>`;
    }

    // Signal Strength Ring
    function signalRing(strength) {
        const pct = strength / 10;
        const r = 18, circ = 2 * Math.PI * r;
        const offset = circ * (1 - pct);
        const color = strength >= 8 ? "#14F195" : strength >= 6 ? "#9945FF" : "#eab308";
        return `
            <div class="signal-ring">
                <svg viewBox="0 0 44 44">
                    <circle cx="22" cy="22" r="${r}" class="signal-ring-bg"/>
                    <circle cx="22" cy="22" r="${r}" class="signal-ring-value"
                        stroke="${color}" stroke-dasharray="${circ.toFixed(1)}" stroke-dashoffset="${offset.toFixed(1)}"/>
                </svg>
                <div class="signal-ring-label" style="color:${color}">${strength}</div>
            </div>`;
    }

    // Metrics
    function renderMetrics(data) {
        const sol = data.highlights?.sol_price || {};
        const tvl = data.highlights?.tvl || {};
        const analysis = data.analysis || {};

        if (sol.price_usd) {
            $("#sol-price").textContent = "$" + sol.price_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            $("#sol-change").innerHTML = fmtChange(sol.change_7d);
            $("#sol-change").className = "metric-change " + (sol.change_7d >= 0 ? "positive" : "negative");
            $("#sol-sub").textContent = `MCap: ${fmtUSD(sol.market_cap)} · Vol: ${fmtUSD(sol.volume_24h)}`;
        }

        if (tvl.current_tvl) {
            $("#sol-tvl").textContent = fmtUSD(tvl.current_tvl);
            $("#tvl-change").innerHTML = fmtChange(tvl.change_14d_pct);
            $("#tvl-change").className = "metric-change " + (tvl.change_14d_pct >= 0 ? "positive" : "negative");
            if (tvl.data_points) renderSparkline($("#tvl-sparkline"), tvl.data_points);
        }

        const narratives = analysis.narratives || [];
        $("#narrative-count").textContent = narratives.length;
        if (analysis.period) $("#period-label").textContent = analysis.period;

        const tps = data.highlights?.network?.avg_tps;
        if (tps) $("#net-tps").textContent = tps.toLocaleString();

        // Agent badge
        const agent = analysis.meta?.agent;
        if (agent) $("#analysis-agent").textContent = agent;
    }

    // Category Filters
    let allNarratives = [];
    function renderFilters(narratives) {
        const categories = [...new Set(narratives.map((n) => n.category))];
        const chips = $("#filter-chips");
        chips.innerHTML = '<button class="chip active" data-filter="all">All</button>' +
            categories.map((c) => `<button class="chip" data-filter="${c}">${c}</button>`).join("");

        chips.addEventListener("click", (e) => {
            const btn = e.target.closest(".chip");
            if (!btn) return;
            chips.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
            btn.classList.add("active");
            const filter = btn.dataset.filter;
            $$(".narrative-card").forEach((card) => {
                card.classList.toggle("hidden", filter !== "all" && card.dataset.category !== filter);
            });
        });
    }

    // Narratives
    function renderNarratives(narratives) {
        allNarratives = narratives;
        const grid = $("#narratives-grid");
        if (!narratives?.length) {
            grid.innerHTML = '<div class="loading-state"><p>No narratives detected. Run the pipeline to generate insights.</p></div>';
            return;
        }
        renderFilters(narratives);

        grid.innerHTML = narratives.map((n, idx) => `
            <div class="narrative-card" data-category="${n.category}">
                <div class="narrative-card-header">
                    <div>
                        <div class="narrative-category">${n.category || "General"}</div>
                        <div class="narrative-title">${n.title}</div>
                    </div>
                    ${signalRing(n.signal_strength)}
                </div>
                <div class="narrative-card-body">
                    <p class="narrative-summary">${n.summary}</p>

                    ${n.evidence ? `
                    <button class="collapsible-toggle" data-target="ev-${idx}">
                        <span class="arrow">&#x25B6;</span> Evidence (${n.evidence.length} signals)
                    </button>
                    <div class="collapsible-content" id="ev-${idx}">
                        <div class="evidence-list">
                            <ul>${n.evidence.map((e) => `<li>${e}</li>`).join("")}</ul>
                        </div>
                    </div>` : ""}

                    ${n.build_ideas ? `
                    <div class="build-ideas">
                        <button class="collapsible-toggle open" data-target="bi-${idx}">
                            <span class="arrow">&#x25B6;</span> Build Ideas (${n.build_ideas.length})
                        </button>
                        <div class="collapsible-content open" id="bi-${idx}">
                            ${n.build_ideas.map((idea) => `
                                <div class="idea">
                                    <div class="idea-title">${idea.title}</div>
                                    <div class="idea-desc">${idea.description}</div>
                                    <div class="idea-meta">
                                        <span class="idea-tag">${idea.complexity || "med"}</span>
                                        <span class="idea-tag">${idea.potential_impact || "med"} impact</span>
                                    </div>
                                </div>
                            `).join("")}
                        </div>
                    </div>` : ""}

                    ${n.signal_types ? `
                    <div class="signal-types">
                        ${n.signal_types.map((t) => `<span class="signal-type">${t}</span>`).join("")}
                    </div>` : ""}

                    ${n.key_projects ? `
                    <div class="key-projects">
                        Key: ${n.key_projects.map((p) => `<span>${p}</span>`).join(" · ")}
                    </div>` : ""}
                </div>
            </div>
        `).join("");

        // Collapsible handlers
        $$(".collapsible-toggle").forEach((toggle) => {
            toggle.addEventListener("click", () => {
                toggle.classList.toggle("open");
                const content = document.getElementById(toggle.dataset.target);
                if (content) content.classList.toggle("open");
            });
        });
    }

    // Data Source Health
    function renderSources(data) {
        const sources = [
            { name: "DeFiLlama", type: "Onchain", status: data.highlights?.tvl?.current_tvl ? "live" : "error" },
            { name: "Solana RPC", type: "Onchain", status: data.highlights?.network?.avg_tps ? "live" : "error" },
            { name: "GitHub API", type: "Developer", status: data.highlights?.trending_repos?.length ? "live" : "error" },
            { name: "CoinGecko", type: "Market", status: data.highlights?.sol_price?.price_usd ? "live" : "error" },
            { name: "Solana Blog", type: "Social", status: data.highlights?.recent_news?.some((n) => n.source === "Solana Foundation") ? "live" : "error" },
            { name: "Helius Blog", type: "Social", status: data.highlights?.recent_news?.some((n) => n.source === "Helius Blog") ? "live" : "partial" },
            { name: "Jupiter Research", type: "Social", status: data.highlights?.recent_news?.some((n) => n.source === "Jupiter") ? "live" : "partial" },
            { name: "SIMD GitHub", type: "Governance", status: "live" },
        ];
        const grid = $("#source-grid");
        grid.innerHTML = sources.map((s) => `
            <div class="source-item">
                <div class="source-dot ${s.status}"></div>
                <div class="source-info">
                    <div class="source-name">${s.name}</div>
                    <div class="source-type">${s.type}</div>
                </div>
            </div>
        `).join("");
    }

    // Signal Panels
    function renderMovers(movers) {
        const panel = $("#panel-movers");
        if (!movers?.length) { panel.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No data</p>"; return; }
        panel.innerHTML = `
            <table class="signal-table">
                <thead><tr><th>Protocol</th><th>Category</th><th>TVL</th><th>7d</th><th>1d</th></tr></thead>
                <tbody>${movers.map((m) => `
                    <tr>
                        <td><strong>${m.name}</strong></td>
                        <td style="font-size:0.7rem;color:var(--text-muted)">${m.category}</td>
                        <td style="font-family:var(--mono)">${fmtUSD(m.tvl)}</td>
                        <td>${fmtChange(m.change_7d)}</td>
                        <td>${fmtChange(m.change_1d)}</td>
                    </tr>
                `).join("")}</tbody>
            </table>`;
    }

    function renderRepos(repos) {
        const panel = $("#panel-repos");
        if (!repos?.length) { panel.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No data</p>"; return; }
        panel.innerHTML = `
            <table class="signal-table">
                <thead><tr><th>Repository</th><th>Stars</th><th>Lang</th><th>Pushed</th></tr></thead>
                <tbody>${repos.map((r) => `
                    <tr>
                        <td>
                            <a href="${r.url}" target="_blank" style="color:var(--accent);text-decoration:none;font-weight:500">${r.name}</a>
                            <br><span style="font-size:0.65rem;color:var(--text-muted)">${(r.description || "").substring(0, 90)}</span>
                        </td>
                        <td style="font-family:var(--mono)">${r.stars}</td>
                        <td style="font-size:0.7rem">${r.language || "\u2014"}</td>
                        <td style="font-size:0.7rem;color:var(--text-muted)">${timeAgo(r.pushed_at)}</td>
                    </tr>
                `).join("")}</tbody>
            </table>`;
    }

    function renderNews(articles) {
        const panel = $("#panel-news");
        if (!articles?.length) { panel.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No data</p>"; return; }
        panel.innerHTML = `<div style="display:flex;flex-direction:column;gap:0.5rem">
            ${articles.map((a) => `
                <div class="news-item">
                    <div>
                        <a href="${a.url}" target="_blank" class="news-title">${a.title}</a>
                        ${a.summary ? `<p class="news-summary">${a.summary.substring(0, 140)}</p>` : ""}
                    </div>
                    <span class="badge badge-outline" style="flex-shrink:0">${a.source}</span>
                </div>
            `).join("")}
        </div>`;
    }

    // Tabs
    function initTabs() {
        $$(".tab").forEach((tab) => {
            tab.addEventListener("click", () => {
                $$(".tab").forEach((t) => t.classList.remove("active"));
                $$(".tab-panel").forEach((p) => p.classList.remove("active"));
                tab.classList.add("active");
                $(`#panel-${tab.dataset.tab}`).classList.add("active");
            });
        });
    }

    // Init
    async function init() {
        initTabs();
        try {
            const resp = await fetch("data.json");
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const data = await resp.json();

            // Header
            if (data.generated_at) {
                const d = new Date(data.generated_at);
                $("#last-updated").textContent = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
            }
            const meta = data.analysis?.meta || {};
            if (meta.signals_analyzed) {
                $("#signal-count").textContent = meta.signals_analyzed + " signals";
            }

            // Summary
            if (data.analysis?.executive_summary) {
                $("#executive-summary").textContent = data.analysis.executive_summary;
            }

            renderMetrics(data);
            renderNarratives(data.analysis?.narratives || []);
            renderSources(data);
            renderMovers(data.highlights?.top_movers);
            renderRepos(data.highlights?.trending_repos);
            renderNews(data.highlights?.recent_news);

        } catch (err) {
            console.error("Load error:", err);
            $("#narratives-grid").innerHTML = '<div class="loading-state"><p>Failed to load data.json</p></div>';
        }
    }

    document.readyState === "loading"
        ? document.addEventListener("DOMContentLoaded", init)
        : init();
})();
