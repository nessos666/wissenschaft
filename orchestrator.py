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
from prisma import compute_prisma
from cache import ResponseCache


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
        
        # Cache-Check — Abschluss-Review F5: früher early-return mit Mini-Schema
        # ({cached, success, note}), das researcher/prisma/synthesis fehlte →
        # Konsumenten (Dossier-Writer) crashten bei Cache-Hit. Jetzt: Treffer
        # rehydrieren und Pipeline normal weiterlaufen lassen (schema-identisch).
        cache_herkunft = False
        if use_cache and depth != "tief":
            cached = self.cache.get(query, depth)
            if cached and raw_results is None:
                cache_herkunft = True
                raw_results = cached
        
        # Domain
        from query_analyzer import analyze_query
        q = analyze_query(query)
        domain = domain or q.domain_guess
        
        # Phase 1: Researcher — bei Cache-Hit überspringen (kein Netz-Request!)
        if cache_herkunft:
            # Schema-identisches Minimal-Ergebnis: Suche entfällt, Rest läuft
            r = type("R", (), {"success": True, "data": {"results": raw_results or [],
                "total_sources": 0, "sources_versucht": 0,
                "sources_geliefert": [], "search_performed": False}})()
        else:
            r = self.researcher.run({"query": query, "depth": depth, "domain": domain})
            if not r.success:
                return {"error": "Researcher fehlgeschlagen", "details": r.errors}
        
        # Block 2: Researcher liefert echte Treffer (search_performed=True).
        # Wenn KEINE externen raw_results gegeben sind, nutze die internen.
        interne_treffer = r.data.get("results", []) if r.data else []
        if raw_results is None and interne_treffer:
            raw_results = interne_treffer
        
        # Block 5: Dedup VOR Verifier — aus Roh-Treffern Duplikate entfernen
        # (DOI-Match + Titel-Fuzzy). raw_results sind rohe Dicts.
        from deduplicator import deduplicate, searchresult_from_dict
        # Abschluss-Review F1: ERST normalisieren, DANN zählen — Nicht-Dict-Müll
        # (String/None) darf nicht als "Record" in PRISMA identified landen
        # (sonst: identified=2, screened=1 = erfundene "Duplikat-Entfernung").
        sr_liste = [sr for sr in (searchresult_from_dict(x) for x in (raw_results or []))
                    if sr is not None]
        roh_anzahl = len(sr_liste)  # nur valide Records
        dedupliziert = deduplicate(sr_liste) if sr_liste else []
        # Deduplizierte zurück in Dicts für Verifier (Pipeline-Vertrag)
        raw_nach_dedup = [{
            "title": sr.title, "authors": sr.authors, "year": sr.year,
            "doi": sr.doi, "url": sr.url, "abstract": sr.abstract,
            "source": sr.source, "citations": sr.citations,
            "pdf_url": sr.pdf_url, "is_oa": sr.is_oa,
        } for sr in dedupliziert]
        dedup_anzahl = len(raw_nach_dedup)
        
        # Phase 2: Verifier (auf deduplizierten Treffern)
        v_input = {"results": raw_nach_dedup}
        v = self.verifier.run(v_input)
        
        # Phase 3: Evidence Scoring
        # Block 3 (Robustheit): zentrale Normalisierung — rohe externe Daten
        # können Nicht-Dict-Einträge und None-Felder enthalten, nie crashen.
        from deduplicator import searchresult_from_dict
        search_results = []
        verified_map = {}
        for x in (v.data.get("verified_results") or []):
            if isinstance(x, dict):
                verified_map[x.get("title", "")] = x.get("trust_score", 0.5)
        # Block 5: Evidence auf den DEDUPLIZIERTEN Treffern (raw_nach_dedup)
        for item in (raw_nach_dedup or []):
            sr = searchresult_from_dict(item)
            if sr is None:
                continue
            # Trust-Score aus Verifier-Phase übernehmen (falls vorhanden)
            sr.trust_score = verified_map.get(sr.title, 0.5)
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
        
        # Phase 7: PRISMA — Zahlen aus ECHTEN Stufen (Block 5):
        # identified = Roh-Treffer, screened = nach Dedup, included = final
        total_raw = roh_anzahl
        total_dedup = dedup_anzahl
        # Block 3: defensiv — Einträge können Nicht-Dict sein
        oa_count = sum(1 for x in (raw_nach_dedup or [])
                       if isinstance(x, dict) and x.get("pdf_url"))
        final_count = min(total_dedup, 20)
        prisma_flow = compute_prisma(total_raw, total_dedup, oa_count, final_count)
        
        # Cache speichern (deduplizierte Treffer — Block 5)
        if raw_nach_dedup and use_cache:
            self.cache.set(query, raw_nach_dedup, depth,
                          sources=[x.get("source", "?") for x in raw_nach_dedup
                                   if isinstance(x, dict)])
        
        total_ms = (time.time() - t0) * 1000
        
        # Block 2+5: DEDUPLIZIERTE Researcher-Ergebnisse im Ergebnis führen
        researcher_results = (raw_nach_dedup or [])[:20]
        return {
            "pipeline_success": True,
            "cached": cache_herkunft,
            "query": query, "domain": domain, "depth": depth,
            "researcher": {"sources": r.data.get("total_sources", 0),
                           "sources_versucht": r.data.get("sources_versucht", 0),
                           "sources_geliefert": r.data.get("sources_geliefert", []),
                           "results": researcher_results,
                           "search_performed": bool(r.data.get("search_performed"))},
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
