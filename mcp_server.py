#!/usr/bin/env python3
"""MCP-Server-Starter (Fusion Option B) — /wissenschaft als MCP für Hermes.

Startet die vendored paper-search-mcp Bibliothek als streamable-http MCP
Server auf Port 8100 (Hermes-Config: paper-search → http://localhost:8100/mcp).
Damit kann auch Hermes selbst die 21 Quellen über search_papers-Tools nutzen.

Start:  .venv/bin/python mcp_server.py
Stop:   Ctrl-C (oder process kill)
"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
VENDOR = REPO / "vendor" / "paper_search_mcp"
if str(VENDOR) not in sys.path:
    sys.path.insert(0, str(VENDOR))

from paper_search_mcp.server import mcp  # noqa: E402

mcp.settings.host = os.environ.get("WISSENSCHAFT_MCP_HOST", "127.0.0.1")
mcp.settings.port = 8100
mcp.settings.log_level = "INFO"

if __name__ == "__main__":
    print("🔬 /wissenschaft paper-search MCP Server auf 0.0.0.0:8100")
    print("   21 Quellen (CrossRef, PubMed, Europe PMC, Semantic Scholar, …)")
    mcp.run(transport="streamable-http")
