# Vendored: paper-search-mcp (v0.1.4)

- **Quelle:** https://github.com/openags/paper-search-mcp (MIT-Lizenz)
- **Copyright:** (c) 2025 OPENAGS — siehe LICENSE im selben Ordner
- **Eingebettet am:** 2026-09-08 (Fusion Option A)
- **Zweck:** 17+ Quellen-Connectors für die Multi-Quellen-Suche
  (CrossRef, PubMed, Europe PMC, Semantic Scholar, OpenAlex, CORE, DOAJ,
  OpenAIRE, Zenodo, DBLP, HAL, SSRN, CiteSeerX, arXiv, bioRxiv, medRxiv, …)
- **Entfernt beim Vendoren:** .git, .venv, uv.lock, Dockerfile, server_http.py,
  smithery.yaml, .github, docs/images (MCP-Server-Spezifika — die Brücke
  sources/papersearch.py nutzt die Connectors DIREKT, ohne fastmcp)
- **Änderungen:** keine am Original-Code; nur Auswahl der aktiven Quellen
  in sources/papersearch.py (Qualitäts-Priorität: kuratierte zuerst)

## Entfernte Komponenten

- `academic_platforms/sci_hub.py` (+ Test): Sci-Hub-Downloader wurde entfernt —
  rechtlich heikel und im Projekt nirgends verwendet.
