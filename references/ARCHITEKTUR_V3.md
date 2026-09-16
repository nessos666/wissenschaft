# /wissenschaft V3 — Architektur-Referenz

## 7-Phasen-Orchestrator

```
QUERY → Researcher → Verifier → Evidence → Synthesis → Cluster → Reviewer → PRISMA → Export
         (sucht)     (prüft)    (bewertet)  (verdichtet) (gruppiert) (qualität)  (standard)
```

### Agent-Rollen

| Agent | Input | Output |
|-------|-------|--------|
| Researcher | query, depth, domain | source_list, mcp_calls |
| Verifier | raw_results | verified_results, trust_scores 0-1 |
| Evidence | verified_results | evidence_levels (🥇Meta > 🥈Review > 🥉RCT) |
| Synthesis | verified_results, domain | executive_summary, top10, next_searches |
| Cluster | verified_results | topic_clusters, source_distribution, year_distribution |
| Reviewer | top10, stats, domain | quality_score 0-10, gaps[], recommendations[] |
| PRISMA | counts | ASCII flow diagram, Markdown table |

### Trust-Score-Formel
```
trust = DOI_verified(0.35) + URL_reachable(0.25) + Author_match(0.20) + Source_reputation(0.20)
```

### Cache-Strategie
- SQLite, 24h TTL (Standard), 7d (Tief)
- Key = sha256(query|depth)
- Zweiter Lauf: 31× speedup (155ms → 5ms)

## 105-Quellen-Registry

17 Kategorien von Universal (OpenAlex) über Lateinamerika (SciELO) bis Spezial (NDLTD).
MCP-integriert: 20 Quellen. OpenAlex-abgedeckt: 10. Direct REST: 8. Manuell: 5.

## Quellen-Tiers

| Tier | Auslöser | Beispiele |
|------|----------|-----------|
| 1 — IMMER | Jede Suche | OpenAlex, CrossRef, Semantic Scholar |
| 2 — DOMAIN | Domain-Match | arXiv, PubMed, SSRN, GitHub |
| 3 — FALLBACK | < 10 Ergebnisse | CORE, BASE, DOAJ, Zenodo |
| 4 — MANUELL | Nur explizit | Google Scholar, JSTOR, ResearchGate |

## Evidence-Hierarchie

🥇 Meta-Analysis (1.0) > 🥈 Systematic Review (0.9) > 🥉 RCT (0.85) > 📊 Cohort (0.7) > 📋 Case Study (0.4)

## Pitfalls

- **Semantic Scholar MCP liefert oft 0** → API-Key fehlt. Als "degraded" markieren, nicht als Fehler.
- **Regional-APIs instabil** (SciELO, Redalyc, J-STAGE) → via OpenAlex abgedeckt (schon in MCP-Suche).
- **sentence-transformers fehlt** → Qdrant überspringen, Ergebnisse als Datei trotzdem speichern.
- **brain_search.py findet neue Collections nicht** → Manuell in BRAINS-Liste in brain_search.py eintragen.
- **OpenAlex-Filter-Timeout** → Direkte OAI-PMH-Endpoints bevorzugen.
