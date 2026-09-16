---
name: trading-sources
domain: trading
triggers: [trading, FVG, ICT, SMC, microstructure, futures, orderflow, NQ, ES, backtest, strategy, RL, reinforcement, Quant]
sources:
  - name: SSRN
    type: mcp
    tool: mcp_paper_search_search_ssrn
    query_template: "{query} finance trading"
    max_results: 10
  - name: RePEc
    type: direct
    endpoint: https://api.repec.org/...
    query_template: "{query}"
    max_results: 10
  - name: arXiv q-fin
    type: mcp
    tool: mcp_paper_search_search_arxiv
    query_template: "{query} quantitative finance"
    max_results: 10
  - name: NBER
    type: direct
    endpoint: https://nber.org/api/...
    query_template: "{query}"
    max_results: 10
---

# Trading Research Skills

Diese Quellen werden aktiviert wenn die Query Trading/Finance-Keywords enthält.
