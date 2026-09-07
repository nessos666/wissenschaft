# /wissenschaft — Wissenschaftliche Recherche-Pipeline

> **Ein Slash-Command für Hermes:** `/wissenschaft <Thema>` → akademische Recherche
> mit Dossier-Erstellung. V3, eigenständiges Tool (nicht Teil von SUCHER-1000).

## Was es kann

- **Suchplan:** Query-Analyse + Quellen-Routing (MCP + Direkt-Quellen je Domäne)
- **4-Agent-Pipeline:** Researcher → Verifier → Synthesis → Reviewer
- **Evidence-Scoring:** Trust-Scores für Papers (DOI/URL/Autoren-Checks)
- **PRISMA:** Flussdiagramm + Markdown für systematische Reviews
- **Export:** Markdown-Report, BibTeX, RIS, JSON
- **Qdrant-Save:** Ergebnisse vektorisieren (optional)

## Struktur

```
12_Wissenschaft_Tool/
├── wissenschaft_cli.py      ← CLI-Einstieg (/wissenschaft)
├── orchestrator.py          ← 4-Agent-Pipeline (V3)
├── agents/                  ← researcher, verifier, synthesis, reviewer
├── query_analyzer.py        ← Query → Domänen-Rate
├── source_router.py         ← Domäne+Tiefe → Quellenliste
├── verifier.py              ← DOI/URL/Autoren-Checks + Trust-Score
├── evidence_scorer.py       ← Evidence-Bewertung
├── deduplicator.py          ← Duplikat-Erkennung
├── clusterer.py             ← Themen-Cluster
├── prisma.py                ← PRISMA-Diagramm
├── ranker.py                ← Ranking (Ausbau geplant)
├── formatter.py             ← Markdown/BibTeX/RIS/JSON-Export
├── cache.py                 ← Response-Cache (24h TTL)
├── qdrant_save.py           ← Qdrant-Vektorisierung (optional)
├── clients/                 ← Direkt-Quellen-Clients
├── skills/                  ← Domänen-Wissen (trading/physics/medicine)
├── tests/                   ← 30 Tests (Standardbibliothek-only)
└── requirements.txt         ← keine Pflicht-Abhängigkeiten
```

## Nutzung

```bash
# Suchplan anzeigen
python3 wissenschaft_cli.py "<Thema>" --tiefe standard --plan

# Pipeline mit Roh-Ergebnissen (JSON aus externer Suche)
python3 wissenschaft_cli.py "<Thema>" --orchestrate --input ergebnisse.json
```

## Git-Ordner

- Branch `main`, Code versioniert (29 Dateien)
- Dossiers/Recherche-Daten bleiben lokal (`.gitignore`) — der Ordner enthält nur Code
- Jede Verbesserung = eigener Commit (Block-Disziplin)

## Verbesserungs-Plan

Siehe `docs/plans/VERBESSERUNG.md` — priorisierte Liste (Such-Client, Robustheit,
Export, PRISMA-Verdrahtung, Git-Hygiene …), umgesetzt Block für Block.
