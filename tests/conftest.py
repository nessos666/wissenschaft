"""conftest.py — /wissenschaft Test-Suite ist OFFLINE.

Abschluss-Review F8: Tests dürfen keine echten Netz-Requests machen
(offline flaky/langsam). Dieses Auto-Fixture ersetzt urllib.request.urlopen
für ALLE Tests: DOI-Checks (api.crossref.org) liefern lokale Antworten,
URL-Checks gelten als erreichbar — nur wenn ein Test explizit ein eigenes
Mock setzt (monkeypatch überschreibt), gewinnt dessen Version.
"""
import urllib.request
import urllib.error

import pytest


@pytest.fixture(autouse=True)
def _offline_netz(monkeypatch):
    """Ersetzt urlopen: CrossRef-DOIs → valide Antwort, URLs → erreichbar."""

    def lokale_antwort(url: str):
        if "crossref.org/works/" in url:
            doi = url.split("works/")[-1].split("?")[0]
            # Bekannte Test-DOIs valide, alles andere 404
            if doi in ("10.1613/jair.301", "10.1/x", "10.1/1", "10.1/2",
                       "10.9/z", "10.1234/abc"):
                body = ('{"message": {"title": ["Test-Titel"],'
                        '"author": [{"given": "Anna", "family": "Becker"}]}}')
            else:
                raise urllib.error.HTTPError(url, 404, "unbekannter DOI",
                                             {}, None)
            return 200, body
        # URL-Check (HEAD): erreichbar
        return 200, ""

    def fake_urlopen(req, timeout=None, **kw):
        url = req.full_url if hasattr(req, "full_url") else str(req)

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

        status, body = lokale_antwort(url)
        if status >= 400:
            raise urllib.error.HTTPError(url, status, "fehler", {}, None)
        return Resp(status, body)

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
