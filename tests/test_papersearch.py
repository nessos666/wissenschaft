"""Fusion Option A — tests für sources/papersearch.py (Brücke zu 17 Quellen).

Offline testbar: Dedup-Logik + Feld-Normalisierung (kein Netz nötig).
Die Live-Suche selbst ist in Live-Smokes verifiziert (24 Treffer/8 Quellen).
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

papersearch = pytest.importorskip("sources.papersearch")


def test_dedupe_doi():
    """Gleiche DOI → ein Treffer."""
    p1 = {"doi": "10.1/x", "title": "A"}
    p2 = {"doi": "10.1/x", "title": "A Kopie"}
    out = papersearch._dedupe([p1, p2])
    assert len(out) == 1


def test_dedupe_titel():
    """Ohne DOI: gleicher Titel+Autors → dedupliziert."""
    p1 = {"title": "Water retention in bentonite", "authors": "Muster"}
    p2 = {"title": "Water retention in bentonite", "authors": "Muster"}
    p3 = {"title": "Anderes Paper", "authors": "Anders"}
    assert len(papersearch._dedupe([p1, p2, p3])) == 2


def test_norm_feld_mapping():
    """paper-search-Felder → unser Schema (title/doi/url/source/year)."""
    roh = {"title": "Titel X", "doi": "https://doi.org/10.1/y",
           "url": "https://x.de", "pdf_url": "https://x.de/pdf",
           "source": "crossref", "published_date": "2024-03-01T00:00:00Z",
           "authors": "A; B", "citations": 42, "abstract": "Abstrakt"}
    n = papersearch._norm(roh)
    assert n["doi"] == "10.1/y"  # doi.org-Präfix gestrippt
    assert n["year"] == "2024"  # aus published_date
    assert n["source"] == "CrossRef"  # humanisiert
    assert n["citations"] == 42


def test_norm_fehltoleranz():
    """Kaputte Einträge crashen nicht."""
    n = papersearch._norm({})
    assert n["title"] == ""
    assert n["doi"] == ""
    assert n["citations"] == 0


def test_search_leere_query():
    erg = papersearch.search_papers("   ")
    assert erg["total"] == 0
    assert erg["papers"] == []


def test_search_unbekannte_quelle():
    erg = papersearch.search_papers("test", sources="gibt_es_nicht")
    assert erg["total"] == 0
    assert "keine valide Quelle" in str(erg["errors"])


def test_search_quellen_auswahl():
    """Nur ausgewählte Quelle suchen (kein Netz — wird gemockt)."""
    import sources.papersearch as ps

    def fake_eine(cls, query, max_results):
        return [{"title": "Paper", "doi": "10.1/a", "url": "u",
                 "source": "arxiv", "published_date": "2020"}]

    ps._search_eine = fake_eine
    erg = ps.search_papers("test", sources="arxiv", timeout_s=5)
    assert erg["total"] >= 1
    assert erg["sources_used"] == ["arxiv"]
