"""Synthesis Agent — verdichtet Ergebnisse, erstellt Executive Summary."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents import BaseAgent, AgentResult

class SynthesisAgent(BaseAgent):
    def __init__(self):
        super().__init__("Synthesis", "Verdichtet Ergebnisse und erstellt Summary")
    
    def run(self, input_data: dict) -> AgentResult:
        t0 = time.time()
        verified = input_data.get("verified_results", [])
        query = input_data.get("query", "")
        domain = input_data.get("domain", "multidisciplinary")
        
        if not verified:
            return self.fail(["Keine verifizierten Ergebnisse"])
        
        # Top 10 nach Trust-Score
        sorted_results = sorted(verified, key=lambda x: x.get("trust_score", 0), reverse=True)
        top10 = sorted_results[:10]
        
        # Executive Summary generieren
        summary_lines = []
        high_trust = [r for r in sorted_results if r.get("trust_score", 0) >= 0.7]
        low_trust = [r for r in sorted_results if r.get("trust_score", 0) < 0.4]
        
        summary_lines.append(f"Von {len(verified)} Papers haben {len(high_trust)} hohes Vertrauen (≥0.7).")
        
        if top10:
            best = top10[0]
            summary_lines.append(f"Top-Paper: '{best['title'][:80]}' (Trust: {best['trust_score']}, {best.get('source','?')}).")
        
        if low_trust:
            summary_lines.append(f"⚠️ {len(low_trust)} Papers mit niedrigem Vertrauen (<0.4) — manuell prüfen.")
        
        # Nächste Suche vorschlagen
        next_searches = []
        if domain == "trading":
            next_searches = [f"{query} empirical study", f"{query} systematic review"]
        elif domain == "medicine":
            next_searches = [f"{query} meta-analysis", f"{query} clinical trial"]
        else:
            next_searches = [f"{query} review", f"{query} latest research"]
        
        self.log(f"Top 10 extrahiert. {len(high_trust)} high-trust Papers.")
        
        return self.ok({
            "top10": top10,
            "executive_summary": "\n".join(summary_lines),
            "next_searches": next_searches,
            "stats": {
                "total": len(verified),
                "high_trust": len(high_trust),
                "low_trust": len(low_trust),
                "avg_trust": round(sum(r.get("trust_score",0) for r in sorted_results)/max(len(sorted_results),1),2),
            }
        }, duration=(time.time()-t0)*1000)
