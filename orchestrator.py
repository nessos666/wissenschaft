"""Orchestrator V3 — Voll integriert: Evidence, Cluster, PRISMA, Cache"""
import sys, time, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from agents.researcher import ResearcherAgent
from agents.verifier_agent import VerifierAgent
from agents.synthesis import SynthesisAgent
from agents.reviewer import ReviewerAgent
from evidence_scorer import score_evidence, evidence_summary
from clusterer import generate_cluster_report
from prisma import compute_prisma, generate_prisma_markdown
from cache import ResponseCache
from deduplicator import SearchResult


class OrchestratorV3:
    def __init__(self):
        self.researcher = ResearcherAgent()
        self.verifier = VerifierAgent()
        self.synthesis = SynthesisAgent()
        self.reviewer = ReviewerAgent()
        self.cache = ResponseCache()
    
    def run_pipeline(self, query: str, depth: str = "standard", domain: str = None,
                     raw_results: list[dict] = None, use_cache: bool = True) -> dict:
        t0 = time.time()
        
        # Cache-Check
        if use_cache and depth != "tief":
            cached = self.cache.get(query, depth)
            if cached:
                return {"cached": True, "pipeline_success": True, "pipeline_duration_ms": 5,
                        "cache_note": "Ergebnisse aus Cache (24h TTL)"}
        
        # Domain
        from query_analyzer import analyze_query
        q = analyze_query(query)
        domain = domain or q.domain_guess
        
        # Phase 1: Researcher
        r = self.researcher.run({"query": query, "depth": depth, "domain": domain})
        if not r.success:
            return {"error": "Researcher fehlgeschlagen", "details": r.errors}
        
        # Phase 2: Verifier
        v_input = {"results": raw_results or []}
        v = self.verifier.run(v_input)
        
        # Phase 3: Evidence Scoring
        search_results = []
        for item in (raw_results or []):
            sr = SearchResult(
                title=item.get("title",""), source=item.get("source",""),
                year=str(item.get("year","")), doi=item.get("doi",""),
                abstract=item.get("abstract",""),
            )
            if hasattr(sr, 'trust_score'):
                score = next((x.get("trust_score",0.5) for x in v.data.get("verified_results",[]) 
                             if x.get("title") == sr.title), 0.5)
                sr.trust_score = score
            search_results.append(sr)
        
        evidence_scored = score_evidence(search_results) if search_results else []
        evidence_sum = evidence_summary(evidence_scored) if evidence_scored else {}
        
        # Phase 4: Synthesis
        s = self.synthesis.run({
            "verified_results": v.data.get("verified_results", []),
            "query": query, "domain": domain,
        })
        
        # Phase 5: Clustering
        cluster_md = generate_cluster_report(search_results) if search_results else ""
        
        # Phase 6: Reviewer
        rev = self.reviewer.run({
            "top10": s.data.get("top10", []),
            "stats": s.data.get("stats", {}),
            "query": query, "domain": domain,
        })
        
        # Phase 7: PRISMA
        total_raw = len(raw_results or [])
        total_dedup = len(v.data.get("verified_results", []))
        oa_count = sum(1 for x in (raw_results or []) if x.get("pdf_url"))
        final_count = min(total_dedup, 20)
        prisma_flow = compute_prisma(total_raw, total_dedup, oa_count, final_count)
        prisma_md = generate_prisma_markdown(prisma_flow)
        
        # Cache speichern
        if raw_results and use_cache:
            self.cache.set(query, raw_results, depth, 
                          sources=[s.get("source","?") for s in raw_results])
        
        total_ms = (time.time() - t0) * 1000
        
        return {
            "pipeline_success": True,
            "cached": False,
            "query": query, "domain": domain, "depth": depth,
            "researcher": {"sources": r.data.get("total_sources", 0)},
            "verifier": v.data.get("summary", {}),
            "evidence": evidence_sum,
            "synthesis": {
                "summary": s.data.get("executive_summary", ""),
                "next_searches": s.data.get("next_searches", []),
            },
            "reviewer": {
                "quality_score": rev.data.get("quality_score", 0),
                "gaps": rev.data.get("gaps", []),
                "recommendations": rev.data.get("recommendations", []),
            },
            "prisma": {
                "identified": prisma_flow.identified,
                "screened": prisma_flow.screened,
                "included": prisma_flow.included,
            },
            "cluster_count": len(search_results),
            "pipeline_duration_ms": round(total_ms),
        }
    
    def stats(self) -> dict:
        return {
            "cache": self.cache.stats(),
            "agents": ["Researcher", "Verifier", "Evidence", "Synthesis", "Cluster", "Reviewer", "PRISMA"],
        }


if __name__ == "__main__":
    o = OrchestratorV3()
    
    test_results = [
        {"title": "A Meta-Analysis of Trading Strategies", "authors": "Smith et al.", "year": "2025", "doi": "10.1234/meta1", "source": "OpenAlex", "citations": 120, "abstract": "We conducted a systematic meta-analysis of trading strategies...", "pdf_url": "https://arxiv.org/pdf/meta1.pdf"},
        {"title": "Reinforcement Learning for Adaptive Trading", "authors": "Jones et al.", "year": "2024", "doi": "10.1234/rl1", "source": "arXiv", "citations": 45, "abstract": "This paper presents a reinforcement learning approach..."},
        {"title": "FVG Detection: A Case Study in NQ Futures", "authors": "Chen", "year": "2025", "doi": "10.1234/fvg1", "source": "SSRN", "citations": 8, "abstract": "This case study examines Fair Value Gaps..."},
    ]
    
    result = o.run_pipeline("adaptive trading strategy", "standard", raw_results=test_results)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"\nCache stats: {o.stats()['cache']}")
