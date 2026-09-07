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
from pathlib import Path

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
}
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


def _search_eine(searcher_cls, query: str, max_results: int) -> list:
    """Eine Quelle synchron abfragen (in Thread ausgeführt). Nie crashen."""
    try:
        searcher = searcher_cls()
        papers = searcher.search(query, max_results=max_results)
        return [p.to_dict() for p in (papers or [])]
    except Exception:
        return []


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
        tasks = {q: asyncio.to_thread(_search_eine, SEARCHER_MAP[q],
                                      query, max_results_per_source)
                 for q in quellen}
        done = await asyncio.wait_for(
            asyncio.gather(*tasks.values(), return_exceptions=True),
            timeout=timeout_s)
        ergebnis = {}
        for q, res in zip(tasks.keys(), done):
            if isinstance(res, Exception):
                ergebnis[q] = []
            else:
                ergebnis[q] = res
        return ergebnis

    try:
        roh_nach_quelle = asyncio.run(_lauf())
    except Exception:
        roh_nach_quelle = {}

    alle_roh = []
    genutzt = []
    fehler = {}
    for q, treffer in roh_nach_quelle.items():
        if treffer:
            genutzt.append(q)
            alle_roh.extend(treffer)
        else:
            fehler[q] = "keine Treffer/Fehler"
    papers = [_norm(p) for p in _dedupe(alle_roh)]
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
