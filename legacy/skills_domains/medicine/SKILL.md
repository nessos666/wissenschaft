---
name: medicine-sources
domain: medicine
triggers: [medizin, klinisch, patient, therapie, diagnose, pharma, impfstoff, erkrankung, symptom, infection, maternal, autism, genetics, DNA, genom, mutation, Krebs, Alzheimer, diabetes]
sources:
  - name: PubMed
    type: mcp
    tool: mcp_paper_search_search_pubmed
    query_template: "{query}"
    max_results: 10
  - name: Europe PMC
    type: mcp
    tool: mcp_paper_search_search_europepmc
    query_template: "{query}"
    max_results: 10
  - name: bioRxiv
    type: mcp
    tool: mcp_paper_search_search_biorxiv
    query_template: "{query}"
    max_results: 10
---

# Medical Research Skills

Diese Quellen werden aktiviert wenn die Query medizinische Keywords enthält.
