"""Tests für verifier.py — offline (Transport gemockt, Abschluss-Review F8).

Die Logik (DOI-valid/nicht, URL erreichbar/nicht, Trust-Score) wird mit
gemocktem urlopen getestet — keine echten Netz-Requests (offline flaky).
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from verifier import Verifier, VerifiedResult
from deduplicator import SearchResult


# ---------- Fixtures: gemockter Transport ----------

def _mock_urlopen(antworten: dict):
    """Ersetzt urllib.request.urlopen: URL-Teil → (status, body)."""
    import urllib.request
    import urllib.error
    original = urllib.request.urlopen

    def fake(req, timeout=None, **kw):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        for teil, (status, body) in antworten.items():
            if teil in url:
                class Resp:
                    def __init__(self, code, inhalt):
                        self.status = code
                        self.body = inhalt.encode() if isinstance(inhalt, str) else inhalt
                    def read(self):
                        return self.body
                    def __enter__(self):
                        return self
                    def __exit__(self, *a):
                        return False
                if status >= 400:
                    raise urllib.error.HTTPError(url, status, "err", {}, None)
                return Resp(status, body)
        raise urllib.error.HTTPError(url, 404, "nicht gefunden", {}, None)

    return fake


# ---------- DOI-Checks (Logik, offline) ----------

def test_verify_valid_doi(monkeypatch):
    """CrossRef-Antwort mit Titel → DOI valide + Titel extrahiert."""
    import urllib.request
    body = '{"message": {"title": ["Reinforcement Learning: A Survey"]}}'
    monkeypatch.setattr(urllib.request, "urlopen",
                        _mock_urlopen({"crossref.org": (200, body)}))
    v = Verifier(timeout=5)
    result = v.check_doi("10.1613/jair.301")
    assert result["valid"], f"Valid DOI failed: {result.get('error')}"
    assert "Reinforcement" in result.get("title", "")


def test_verify_broken_doi(monkeypatch):
    """CrossRef 404 → DOI nicht valide."""
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        _mock_urlopen({"crossref.org": (404, "")}))
    v = Verifier(timeout=5)
    result = v.check_doi("10.9999/doesnotexist123456789")
    assert not result["valid"]


def test_verify_no_doi():
    v = Verifier(timeout=5)
    result = v.check_doi("")
    assert not result["valid"]


# ---------- URL-Checks (Logik, offline) ----------

def test_url_check_google(monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        _mock_urlopen({"google.com": (200, "")}))
    v = Verifier(timeout=5)
    assert v.check_url("https://google.com")


def test_url_check_broken(monkeypatch):
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen",
                        _mock_urlopen({"unbekannt": (404, "")}))
    v = Verifier(timeout=5)
    assert not v.check_url("https://thisurldoesnotexist99999.com")


# ---------- Voll-Verifikation ----------

def test_verify_full_paper(monkeypatch):
    import urllib.request
    body = '{"message": {"title": ["Reinforcement Learning: A Survey"]}}'
    monkeypatch.setattr(urllib.request, "urlopen",
                        _mock_urlopen({"crossref.org": (200, body),
                                       "doi.org": (200, "")}))
    v = Verifier()
    r = SearchResult(
        title="Reinforcement Learning: A Survey",
        authors="Kaelbling; Littman; Moore",
        year="1996", doi="10.1613/jair.301",
        url="https://doi.org/10.1613/jair.301",
        source="OpenAlex", citations=8836,
    )
    vr = v.verify(r)
    assert vr.doi_verified
    assert vr.trust_score > 0.5


def test_verify_paper_no_doi():
    v = Verifier()
    r = SearchResult(title="Some Paper", authors="Author", year="2020",
                     source="arXiv")
    vr = v.verify(r)
    assert not vr.doi_verified
    assert len(vr.warnings) > 0


def test_summary(monkeypatch):
    import urllib.request
    body = '{"message": {"title": ["Test"]}}'
    monkeypatch.setattr(urllib.request, "urlopen",
                        _mock_urlopen({"crossref.org": (200, body)}))
    v = Verifier()
    r = SearchResult(title="Test", doi="10.1613/jair.301", source="OpenAlex")
    summary = v.summary([v.verify(r)])
    assert summary["total"] == 1
