#!/usr/bin/env python3
"""
/wissenschaft CLI V3.1 — Rebuilt 22.07.2026
Main entry point for the scientific research pipeline.

USAGE:
  wissenschaft_cli.py "QUERY" --tiefe schnell|standard|tief [--plan]

MODES:
  --plan         Output search plan (which sources/tools to call)
  (default)      Run search + dedup + rank + format pipeline
"""

import argparse
import json
import sys
import re
import hashlib
import sqlite3
import time
from pathlib import Path
from datetime import datetime, timedelta

# === CONFIG ===
BASE_DIR = Path(__file__).resolve().parent
REGISTRY_PATH = BASE_DIR / "knowledge_registry.yaml"
CACHE_DB = BASE_DIR / "cache" / "wissenschaft_cache.db"
OUTPUT_DIR = BASE_DIR

# Source Tiers
DEFAULT_TIER1 = ["openalex", "crossref", "semantic_scholar", "arxiv", "pubmed", "ssrn"]

DOMAIN_SOURCES = {
    "trading": ["ssrn", "arxiv", "github"],
    "ai": ["arxiv", "github", "paperswithcode", "huggingface"],
    "medical": ["pubmed", "medrxiv", "cochrane"],
    "physics": ["arxiv", "inspire"],
    "chemistry": ["pubchem", "chemrxiv"],
    "biology": ["pubmed", "biorxiv"],
    "economics": ["ssrn", "repec", "nber"],
    "computer_science": ["arxiv", "github", "paperswithcode", "dblp"],
    "general": ["openalex", "crossref", "semantic_scholar"],
}

SYNONYMS = {
    "trading": ["market microstructure", "order flow", "price action", "technical analysis"],
    "ai": ["machine learning", "deep learning", "neural network", "LLM", "transformer"],
    "medical": ["clinical trial", "diagnosis", "treatment", "therapy"],
}

# === CACHE ===
def get_cache():
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, result TEXT, created_at TIMESTAMP)")
    conn.commit()
    return conn

def cache_get(key, ttl_hours=24):
    conn = get_cache()
    row = conn.execute("SELECT result, created_at FROM cache WHERE key=?", (key,)).fetchone()
    if row:
        result, created = row
        age = datetime.now() - datetime.fromisoformat(created)
        if age < timedelta(hours=ttl_hours):
            return json.loads(result)
    return None

