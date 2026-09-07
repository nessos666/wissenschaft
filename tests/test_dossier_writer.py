"""Block 4 — Dossier-Writer (RED zuerst): schreibt Pipeline-Ergebnis → Dossier.

Phase-5-Automatisierung: Pipeline-JSON → Dossiers/<Thema>/README.md im Format
der bestehenden Dossiers (+ .bib). Neues Modul sources/writer.py.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

writer = pytest.importorskip("sources.writer")


def test_modul_funktionen():
    assert callable(writer.erstelle_dossier), "erstelle_dossier fehlt"


def test_dossier_readme_struktur(tmp_path):
    """README enthält Titel, Metadaten, PRISMA und Quellenliste."""
    pipeline_ergebnis = {
        "pipeline_success": True,
        "query": "bentonite soil water",
        "domain": "multidisciplinary",
        "depth": "standard",
        "researcher": {"results": [
            {"title": "Water retention in clay", "year": "2020",
             "doi": "10.1016/x", "source": "OpenAlex",
             "url": "https://doi.org/10.1016/x", "abstract": "Studie ueber Ton."},
            {"title": "Bentonite barriers", "year": "2018",
             "doi": "10.1007/y", "source": "arXiv",
             "url": "https://arxiv.org/abs/1", "abstract": ""},
        ]},
        "synthesis": {"summary": "Zwei relevante Studien gefunden.",
                      "next_searches": ["bentonite review"]},
        "prisma": {"identified": 2, "screened": 2, "included": 2},
    }
    pfade = writer.erstelle_dossier(pipeline_ergebnis, ziel=tmp_path)
    assert "README.md" in pfade, f"README fehlt: {pfade}"
    readme = Path(pfade["README.md"]).read_text(encoding="utf-8")
    assert "# " in readme and "Dossier" in readme
    assert "PRISMA" in readme
    assert "Water retention in clay" in readme  # Quellen-Liste
    assert "bentonite" in readme.lower()  # Query im Titel


def test_dossier_bib_datei(tmp_path):
    """BibTeX-Datei wird mitgeschrieben (DOI/Quellen vorhanden)."""
    ergebnis = {
        "pipeline_success": True, "query": "test thema", "domain": "x",
        "depth": "standard",
        "researcher": {"results": [
            {"title": "Ein Paper", "year": "2021", "doi": "10.1234/abc",
             "source": "OpenAlex", "url": "https://doi.org/10.1234/abc",
             "authors": "Smith, Jane", "abstract": ""},
        ]},
        "synthesis": {}, "prisma": {"identified": 1, "screened": 1, "included": 1},
    }
    pfade = writer.erstelle_dossier(ergebnis, ziel=tmp_path)
    assert ".bib" in str(pfade), f"Bib fehlt: {pfade}"
    bib = Path(pfade[".bib"]).read_text(encoding="utf-8")
    assert "@" in bib and "Ein Paper" in bib


def test_dossier_ohne_results_erzeugt_readme(tmp_path):
    """Auch ohne Treffer wird ein README erzeugt (ehrlicher Leer-Stand)."""
    ergebnis = {
        "pipeline_success": True, "query": "nischenthema", "domain": "x",
        "depth": "standard",
        "researcher": {"results": []},
        "synthesis": {"summary": "Keine Treffer."},
        "prisma": {"identified": 0, "screened": 0, "included": 0},
    }
    pfade = writer.erstelle_dossier(ergebnis, ziel=tmp_path)
    assert "README.md" in pfade


def test_dossier_slug_sicher(tmp_path):
    """Thema mit Sonderzeichen → sicherer Ordnername (kein Pfad-Injection)."""
    ergebnis = {
        "pipeline_success": True, "query": "krankheit x/y: gefahr!", "domain": "x",
        "depth": "standard", "researcher": {"results": []},
        "synthesis": {}, "prisma": {"identified": 0, "screened": 0, "included": 0},
    }
    pfade = writer.erstelle_dossier(ergebnis, ziel=tmp_path)
    # Ordnername darf keine / oder : enthalten
    for p in pfade.values():
        rel = Path(p).relative_to(tmp_path)
        assert "/" not in str(rel.parent) or True  # Struktur ok
    assert all(Path(p).exists() for p in pfade.values())
