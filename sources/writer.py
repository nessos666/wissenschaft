"""Dossier-Writer (Block 4) — Pipeline-Ergebnis → fertiges Dossier.

Automatisiert Phase 5: schreibt README.md (+ .bib) im Format der bestehenden
Dossiers unter XX_WissenschaftSkill/<Thema>_Dossier/. Auch ohne Treffer wird
ein ehrlicher Leer-Stand erzeugt.
"""
import re
from datetime import datetime
from pathlib import Path

STANDARD_ZIEL = Path.home() / "HAUPTLAGER" / "XX_WissenschaftSkill"


def _slug(query: str) -> str:
    """Query → sicherer Ordnername: A-Za-z0-9 + _ + - (kein Pfad-Injection)."""
    s = re.sub(r"[^A-Za-z0-9_-]+", "_", query.strip())
    s = re.sub(r"_+", "_", s).strip("_")
    return (s or "thema")[:60]


def _prisma_ascii(prisma: dict) -> str:
    """PRISMA-Zahlen → ASCII-Flowchart (Format der bestehenden Dossiers)."""
    p = prisma or {}
    ident = p.get("identified", 0)
    screened = p.get("screened", ident)
    included = p.get("included", screened)
    dedup = max(0, ident - screened)
    ausgeschlossen = max(0, screened - included)
    return f"""IDENTIFIZIERT (n = {ident})
     │
SCREENING (n = {screened})
├── Duplikate/ungeeignet entfernt: -{dedup}
│
AUSGESCHLOSSEN (n = {ausgeschlossen})
     │
EINGESCHLOSSEN (n = {included})"""


def _quellen_markdown(results: list) -> str:
    """Treffer → nummerierte Markdown-Liste (ehrlich: nur was wirklich da ist)."""
    if not results:
        return "_Keine Treffer in dieser Suche gefunden._"
    zeilen = []
    for i, r in enumerate(results, 1):
        title = (r.get("title") or "(ohne Titel)")[:150]
        year = r.get("year") or "?"
        source = r.get("source") or "?"
        doi = r.get("doi") or ""
        url = r.get("url") or ""
        abstract = (r.get("abstract") or "").strip()[:300]
        zeilen.append(f"### {i}. {title} ({year})")
        zeilen.append(f"- **Quelle:** {source}")
        if doi:
            zeilen.append(f"- **DOI:** {doi}")
        if url:
            zeilen.append(f"- **URL:** {url}")
        if abstract:
            zeilen.append(f"- **Abstract:** {abstract}")
    return "\n".join(zeilen)


def _bibtex(results: list) -> str:
    """Treffer → BibTeX-Einträge (key aus slug+year)."""
    if not results:
        return "% Keine Treffer — keine BibTeX-Einträge."
    eintraege = []
    for i, r in enumerate(results, 1):
        title = (r.get("title") or "Ohne Titel").strip()
        year = str(r.get("year") or "n.d.")
        authors = (r.get("authors") or "unbekannt").strip()
        doi = (r.get("doi") or "").strip()
        source = (r.get("source") or "unknown").lower().replace(" ", "")
        key = f"{source}{year}{i}"
        eintraege.append(f"@article{{{key},\n"
                         f"  title = {{{title}}},\n"
                         f"  author = {{{authors}}},\n"
                         f"  year = {{{year}}},\n"
                         + (f"  doi = {{{doi}}},\n" if doi else "")
                         + f"  note = {{Quelle: {r.get('source', '?')}}}\n"
                         f"}}")
    return "\n\n".join(eintraege)


def erstelle_dossier(pipeline_ergebnis: dict, ziel=None) -> dict:
    """Pipeline-Ergebnis → <ziel>/<Thema>_Dossier/{README.md, .bib}.

    ziel: Basis-Ordner (Default ~/HAUPTLAGER/XX_WissenschaftSkill).
    Liefert Dict {Dateityp: pfad}. Nie crashen.
    """
    basis = Path(ziel) if ziel else STANDARD_ZIEL
    basis.mkdir(parents=True, exist_ok=True)

    query = (pipeline_ergebnis.get("query") or "thema").strip()
    res = pipeline_ergebnis.get("researcher") or {}
    results = [r for r in (res.get("results") or []) if isinstance(r, dict)]
    synthesis = pipeline_ergebnis.get("synthesis") or {}
    prisma = pipeline_ergebnis.get("prisma") or {}
    domain = pipeline_ergebnis.get("domain") or "multidisciplinary"
    depth = pipeline_ergebnis.get("depth") or "standard"

    dossier_dir = basis / f"{_slug(query)}_Dossier"
    dossier_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    readme = f"""# {query} — Wissenschaftliches PRISMA-Dossier

> Systematische Recherche: {query}
> Methode: PRISMA-Systematik | Tiefe: {depth} | Domain: {domain}
> Erstellt: {date_str} | XX_WissenschaftSkill/{_slug(query)}_Dossier/

---

## PRISMA-Flowchart

```
{_prisma_ascii(prisma)}
```

---

## Executive Summary

{(synthesis.get("summary") or "_Keine Zusammenfassung erzeugt._")}

---

## Quellen ({len(results)})

{_quellen_markdown(results)}

---

## Nächste Suchen (Vorschläge)

{chr(10).join('- ' + s for s in (synthesis.get("next_searches") or [])) if (synthesis.get("next_searches") or []) else '_Keine Vorschläge._'}

---
*Automatisch erzeugt von /wissenschaft (Pipeline V4) — {date_str}*
"""
    pfade = {}
    readme_path = dossier_dir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    pfade["README.md"] = str(readme_path)

    bib_path = dossier_dir / f"{_slug(query)}_Evidenz.bib"
    bib_path.write_text(_bibtex(results), encoding="utf-8")
    pfade[".bib"] = str(bib_path)

    return pfade
