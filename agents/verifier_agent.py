"""Verifier Agent — prüft Fakten (DOI, URL, Autoren)."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents import BaseAgent, AgentResult
from verifier import Verifier
from deduplicator import SearchResult

class VerifierAgent(BaseAgent):
    def __init__(self):
        super().__init__("Verifier", "Prüft Fakten und berechnet Trust-Scores")
        self.verifier = Verifier(timeout=5)
    
    def run(self, input_data: dict) -> AgentResult:
        t0 = time.time()
        results_raw = input_data.get("results", [])
        
        if not results_raw:
            return self.fail(["Keine Ergebnisse zum Verifizieren"])
        
        # Roh-Daten in SearchResult konvertieren
        search_results = []
        for r in results_raw:
            search_results.append(SearchResult(
                title=r.get("title", ""),
                authors=r.get("authors", ""),
                year=str(r.get("year", "")),
                doi=r.get("doi", ""),
                url=r.get("url", ""),
                pdf_url=r.get("pdf_url", ""),
                source=r.get("source", "Unknown"),
                citations=int(r.get("citations", 0)),
                abstract=r.get("abstract", "")[:500],
            ))
        
        # Verifizieren
        verified = self.verifier.verify_all(search_results)
        summary = self.verifier.summary(verified)
        
        self.log(f"{len(verified)} Papers geprüft. Avg Trust: {summary.get('avg_trust', 0)}")
        
        # Ergebnisse serialisieren
        verified_data = []
        for vr in verified:
            verified_data.append({
                "title": vr.result.title,
                "doi": vr.result.doi,
                "source": vr.result.source,
                "trust_score": vr.trust_score,
                "doi_verified": vr.doi_verified,
                "url_reachable": vr.url_reachable,
                "warnings": vr.warnings,
            })
        
        return self.ok({
            "verified_results": verified_data,
            "summary": summary,
        }, duration=(time.time()-t0)*1000)
