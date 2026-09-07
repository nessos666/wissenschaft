"""
Evidence Scorer — Bewertet Papers nach Evidenz-Level.
Hierarchie: Meta-Analysis > Systematic Review > RCT > Cohort > Case-Control > Case Study > Expert Opinion > Preprint
"""
import re
from deduplicator import SearchResult

EVIDENCE_HIERARCHY = {
    "meta_analysis":       {"score": 1.0, "label": "Meta-Analyse", "icon": "🥇"},
    "systematic_review":   {"score": 0.9, "label": "Systematischer Review", "icon": "🥈"},
    "rct":                 {"score": 0.85, "label": "RCT (Randomisierte Studie)", "icon": "🥉"},
    "cohort_study":        {"score": 0.7, "label": "Kohortenstudie", "icon": "📊"},
    "case_control":        {"score": 0.6, "label": "Fall-Kontroll-Studie", "icon": "📊"},
    "case_study":          {"score": 0.4, "label": "Fallstudie", "icon": "📋"},
    "expert_opinion":      {"score": 0.3, "label": "Expertenmeinung", "icon": "💬"},
    "preprint":            {"score": 0.5, "label": "Preprint (ungeprüft)", "icon": "📝"},
    "unknown":             {"score": 0.5, "label": "Unbekannt", "icon": "❓"},
}

KEYWORD_PATTERNS = {
    "meta_analysis":     [r'\bmeta.analysis\b', r'\bmeta-analysis\b', r'\bmetaanalysis\b', r'\bmetaanalyse\b'],
    "systematic_review": [r'\bsystematic review\b', r'\bsystematischer review\b', r'\bsystematic literature\b'],
    "rct":               [r'\brandomi[sz]ed controlled trial\b', r'\bRCT\b', r'\brandomi[sz]ed\b'],
    "cohort_study":      [r'\bcohort\b', r'\bkohortenstudie\b', r'\blongitudinal\b'],
    "case_control":      [r'\bcase.control\b', r'\bfall.kontroll\b'],
    "case_study":        [r'\bcase study\b', r'\bfallstudie\b'],
    "expert_opinion":    [r'\bexpert opinion\b', r'\beditorial\b', r'\bcommentary\b'],
    "preprint":          [r'\bpreprint\b', r'\bworking paper\b', r'\barxiv\b', r'\bssrn\b', r'\bbiorxiv\b'],
}

def classify_evidence(title: str, abstract: str = "", source: str = "") -> str:
    """Klassifiziert Evidenz-Level aus Titel/Abstract/Quelle."""
    text = f"{title} {abstract}".lower()
    
    for level, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return level
    
    # Source-basierte Heuristik
    source_lower = source.lower()
    if any(s in source_lower for s in ["arxiv", "ssrn", "biorxiv", "medrxiv", "preprint"]):
        return "preprint"
    
    return "unknown"

def score_evidence(results: list[SearchResult]) -> list[dict]:
    """Bewertet Evidenz-Level für alle Ergebnisse."""
    scored = []
    for r in results:
        level = classify_evidence(r.title, r.abstract, r.source)
        evidence = EVIDENCE_HIERARCHY.get(level, EVIDENCE_HIERARCHY["unknown"])
        
        # Kombinierter Score: Evidence × Trust (wenn vorhanden)
        trust = getattr(r, 'doi_verified', False) or 0.5
        if hasattr(r, 'trust_score'):
            trust = r.trust_score
        
        combined = evidence["score"] * 0.6 + trust * 0.4
        
        scored.append({
            "title": r.title[:80],
            "source": r.source,
            "evidence_level": level,
            "evidence_label": evidence["label"],
            "evidence_icon": evidence["icon"],
            "evidence_score": evidence["score"],
            "combined_score": round(combined, 2),
        })
    
    scored.sort(key=lambda x: x["combined_score"], reverse=True)
    return scored

def evidence_summary(scored: list[dict]) -> dict:
    """Zusammenfassung der Evidenz-Verteilung."""
    if not scored:
        return {}
    
    levels = {}
    for s in scored:
        level = s["evidence_level"]
        levels[level] = levels.get(level, 0) + 1
    
    avg = round(sum(s["evidence_score"] for s in scored) / len(scored), 2)
    top_level = max(levels, key=levels.get) if levels else "unknown"
    
    return {
        "avg_evidence": avg,
        "dominant_level": EVIDENCE_HIERARCHY.get(top_level, {}).get("label", top_level),
        "distribution": levels,
        "top_paper": scored[0] if scored else None,
    }

if __name__ == "__main__":
    results = [
        SearchResult(title="A Meta-Analysis of Trading Strategies", source="OpenAlex", abstract="We conducted a systematic meta-analysis..."),
        SearchResult(title="FVG Detection: A Case Study", source="SSRN", abstract="This case study examines..."),
        SearchResult(title="Reinforcement Learning: A Survey", source="arXiv", abstract="This paper surveys..."),
        SearchResult(title="Randomized Controlled Trial of HFT", source="PubMed", abstract="In this randomized controlled trial..."),
    ]
    scored = score_evidence(results)
    for s in scored:
        print(f"{s['evidence_icon']} {s['evidence_label']:25s} ({s['evidence_score']:.2f}) | {s['title'][:55]}")
    print(f"\nSummary: {evidence_summary(scored)['avg_evidence']} avg evidence, dominant: {evidence_summary(scored)['dominant_level']}")
