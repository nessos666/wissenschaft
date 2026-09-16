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


def _bibtex_escape(text: str) -> str:
    """LaTeX/BibTeX-Sonderzeichen escapen (& % # _ { } ~ $ ^).

    Abschluss-Review F4: reale Titel enthalten '&'/'_' häufig → ohne Escaping
    wäre die .bib-Datei invalide.
    """
    ersatz = {"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_",
              "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
              "$": r"\$", "^": r"\textasciicircum{}"}
    return "".join(ersatz.get(c, c) for c in text)


def _bibtex_authors(authors: str) -> str:
    """Autorenliste → BibTeX-Format: 'A; B' bzw. 'A and B'."""
    if not authors or authors == "unbekannt":
        return "unbekannt"
    teile = [a.strip() for a in authors.replace("; ", ";").split(";")
             if a.strip()]
    if len(teile) <= 1:
        # 'Nachname, Vorname'-Paare NICHT zerlegen — nur saubere Namen
        teile = [authors.strip()]
    return " and ".join(_bibtex_escape(t) for t in teile[:20])


def _bibtex(results: list) -> str:
    """Treffer → BibTeX-Einträge (key aus slug+year, escaped)."""
    if not results:
        return "% Keine Treffer — keine BibTeX-Einträge."
    eintraege = []
    for i, r in enumerate(results, 1):
        title = _bibtex_escape((r.get("title") or "Ohne Titel").strip())
        year = str(r.get("year") or "n.d.")
        authors = _bibtex_authors((r.get("authors") or "").strip())
        doi = (r.get("doi") or "").strip()
        source = (r.get("source") or "unknown").lower().replace(" ", "")
        key = f"{source}{year}{i}"
        eintraege.append(f"@article{{{key},\n"
                         f"  title = {{{title}}},\n"
                         f"  author = {{{authors}}},\n"
                         f"  year = {{{year}}},\n"
                         + (f"  doi = {{{_bibtex_escape(doi)}}},\n" if doi else "")
                         + f"  note = {{Quelle: {_bibtex_escape(str(r.get('source', '?')))}}}\n"
                         f"}}")
    return "\n\n".join(eintraege)


def _offene_quellen_markdown(pipeline_ergebnis: dict) -> str:
    """Ehrlicher Quellen-Status: offen / ohne Treffer sind KEINE Fehler.

    David (2026-09): "Wenn manche Daten schneller bearbeitet werden als die
    anderen, dann muss das Tool anzeigen, dass diese Sachen noch offen sind —
    es ist nicht schlimm."
    """
    r = pipeline_ergebnis.get("researcher") or {}
    offen = r.get("sources_offen") or []
    ohne = r.get("sources_ohne_treffer") or []
    antworteten = r.get("sources_geliefert") or []
    versucht = r.get("sources_versucht") or 0
    if not offen and not ohne:
        return ""
    aus = ["\n## Quellen-Status\n"]
    aus.append(f"Von **{versucht} angefragten** Quellen lieferten "
               f"**{len(antworteten)} Treffer**.\n")
    if offen:
        aus.append(f"**⏳ {len(offen)} Quellen rechneten beim Erstellen noch** — "
                   f"das ist kein Fehler. Sie waren zu langsam für dieses Mal; "
                   f"ihre Treffer kommen beim nächsten Lauf (Cache) nach:\n")
        aus.append(", ".join(f"`{q}`" for q in sorted(offen)) + "\n")
    if ohne:
        aus.append(f"\n**{len(ohne)} Quellen hatten zu diesem Thema nichts** — "
                   f"sie wurden gefragt und haben geantwortet, nur ohne "
                   f"passenden Treffer (bei über 140 Spezialquellen völlig normal):\n")
        aus.append(", ".join(f"`{q}`" for q in sorted(ohne)) + "\n")
    return "\n".join(aus)


