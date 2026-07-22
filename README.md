# 🔬 wissenschaft

<p align="center">
  <b>Multi-Source Scientific Research Pipeline</b><br>
  Domain Detection → Parallel Search → Dedup → Rank → Export<br><br>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/sources-30%2B-orange" alt="Sources">
  <img src="https://img.shields.io/badge/zero%20API%20keys-✅-brightgreen" alt="Zero API Keys">
</p>

---

## What It Does

`wissenschaft` takes a research question and runs it through a multi-stage pipeline:

```
"LLM hallucination benchmark"
        │
        ▼
  Domain Detection ("ai") + Query Expansion
        │
        ▼
  Parallel Search (DDGS web search)
        │
        ▼
  Fuzzy Deduplication (DOI + Title 0.70)
        │
        ▼
  Relevance Ranking (Citations + Recency + Authority)
        │
        ▼
  Export (.md report + .json data + Qdrant vector storage)
```

## Quick Start

```bash
# Clone
git clone https://github.com/nessos666/wissenschaft.git
cd wissenschaft

# Install
pip install ddgs

# Search (zero API keys needed)
python3 wissenschaft_cli.py "transformer attention mechanism survey" --tiefe standard

# Search with JSON output
python3 wissenschaft_cli.py "your topic" --tiefe tief --format json --output results.json

# Generate search plan (for MCP paper-search)
python3 wissenschaft_cli.py "your topic" --plan
```

## Usage

| Command | What it does |
|---------|-------------|
| `wissenschaft_cli.py "QUERY" --tiefe schnell` | Quick search (~20 results) |
| `wissenschaft_cli.py "QUERY" --tiefe standard` | Standard depth (~50 results) |
| `wissenschaft_cli.py "QUERY" --tiefe tief` | Deep search (~100 results) |
| `wissenschaft_cli.py "QUERY" --plan` | JSON search plan only (no execution) |
| `wissenschaft_cli.py "QUERY" --format json` | JSON output instead of Markdown |
| `qdrant_save.py --input results.json` | Save papers to Qdrant vector DB |
| `qdrant_save.py --list-collections` | List all Qdrant collections |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  PHASE 1 — QUERY ANALYSIS                              │
│  query_analyzer.py  →  Boolean parsing, Domain detect  │
│  source_router.py   →  knowledge_registry.yaml (30+)   │
│                        Tier 1: Always (6 sources)       │
│                        Tier 2: Domain-specific (10+)    │
│                        Tier 3: Fallback (< 10 hits)     │
│                        Tier 4: Manual only              │
└──────────────────┬──────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 2 — PARALLEL SEARCH                             │
│  Option A: DDGS web search (zero API keys, always works)│
│  Option B: MCP paper-search (20 sources parallel)       │
│  → 5 async dispatchers                                  │
└──────────────────┬──────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 3 — DEDUPLICATE & RANK                          │
│  deduplicator.py  →  DOI + Fuzzy Title (0.70 threshold) │
│  ranker.py        →  Citations + Recency + URL Authority│
└──────────────────┬──────────────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────────────┐
│  PHASE 4 — EXPORT                                      │
│  formatter.py     →  .md report + .json data            │
│  qdrant_save.py   →  384-dim vector storage (optional)  │
└─────────────────────────────────────────────────────────┘
```

## Domain Detection

Uses `\b` word-boundary regex. 8 domains auto-detected from query text:

| Domain | Example Triggers | Tier-2 Sources |
|--------|-----------------|----------------|
| **ai** | LLM, transformer, GPT, Claude, Kimi, DeepSeek, hallucination | arXiv, GitHub, PapersWithCode, HuggingFace |
| **trading** | FVG, ICT, microstructure, backtest, order flow | SSRN, arXiv, GitHub |
| **medical** | clinical trial, diagnosis, therapy | PubMed, medRxiv, Cochrane |
| **physics** | quantum, relativity, entropy | arXiv, Inspire |
| **biology** | genome, DNA, RNA, protein | PubMed, bioRxiv |
| **economics** | GDP, inflation, stock market | SSRN, RePEc, NBER |
| **chemistry** | molecule, catalyst, polymer | ChemRxiv, PubChem |
| **computer_science** | algorithm, compiler, distributed | arXiv, DBLP, GitHub |

## Qdrant Integration (Optional)

```bash
# Save papers to Qdrant vector DB (384-dim, Cosine distance)
echo '{"papers":[{"title":"Example Paper","doi":"10.1234/x","abstract":"Lorem ipsum...","source":"arxiv","year":"2026"}]}' > papers.json
python3 qdrant_save.py --input papers.json --collection my_research

# List all collections
python3 qdrant_save.py --list-collections
```

Requires Qdrant running on `localhost:6333`. Hash-based 384-dim vectors — no `sentence-transformers` needed.

## Hermes Agent Integration

This tool is also a skill for [Hermes Agent](https://hermes-agent.nousresearch.com). Load with:

```
/skill wissenschaft
/wissenschaft "your query" --tiefe tief
```

## Requirements

| Component | Required? | Notes |
|-----------|-----------|-------|
| Python 3.10+ | ✅ | — |
| `ddgs` | ✅ | `pip install ddgs` |
| Qdrant | ❌ Optional | For vector storage |
| MCP paper-search | ❌ Optional | For 20-source parallel search |
| `sentence-transformers` | ❌ Not needed | Hash-based fallback used |

## File Overview

```
wissenschaft/
├── wissenschaft_cli.py        🔧 Main CLI (270 lines)
├── qdrant_save.py             📦 Qdrant vector storage
├── knowledge_registry.yaml    📚 30+ academic sources, 4 tiers
├── README.md                  📖 You are here
├── LICENSE                    ⚖️ MIT
├── .gitignore
├── scripts/
│   ├── query_analyzer.py      🧠 Boolean parsing + domain detection
│   ├── ranker.py              📊 Relevance ranking
│   ├── deduplicator.py        🔍 Fuzzy deduplication
│   └── formatter.py           📝 Markdown/JSON export
└── references/
    ├── architecture.md        🏗️ Pipeline design document
    └── v3-architecture.md     🔬 7-phase orchestrator design
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Zero API keys (DDGS fallback) | Works anywhere, no billing, no registration |
| 0.70 dedup threshold | Sweet spot — catches "FVG Detection in NASDAQ" ≈ "Detection of Fair Value Gaps" |
| `\b` word-boundary regex | Prevents "es" in "processes" matching as trading keyword |
| 24h SQLite cache | Second identical search = instant (155ms → 5ms) |
| Hash-based 384-dim vectors | No sentence-transformers dependency for Qdrant |
| Semantic Scholar = "degraded" | Returns 0 without API key — graceful degradation |

## License

MIT — use freely, modify, distribute. See [LICENSE](LICENSE).

---

<p align="center">
  <sub>Part of the Hermes Agent ecosystem · Built for researchers who want answers, not API bills</sub>
</p>
