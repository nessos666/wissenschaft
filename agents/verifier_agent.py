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
        # Block 3 (Robustheit): zentrale Normalisierung (deduplicator) —
        # Einträge können Nicht-Dict sein (String), Felder int/None/Dict statt
        # str, Zitationen nicht-numerisch. Nie crashen.
        from deduplicator import searchresult_from_dict
        search_results = []
        for r in results_raw:
            sr = searchresult_from_dict(r)
            if sr is not None:
                search_results.append(sr)
        
        # Verifizieren
        verified = self.verifier.verify_all(search_results)
        summary = self.verifier.summary(verified)
        
        self.log(f"{len(verified)} Papers geprüft. Avg Trust: {summary.get('avg_trust', 0)}")
        
        # Ergebnisse serialisieren
        verified_data = []
        for vr in verified:
            # Block 6 (einheitliches Datenmodell): ALLE Metadaten durchreichen —
            # vorher gingen year/authors/citations/abstract/url verloren und
            # nachgelagerte Phasen (Evidence, Dossier) hatten nur Teildaten.
            verified_data.append({
                "title": vr.result.title,
                "year": vr.result.year,
                "authors": vr.result.authors,
                "citations": vr.result.citations,
                "abstract": vr.result.abstract,
                "url": vr.result.url,
                "pdf_url": vr.result.pdf_url,
                "is_oa": vr.result.is_oa,
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
