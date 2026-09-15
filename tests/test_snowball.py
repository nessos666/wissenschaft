"""Verbesserung 5 — Zitations-Snowballing (offline testbar, gemockt)."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

from sources import snowball as sb


def test_doi_sauber():
    assert sb._doi_sauber("https://doi.org/10.1/x") == "10.1/x"
    assert sb._doi_sauber("10.1/y") == "10.1/y"
    assert sb._doi_sauber("") == ""


def test_hole_referenzen_ohne_doi():
    assert sb.hole_referenzen("") == []


def test_hole_referenzen_parst_crossref(monkeypatch):
    """CrossRef reference-Liste → _norm-Format."""
    class FakeResp:
        status_code = 200
        def json(self):
            return {"message": {"reference": [
                {"DOI": "10.1/ref1", "article-title": "Klassiker A", "year": "2004"},
                {"unstructured": "Buchkapitel ohne DOI", "year": "1999"},
                {"volume-title": "Ohne alles"},
            ]}}
    monkeypatch.setattr(sb.requests, "get", lambda *a, **k: FakeResp())
    out = sb.hole_referenzen("10.1/orig", max_refs=5)
    assert len(out) == 3
    assert out[0]["doi"] == "10.1/ref1"
    assert out[0]["source"] == "CrossRef-Snowball"
    assert out[1]["title"] == "Buchkapitel ohne DOI"


def test_hole_referenzen_fehler_kein_crash(monkeypatch):
    def kaputt(*a, **k):
        raise OSError("kein Netz")
    monkeypatch.setattr(sb.requests, "get", kaputt)
    assert sb.hole_referenzen("10.1/x") == []


def test_hole_citing_parst_s2(monkeypatch):
    class FakeResp:
        status_code = 200
        def json(self):
            return {"data": [{"citingPaper": {
                "title": "Zitiert A", "year": 2025,
                "externalIds": {"DOI": "10.2/cit"},
                "authors": [{"name": "Becker, A"}], "abstract": "Text"}}]}
    monkeypatch.setattr(sb.requests, "get", lambda *a, **k: FakeResp())
    out = sb.hole_citing("10.1/x", max_citing=3)
    assert len(out) == 1
    assert out[0]["source"] == "S2-Snowball"
    assert out[0]["doi"] == "10.2/cit"


def test_hole_citing_404_leer(monkeypatch):
    class FakeResp:
        status_code = 404
    monkeypatch.setattr(sb.requests, "get", lambda *a, **k: FakeResp())
    assert sb.hole_citing("10.1/x") == []


def test_snowball_sammelt_und_dedupliziert_titel(monkeypatch):
    """snowball() hängt Referenzen an; Seeds ohne DOI werden übersprungen."""
    monkeypatch.setattr(sb, "hole_referenzen",
                        lambda doi, max_refs=6: [{"title": f"Ref-{doi}", "doi": "",
                                                  "year": "", "url": "", "pdf_url": "",
                                                  "source": "CrossRef-Snowball",
                                                  "citations": 0, "abstract": "",
                                                  "authors": ""}])
    monkeypatch.setattr(sb, "hole_citing", lambda *a, **k: [])
    treffer = [{"title": "Seed 1", "doi": "10.1/a", "url": ""},
               {"title": "Seed ohne DOI", "doi": "", "url": ""}]
    zusatz = sb.snowball(treffer, max_seeds=3)
    assert len(zusatz) == 1  # nur für den Seed MIT DOI