def _qualitaets_tabelle(results: list, verifier_detail: list) -> str:
    """Verbesserung 7: Übersichtstabelle mit Qualitäts-Spalten —
    DOI-verifiziert | OA-PDF | Citations | Trust je Paper."""
    if not results:
        return ""
    detail = {}
    for v in (verifier_detail or []):
        if isinstance(v, dict):
            detail[(v.get("title") or "").lower()] = v
    zeilen = ["| # | Titel (Jahr) | Quelle | DOI ✓ | PDF | Zit. | Trust |",
              "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results[:25], 1):
        v = detail.get((r.get("title") or "").lower(), {})
        doi_ok = "✓" if v.get("doi_verified") else ("–" if not r.get("doi") else "✗")
        pdf = "✓" if r.get("pdf_url") else "–"
        trust = v.get("trust_score")
        trust_s = f"{trust:.2f}" if isinstance(trust, (int, float)) else "–"
        titel = (r.get("title") or "")[:70].replace("|", "/")
        zeilen.append(f"| {i} | {titel} ({r.get('year') or '?'}) | "
                      f"{r.get('source') or '?'} | {doi_ok} | {pdf} | "
                      f"{r.get('citations') or 0} | {trust_s} |")
    return "\n".join(zeilen)


def erstelle_dossier(pipeline_ergebnis: dict, ziel=None,
                     download_pdfs: bool = False) -> dict:
    """Pipeline-Ergebnis → <ziel>/<Thema>_Dossier/{README.md, .bib}.

    ziel: Basis-Ordner (Default ~/HAUPTLAGER/XX_WissenschaftSkill).
    download_pdfs (Verbesserung 3): lädt OA-PDFs der Treffer nach
    <Thema>_Dossier/pdfs/ (pdf_url direkt, sonst Unpaywall über DOI).
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
    quellen_geliefert = res.get("sources_geliefert") or []
    quellen_versucht = res.get("sources_versucht") or "?"
    quellen_ohne = res.get("sources_ohne_antwort") or []

    dossier_dir = basis / f"{_slug(query)}_Dossier"
    dossier_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    readme = f"""# {query} — Wissenschaftliches PRISMA-Dossier

> Systematische Recherche: {query}
> Methode: PRISMA-Systematik | Tiefe: {depth} | Domain: {domain}
> Quellen: {len(quellen_geliefert)} von {quellen_versucht} aktiv ({", ".join(quellen_geliefert) if quellen_geliefert else "keine"})
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

## Qualitäts-Übersicht ({min(len(results), 25)} Paper)

{_qualitaets_tabelle(results, pipeline_ergebnis.get("verifier_detail") or [])}

---

## Quellen ({len(results)})

{_quellen_markdown(results)}
{_offene_quellen_markdown(pipeline_ergebnis)}

---

## Nächste Suchen (Vorschläge)

{chr(10).join('- ' + s for s in (synthesis.get("next_searches") or [])) if (synthesis.get("next_searches") or []) else '_Keine Vorschläge._'}

---
*Automatisch erzeugt von /wissenschaft (Pipeline V4) — {date_str}*

## Quellen ohne Antwort in diesem Lauf

{chr(10).join('- ' + q for q in quellen_ohne) if quellen_ohne else '_Alle aktivierten Quellen antworteten (oder lieferten keine Treffer zum Thema)._'}
"""
    pfade = {}
    readme_path = dossier_dir / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    pfade["README.md"] = str(readme_path)

    bib_path = dossier_dir / f"{_slug(query)}_Evidenz.bib"
    bib_path.write_text(_bibtex(results), encoding="utf-8")
    pfade[".bib"] = str(bib_path)

    # Verbesserung 3: OA-PDFs der Treffer laden (pdf_url direkt, sonst
    # Unpaywall über DOI). Nie crashen — wenn's schiefgeht, Dossier ohne PDFs.
    if download_pdfs and results:
        try:
            from sources.downloader import lade_pdfs
            pdf_stat = lade_pdfs(results, dossier_dir,
                                 unpaywall_email="kontakt@wissenshaft.tool")
            if pdf_stat["geladen"]:
                pfade["pdfs"] = pdf_stat["geladen"]
                # PDF-Abschnitt im README nachtragen
                pdf_zeilen = "\n".join(
                    f"- [{Path(p).name}]({Path(p).name})"
                    for p in pdf_stat["geladen"])
                readme += (f"\n## PDFs ({len(pdf_stat['geladen'])} geladen)\n\n"
                           f"{pdf_zeilen}\n")
                readme_path.write_text(readme, encoding="utf-8")
        except Exception:
            pass  # PDF-Download ist Bonus — Dossier existiert trotzdem

    return pfade
