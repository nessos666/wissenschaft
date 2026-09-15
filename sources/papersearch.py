"""MCP-freie Brücke zu den 21 Quellen-Connectors (Fusion, Option A).

Nutzt die vendored paper-search-mcp Connectors DIREKT (ohne server.py →
kein fastmcp/mcp nötig). Jeder Connector ist eine Searcher-Klasse mit
.search(query, max_results) → Paper-Objekte mit .to_dict().

Design (free-first, wie das Original):
- 21 Quellen parallel (asyncio.to_thread), Quelle-down → andere liefert
- Dedup: DOI → title|authors → paper_id (wie server._dedupe_papers)
- Liefert IMMER eine Liste (nie None/crash)
"""
import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Eigener Executor mit vielen Workern — der asyncio-Default (min(32, cpu+4))
# erlaubt nur ~4-8 gleichzeitige Threads, wodurch 20 Quellen in Wellen liefen
# und hängende Quellen die schnellen blockierten (Fusion-Fix).
_EXECUTOR = ThreadPoolExecutor(max_workers=24, thread_name_prefix="wissq")

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "paper_search_mcp"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from paper_search_mcp.academic_platforms.arxiv import ArxivSearcher
from paper_search_mcp.academic_platforms.pubmed import PubMedSearcher
from paper_search_mcp.academic_platforms.biorxiv import BioRxivSearcher
from paper_search_mcp.academic_platforms.medrxiv import MedRxivSearcher
from paper_search_mcp.academic_platforms.semantic import SemanticSearcher
from paper_search_mcp.academic_platforms.crossref import CrossRefSearcher
from paper_search_mcp.academic_platforms.openalex import OpenAlexSearcher
from paper_search_mcp.academic_platforms.pmc import PMCSearcher
from paper_search_mcp.academic_platforms.europepmc import EuropePMCSearcher
from paper_search_mcp.academic_platforms.dblp import DBLPSearcher
from paper_search_mcp.academic_platforms.zenodo import ZenodoSearcher
from paper_search_mcp.academic_platforms.hal import HALSearcher
from paper_search_mcp.academic_platforms.ssrn import SSRNSearcher
from paper_search_mcp.academic_platforms.openaire import OpenAiresearcher as OpenAireSearcher
from paper_search_mcp.academic_platforms.doaj import DOAJSearcher
from paper_search_mcp.academic_platforms.citeseerx import CiteSeerXSearcher
from paper_search_mcp.academic_platforms.core import CORESearcher
from paper_search_mcp.academic_platforms.iacr import IACRSearcher

# Aktive Quellen. REIHENFOLGE = Qualitäts-Priorität (Fusion-Fix): kuratierte,
# DOI-basierte Quellen (CrossRef/PubMed/EuropePMC/Semantic…) liefern
# relevanz-sortierte Metadaten und kommen ZUERST; Preprint-Server
# (arXiv/bioRxiv…) matchen Volltext und produzieren Rauschen → zuletzt.
SEARCHER_MAP = {
    "crossref": CrossRefSearcher,
    "pubmed": PubMedSearcher,
    "europepmc": EuropePMCSearcher,
    "semantic": SemanticSearcher,
    "openalex": OpenAlexSearcher,
    "pmc": PMCSearcher,
    "core": CORESearcher,
    "doaj": DOAJSearcher,
    "openaire": OpenAireSearcher,
    "zenodo": ZenodoSearcher,
    "dblp": DBLPSearcher,
    "hal": HALSearcher,
    "ssrn": SSRNSearcher,
    "citeseerx": CiteSeerXSearcher,
    "arxiv": ArxivSearcher,
    "biorxiv": BioRxivSearcher,
    "medrxiv": MedRxivSearcher,
    "iacr": IACRSearcher,  # Kryptographie (Nische — ans Ende)
}
ALL_SOURCES = list(SEARCHER_MAP.keys())

# Extra-Quellen (Quellen-Ausbau 2026-09): eigene Connectors für Chemie/Physik/
# Generisch. Funktionen liefern direkt unser _norm-Format.
from sources.quellen_extra import EXTRA_QUELLEN
from sources.quellen_extra2 import EXTRA_QUELLEN_2
from sources.quellen_extra3 import EXTRA_QUELLEN_3

EXTRA_QUELLEN.update(EXTRA_QUELLEN_2)
EXTRA_QUELLEN.update(EXTRA_QUELLEN_3)

