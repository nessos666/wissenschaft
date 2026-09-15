"""Abschluss-Review-Fixes (OpenCode-Findings F1-F6) — Regressionstests.

Jeder Test bildet einen verifizierten OpenCode-Befund ab.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

from deduplicator import SearchResult, deduplicate
from sources.writer import _bibtex, _bibtex_escape
from sources import searcher
from verifier import Verifier
from orchestrator import OrchestratorV3


# ---------- F1: PRISMA zählt Müll nicht als Record ----------

def test_prisma_ident_zahlt_nur_valide_records():
    """[String, {valider}] → identified=1 (Müll ist KEIN Record)."""
    orch = OrchestratorV3()

    class FakeResearcher:
        def run(self, input_data):
            from agents import AgentResult
            # raw_results wird direkt übergeben (nicht über Researcher)
            return AgentResult(agent_name="Fake", success=True,
                               data={"results": []}, errors=[])

    orch.researcher = FakeResearcher()
    r = orch.run_pipeline("müll test", depth="standard",
                          raw_results=["kein dict", {"title": "Valides Paper",
                                                     "doi": "10.1/x"}],
                          use_cache=False)
    assert r.get("pipeline_success")
    assert r["prisma"]["identified"] == 1, "Müll wurde als Record gezählt!"
    assert r["prisma"]["screened"] == 1


# ---------- F2: Merge verliert pdf_url/authors nicht ----------

def test_dedup_merge_behaelt_pdf_url_authors():
    """OpenAlex zuerst (leer), arXiv-Kopie mit PDF → PDF überlebt den Merge."""
    a = SearchResult(title="Paper X", doi="10.1/x", source="OpenAlex",
                     year="2020", url="https://oa/w1")
    b = SearchResult(title="Paper X", doi="10.1/x", source="arXiv",
                     year="2021", pdf_url="https://arxiv.org/pdf/2401.pdf",
                     authors="Musterfrau", url="http://arxiv.org/abs/2401")
    out = deduplicate([a, b])
    assert len(out) == 1
    ueberlebt = out[0]
    assert ueberlebt.pdf_url == "https://arxiv.org/pdf/2401.pdf", "pdf_url verloren!"
    assert ueberlebt.authors == "Musterfrau", "authors verloren!"
    assert ueberlebt.year == "2020"  # erstes nicht-leeres Feld gewinnt


# ---------- F4: BibTeX escaped ----------

def test_bibtex_escaping():
    """& % # _ in Titeln → valide .bib (escaped)."""
    out = _bibtex([{"title": "Water & Soil #1_Test", "year": "2020",
                    "authors": "Becker, A", "doi": "10.1/x",
                    "source": "CrossRef"}])
    assert r"\&" in out, "& nicht escaped!"
    assert r"\#" in out, "# nicht escaped!"
    assert r"\_" in out, "_ nicht escaped!"


def test_bibtex_escape_funktion():
    assert _bibtex_escape("a & b") == r"a \& b"
    assert _bibtex_escape("100%") == r"100\%"


# ---------- F5: Cache-Hit liefert volles Schema ----------

def test_cache_hit_volles_schema():
    """Cache-Hit → researcher/prisma/synthesis vorhanden (schema-identisch)."""
    orch = OrchestratorV3()
    # Erst in den Cache schreiben (simuliert einen früheren Frisch-Lauf)
    treffer = [{"title": "Gecachtes Paper", "year": "2022", "doi": "10.9/z",
                "url": "https://x.de/1", "source": "CrossRef",
                "abstract": "", "authors": "X, Y", "citations": 1}]
    orch.cache.set("cache schema test", treffer, "standard", sources=["CrossRef"])

    # Cache-Hit abrufen (use_cache=True, keine raw_results)
    r = orch.run_pipeline("cache schema test", depth="standard",
                          raw_results=None, use_cache=True)
    assert r.get("cached") is True, "kein Cache-Hit!"
    # Volles Schema vorhanden:
    assert "researcher" in r and "results" in r["researcher"], "researcher fehlt!"
    assert r["researcher"]["results"], "Treffer fehlen im Cache-Hit!"
    assert "prisma" in r, "prisma fehlt!"
    assert r["prisma"]["identified"] >= 1


# ---------- F6: Verifier-Gesamtbudget ----------

def test_verifier_budget_kuerzt(monkeypatch):
    """Budget 0.02s + langsamer Live-Check (0.05s) → Rest schnell abgefertigt."""
    import time as _t
    v = Verifier()
    v.budget_s = 0.02
    papiere = [SearchResult(title=f"Paper {i}", doi=f"10.1/{i}",
                            source="X") for i in range(5)]
    # Live-Check simuliert: dauert 0.05s (wie ein echter DOI-Request)
    def langsamer_check(doi):
        _t.sleep(0.05)
        return {"valid": True, "title": "Paper"}
    monkeypatch.setattr(v, "check_doi", langsamer_check)
    monkeypatch.setattr(v, "check_url", lambda url: True)
    t0 = _t.time()
    out = v.verify_all(papiere)
    dauer = _t.time() - t0
    assert len(out) == 5, "alle müssen ein Ergebnis haben (liefert immer etwas)"
    # Budget muss gegriffen haben: deutlich schneller als 5×0.05s=0.25s
    assert dauer < 0.2, f"Budget griff nicht — dauerte {dauer:.2f}s"
    assert any("Budget" in w for vr in out for w in vr.warnings), \
        "Budget-Warnung fehlt — Budget griff nicht"


# ---------- Verbesserung 8: Zeitraum-Filter ----------

def test_zeitraum_filter_grenzen(monkeypatch):
    """jahr_von/jahr_bis filtern Treffer; unbekanntes Jahr bleibt."""
    orch = OrchestratorV3()

    class FakeResearcher:
        def run(self, input_data):
            from agents import AgentResult
            return AgentResult(agent_name="Fake", success=True,
                               data={"results": []}, errors=[])

    orch.researcher = FakeResearcher()
    r = orch.run_pipeline(
        "zeitraum test", depth="standard", raw_results=[
            {"title": "Alt 2010", "year": "2010", "source": "CrossRef"},
            {"title": "Mittel 2020", "year": "2020", "source": "CrossRef"},
            {"title": "Neu 2025", "year": "2025", "source": "CrossRef"},
            {"title": "Ohne Jahr", "year": "", "source": "CrossRef"},
        ], use_cache=False, jahr_von="2015", jahr_bis="2024")
    treffer = (r.get("researcher") or {}).get("results") or []
    titel = [t["title"] for t in treffer]
    assert "Alt 2010" not in titel, "2010 muss raus"
    assert "Neu 2025" not in titel, "2025 muss raus"
    assert "Mittel 2020" in titel
    assert "Ohne Jahr" in titel, "unbekanntes Jahr bleibt"


def test_zeitraum_filter_ohne_grenzen():
    """Ohne jahr_von/jahr_bis bleibt alles."""
    orch = OrchestratorV3()

    class FakeResearcher:
        def run(self, input_data):
            from agents import AgentResult
            return AgentResult(agent_name="Fake", success=True,
                               data={"results": []}, errors=[])

    orch.researcher = FakeResearcher()
    r = orch.run_pipeline("x", depth="standard", raw_results=[
        {"title": "A", "year": "1990", "source": "CrossRef"},
        {"title": "B", "year": "2025", "source": "CrossRef"},
    ], use_cache=False)
    assert len((r.get("researcher") or {}).get("results") or []) == 2
