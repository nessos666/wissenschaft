"""Verbesserung 3 — PDF-Downloader + Dossier-Integration (offline testbar)."""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

from sources.downloader import _sicherer_name


def test_sicherer_name():
    """Dateiname: bereinigt, keine Sonderzeichen, DOI-Suffix."""
    name = _sicherer_name("EMDR: Therapy & Growth!", "10.1016/j.x.2024.01", 3)
    assert name.startswith("03_EMDR_Therapy_Growth")
    assert name.endswith(".pdf")
    assert "&" not in name and ":" not in name


def test_sicherer_name_ohne_doi():
    name = _sicherer_name("Bentonite Clay", "", 1)
    assert name == "01_Bentonite_Clay.pdf"


def test_sicherer_name_laenge():
    lang = _sicherer_name("X" * 200, "10.1/y" + "9" * 40, 9)
    assert len(lang) <= 100


def test_lade_pdfs_mockt_requests(monkeypatch):
    """lade_pdfs: pdf_url → Download; ohne url/doi → 'ohne_pdf'."""
    import sources.downloader as dl

    class FakeResp:
        status_code = 200
        headers = {"Content-Type": "application/pdf"}
        def iter_content(self, chunk_size=8192):
            yield b"%PDF-1.4 " + b"x" * 2500  # >1000 Bytes = valide

    def fake_get(url, **kw):
        return FakeResp()

    monkeypatch.setattr(dl.requests, "get", fake_get)
    treffer = [
        {"title": "Paper Mit Pdf", "doi": "", "pdf_url": "https://x.de/a.pdf"},
        {"title": "Paper Ohne", "doi": "", "pdf_url": ""},
    ]
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        stat = dl.lade_pdfs(treffer, Path(td), unpaywall_email="")
        assert len(stat["geladen"]) == 1
        assert stat["ohne_pdf"] == 1
        pdf = Path(stat["geladen"][0])
        assert pdf.exists() and pdf.read_bytes().startswith(b"%PDF")


def test_dossier_mit_download_pdfs(monkeypatch):
    """erstelle_dossier(download_pdfs=True): PDFs-Abschnitt im README."""
    from sources.writer import erstelle_dossier
    import sources.downloader as dl

    class FakeResp:
        status_code = 200
        headers = {"Content-Type": "application/pdf"}
        def iter_content(self, chunk_size=8192):
            yield b"%PDF-1.4 " + b"y" * 2500

    def fake_get(url, **kw):
        return FakeResp()
    monkeypatch.setattr(dl.requests, "get", fake_get)

    import tempfile
    ergebnis = {
        "query": "bentonite test", "depth": "standard", "domain": "x",
        "researcher": {"results": [
            {"title": "Bentonite Paper", "doi": "", "pdf_url": "https://x/a.pdf",
             "source": "arXiv", "year": "2024"},
        ], "sources_geliefert": ["arXiv"], "sources_versucht": 28},
        "prisma": {"identified": 1, "screened": 1, "included": 1},
        "synthesis": {"summary": "Zusammenfassung", "next_searches": []},
    }
    with tempfile.TemporaryDirectory() as td:
        pfade = erstelle_dossier(ergebnis, ziel=td, download_pdfs=True)
        assert "pdfs" in pfade, "PDFs fehlen im Ergebnis"
        readme = Path(pfade["README.md"]).read_text()
        assert "## PDFs (1 geladen)" in readme
