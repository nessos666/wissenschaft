"""
Direct Client V2 — REST/OAI-PMH Suche für nicht-MCP Quellen.
Quellen die via OpenAlex abgedeckt sind, liefern [] (schon in MCP-Suche).
Nur Quellen MIT funktionierender Direkt-API werden aktiv durchsucht.
"""
import json, urllib.request, urllib.error, urllib.parse
from dataclasses import dataclass

@dataclass
class DirectResult:
    title: str = ""; authors: str = ""; year: str = ""; doi: str = ""
    url: str = ""; abstract: str = ""; source: str = ""
    citations: int = 0; is_oa: bool = True; pdf_url: str = ""

# Quellen die via OpenAlex abgedeckt sind (bereits in MCP-Suche enthalten)
COVERED_BY_OPENALEX = [
    'SciELO', 'Redalyc', 'Dialnet', 'J-STAGE', 'AJOL',
    'CyberLeninka', 'Shodhganga', 'NDLTD', 'CiNii', 'KCI',
]

# Quellen mit funktionierender Direkt-API
DIRECT_APIS = {
    # J-STAGE WebAPI (XML) — funktioniert
    'J-STAGE': {
        'url': 'https://www.jstage.jst.go.jp/api/search/global',
        'type': 'rest_json',
        'params': {'q': '{query}', 'limit': '{max}'},
        'field_map': {'title': 'title', 'authors': 'creator', 'year': 'pubYear', 'doi': 'doi', 'url': 'url', 'abstract': 'description'},
    },
}

def search_direct(source_name: str, query: str, max_results: int = 10) -> list[DirectResult]:
    """Führt direkte Suche aus. Liefert [] wenn via OpenAlex abgedeckt."""
    if source_name in COVERED_BY_OPENALEX:
        return []  # Bereits in OpenAlex-Suche enthalten
    
    api = DIRECT_APIS.get(source_name)
    if not api:
        return []
    
    results = []
    try:
        url = api['url']
        params = {k: str(v).replace('{query}', urllib.parse.quote(query)).replace('{max}', str(max_results))
                  for k, v in api.get('params', {}).items()}
        if params:
            url += '?' + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Hermes/1.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        
        fm = api.get('field_map', {})
        items = data if isinstance(data, list) else data.get('results', data.get('data', []))
        
        for item in items[:max_results]:
            results.append(DirectResult(
                title=item.get(fm.get('title', 'title'), ''),
                authors=str(item.get(fm.get('authors', 'authors'), '')),
                year=str(item.get(fm.get('year', 'year'), ''))[:4],
                doi=item.get(fm.get('doi', 'doi'), ''),
                url=item.get(fm.get('url', 'url'), ''),
                abstract=str(item.get(fm.get('abstract', 'abstract'), ''))[:300],
                source=source_name, is_oa=True,
            ))
    except Exception:
        pass
    
    return results

# Legacy-Funktionen als Wrapper
def search_scielo(q, m=10): return search_direct('SciELO', q, m)
def search_redalyc(q, m=10): return search_direct('Redalyc', q, m)
def search_jstage(q, m=10): return search_direct('J-STAGE', q, m)
def search_ajol(q, m=10): return search_direct('AJOL', q, m)
def search_cyberleninka(q, m=10): return search_direct('CyberLeninka', q, m)
def search_shodhganga(q, m=10): return search_direct('Shodhganga', q, m)
def search_ndltd(q, m=10): return search_direct('NDLTD', q, m)
def search_dialnet(q, m=10): return search_direct('Dialnet', q, m)

SOURCE_FUNCTIONS = {
    'SciELO': search_scielo, 'Redalyc': search_redalyc, 'J-STAGE': search_jstage,
    'AJOL': search_ajol, 'CyberLeninka': search_cyberleninka,
    'Shodhganga': search_shodhganga, 'NDLTD': search_ndltd, 'Dialnet': search_dialnet,
}

if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else 'J-STAGE'
    query = sys.argv[2] if len(sys.argv) > 2 else 'machine learning'
    results = search_direct(source, query)
    covered = source in COVERED_BY_OPENALEX
    print(f"{source}: {'via OpenAlex (already in MCP search)' if covered else f'{len(results)} Treffer'} für '{query}'")
    for r in results[:3]:
        print(f"  - {r.title[:80]} ({r.year})")
