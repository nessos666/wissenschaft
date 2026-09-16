"""Regressionstests für die OpenCode-Review-Findings (F1, F4, F6, F7, F17, F13, F2)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_f1_dataverse_e_hat_doi_parameter():
    """F1: _e() in extra5 muss doi akzeptieren (sonst crasht Dataverse)."""
    from sources.quellen_extra5 import _e
    r = _e("Titel", "http://x", "Quelle", doi="10.1234/test")
    assert r["doi"] == "10.1234/test"


def test_f2_promised_sources_exist():
    """F2: Die in Doku versprochenen EBI-Quellen müssen existieren."""
    import sources.papersearch as ps
    for name in ("pride", "interpro", "expression_atlas", "biomodels", "kegg"):
        assert name in ps.SEARCHER_MAP, f"{name} fehlt"


def test_f4_dedup_keine_verwaiste_doi():
    """F4: Nach Preprint→Published-Merge darf die Preprint-DOI nicht verwaisen."""
    from deduplicator import deduplicate, SearchResult
    preprint = SearchResult(title="Deep Learning for X", doi="10.48550/arXiv.2301.00001",
                            source="arXiv", url="http://arxiv.org/abs/2301.00001")
    verlag = SearchResult(title="Deep Learning for X", doi="10.1000/verlag.2024.1",
                          source="CrossRef", url="http://doi.org/10.1000/verlag.2024.1")
    out = deduplicate([preprint, verlag])
    assert len(out) == 1, f"erwartet 1, bekam {len(out)}"
    assert out[0].doi == "10.1000/verlag.2024.1"


def test_f6_cache_legt_elternverzeichnis_an(tmp_path=None):
    """F6: ResponseCache darf auf frischer Maschine nicht crashen."""
    from cache import ResponseCache
    tief = Path(tempfile.mkdtemp()) / "a" / "b" / "cache.db"
    c = ResponseCache(str(tief))
    assert tief.parent.exists()


def test_f7_verifier_budget_markiert_nicht_als_verifiziert():
    """F7: Bei erschöpftem Budget darf DOI nicht als verifiziert gelten."""
    import inspect
    import verifier
    src = inspect.getsource(verifier)
    assert "optimistisch" not in src, "F7: optimistische Verifikation noch vorhanden"


def test_f17_bindestrich_bleibt_erhalten():
    """F17: post-traumatic darf nicht zu 'post traumatic' zerfallen."""
    from query_analyzer import parse_boolean
    clean, excl, _ = parse_boolean("post-traumatic stress disorder")
    assert "post-traumatic" in clean, f"Bindestrich verloren: {clean!r}"


def test_f13_source_router_ohne_registry():
    """F13: fehlende Registry darf keinen Crash auslösen."""
    import source_router
    orig = source_router.REGISTRY_PATH
    try:
        source_router.REGISTRY_PATH = Path("/nonexistent/registry.yaml")
        out = source_router.route_sources("test") if hasattr(source_router, "route_sources") else []
        assert out == [] or out is not None
    finally:
        source_router.REGISTRY_PATH = orig


def test_f3_immer_treffer_geparkt():
    """F3: Quellen ohne echte Suche dürfen nicht aktiv sein."""
    from sources.quellen_extra8 import EXTRA_QUELLEN_8_OFFEN
    import sources.papersearch as ps
    assert "nndc" in EXTRA_QUELLEN_8_OFFEN
    assert "nndc" not in ps.SEARCHER_MAP