def cache_set(key, result):
    conn = get_cache()
    conn.execute("INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                 (key, json.dumps(result), datetime.now().isoformat()))
    conn.commit()

# === DOMAIN DETECTION ===
def detect_domain(query):
    """Word-boundary domain detection. Prevents 'es' in 'processes' matching 'trading'."""
    domain_keywords = {
        "trading": [r"trading", r"market", r"order.flow", r"FVG", r"ICT", r"SMC", r"backtest",
                     r"microstructure", r"liquidity"],
        "ai": [r"LLM", r"transformer", r"GPT", r"Claude", r"Kimi", r"DeepSeek", r"Qwen", r"Mistral",
               r"Gemini", r"Grok", r"Llama", r"neural.network", r"machine.learning",
               r"deep.learning", r"attention", r"RLHF", r"fine.tun", r"agentic",
               r"hallucination", r"benchmark", r"open.weight"],
        "medical": [r"clinical.trial", r"diagnosis", r"disease", r"patient", r"surgery",
                    r"treatment", r"therapy"],
        "physics": [r"quantum", r"relativity", r"particle", r"wave.function", r"entropy"],
        "biology": [r"genome", r"DNA", r"RNA", r"protein", r"cell", r"bacteria"],
        "economics": [r"GDP", r"inflation", r"monetary", r"fiscal", r"stock.market"],
        "chemistry": [r"molecule", r"compound", r"reaction", r"catalyst"],
        "computer_science": [r"algorithm", r"compiler", r"database", r"distributed"],
    }

    query_lower = query.lower()
    scores = {}
    for domain, keywords in domain_keywords.items():
        score = 0
        for kw in keywords:
            matches = len(re.findall(r'\b' + kw + r'\b', query_lower))
            score += matches
        if score > 0:
            scores[domain] = score

    if scores:
        return max(scores, key=scores.get)
    return "general"

def expand_query(query, domain):
    """Add domain-specific synonyms to query."""
    if domain in SYNONYMS:
        extras = " OR ".join(SYNONYMS[domain][:3])
        return f"({query}) OR ({extras})"
    return query

# === SEARCH PLAN ===
def generate_plan(query, depth):
    """Generate search plan: which sources and queries to use."""
    domain = detect_domain(query)
    tier1 = DEFAULT_TIER1.copy()
    domain_specific = DOMAIN_SOURCES.get(domain, [])
    tier2 = [s for s in domain_specific if s not in tier1]
    expanded = expand_query(query, domain)

    num_results = {"schnell": 20, "standard": 50, "tief": 100}[depth]

    plan = {
        "query": query,
        "expanded_query": expanded,
        "domain": domain,
        "depth": depth,
        "num_results_target": num_results,
        "tier1_sources": tier1,
        "tier2_sources": tier2,
        "mcp_tools_to_call": [],
        "boolean_operators_detected": {
            "AND": "AND" in query.upper(),
            "OR": "OR" in query.upper(),
            "NOT": "NOT" in query.upper(),
            "negations": len(re.findall(r'-\w+', query)),
        },
        "fallback_web_searches": [],
    }

    for source in tier1:
        limit_per = max(3, num_results // len(tier1))
        plan["mcp_tools_to_call"].append({
            "tool": f"mcp__paper_search__search_{source}",
            "query": expanded,
            "limit": limit_per,
        })

    for source in tier2[:3]:
        plan["fallback_web_searches"].append({
            "search": f"{query} research paper {source}",
            "source": source,
        })

    return plan

# === PIPELINE RUNNER ===
def run_pipeline(query, depth):
    """Run full pipeline using DDGS web search fallback."""
    plan = generate_plan(query, depth)
    domain = plan["domain"]
    expanded = plan["expanded_query"]

    results = []
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(f"{expanded} research paper study {domain}",
                               max_results=plan["num_results_target"]):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")[:500],
                    "source": "web_search_ddgs",
                })
    except ImportError:
        results.append({
            "title": "DDGS not available",
            "url": "",
            "snippet": "Install with: pip install ddgs",
            "source": "error",
        })

    return {
        "plan": plan,
        "results": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }

# === DEDUPLICATOR ===
def deduplicate(results, threshold=0.70):
    """Fuzzy title deduplication using Jaccard similarity."""
    if len(results) <= 1:
        return results

    def title_similarity(a, b):
        wa = set(re.findall(r'\w+', a.lower()))
        wb = set(re.findall(r'\w+', b.lower()))
        if not wa or not wb:
            return 0
        return len(wa.intersection(wb)) / len(wa.union(wb))

    kept = []
    for r in results:
        title = r.get("title", "")
        is_dup = False
        for k in kept:
            if title_similarity(title, k.get("title", "")) > threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append(r)

    return kept

# === RANKER ===
def rank(results):
    """Rank by snippet length, URL authority, and recency heuristics."""
    scored = []
    for r in results:
        score = 0.0
        snippet = r.get("snippet", "")
        title = r.get("title", "")
        url = r.get("url", "")

        score += min(len(snippet) / 500, 1.0)
        if "arxiv" in url:
            score += 0.3
        if ".edu" in url:
            score += 0.2
        if ".org" in url:
            score += 0.1

        years = re.findall(r'(20\d{2})', snippet + " " + title)
        if years:
            most_recent = max(int(y) for y in years)
            score += max(0, (most_recent - 2020) / 10)

        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]

