# Fremdkomponenten und Lizenzen

## paper-search-mcp

Teile der Such-Schicht stammen aus
[paper-search-mcp](https://github.com/openags/paper-search-mcp) — Lizenz: MIT.

- Lizenztext: `vendor/paper_search_mcp/LICENSE`
- Herkunft und Anpassungen: `vendor/paper_search_mcp/ATTRIBUTION.md`

### Entfernte Komponenten

- `academic_platforms/sci_hub.py` (+ Test): Sci-Hub-Downloader wurde entfernt —
  rechtlich heikel und im Projekt nirgends verwendet.

## Eigenständige Teile

Die Verarbeitungs-Pipeline (Deduplizierung, Ranking, Verifier, Evidence,
PRISMA, Dossier-Writer) ist eigenständig entwickelt.
