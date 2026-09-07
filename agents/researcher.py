"""Researcher Agent — führt Quellensuche durch (MCP + Direct)."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents import BaseAgent, AgentResult
from source_router import route_sources

class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__("Researcher", "Sucht wissenschaftliche Quellen")
    
    def run(self, input_data: dict) -> AgentResult:
        t0 = time.time()
        query = input_data.get("query", "")
        depth = input_data.get("depth", "standard")
        domain = input_data.get("domain", "multidisciplinary")
        
        if not query:
            return self.fail(["Keine Query angegeben"])
        
        self.log(f"Suche '{query[:60]}...' (Domain: {domain}, Tiefe: {depth})")
        
        try:
            # Block 2: ECHTE Suche — Researcher fragt key-freie APIs direkt ab
            # (statt nur Quellen zu routen). Quelle down → andere liefert.
            max_results = {"schnell": 3, "standard": 8, "tief": 15}.get(depth, 8)
            from sources.searcher import search as echte_suche
            treffer = echte_suche(query, max_results=max_results)
            
            sources = []
            try:
                sources = route_sources(domain, depth)
            except Exception as e:
                # Abschluss-Review F7: Registry fehlt/kaputt (frische Maschine) →
                # nicht failen, leere Quellenliste reicht (echte Suche läuft trotzdem)
                self.log(f"Quellen-Registry nicht verfügbar ({type(e).__name__}): "
                         f"nutze direkte Suche ohne Quellenliste")
            mcp_sources = [s for s in sources if s.mcp_tool]
            direct_sources = [s for s in sources if not s.mcp_tool]
            
            self.log(f"{len(treffer)} echte Treffer ({len(mcp_sources)} MCP-"
                     f"{'Quelle' if len(mcp_sources)==1 else 'Quellen'} geroutet)")
            
            return self.ok({
                "query": query,
                "domain": domain,
                "depth": depth,
                "total_sources": len(sources),
                "mcp_sources": [{"name": s.name, "tool": s.mcp_tool, "tier": s.tier} for s in mcp_sources],
                "direct_sources": [{"name": s.name, "tier": s.tier} for s in direct_sources],
                "results": treffer,  # Block 2: echte Suchergebnisse
                "search_performed": True,
            }, duration=(time.time()-t0)*1000)
        except Exception as e:
            return self.fail([str(e)])
