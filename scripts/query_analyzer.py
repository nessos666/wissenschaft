#!/usr/bin/env python3
"""
Query Analyzer V2 — Boolean + Domain. Direkt ausfuehrbar.
Teil des /wissenschaft Tools.
"""
import sys, json, os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from wissenschaft_cli import detect_domain, expand_query
    query = sys.argv[1] if len(sys.argv) > 1 else "FVG AND microstructure NOT bitcoin"
    domain = detect_domain(query)
    expanded = expand_query(query, domain)
    print(json.dumps({
        "query": query,
        "domain": domain,
        "expanded_query": expanded
    }, indent=2, ensure_ascii=False))
except ImportError:
    print(json.dumps({"error": "Run from project root: python3 scripts/query_analyzer.py 'QUERY'"}))