# Gesamt-Reihenfolge (Qualitäts-Priorität): kuratierte DOI-Quellen zuerst,
# dann Preprints, dann die neuen Domänen-Quellen.
SEARCHER_MAP.update({name: fn for name, fn in EXTRA_QUELLEN.items()})
ALL_SOURCES = list(SEARCHER_MAP.keys())


def _paper_key(paper: dict) -> str:
    """Eindeutiger Schlüssel für Dedup: DOI → title|authors → id."""
    doi = (paper.get("doi") or "").strip().lower()
    if doi:
        return f"doi:{doi}"
    title = (paper.get("title") or "").strip().lower()
    authors = (paper.get("authors") or "").strip().lower()
    if title:
        return f"title:{title}|authors:{authors}"
    pid = (paper.get("paper_id") or "").strip().lower()
    return f"id:{pid}"


def _dedupe(papers: list) -> list:
    seen, out = set(), []
    for p in papers:
        k = _paper_key(p)
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    return out


def _norm(paper: dict) -> dict:
    """paper-search-Felder → unser Such-Schema (searcher.py-Vertrag).

    title, doi, url, pdf_url, source, year, authors, abstract, citations
    """
    # Jahr aus published_date (2024-03-01T...) oder direkt year
    year = paper.get("year")
    if not year and paper.get("published_date"):
        year = str(paper["published_date"])[:4]
    source = (paper.get("source") or "").lower()
    # Quellen-Namen humanisieren
    NAMEN = {"arxiv": "arXiv", "pubmed": "PubMed", "biorxiv": "bioRxiv",
             "medrxiv": "medRxiv", "semantic": "Semantic Scholar",
             "crossref": "CrossRef", "openalex": "OpenAlex", "pmc": "PubMed Central",
             "europepmc": "Europe PMC", "dblp": "DBLP", "zenodo": "Zenodo",
             "hal": "HAL", "ssrn": "SSRN", "openaire": "OpenAIRE",
             "doaj": "DOAJ", "citeseerx": "CiteSeerX", "core": "CORE"}
    return {
        "title": (paper.get("title") or "")[:500],
        "year": year,
        "doi": (paper.get("doi") or "").replace("https://doi.org/", ""),
        "url": paper.get("url") or "",
        "pdf_url": paper.get("pdf_url") or "",
        "source": NAMEN.get(source, source or "?"),
        "citations": int(paper.get("citations") or 0),
        "abstract": (paper.get("abstract") or "")[:1000],
        "authors": (paper.get("authors") or "")[:300],
    }


def _search_eine(quelle, query: str, max_results: int) -> list:
    """Eine Quelle abfragen (in Thread ausgeführt). Nie crashen.

    quelle: Searcher-KLASSE (Vendor, Paper-Objekte → _norm) ODER Funktion
    (Extra-Quellen, liefern bereits normierte Dicts).
    """
    try:
        if isinstance(quelle, type):
            searcher = quelle()
            papers = searcher.search(query, max_results=max_results)
            return [_norm(p.to_dict()) for p in (papers or [])]
        # Funktion (Extra-Quelle): liefert schon unser Schema
        return quelle(query, max_results=max_results) or []
    except Exception:
        return []


def _reichere_abstracts_an(papers: list, timeout_s: float = 8.0) -> list:
    """Verbesserung 4: Für Treffer mit DOI aber ohne Abstract den CrossRef-
    Metadaten-Nachschlag machen (JATS-XML-Abstract). Parallel, kurz.
    Nie crashen — Treffer ohne Abstract bleiben einfach leer.
    """
    import re as _re
    beduerftig = [p for p in papers
                  if p.get("doi") and not (p.get("abstract") or "").strip()]
    if not beduerftig:
        return papers

    def _lade(doi: str) -> str:
        try:
            import requests as _req
            r = _req.get(f"https://api.crossref.org/works/{doi}",
                         headers={"User-Agent":
                                  "WissenschaftTool/4.0 (mailto:kontakt@wissenshaft.tool)"},
                         timeout=min(timeout_s, 8.0))
            if r.status_code != 200:
                return ""
            abstr = (r.json().get("message", {}).get("abstract") or "")
            # JATS-XML-Tags grob entfernen
            abstr = _re.sub(r"<[^>]+>", " ", abstr)
            return _re.sub(r"\s+", " ", abstr).strip()[:1000]
        except Exception:
            return ""

    async def _lauf():
        import asyncio as _aio
        tasks = {id(p): _aio.get_event_loop().run_in_executor(
                     _EXECUTOR, _lade, p["doi"]) for p in beduerftig}
        ergebnis = {}
        for pid, t in tasks.items():
            try:
                ergebnis[pid] = await _aio.wait_for(t, timeout=min(timeout_s, 8.0))
            except Exception:
                ergebnis[pid] = ""
        return ergebnis

    try:
        gefuellt = asyncio.run(_lauf())
    except Exception:
        return papers
    for p in beduerftig:
        txt = gefuellt.get(id(p), "")
        if txt:
            p["abstract"] = txt
    return papers


