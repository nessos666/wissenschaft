"""Verbesserung 1 — Relevanz-Ranking (ranker.py verdrahtet).

Der Ranker sortiert nach Query-Titel-Match (nicht nur Citations/Quellen-
Reihenfolge), und der Orchestrator nutzt ihn NACH Dedup.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

from deduplicator import SearchResult
from ranker import rank_results, _relevanz_score


def test_relevanz_score_volle_abdeckung():
    """Alle Query-Begriffe im Titel → hoher Score."""
    assert _relevanz_score("Posttraumatic Growth after EMDR Therapy",
                           "posttraumatic growth EMDR") == 3.0


def test_relevanz_score_keine_abdeckung():
    """Kaum Query-Abdeckung im Titel (nur 'growth' von 3) → niedrig."""
    assert _relevanz_score("Crystal growth of strontium iridate",
                           "posttraumatic growth EMDR") <= 1.0


def test_relevanz_dominanz_vor_citations():
    """Relevantes Paper schlägt Zitier-Schwergewicht OHNE Query-Match."""
    relevant = SearchResult(title="EMDR Therapy for Posttraumatic Growth",
                            year="2024", citations=5, source="CrossRef")
    schwergewicht = SearchResult(title="Strontium Crystal Growth",
                                 year="2019", citations=900, source="arXiv")
    out = rank_results([schwergewicht, relevant], query="posttraumatic growth EMDR")
    assert out[0] is relevant, "Relevanz muss vor Citations gewinnen!"


def test_quellen_trust_echte_liste():
    """Kuratierte Quellen (PubMed) > Preprints (arXiv) bei gleicher Relevanz."""
    pubmed = SearchResult(title="EMDR and Trauma Growth", year="2024",
                          citations=10, source="PubMed")
    preprint = SearchResult(title="EMDR and Trauma Growth", year="2024",
                            citations=10, source="arXiv")
    out = rank_results([preprint, pubmed], query="EMDR trauma growth")
    assert out[0] is pubmed


def test_orchestrator_rankt_nach_dedup():
    """Orchestrator: Ergebnisse kommen RELEVANZ-sortiert heraus."""
    from orchestrator import OrchestratorV3
    orch = OrchestratorV3()

    class FakeResearcher:
        def run(self, input_data):
            from agents import AgentResult
            return AgentResult(agent_name="Fake", success=True,
                               data={"results": []}, errors=[])

    orch.researcher = FakeResearcher()
    r = orch.run_pipeline("EMDR posttraumatic growth", depth="standard",
                          raw_results=[
                              {"title": "Strontium Crystal Growth",
                               "year": "2019", "citations": 900,
                               "source": "arXiv", "url": "https://x/1"},
                              {"title": "EMDR Therapy and Posttraumatic Growth",
                               "year": "2024", "citations": 5,
                               "source": "CrossRef", "url": "https://x/2"},
                          ], use_cache=False)
    assert r.get("pipeline_success")
    treffer = (r.get("researcher") or {}).get("results") or []
    assert treffer and "EMDR Therapy" in treffer[0]["title"], \
        f"Relevanz-Sortierung fehlt — Top: {treffer[0]['title'] if treffer else 'leer'}"
