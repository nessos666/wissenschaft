#!/usr/bin/env python3
"""/wissenschaft V2 — 4-Agent-Pipeline mit Verifier, Skills, Async, Qdrant."""
import sys, json, argparse
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from query_analyzer import analyze_query
from source_router import route_sources
from orchestrator import OrchestratorV3 as Orchestrator
from formatter import save_exports


def main():
    parser = argparse.ArgumentParser(description="Wissenschaftliche Recherche V2")
    parser.add_argument("query", nargs="?", help="Suchbegriff")
    parser.add_argument("--tiefe", choices=["schnell", "standard", "tief"], default="standard")
    parser.add_argument("--plan", action="store_true", help="Nur Suchplan ausgeben")
    parser.add_argument("--input", type=str, help="JSON-Datei mit Roh-Ergebnissen")
    parser.add_argument("--orchestrate", action="store_true", help="4-Agent-Pipeline nutzen")
    parser.add_argument("--dossier", action="store_true",
                        help="KOMPLETT: echte Suche → Pipeline → Dossier erstellen "
                             "(kein --input nötig — Researcher sucht selbst)")
    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        return

    # Analyse
    q = analyze_query(args.query)

    if args.dossier:
        # Block 4: KOMPLETT-Lauf — echte Suche (Researcher) → Pipeline → Dossier
        print(f"🔬 /wissenschaft — Komplett-Recherche: '{args.query}' (Tiefe: {args.tiefe})")
        orch = Orchestrator()
        result = orch.run_pipeline(query=args.query, depth=args.tiefe,
                                   raw_results=None, use_cache=False)
        if not result.get("pipeline_success"):
            print(f"  ✗ Pipeline fehlgeschlagen: {result.get('error', '?')}")
            return
        from sources.writer import erstelle_dossier
        pfade = erstelle_dossier(result)
        print(f"  ✅ Pipeline: success | "
              f"{len((result.get('researcher') or {}).get('results') or [])} Treffer "
              f"aus {len((result.get('researcher') or {}).get('sources_geliefert') or [])} "
              f"von {(result.get('researcher') or {}).get('sources_versucht', '?')} Quellen")
        print(f"  📁 Dossier erstellt:")
        for typ, pfad in pfade.items():
            print(f"     {typ:10s} → {pfad}")
        return
    
    if args.plan:
        sources = route_sources(q.domain_guess, args.tiefe)
        mcp = [{"tool": s.mcp_tool, "source_name": s.name, "tier": s.tier} for s in sources if s.mcp_tool]
        direct = [{"name": s.name, "tier": s.tier} for s in sources if not s.mcp_tool]
        plan = {
            "query": q.original, "domain": q.domain_guess, "confidence": q.domain_confidence,
            "depth": args.tiefe, "mcp_calls": mcp, "direct_sources": direct,
        }
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return

    if args.orchestrate and args.input:
        # 4-Agent-Pipeline
        with open(args.input) as f:
            data = json.load(f)
        
        orch = Orchestrator()
        result = orch.run_pipeline(
            query=args.query,
            depth=args.tiefe,
            raw_results=data.get("results", []),
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Export wenn Ergebnisse da sind
        if result.get("synthesis", {}).get("top10_count", 0) > 0:
            from deduplicator import SearchResult
            verified = result.get("synthesis", {}).get("verified_results", [])
            papers = []
            for v in verified:
                papers.append(SearchResult(
                    title=v.get("title",""), source=v.get("source",""), doi=v.get("doi",""),
                    citations=v.get("citations",0),
                ))
            if papers:
                paths = save_exports(args.query, papers)
                print(f"\nExports: {len(paths)} Dateien")
        return

    # Fallback: Einfache Analyse
    print(f"Query: {q.original}")
    print(f"Domain: {q.domain_guess} (conf={q.domain_confidence:.1f})")
    print(f"Tiefe: {args.tiefe}")
    sources = route_sources(q.domain_guess, args.tiefe)
    print(f"Quellen: {len(sources)} geroutet")
    print(f"Verfügbar: --plan | --orchestrate --input FILE")


if __name__ == "__main__":
    main()
