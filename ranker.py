"""
Ranker — Sortiert Ergebnisse nach Relevanz, Jahr, Citations und OA-Status.
"""
from deduplicator import SearchResult

def rank_results(results: list[SearchResult], depth: str = "standard") -> list[SearchResult]:
    """Rankt Ergebnisse nach kombinierter Metrik."""
    max_citations = max((r.citations for r in results), default=1)
    current_year = 2026
    
    def score(r: SearchResult) -> float:
        s = 0.0
        
        # Citation-Score (0-3 Punkte)
        if max_citations > 0:
            s += min(r.citations / max_citations * 3, 3.0)
        
        # Recency (0-2 Punkte)
        try:
            year = int(r.year) if r.year else 2010
            age = max(current_year - year, 0)
            s += max(2.0 - age * 0.2, 0)
        except (ValueError, TypeError):
            s += 1.0
        
        # Source-Trust (0-2 Punkte)
        source_trust = {
            "CrossRef": 2.0, "OpenAlex": 1.8, "Semantic Scholar": 1.8,
            "arXiv": 1.5, "PubMed": 2.0, "Europe PMC": 2.0,
            "SSRN": 1.5, "RePEc": 1.8, "NBER": 1.8,
            "Zenodo": 1.5,
        }
        s += source_trust.get(r.source, 1.0)
        
        # OA-Bonus (0-1 Punkte)
        if r.is_oa:
            s += 1.0
        if r.pdf_url:
            s += 0.5
        
        # Has abstract bonus
        if r.abstract and len(r.abstract) > 50:
            s += 1.0
        
        return s
    
    scored = [(score(r), r) for r in results]
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Top-N je nach Tiefe
    limits = {"schnell": 15, "standard": 30, "tief": 50}
    limit = limits.get(depth, 30)
    
    return [r for _, r in scored[:limit]]

if __name__ == "__main__":
    results = [
        SearchResult(title="FVG Detection in NQ", year="2025", citations=87, source="OpenAlex", is_oa=True),
        SearchResult(title="Market Microstructure", year="2018", citations=12, source="CrossRef", is_oa=False),
        SearchResult(title="New FVG Research", year="2026", citations=3, source="Semantic Scholar", is_oa=True, pdf_url="http://x.com/p.pdf"),
    ]
    ranked = rank_results(results)
    for r in ranked:
        print(f"  {r.title} ({r.year}, {r.citations} cit, OA={r.is_oa})")
