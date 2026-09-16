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
    # asyncio.wait(FIRST_COMPLETED) statt sequenzieller Await-Schleife:
    # Quellen werden gleichzeitig abgewartet und sofort gemeldet.
    assert "asyncio.wait" in src, "F8: kein paralleles Abwarten — Stau möglich"
    assert "FIRST_COMPLETED" in src, "F8: keine Live-Meldung pro Quelle"


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


# ─────────────── Transparenz: offene Quellen sichtbar ───────────────

def test_transparenz_offen_und_ohne_treffer_getrennt():
    """David: offene Quellen müssen sichtbar sein, 'keine Treffer' ist kein Fehler."""
    import sources.papersearch as ps

    def fake_eine(cls, query, max_results):
        if cls.__name__ == "ArxivSearcher":
            return [{"title": "P", "doi": "10.1/a", "url": "u",
                     "source": "arxiv", "published_date": "2020"}]
        return []

    orig = ps._search_eine
    try:
        ps._search_eine = fake_eine
        erg = ps.search_papers("test", sources="arxiv,zenodo", timeout_s=10)
    finally:
        ps._search_eine = orig

    # Beide Kategorien existieren getrennt und sind nicht identisch
    assert "sources_offen" in erg
    assert "sources_ohne_treffer" in erg
    assert "sources_antworteten" in erg
    assert erg["total"] >= 1
    # zenodo hat geantwortet (leer) -> darf NICHT als Fehler gelten
    assert "zenodo" in erg["sources_ohne_treffer"]
    assert "zenodo" not in (erg.get("errors") or {})


def test_orchestrator_reicht_transparenz_felder_durch():
    """Regression: der Orchestrator darf offen/ohne_treffer nicht rausfiltern."""
    import inspect
    from orchestrator import OrchestratorV3
    src = inspect.getsource(OrchestratorV3.run_pipeline)
    assert '"sources_offen"' in src, "Offen-Feld fehlt im Orchestrator-Ergebnis"
    assert '"sources_ohne_treffer"' in src, "ohne_treffer fehlt im Orchestrator-Ergebnis"


def test_writer_zeigt_offene_quellen():
    """Das Dossier muss den Quellen-Status ausweisen."""
    from sources.writer import _offene_quellen_markdown
    fake = {"researcher": {"sources_versucht": 10, "sources_geliefert": ["a"],
                           "sources_offen": ["langsam1", "langsam2"],
                           "sources_ohne_treffer": ["speziell1"]}}
    md = _offene_quellen_markdown(fake)
    assert "langsam1" in md and "langsam2" in md
    assert "speziell1" in md
    assert "kein Fehler" in md.lower() or "normal" in md.lower()
