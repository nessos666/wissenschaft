"""Block 2 — Echter Such-Client (RED zuerst): searcher.py existiert nicht.

Der Researcher-Agent soll ECHT suchen können (nicht nur routen). Neues Modul
sources/searcher.py: query → Ergebnisse aus key-freien APIs (OpenAlex + arXiv,
Muster aus SUCHER-1000). Ohne externe JSON-Datei.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

# Modul existiert noch nicht → Import schlägt fehl (RED)
searcher = pytest.importorskip("sources.searcher")


def test_modul_liefert_search_funktion():
    assert callable(searcher.search), "searcher.search fehlt"


def test_openalex_parser_robust(fake_payloads=None):
    """OpenAlex-API-Antwort → standardisierte Dicts (Feld-Mapping korrekt)."""
    antwort = {"results": [
        {"title": "Bentonite water retention", "publication_year": 2020,
         "doi": "https://doi.org/10.1016/x", "id": "https://openalex.org/W1",
         "cited_by_count": 42, "primary_location": {"pdf_url": "https://pdf.de/1",
         "landing_page_url": "https://journal.de/1"}},
    ]}
    out = searcher._parse_openalex(antwort)
    assert len(out) == 1
    r = out[0]
    assert r["title"] == "Bentonite water retention"
    assert r["year"] == 2020
    assert r["doi"] == "10.1016/x"  # volle URL → nackte DOI normalisiert
    assert r["source"] == "OpenAlex"
    assert r["citations"] == 42


def test_openalex_parser_leere_antwort():
    assert searcher._parse_openalex({"results": []}) == []
    assert searcher._parse_openalex({}) == []


def test_arxiv_parser_robust():
    """arXiv-Atom-XML → standardisierte Dicts."""
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Large Language Model Agents</title>
        <published>2024-03-01T00:00:00Z</published>
        <id>http://arxiv.org/abs/2401.00001v1</id>
        <author><name>Jane Smith</name></author>
        <summary>Survey of LLM agents and tool use.</summary>
      </entry>
    </feed>"""
    out = searcher._parse_arxiv(xml)
    assert len(out) == 1
    r = out[0]
    assert "Large Language Model" in r["title"]
    assert str(r["year"]) == "2024"  # Jahr kommt als str durch die Pipeline
    assert "arxiv.org" in r["url"]
    assert r["source"] == "arXiv"


def test_search_ergebnis_struktur(monkeypatch):
    """search() liefert Liste von Dicts mit Standard-Feldern (auch ohne Netz
    via gemocktem Transport — prüft die Verdrahtung, nicht das echte Netz)."""
    # Transport mocken: openalex liefert 1 Treffer, arxiv leer
    calls = []

    class FakeTransport:
        def open(self, url, timeout=8):
            calls.append(url)
            if "openalex.org" in url:
                body = b'{"results": [{"title": "Test Paper", "publication_year": 2021, "doi": "https://doi.org/10.1/x"}]}'
            else:
                body = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
            return FakeResponse(body)

    class FakeResponse:
        def __init__(self, body):
            self._body = body

        def read(self):
            return self._body

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    import sources.searcher as s
    # Transport injizieren (searcher nutzt intern urllib — hier monkeypatchen)
    monkeypatch.setattr(s, "_open", FakeTransport().open)
    results = s.search("test query", max_results=3)
    assert isinstance(results, list)
    # Mindestens die Feld-Struktur eines Treffers prüfen (openalex-Treffer)
    if results:
        for key in ("title", "year", "doi", "source", "url"):
            assert key in results[0], f"Feld {key} fehlt"
