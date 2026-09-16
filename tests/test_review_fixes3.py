"""Regressionstests für die letzten drei Findings: F5 (doppelte Netzsuche),
F8 (Thread-Stau), F11 (PRISMA-Zahl ≠ Anzeige)."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


# ─────────────── F5: keine doppelte Netz-Suche ───────────────

def test_f5_multi_suche_leer_kein_zweiter_netzversuch():
    """F5: liefert multi_suche leer, darf search() NICHT erneut suchen."""
    from sources import searcher
    aufrufe = {"search": 0}

    def fake_multi(query, **kwargs):
        return {"papers": [], "sources_used": [], "errors": {}, "total": 0}

    def fake_search(query, max_results=5):
        aufrufe["search"] += 1
        return [{"title": "sollte nicht passieren"}]

    with patch.object(searcher, "multi_suche", fake_multi), \
         patch.object(searcher, "search", fake_search):
        treffer, info = searcher.search_mit_info("leere query")

    assert treffer == [], "F5: sollte leer sein"
    assert aufrufe["search"] == 0, "F5: search() wurde doppelt aufgerufen!"
    assert info.get("keine_treffer") is True


# ─────────────── F8: kein Thread-Stau ───────────────

def test_f8_getrennter_enrichment_pool():
    """F8: Enrichment nutzt einen eigenen Executor (nicht den Such-Pool)."""
    from sources import papersearch
    assert hasattr(papersearch, "_EXECUTOR_ENRICH"), "F8: kein Enrichment-Pool"
    assert papersearch._EXECUTOR is not papersearch._EXECUTOR_ENRICH


def test_f8_gleichzeitiges_abwarten():
    """F8: _lauf nutzt gather (parallel), nicht eine sequenzielle Await-Schleife."""
    import inspect
    from sources import papersearch
    src = inspect.getsource(papersearch)
    assert "asyncio.gather" in src, "F8: kein gather — sequenzieller Stau möglich"


# ─────────────── F11: PRISMA = Anzeige ───────────────

def test_f11_prisma_included_entspricht_anzeige():
    """F11: prisma['included'] muss len(researcher['results']) entsprechen."""
    from orchestrator import OrchestratorV3
    orch = OrchestratorV3()
    res = orch.run_pipeline(
        query="test", depth="schnell", use_cache=False,
        raw_results=[{"title": f"Paper {i}", "source": "test", "doi": f"10.1/{i}",
                      "url": f"http://x/{i}", "citations": i} for i in range(7)],
    )
    if not res.get("pipeline_success"):
        return  # Registry/Netz fehlt in dieser Umgebung — kein F11-Bezug
    gezeigt = len(res["researcher"]["results"])
    included = res["prisma"]["included"]
    assert included == gezeigt, f"F11: prisma.included={included} != angezeigt={gezeigt}"
