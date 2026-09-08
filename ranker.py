"""
Ranker — Sortiert Ergebnisse nach Relevanz (Query-Titel-Match), Jahr,
Citations, Source-Trust und OA-Status. (Verbesserung 1: Relevanz-Ranking)
"""
import re
from deduplicator import SearchResult

# Stoppwörter für Query-Begriffe (keine Relevanz-Signalwirkung)
_STOPWÖRTER = {
    "the", "and", "for", "with", "from", "that", "this", "study", "analysis",
    "effect", "effects", "using", "based", "a", "an", "of", "in", "on", "to",
    "is", "are", "was", "were", "by", "their", "its", "as", "at", "into",
    "toward", "towards", "between", "during", "after", "before", "over",
    "under", "through", "via", "de", "la", "le", "les", "und", "der", "die",
    "das", "eine", "einer", "für", "mit", "bei", "von", "zur", "zum",
}

_SOURCE_TRUST = {
    # Kuratierte DOI-/Fach-Datenbanken (höchster Trust)
    "CrossRef": 2.0, "PubMed": 2.0, "PubMed Central": 2.0,
    "Europe PMC": 2.0, "Semantic Scholar": 1.8, "OpenAlex": 1.8,
    "CORE": 1.8, "DOAJ": 1.7, "OpenAIRE": 1.7, "DataCite": 1.6,
    "INSPIRE-HEP": 1.8, "HAL": 1.6, "Zenodo": 1.5, "DBLP": 1.7,
    # Preprint-Server (relevant, aber ungeprüft)
    "arXiv": 1.5, "bioRxiv": 1.5, "medRxiv": 1.5, "ChemRxiv": 1.5,
    "SSRN": 1.4, "PsyArXiv": 1.4, "engrXiv": 1.4, "EarthArXiv": 1.4,
    "SocArXiv": 1.3, "AfricArXiv": 1.3,
    # Daten-/Kristall-Repositorien
    "Figshare": 1.3, "COD": 1.3, "CiteSeerX": 1.2,
}


def _relevanz_score(titel: str, query: str) -> float:
    """Query-Abdeckung im Titel (0-3 Punkte): Anteil der nicht-Stoppwort-
    Query-Begriffe, die im Titel vorkommen. Kern der Relevanz (V1)."""
    if not query or not titel:
        return 1.0
    q_terms = [t for t in re.split(r"\W+", query.lower())
               if t and t not in _STOPWÖRTER and len(t) > 2]
    if not q_terms:
        return 1.0
    titel_l = titel.lower()
    treffer = sum(1 for t in q_terms if t in titel_l)
    return min(treffer / len(q_terms) * 3.0, 3.0)


def rank_results(results: list[SearchResult], depth: str = "standard",
                 query: str = "") -> list[SearchResult]:
    """Rankt Ergebnisse nach kombinierter Metrik (Relevanz + Qualität).

    Relevanz (0-3) + Citations (0-3) + Recency (0-2) + Source-Trust (0-2)
    + OA (0-1.5) + Abstract (0-1). Sortiert absteigend, begrenzt nach Tiefe.
    """
    max_citations = max((r.citations for r in results), default=1)
    current_year = 2026

    def score(r: SearchResult) -> float:
        s = 0.0
        # Relevanz zur Query (Verbesserung 1 — NEU)
        s += _relevanz_score(r.title, query)
        # Citation-Score (0-3)
        if max_citations > 0:
            s += min(r.citations / max_citations * 3, 3.0)
        # Recency (0-2)
        try:
            year = int(r.year) if r.year else 2010
            age = max(current_year - year, 0)
            s += max(2.0 - age * 0.2, 0)
        except (ValueError, TypeError):
            s += 1.0
        # Source-Trust (0-2) — echte Quellen-Liste (V1-Fix)
        s += _SOURCE_TRUST.get(r.source, 1.0)
        # OA-Bonus (0-1.5)
        if r.is_oa:
            s += 1.0
        if r.pdf_url:
            s += 0.5
        # Abstract-Bonus (0-1)
        if r.abstract and len(r.abstract) > 50:
            s += 1.0
        return s

    scored = [(score(r), r) for r in results]
    scored.sort(key=lambda x: x[0], reverse=True)

    limits = {"schnell": 15, "standard": 30, "tief": 50}
    limit = limits.get(depth, 30)
    return [r for _, r in scored[:limit]]


if __name__ == "__main__":
    results = [
        SearchResult(title="Posttraumatic Growth after EMDR Therapy", year="2025",
                     citations=87, source="CrossRef", is_oa=True,
                     abstract="We studied EMDR therapy and posttraumatic growth in detail."),
        SearchResult(title="Crystal Growth of Strontium Iridate", year="2020",
                     citations=45, source="arXiv", is_oa=True),
        SearchResult(title="Mindfulness and Trauma Recovery", year="2026",
                     citations=3, source="PsyArXiv", is_oa=True,
                     pdf_url="http://x.com/p.pdf"),
    ]
    q = "posttraumatic growth EMDR therapy"
    ranked = rank_results(results, query=q)
    print(f"Ranking für '{q}':")
    for r in ranked:
        print(f"  {r.title} ({r.year}, {r.citations} cit, {r.source})")
