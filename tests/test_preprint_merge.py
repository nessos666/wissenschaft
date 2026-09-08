"""Verbesserung 2 — Preprint→Published-Merging.

arXiv/bioRxiv-Preprint (DOI 10.48550/…) + Verlags-Version (CrossRef/PubMed,
anderer DOI) derselben Arbeit → EIN Eintrag, Verlag gewinnt.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from deduplicator import SearchResult, deduplicate


def test_preprint_und_published_mergen():
    """arXiv-Preprint + CrossRef-Published (verschiedene DOIs, ähnlicher
    Titel) → EIN Eintrag, CrossRef gewinnt."""
    arxiv = SearchResult(
        title="EMDR Therapy for Complex Posttraumatic Stress Disorder",
        doi="10.48550/arXiv.2301.12345", source="arXiv", year="2023",
        url="http://arxiv.org/abs/2301.12345",
        pdf_url="https://arxiv.org/pdf/2301.12345")
    verlag = SearchResult(
        title="EMDR Therapy for Complex Posttraumatic Stress Disorder",
        doi="10.1093/oxfordhb/9780192898357.013.48", source="CrossRef",
        year="2023", url="https://doi.org/10.1093/oxfordhb/x")
    out = deduplicate([arxiv, verlag])
    assert len(out) == 1, f"Preprint+Published nicht gemerged: {len(out)}"
    assert out[0].source == "CrossRef", "Verlag muss gewinnen!"
    assert "arXiv" in out[0].merged_from
    # pdf_url des Preprints bleibt erhalten (Open-Access-Volltext)
    assert out[0].pdf_url == "https://arxiv.org/pdf/2301.12345"


def test_preprint_zuerst_verlag_spaeter():
    """Umgekehrte Reihenfolge: Preprint zuerst, Verlag später → Verlag
    ersetzt den Preprint (nicht umgekehrt)."""
    arxiv = SearchResult(
        title="Water retention in bentonite clay barriers",
        doi="10.48550/arXiv.2402.99", source="arXiv", year="2024")
    verlag = SearchResult(
        title="Water retention in bentonite clay barriers",
        doi="10.1016/j.clay.2024.107", source="CrossRef", year="2024")
    out = deduplicate([arxiv, verlag])
    assert len(out) == 1
    assert out[0].source == "CrossRef", "Späterer Verlagseintrag muss gewinnen!"


def test_zwei_verschiedene_verlagspaper_bleiben():
    """Zwei VERLAGS-Paper mit ähnlichen Titeln aber verschiedenen DOIs
    sind NICHT dasselbe (kein Preprint beteiligt) → bleiben getrennt."""
    a = SearchResult(title="EMDR Therapy for PTSD in Adults",
                     doi="10.1016/j.a.2024.01", source="CrossRef")
    b = SearchResult(title="EMDR Therapy for PTSD in Adults: A Review",
                     doi="10.1016/j.b.2024.02", source="CrossRef")
    out = deduplicate([a, b])
    assert len(out) == 2, "Verlags-Paper mit versch. DOIs dürfen nicht mergen!"


def test_zwei_verschiedene_arxiv_paper_bleiben():
    """Zwei arXiv-Preprints mit ähnlichem Titel (gleiche Quelle) bleiben
    getrennt (verschiedene Arbeiten)."""
    a = SearchResult(title="Graph Neural Networks for Traffic",
                     doi="10.48550/arXiv.2401.001", source="arXiv")
    b = SearchResult(title="Graph Neural Networks for Traffic Prediction",
                     doi="10.48550/arXiv.2401.002", source="arXiv")
    out = deduplicate([a, b])
    assert len(out) == 2, "Zwei arXiv-Paper mit versch. DOIs bleiben getrennt!"
