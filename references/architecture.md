# /wissenschaft Architektur — Wie das Tool funktioniert

## Pipeline

```
User: /wissenschaft "query" --tiefe standard
         │
         ▼
   query_analyzer.py  ← Boolean, Domain, Synonyme
         │
         ▼
   source_router.py    ← knowledge_registry.yaml (105 Quellen)
         │
    ┌────┼────┐
    ▼    ▼    ▼
   MCP  OpenAlex Direct
 (20)  (10 reg.) (8 REST)
         │
         ▼
   deduplicator.py     ← DOI + Titel-Fuzzy (0.70)
         │
         ▼
   ranker.py           ← Citations + Recency + OA-Bonus
         │
         ▼
   formatter.py        ← .md + .bib + .ris + .json + DOI-verify
         │
         ▼
   qdrant_save.py      ← Vektorisierung (384-dim, Port 6335)
```

## Schichten

| Schicht | Was | Wann |
|---------|-----|------|
| MCP paper-search | 20 Quellen direkt | Immer (TIER 1) |
| OpenAlex-Abdeckung | 10 regionale Quellen | Automatisch via MCP |
| Direct REST | 8 Quellen eigener Client | TIER 2/3 |
| Manuell | 5 Quellen (no API) | Nur explizit |

## Entscheidungen

- **Kein API-Key nötig:** Alles via MCP paper-search
- **0.70 Dedup-Schwelle:** Fängt "FVG Detection in NASDAQ" ≈ "Detection of Fair Value Gaps"
- **Word-Boundary Domain-Matching:** `\b` Regex verhindert "es" in "processes" → "trading"
- **Semantic Scholar = degraded:** Wenn 0 Treffer, Warnung statt Fehler