def search_papers(query: str, max_results_per_source: int = 3,
                  sources: str = "all", timeout_s: float = 45.0) -> dict:
    """Multi-Quellen-Suche (21 Quellen parallel, dedupliziert).

    Liefert Dict wie das Original: {query, sources_used, total, papers,
    errors}. papers = deduplizierte, normalisierte Dicts (unser Schema).
    Nie crashen.
    """
    if not query or not query.strip():
        return {"query": query, "sources_used": [], "total": 0,
                "papers": [], "errors": {}}
    if sources == "all":
        quellen = ALL_SOURCES
    else:
        quellen = [s.strip() for s in sources.split(",")
                   if s.strip() in SEARCHER_MAP]
    if not quellen:
        return {"query": query, "sources_used": [], "total": 0,
                "papers": [], "errors": {"sources": "keine valide Quelle"}}

    async def _lauf():
        # Tasks PARALLEL starten, aber pro Quelle einzeln abwarten mit
        # Kurz-Timeout (8s): schnelle Quellen (CrossRef ~1s) liefern sofort,
        # hängende/rate-limitede Quellen (interne Retries bis 30s) werden
        # abgebrochen statt den GESAMT-Lauf zu blockieren (Fusion-Fix).
        tasks = {q: asyncio.get_event_loop().run_in_executor(
                     _EXECUTOR, _search_eine, SEARCHER_MAP[q], query,
                     max_results_per_source)
                 for q in quellen}
        # Davids Timeout-Philosophie (2026-09): KEIN aggressives Abschneiden —
        # langsame Quellen dürfen arbeiten (bis 60s pro Quelle, parallel).
        # Schnelle Quellen liefern sofort, langsame kommen nach. Teilwissen
        # ist ok — der Rest fließt in Folgeläufe/Cache.
        pro_quelle_s = min(60.0, timeout_s)
        ergebnis = {}
        for q, t in tasks.items():
            try:
                ergebnis[q] = await asyncio.wait_for(t, timeout=pro_quelle_s)
            except Exception:
                ergebnis[q] = []  # Quelle zu langsam/Fehler — andere liefern
        return ergebnis

    try:
        roh_nach_quelle = asyncio.run(_lauf())
    except Exception:
        roh_nach_quelle = {}

    # Round-Robin-Mischung (Qualitäts-Verbesserung): statt flach zu
    # konkatenieren (Top-Quellen würden die Liste dominieren — die ersten
    # max_results wären nur CrossRef/PubMed/EuropePMC), wird je 1 Treffer
    # pro Quelle gemischt, dann je 2. … — Relevanz (Quellen-Priorität)
    # UND Vielfalt über alle liefernden Quellen.
    genutzt = []
    fehler = {}
    for q, treffer in roh_nach_quelle.items():
        if treffer:
            genutzt.append(q)
        else:
            fehler[q] = "keine Treffer/Fehler"
    gemischt = []
    max_len = max((len(v) for v in roh_nach_quelle.values()), default=0)
    for i in range(max_len):
        for q in genutzt:
            treffer_q = roh_nach_quelle[q]
            if i < len(treffer_q):
                gemischt.append(treffer_q[i])
    papers = _dedupe(gemischt)  # bereits normiert in _search_eine
    # Verbesserung 4: fehlende Abstracts per CrossRef-Nachschlag anreichern
    papers = _reichere_abstracts_an(papers)
    return {"query": query, "sources_used": genutzt, "total": len(papers),
            "papers": papers, "errors": fehler}


if __name__ == "__main__":
    import sys as _s
    thema = _s.argv[1] if len(_s.argv) > 1 else "posttraumatic growth EMDR"
    erg = search_papers(thema, max_results_per_source=3)
    print(f"Suche '{thema}': {erg['total']} Treffer aus "
          f"{len(erg['sources_used'])} Quellen")
    print("Quellen:", ", ".join(erg["sources_used"]))
    for p in erg["papers"][:8]:
        print(f"  [{p['source']}] {p['title'][:65]} ({p['year']})")
