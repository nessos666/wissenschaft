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
    parser.add_argument("--download", action="store_true",
                        help="Mit --dossier: OA-PDFs der Treffer laden "
                             "(Verbesserung 3 — pdf_url direkt, sonst Unpaywall)")
    parser.add_argument("--jahr-von", type=str, default="",
                        help="Nur Treffer ab diesem Jahr (Verbesserung 8)")
    parser.add_argument("--jahr-bis", type=str, default="",
                        help="Nur Treffer bis zu diesem Jahr (Verbesserung 8)")
    parser.add_argument("--quellen", type=str, default="",
                        help="Delta-Folgelauf (Verbesserung 10): nur diese "
                             "kommagetrennten Quellen abfragen, z.B. "
                             "'openalex,semantic' — für Lücken aus dem letzten Lauf")
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
                                   raw_results=None, use_cache=False,
                                   jahr_von=args.jahr_von, jahr_bis=args.jahr_bis,
                                   nur_quellen=args.quellen)
        if not result.get("pipeline_success"):
            print(f"  ✗ Pipeline fehlgeschlagen: {result.get('error', '?')}")
            return
        from sources.writer import erstelle_dossier
        try:
            pfade = erstelle_dossier(result, download_pdfs=args.download)
        except Exception as e:  # F10: Vertrag 'nie crashen' auch bei Disk/Permission-Fehler
            print(f"⚠️  Dossier konnte nicht geschrieben werden: {type(e).__name__}: {e}")
            print("   Die Recherche-Ergebnisse oben bleiben gültig.")
            pfade = None
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
        try:
            with open(args.input) as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Eingabedatei nicht gefunden: {args.input}")
            return 1
        except json.JSONDecodeError as e:
            print(f"❌ Ungültiges JSON in {args.input}: {e}")
            return 1
        
        orch = Orchestrator()
        result = orch.run_pipeline(
            query=args.query,
            depth=args.tiefe,
            raw_results=data.get("results", []),
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Export wenn Ergebnisse da sind
        if len(result.get("verifier_detail", [])) > 0:
            from deduplicator import SearchResult
            verified = result.get("verifier_detail", [])
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