# === FORMATTER ===
def format_output(results, plan, output_format="md"):
    """Format results as markdown or JSON."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    domain = plan["domain"]
    query = plan["query"]
    depth = plan["depth"]

    if output_format == "json":
        return json.dumps({
            "query": query, "domain": domain, "depth": depth,
            "count": len(results), "results": results,
            "timestamp": now,
        }, indent=2, ensure_ascii=False)

    lines = [
        f"# 🔬 Wissenschaftliche Recherche: _{query}_",
        "",
        f"**Datum:** {now} | **Tiefe:** {depth} | **Domain:** {domain}",
        f"**Ergebnisse:** {len(results)} (nach Deduplizierung und Ranking)",
        "",
        "---", "",
        "## 📋 Top-Ergebnisse", "",
    ]

    for i, r in enumerate(results[:10], 1):
        title = r.get("title", "Ohne Titel")
        url = r.get("url", "")
        snippet = r.get("snippet", "")[:300]
        lines.append(f"**{i}. [{title}]({url})**")
        if snippet:
            lines.append(f"> {snippet}")
        lines.append("")

    if len(results) > 10:
        lines.append(f"*... und {len(results) - 10} weitere Ergebnisse.*\n")

    lines.extend([
        "---", "",
        "## 🔧 Suchplan", "",
        f"- **Query:** `{query}`",
        f"- **Domain:** {domain}",
        f"- **Tiefe:** {depth}",
        f"- **Tier-1:** {', '.join(plan['tier1_sources'])}",
        f"- **Tier-2:** {', '.join(plan.get('tier2_sources', [])) or 'keine'}",
        f"- **Boolean:** AND={plan['boolean_operators_detected']['AND']}, OR={plan['boolean_operators_detected']['OR']}, NOT={plan['boolean_operators_detected']['NOT']}",
        "", "---",
    ])

    return "\n".join(lines)

# === MAIN ===
def main():
    parser = argparse.ArgumentParser(description="/wissenschaft V3.1 — Wissenschaftliche Recherche")
    parser.add_argument("query", nargs="?", help="Suchbegriff (Boolean: AND, OR, NOT, -term)")
    parser.add_argument("--tiefe", choices=["schnell", "standard", "tief"], default="standard")
    parser.add_argument("--plan", action="store_true", help="NUR Suchplan ausgeben")
    parser.add_argument("--orchestrate", action="store_true", help="7-Phasen (KAPUTT)")
    parser.add_argument("--input", help="JSON-Input (fuer Orchestrator)")
    parser.add_argument("--output", help="Output-Pfad (.md oder .json)")
    parser.add_argument("--format", choices=["md", "json"], default="md")

    args = parser.parse_args()

    if not args.query:
        print(json.dumps({"error": "Kein Query. Usage: wissenschaft_cli.py 'QUERY' [--tiefe TIEFE]"}))
        sys.exit(1)

    if args.orchestrate:
        print(json.dumps({
            "warning": "Orchestrator KAPUTT (Quality 3.0/10). Phase 5b (manuelles Dossier) nutzen.",
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.plan:
        plan = generate_plan(args.query, args.tiefe)
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return plan

    output = run_pipeline(args.query, args.tiefe)
    plan = output["plan"]
    results_raw = output["results"]

    results = deduplicate(results_raw)
    results = rank(results)

    formatted = format_output(results, plan, args.format)

    safe_query = re.sub(r'[^\w]+', '_', args.query)[:50]
    ext = "json" if args.format == "json" else "md"
    
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = OUTPUT_DIR / f"wissenschaft_{safe_query}_{args.tiefe}.{ext}"

    out_path.write_text(formatted, encoding="utf-8")

    print(f"✅ {len(results)} Ergebnisse -> {out_path}")
    print(f"   Domain: {plan['domain']} | Tiefe: {args.tiefe} | Quellen: {len(plan['tier1_sources'])} T1 + {len(plan.get('tier2_sources',[]))} T2")

    return formatted

if __name__ == "__main__":
    main()
