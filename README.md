# 🔬 /wissenschaft — Scientific Research CLI Tool

**Multi-source scientific research pipeline.** Query → Domain Detection → Parallel Search → Dedup → Rank → Export. Works with MCP paper-search (20 sources) or standalone with DDGS web search (zero API keys).

## Quick Start

```bash
# Install
pip install ddgs

# Search (DDGS fallback — no API keys needed)
python3 wissenschaft_cli.py "LLM hallucination benchmark" --tiefe schnell

# Generate search plan (for MCP paper-search)
python3 wissenschaft_cli.py "your query" --plan

# Save results to Qdrant
echo '{"papers":[{"title":"Example","doi":"10.1234/x","abstract":"...","source":"arxiv"}]}' > results.json
python3 qdrant_save.py --input results.json
```

## Modes

| Mode | Command | Output |
|------|---------|--------|
| **Search** | `wissenschaft_cli.py "QUERY" --tiefe TIEFE` | `.md` report |
| **Plan** | `wissenschaft_cli.py "QUERY" --plan` | JSON search plan |
| **Qdrant** | `qdrant_save.py --input results.json` | Vector storage |

## Architecture

```
QUERY → query_analyzer.py (Boolean + Domain)
     → source_router.py (knowledge_registry.yaml, 30+ sources)
     → async_dispatcher (parallel DDGS or MCP calls)
     → deduplicator.py (DOI + Fuzzy Title 0.70)
     → ranker.py (Citations + Recency + Authority)
     → formatter.py (.md + .json export)
     → qdrant_save.py (384-dim vector storage)
```

## Files

```
wissenschaft/
├── wissenschaft_cli.py       Main CLI entry point
├── qdrant_save.py            Qdrant vector storage (384-dim)
├── knowledge_registry.yaml   30+ academic sources, 4 tiers
├── scripts/
│   ├── query_analyzer.py     Boolean parsing + domain detection
│   ├── ranker.py             Result ranking
│   ├── deduplicator.py       Fuzzy deduplication (0.70 threshold)
│   └── formatter.py          Markdown + JSON export
├── references/
│   ├── architecture.md       Pipeline architecture
│   └── v3-architecture.md    V3 7-phase orchestrator design
└── SKILL.md                  Hermes Agent skill definition
```

## Domain Detection

Uses `\b` word-boundary regex to prevent false matches (e.g., "es" in "processes" won't trigger "trading"). 8 domains: ai, trading, medical, physics, biology, economics, chemistry, computer_science.

## Qdrant Integration

```bash
# Requires: Qdrant running on localhost:6333
python3 qdrant_save.py --input results.json --collection my_research
python3 qdrant_save.py --list-collections
```

Vector: 384-dim hash-based fallback (no sentence-transformers needed). Cosine distance.

## Requirements

- Python 3.10+
- `ddgs` (for web search fallback)
- Qdrant (optional, for vector storage)
- MCP paper-search server (optional, for 20-source parallel search)

## License

MIT — Use freely, modify, distribute.
