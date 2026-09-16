"""Source Router V2 — TIER 1+2+3 mit regionalen Quellen"""
from pathlib import Path
from dataclasses import dataclass, field
import yaml

REGISTRY_PATH = Path.home() / ".hermes" / "knowledge_registry.yaml"

@dataclass
class RoutedSource:
    name: str; url: str; tier: int; priority: int; trust: int
    domains: list[str] = field(default_factory=list)
    access_mode: str = "api"; mcp_tool: str = ""; score: float = 0.0

def route_sources(query_domain: str, depth: str = "standard") -> list[RoutedSource]:
    if not REGISTRY_PATH.exists():
        return []
    with open(REGISTRY_PATH) as f:
        reg = yaml.safe_load(f)
    
    tier1, tier2, tier3 = [], [], []
    
    for key, val in reg.items():
        if not key.startswith('category_') or not isinstance(val, list):
            continue
        for s in val:
            if not isinstance(s, dict): continue
            name = s.get('name',''); wp = s.get('workflow_priority', 99)
            domains = s.get('domains',[]); access = s.get('access_mode','api')
            auto = s.get('automation_allowed', True)
            mcp = s.get('mcp',{}); mcp_available = isinstance(mcp, dict) and mcp.get('available',False)
            if not auto: continue
            
            mcp_map = {"OpenAlex":"mcp_paper_search_search_openalex","CrossRef":"mcp_paper_search_search_crossref","Semantic Scholar":"mcp_paper_search_search_semantic","arXiv":"mcp_paper_search_search_arxiv","PubMed":"mcp_paper_search_search_pubmed","Europe PMC":"mcp_paper_search_search_europepmc","Zenodo":"mcp_paper_search_search_zenodo","SSRN":"mcp_paper_search_search_ssrn","DBLP":"mcp_paper_search_search_dblp"}
            
            source = RoutedSource(name=name, url=s.get('url',''), tier=wp if wp<=3 else 4,
                priority=s.get('priority',3), trust=s.get('trust',3),
                domains=domains, access_mode=access,
                mcp_tool=mcp_map.get(name,"") if mcp_available else "")
            
            if wp == 1: tier1.append(source)
            elif wp == 2 and query_domain in domains: source.score=0.8; tier2.append(source)
            elif wp == 3 and query_domain in domains: source.score=0.5; tier3.append(source)
    
    if depth == "schnell": return tier1[:3]
    elif depth == "standard":
        result = tier1[:5]
        result.extend(sorted(tier2, key=lambda x:(x.priority,x.trust), reverse=True)[:5])
        return result
    else:  # tief
        result = tier1
        result.extend(sorted(tier2, key=lambda x:(x.priority,x.trust), reverse=True)[:10])
        result.extend(sorted(tier3, key=lambda x:(x.priority,x.trust), reverse=True)[:5])
        return result

if __name__ == "__main__":
    sources = route_sources("trading", "tief")
    for s in sources:
        mcp = s.mcp_tool or f"direct:{s.name}"
        print(f"[Tier {s.tier}] {s.name} ({s.access_mode}) — {mcp}")
