"""Reviewer Agent — bewertet Qualität und identifiziert Lücken."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents import BaseAgent, AgentResult

class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Reviewer", "Bewertet Qualität und identifiziert Lücken")
    
    def run(self, input_data: dict) -> AgentResult:
        t0 = time.time()
        top10 = input_data.get("top10", [])
        stats = input_data.get("stats", {})
        query = input_data.get("query", "")
        domain = input_data.get("domain", "multidisciplinary")
        
        # Qualitätsbewertung
        quality_score = 8.0  # Basis
        if stats.get("avg_trust", 0) < 0.5:
            quality_score -= 3
        if stats.get("total", 0) < 5:
            quality_score -= 2
        if stats.get("high_trust", 0) > stats.get("total", 1) * 0.6:
            quality_score += 1
        
        # Lücken identifizieren
        gaps = []
        if stats.get("total", 0) < 10:
            gaps.append("Weniger als 10 Ergebnisse — breitere Suche empfohlen")
        
        sources_seen = set()
        for r in top10:
            sources_seen.add(r.get("source", ""))
        if len(sources_seen) < 3:
            gaps.append(f"Nur {len(sources_seen)} Quellen abgedeckt — mehr Quellen empfohlen")
        
        # Empfehlungen
        recommendations = []
        if quality_score < 6:
            recommendations.append("Qualität grenzwertig — manuelle Prüfung empfohlen")
        if gaps:
            recommendations.extend(gaps)
        if domain == "trading" and not any("empirical" in r.get("title","").lower() for r in top10):
            recommendations.append("Keine empirischen Studien gefunden — Suche erweitern")
        
        self.log(f"Qualität: {quality_score}/10. {len(gaps)} Lücken, {len(recommendations)} Empfehlungen.")
        
        return self.ok({
            "quality_score": round(quality_score, 1),
            "gaps": gaps,
            "recommendations": recommendations,
            "sources_covered": list(sources_seen),
        }, duration=(time.time()-t0)*1000)
