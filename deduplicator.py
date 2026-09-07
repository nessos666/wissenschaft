"""
Deduplicator — Entfernt Duplikate per DOI-Match und Titel-Fuzzy-Match.
"""
import re
from difflib import SequenceMatcher
from dataclasses import dataclass, field

@dataclass
class SearchResult:
    title: str = ""
    authors: str = ""
    year: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    source: str = ""
    citations: int = 0
    is_oa: bool = False
    pdf_url: str = ""
    relevance_note: str = ""
    quality_note: str = ""
    merged_from: list[str] = field(default_factory=list)

def normalize_title(title: str) -> str:
    """Normalisiert Titel für Vergleich."""
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def title_similarity(t1: str, t2: str) -> float:
    """Berechnet Ähnlichkeit zweier Titel."""
    return SequenceMatcher(None, normalize_title(t1), normalize_title(t2)).ratio()

def deduplicate(results: list[SearchResult]) -> list[SearchResult]:
    """Entfernt Duplikate: DOI-Match zuerst, dann Titel-Fuzzy > 0.85."""
    unique = []
    seen_dois = {}
    
    for r in results:
        # Stufe 1: DOI-Match
        if r.doi and r.doi in seen_dois:
            seen_dois[r.doi].merged_from.append(r.source)
            # Merge abstract if longer
            if len(r.abstract) > len(seen_dois[r.doi].abstract):
                seen_dois[r.doi].abstract = r.abstract
            if r.citations > seen_dois[r.doi].citations:
                seen_dois[r.doi].citations = r.citations
            continue
        
        if r.doi:
            seen_dois[r.doi] = r
            unique.append(r)
            continue
        
        # Kein DOI — nach Titel-Duplikaten suchen
        is_dup = False
        for u in unique:
            if title_similarity(r.title, u.title) > 0.70:
                u.merged_from.append(r.source)
                if r.citations > u.citations:
                    u.citations = r.citations
                is_dup = True
                break
        
        if not is_dup:
            unique.append(r)
    
    return unique

if __name__ == "__main__":
    # Quick test
    r1 = SearchResult(title="Fair Value Gap Detection in NQ Futures", doi="10.1234/fvg1", source="OpenAlex")
    r2 = SearchResult(title="Fair Value Gap Detection in NQ Futures", doi="10.1234/fvg1", source="CrossRef")
    r3 = SearchResult(title="Detection of Fair Value Gaps in NASDAQ Futures", doi="", source="Semantic Scholar")
    r4 = SearchResult(title="Machine Learning for Market Microstructure", doi="10.1234/ml1", source="OpenAlex")
    
    results = deduplicate([r1, r2, r3, r4])
    print(f"Vorher: 4, Nachher: {len(results)}")
    for r in results:
        print(f"  {r.title[:50]}... [from: {r.source}{' + ' + ', '.join(r.merged_from) if r.merged_from else ''}]")
