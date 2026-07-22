"""
Deduplicator — Entfernt Duplikate per Titel-Fuzzy-Match (Schwelle 0.70).
Teil des /wissenschaft Tools.
"""
import re
from difflib import SequenceMatcher


def normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def title_similarity(t1: str, t2: str) -> float:
    return SequenceMatcher(None, normalize_title(t1), normalize_title(t2)).ratio()


def deduplicate(results: list, threshold=0.70) -> list:
    """DOI-Match zuerst, dann Titel-Fuzzy > threshold."""
    unique = []
    seen_dois = {}
    
    for r in results:
        doi = r.get("doi", "")
        if doi and doi in seen_dois:
            existing = seen_dois[doi]
            existing.setdefault("merged_from", []).append(r.get("source", ""))
            if len(r.get("abstract", "")) > len(existing.get("abstract", "")):
                existing["abstract"] = r["abstract"]
            if r.get("citations", 0) > existing.get("citations", 0):
                existing["citations"] = r["citations"]
            continue
        
        if doi:
            seen_dois[doi] = r
            unique.append(r)
            continue
        
        is_dup = False
        for u in unique:
            if title_similarity(r.get("title", ""), u.get("title", "")) > threshold:
                u.setdefault("merged_from", []).append(r.get("source", ""))
                if r.get("citations", 0) > u.get("citations", 0):
                    u["citations"] = r["citations"]
                is_dup = True
                break
        
        if not is_dup:
            unique.append(r)
    
    return unique
