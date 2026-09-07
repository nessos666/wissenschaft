"""Block 6 — Einheitliches Datenmodell (RED zuerst): Metadaten überleben.

verified_results muss year/authors/citations/abstract/url durchreichen
(vorher nur title/doi/source/trust — nachgelagerte Phasen verloren Daten).
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

from agents.verifier_agent import VerifierAgent


@pytest.fixture
def agent():
    return VerifierAgent()


def test_verifier_reicht_metadaten_durch(agent):
    """Verifier-Ausgabe enthält ALLE Metadaten (nicht nur title/doi/trust)."""
    ergebnis = agent.run({"results": [
        {"title": "Vollständiges Paper", "year": "2021", "authors": "Smith, J",
         "citations": 42, "abstract": "Abstract text", "url": "https://a.de/1",
         "pdf_url": "https://a.de/1.pdf", "doi": "10.1234/abc",
         "source": "OpenAlex"}
    ]})
    assert ergebnis.success
    vr = ergebnis.data["verified_results"][0]
    for feld in ("title", "year", "authors", "citations", "abstract",
                 "url", "pdf_url", "doi", "source", "trust_score"):
        assert feld in vr, f"Feld '{feld}' fehlt in verified_results"


def test_verifier_metadaten_werte_korrekt(agent):
    """Die Werte selbst sind korrekt durchgereicht (nicht leer/default)."""
    ergebnis = agent.run({"results": [
        {"title": "Paper X", "year": "2019", "authors": "Doe, Jane",
         "citations": 7, "abstract": "Wichtiges Abstract",
         "url": "https://b.de/2", "doi": "10.99/xyz", "source": "arXiv"}
    ]})
    vr = ergebnis.data["verified_results"][0]
    assert vr["year"] == "2019"
    assert vr["authors"] == "Doe, Jane"
    assert vr["citations"] == 7
    assert vr["abstract"] == "Wichtiges Abstract"
    assert vr["url"] == "https://b.de/2"
