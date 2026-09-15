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
            max_results = {"schnell": 5, "standard": 15, "tief": 25}.get(depth, 15)
            from sources.searcher import search_mit_info
            treffer, such_info = search_mit_info(query, max_results=max_results)

            # Verbesserung 6: Query-Erweiterung — NUR wenn die Hauptsuche
            # wenig liefert (< 5 Treffer). Ehrlicher Befund: die Langform
            # kann Rauschen bringen (EMDR → 'eye movement' matcht auch
            # Eye-Tracking-Studien), daher nur als Lücken-Füller.
            try:
                from query_analyzer import erweitere_query
                if len(treffer) < 5:
                    varianten = erweitere_query(query)
                    for variante in varianten:
                        extra, _ = search_mit_info(variante, max_results=max_results // 2)
                        vorhandene_titel = {(t.get("title") or "").lower()
                                            for t in treffer}
                        neu = [e for e in extra
                               if (e.get("title") or "").lower() not in vorhandene_titel]
                        if neu:
                            treffer = treffer + neu
                            self.log(f"Query-Erweiterung '{variante[:40]}…': "
                                     f"+{len(neu)} Treffer")
            except Exception:
                pass  # Erweiterung ist Bonus

            # Verbesserung 5: Zitations-Snowballing nur bei Tiefe 'tief' —
            # für die Top-3-Treffer Referenzen (rückwärts, CrossRef) +
            # Zitierende (vorwärts, S2) holen und anhängen. Findet klassische
            # Schlüsselwerke, die die Query-Suche verpasst.
            if depth == "tief" and treffer:
                try:
                    from sources.snowball import snowball
                    zusatz = snowball(treffer, max_seeds=3, pro_seed=6)
                    if zusatz:
                        vorhandene = {(t.get("title") or "").lower()
                                      for t in treffer}
                        neu = [z for z in zusatz
                               if (z.get("title") or "").lower() not in vorhandene]
                        treffer = treffer + neu
                        self.log(f"Snowballing: +{len(neu)} Papers "
                                 f"(Referenzen/Zitierend)")
                except Exception:
                    pass  # Snowballing ist Bonus
            
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

            # Quellen-Transparenz (Qualitäts-Verbesserung): ECHTE gelieferte
            # Quellen aus den Treffer-source-Feldern zählen (nicht Routing).
            gelieferte = sorted({t.get("source", "?") for t in treffer
                                 if isinstance(t, dict)})
            # Gesamtzahl der aktiv versuchten Quellen (Brücke), wenn verfügbar
            try:
                from sources.papersearch import ALL_SOURCES
                versucht = len(ALL_SOURCES)
            except Exception:
                versucht = len(sources) or 0

            self.log(f"{len(treffer)} echte Treffer aus "
                     f"{len(gelieferte)} von {versucht} Quellen "
                     f"({len(mcp_sources)} MCP-Quellen geroutet)")

            return self.ok({
                "query": query,
                "domain": domain,
                "depth": depth,
                "total_sources": len(sources),
                "sources_versucht": versucht,
                "sources_geliefert": gelieferte,
                "sources_ohne_antwort": such_info.get("ohne_antwort", []),
                "mcp_sources": [{"name": s.name, "tool": s.mcp_tool, "tier": s.tier} for s in mcp_sources],
                "direct_sources": [{"name": s.name, "tier": s.tier} for s in direct_sources],
                "results": treffer,  # Block 2: echte Suchergebnisse
                "search_performed": True,
            }, duration=(time.time()-t0)*1000)
        except Exception as e:
            return self.fail([str(e)])
