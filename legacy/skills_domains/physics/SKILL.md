---
name: physics-sources
domain: physics
triggers: [physik, quantum, particle, higgs, CERN, LHC, relativity, cosmology, astrophysics, gravity, string theory, black hole]
sources:
  - name: arXiv Physics
    type: mcp
    tool: mcp_paper_search_search_arxiv
    query_template: "{query} physics"
    max_results: 10
  - name: INSPIRE HEP
    type: direct
    endpoint: https://inspirehep.net/api/literature
    query_template: "{query}"
    max_results: 10
---

# Physics Research Skills

Diese Quellen werden aktiviert wenn die Query Physik-Keywords enthält.
