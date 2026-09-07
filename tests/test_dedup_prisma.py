"""Block 5 — Dedup + PRISMA echt verdrahtet (RED zuerst).

deduplicate() existiert, wird aber nie aufgerufen. Die Kette soll sein:
Suche → Dedup → Verifier → Evidence → PRISMA (Zahlen aus echten Stufen).
PRISMA identified = Roh-Treffer, screened = nach Dedup, included = final.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

from deduplicator import SearchResult, deduplicate
from orchestrator import OrchestratorV3


# ---------- deduplicate selbst ----------

def test_deduplicate_doi_match():
    """Gleiche DOI → ein Treffer (merged_from zeigt die Quelle)."""
    a = SearchResult(title="Paper A", doi="10.1/x", source="OpenAlex")
    b = SearchResult(title="Paper A (Kopie)", doi="10.1/x", source="arXiv")
    out = deduplicate([a, b])
    assert len(out) == 1
    assert "arXiv" in out[0].merged_from


def test_deduplicate_titel_fuzzy():
    """Ähnliche Titel ohne DOI (> 0.85) → dedupliziert."""
    a = SearchResult(title="Water retention in bentonite clay soils", source="A")
    b = SearchResult(title="Water retention in bentonite clay soil", source="B")
    out = deduplicate([a, b])
    assert len(out) == 1


def test_deduplicate_verschiedene_bleiben():
    """Verschiedene Papiere bleiben erhalten."""
    a = SearchResult(title="Paper Eins", doi="10.1/a", source="A")
    b = SearchResult(title="Paper Zwei", doi="10.2/b", source="B")
    assert len(deduplicate([a, b])) == 2


# ---------- Orchestrator-Verdrahtung ----------

def test_orchestrator_prisma_zahlen_nach_dedup(monkeypatch):
    """PRISMA: identified=roh, screened=nach-Dedup — die Pipeline ruft
    deduplicate() auf und PRISMA spiegelt die echten Stufen."""
    calls = {"dedup": 0}

    original_dedup = deduplicate

    def dedup_spy(results):
        calls["dedup"] += 1
        return original_dedup(results)

    monkeypatch.setattr("deduplicator.deduplicate", dedup_spy)

    orch = OrchestratorV3()

    # Researcher gemockt: liefert 2 Treffer mit GLEICHER DOI (1 Duplikat)
    class FakeResearcher:
        def run(self, input_data):
            from agents import AgentResult
            return AgentResult(agent_name="Fake", success=True, data={"results": [
                {"title": "Paper A", "doi": "10.1/x", "source": "OpenAlex",
                 "url": "https://a.de/1", "year": 2020},
                {"title": "Paper A Kopie", "doi": "10.1/x", "source": "arXiv",
                 "url": "https://a.de/2", "year": 2020},
            ]}, errors=[])

    orch.researcher = FakeResearcher()
    r = orch.run_pipeline("dedup test", depth="standard", raw_results=None,
                          use_cache=False)
    assert calls["dedup"] >= 1, "deduplicate() wurde NIE aufgerufen!"
    prisma = r.get("prisma", {})
    # 2 Roh-Treffer, nach Dedup nur 1
    assert prisma.get("identified") == 2, f"identified falsch: {prisma}"
    assert prisma.get("screened") == 1, f"screened falsch (Dedup fehlt): {prisma}"
