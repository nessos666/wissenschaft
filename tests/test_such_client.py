"""Block 2 — Echter Such-Client (RED zuerst): searcher.py existiert nicht.

Der Researcher-Agent soll ECHT suchen können (nicht nur routen). Neues Modul
sources/searcher.py: query → Ergebnisse aus key-freien APIs (CrossRef + arXiv,
harte Timeouts, Quelle-down→andere-liefert). Abschluss-Review-Fix: OpenAlex
hat Budget-System (HTTP 429 '$0') → CrossRef als Primärquelle.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

searcher = pytest.importorskip("sources.searcher")


# ---------- CrossRef-Parser ----------

def test_crossref_parser_robust():
    """CrossRef /works-Antwort → standardisierte Dicts (Feld-Mapping)."""
    antwort = {"message": {"items": [
        {"title": ["EMDR Therapy and Posttraumatic Growth"],
         "DOI": "10.1016/j.janxdis.2021.01.001",
         "URL": "https://doi.org/10.1016/j.janxdis.2021.01.001",
         "issued": {"date-parts": [[2021, 3, 1]]},
         "author": [{"given": "Anna", "family": "Becker"}],
         "is-referenced-by-count": 42},
    ]}}
    out = searcher._parse_crossref(antwort)
    assert len(out) == 1
    r = out[0]
    assert "EMDR" in r["title"]
    assert r["year"] == 2021
    assert r["doi"] == "10.1016/j.janxdis.2021.01.001"  # ohne https://doi.org
    assert r["source"] == "CrossRef"
    assert r["citations"] == 42
    assert "Becker" in r["authors"]


def test_crossref_parser_leere_antwort():
    assert searcher._parse_crossref({"message": {"items": []}}) == []
    assert searcher._parse_crossref({}) == []


def test_crossref_parser_kaputte_eintraege_ueberleben():
    """Nicht-Dict-Einträge + fehlende Titel crashen nicht."""
    antwort = {"message": {"items": ["müll", {"title": ["Gültig"]}, None]}}
    out = searcher._parse_crossref(antwort)
    assert len(out) == 1
    assert out[0]["title"] == "Gültig"


# ---------- arXiv-Parser ----------

def test_arxiv_parser_robust():
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Large Language Model Agents</title>
        <published>2024-03-01T00:00:00Z</published>
        <id>http://arxiv.org/abs/2403.0001v1</id>
        <author><name>Jane Doe</name></author>
        <summary>We study agents.</summary>
      </entry>
    </feed>"""
    out = searcher._parse_arxiv(xml)
    assert len(out) == 1
    r = out[0]
    assert "Large Language Model" in r["title"]
    assert str(r["year"]) == "2024"  # Jahr kommt als str durch die Pipeline
    assert "arxiv.org" in r["url"]
    assert r["source"] == "arXiv"


def test_arxiv_parser_kaputtes_xml():
    assert searcher._parse_arxiv("<<<kaputt>>>") == []


# ---------- search(): Quelle-down→andere-liefert ----------

def test_search_crossref_down_arxiv_liefert(monkeypatch):
    """CrossRef wirft 429 → arXiv liefert trotzdem (nie crashen)."""
    import urllib.request
    original_urlopen = urllib.request.urlopen

    def fake_urlopen(req, timeout=None):
        if "crossref.org" in str(req.full_url):
            raise urllib.error.HTTPError(str(req.full_url), 429, "Rate limit",
                                         {}, None)
        # arXiv: leere Antwort (kein Treffer)
        xml = '<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"/>'
        class R:
            def read(self): return xml.encode()
            def __exit__(self, *a): pass
            def __enter__(self): return self
        return R()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    out = searcher.search("irgendwas", max_results=5)
    assert isinstance(out, list)  # nie None/crash


def test_search_leere_query():
    assert searcher.search("   ") == []
    assert searcher.search("") == []


def test_search_struktur_offline(monkeypatch):
    """Ohne Netz (alles wirft) → leere Liste statt Crash."""
    import urllib.request
    def kaputt(req, timeout=None):
        raise OSError("kein Netz")
    monkeypatch.setattr(urllib.request, "urlopen", kaputt)
    out = searcher.search("bentonite", max_results=5)
    assert out == []
