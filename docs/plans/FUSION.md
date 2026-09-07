# FUSION — 12_Wissenschaft_Tool + paper-search-mcp (21 Quellen)

Stand: 2026-09-08. Auftrag David: „komplette Check, was fusionieren, was nicht,
eigener Git-Ordner, unabhängig von Hermes existieren."

## Ausgangslage (gemessen)

| | **12_Wissenschaft_Tool** (unsere V4) | **paper-search-mcp** (openags, v0.1.4, MIT) |
|---|---|---|
| Ort | `03_PROJEKTE/12_Wissenschaft_Tool` | `06_TECHNIK/13_MCP_Paper_Search/paper-search/paper-search-mcp` |
| Such-Quellen | 2 direkt (CrossRef + arXiv, searcher.py) | **21+** (arxiv…unpaywall, academic_platforms/) |
| Pipeline | 4-Agenten, PRISMA, Evidence, Dossier, CLI | — (nur Suche + Download) |
| Tests | 72 (offline, 0.13 s) | 27 Dateien (pro Connector) |
| Dedup | deduplicator.py (DOI→Fuzzy, merge-Felder) | _dedupe_papers (DOI→title\|authors→id) |
| Abhängigkeiten | Standardbibliothek only | requests, feedparser, pypdf (+ fastmcp/mcp für MCP-Modus) |
| Lizenz | — | MIT (Attribution nötig) |

## Live-Befund (2026-09-08, EMDR-Query)

`search_papers()`: **21 Quellen aktiv, 18 deduplizierte Paper**, Felder:
abstract, authors, categories, citations, doi, extra, keywords, paper_id,
pdf_url, published_date, references, source, title, url, updated_date.
→ Feld-Mapping auf unser Schema fast 1:1 (year aus published_date).
Hinweis: Relevanz-Ranking ist roh (arXiv Kristall-Paper bei EMDR) — unsere
Pipeline sortiert/verifiziert danach (Verifier, Evidence, PRISMA).

## Fusions-Entscheidung

1. **paper-search-mcp wird VENDORED** (Code ohne .git) nach
   `vendor/paper_search_mcp/` — MIT-Lizenz + README-Attribution behalten.
   Ein Klon = alles da. Kein Submodul (einfach, robust, Davids Mentalität).
2. **sources/searcher.py = Such-Schicht-Adapter**: Primär `search_papers()`
   (21 Quellen), Fallback bisherige Direkt-Suche (CrossRef+arXiv), wenn die
   Bibliothek fehlt. Quelle-down → andere liefert (beide Schichten).
3. **Unsere Pipeline bleibt Verarbeitungs-Schicht** (Dedup robuster —
   behalten, Server-Dedup als 1. Stufe ok).
4. **requirements.txt**: + requests, feedparser, pypdf (für Downloads).
   fastmcp/mcp NUR für MCP-Modus (Option B) — optional.
5. **Unabhängigkeit von Hermes**: knowledge_registry.yaml (in ~/.hermes)
   → Fallback-Kopie ins Repo (`registry/knowledge_registry.yaml`), Router
   sucht erst Repo-lokal, dann ~/.hermes.

## Reihenfolge (Davids Vorgabe)

- [ ] **A**: Searcher auf 21 Quellen (vendoren + Adapter + Mapper) ← JETZT
- [ ] **B**: MCP paper-search reaktivieren (Server starten + hermes mcp enable)
- [ ] C: ergibt sich (Dossier-PDF-Download über paper.py etc.)
