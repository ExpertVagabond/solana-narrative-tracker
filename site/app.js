// Solana Narrative Tracker — Frontend
(function () {
    "use strict";

    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    function formatUSD(n) {
        if (n == null) return "—";
        if (n >= 1e9) return "$" + (n / 1e9).toFixed(2) + "B";
        if (n >= 1e6) return "$" + (n / 1e6).toFixed(1) + "M";
        if (n >= 1e3) return "$" + (n / 1e3).toFixed(1) + "K";
        return "$" + n.toFixed(2);
    }

    function formatChange(n) {
        if (n == null) return "";
        const cls = n >= 0 ? "positive" : "negative";
        const sign = n >= 0 ? "+" : "";
        return `<span class="${cls}">${sign}${n.toFixed(1)}%</span>`;
    }

    function timeAgo(iso) {
        if (!iso) return "";
        const d = new Date(iso);
        const now = new Date();
        const diff = Math.floor((now - d) / 1000);
        if (diff < 3600) return Math.floor(diff / 60) + "m ago";
        if (diff < 86400) return Math.floor(diff / 3600) + "h ago";
        return Math.floor(diff / 86400) + "d ago";
    }

    function renderMetrics(data) {
        const sol = data.highlights?.sol_price || {};
        const tvl = data.highlights?.tvl || {};

        $("#sol-price").textContent = sol.price_usd ? "$" + sol.price_usd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—";
        $("#sol-change").innerHTML = formatChange(sol.change_7d);
        $("#sol-change").className = "metric-change " + (sol.change_7d >= 0 ? "positive" : "negative");

        $("#sol-tvl").textContent = formatUSD(tvl.current_tvl);
        $("#tvl-change").innerHTML = formatChange(tvl.change_14d_pct);
        $("#tvl-change").className = "metric-change " + (tvl.change_14d_pct >= 0 ? "positive" : "negative");

        const analysis = data.analysis || {};
        const narrativeCount = (analysis.narratives || []).length;
        $("#narrative-count").textContent = narrativeCount;

        const tps = data.highlights?.network?.avg_tps;
        if (tps) $("#net-tps").textContent = tps.toLocaleString();
    }

    function renderNarratives(narratives) {
        const grid = $("#narratives-grid");
        if (!narratives || narratives.length === 0) {
            grid.innerHTML = '<div class="loading-state"><p>No narratives detected yet. Run the analysis pipeline to generate insights.</p></div>';
            return;
        }

        grid.innerHTML = narratives.map((n) => `
            <div class="narrative-card">
                <div class="narrative-header">
                    <div>
                        <div class="narrative-category">${n.category || "General"}</div>
                        <div class="narrative-title">${n.title}</div>
                    </div>
                    <div class="signal-badge ${n.signal_strength >= 7 ? "high" : ""}">${n.signal_strength}</div>
                </div>
                <p class="narrative-summary">${n.summary}</p>
                ${n.evidence ? `
                <div class="evidence-list">
                    <h4>Key Evidence</h4>
                    <ul>${n.evidence.map((e) => `<li>${e}</li>`).join("")}</ul>
                </div>` : ""}
                ${n.build_ideas ? `
                <div class="build-ideas">
                    <h4>Build Ideas</h4>
                    ${n.build_ideas.map((idea) => `
                        <div class="idea">
                            <div class="idea-title">${idea.title}</div>
                            <div class="idea-desc">${idea.description}</div>
                            <div class="idea-meta">
                                <span class="idea-tag">${idea.complexity || "medium"} complexity</span>
                                <span class="idea-tag">${idea.potential_impact || "medium"} impact</span>
                            </div>
                        </div>
                    `).join("")}
                </div>` : ""}
                ${n.signal_types ? `
                <div class="signal-types">
                    ${n.signal_types.map((t) => `<span class="signal-type">${t}</span>`).join("")}
                </div>` : ""}
            </div>
        `).join("");
    }

    function renderMovers(movers) {
        const panel = $("#panel-movers");
        if (!movers || movers.length === 0) {
            panel.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No data available</p>";
            return;
        }
        panel.innerHTML = `
            <table class="signal-table">
                <thead><tr><th>Protocol</th><th>Category</th><th>TVL</th><th>7d Change</th><th>1d Change</th></tr></thead>
                <tbody>
                    ${movers.map((m) => `
                        <tr>
                            <td><strong>${m.name}</strong></td>
                            <td>${m.category}</td>
                            <td>${formatUSD(m.tvl)}</td>
                            <td>${formatChange(m.change_7d)}</td>
                            <td>${formatChange(m.change_1d)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>`;
    }

    function renderRepos(repos) {
        const panel = $("#panel-repos");
        if (!repos || repos.length === 0) {
            panel.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No data available</p>";
            return;
        }
        panel.innerHTML = `
            <table class="signal-table">
                <thead><tr><th>Repository</th><th>Stars</th><th>Language</th><th>Last Push</th></tr></thead>
                <tbody>
                    ${repos.map((r) => `
                        <tr>
                            <td><a href="${r.url}" target="_blank" style="color:var(--accent);text-decoration:none">${r.name}</a><br><span style="font-size:0.7rem;color:var(--text-muted)">${(r.description || "").substring(0, 80)}</span></td>
                            <td>${r.stars}</td>
                            <td>${r.language || "—"}</td>
                            <td>${timeAgo(r.pushed_at)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>`;
    }

    function renderNews(articles) {
        const panel = $("#panel-news");
        if (!articles || articles.length === 0) {
            panel.innerHTML = "<p style='color:var(--text-muted);padding:1rem'>No data available</p>";
            return;
        }
        panel.innerHTML = `
            <div style="display:flex;flex-direction:column;gap:0.5rem">
                ${articles.map((a) => `
                    <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-sm);padding:0.8rem">
                        <div style="display:flex;justify-content:space-between;align-items:start;gap:0.5rem">
                            <div>
                                <a href="${a.url}" target="_blank" style="color:var(--text);text-decoration:none;font-weight:500;font-size:0.85rem">${a.title}</a>
                                ${a.summary ? `<p style="font-size:0.75rem;color:var(--text-muted);margin-top:0.3rem">${a.summary.substring(0, 120)}...</p>` : ""}
                            </div>
                            <span class="badge badge-outline">${a.source}</span>
                        </div>
                    </div>
                `).join("")}
            </div>`;
    }

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

    async function init() {
        initTabs();

        try {
            const resp = await fetch("data.json");
            if (!resp.ok) throw new Error("Failed to load data");
            const data = await resp.json();

            // Update header
            const gen = data.generated_at;
            if (gen) {
                const d = new Date(gen);
                $("#last-updated").textContent = "Updated " + d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
            }

            const analysis = data.analysis || {};
            const meta = analysis.meta || {};
            if (meta.signals_analyzed) {
                $("#signal-count").textContent = meta.signals_analyzed + " signals analyzed";
            }

            // Summary
            if (analysis.executive_summary) {
                $("#executive-summary").textContent = analysis.executive_summary;
            }

            // Metrics
            renderMetrics(data);

            // Narratives
            renderNarratives(analysis.narratives || []);

            // Signal panels
            renderMovers(data.highlights?.top_movers);
            renderRepos(data.highlights?.trending_repos);
            renderNews(data.highlights?.recent_news);

        } catch (err) {
            console.error("Failed to load data:", err);
            $("#narratives-grid").innerHTML = '<div class="loading-state"><p>Failed to load data. Please check that data.json exists.</p></div>';
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
