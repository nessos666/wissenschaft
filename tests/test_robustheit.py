"""Block 3 — Robustheit: Pipeline überlebt unsaubere Daten (RED zuerst).

Die Pipeline darf NIE crashen, wenn externe raw_results unsauber sind:
int statt str, None-Werte, nicht-numerische Zitationen, Nicht-Dict-Einträge.
Muster aus SUCHER-OpenAIRE-Fix: defensive Normalisierung an Pipeline-Grenzen.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from orchestrator import OrchestratorV3


@pytest.fixture
def orch():
    # use_cache=False MUSS erzwungen werden — sonst überspringt der Cache
    # die Pipeline und die Tests testen den Cache, nicht die Robustheit!
    return OrchestratorV3()


def _run(orch, query, results):
    return orch.run_pipeline(query, depth="standard", raw_results=results,
                             use_cache=False)


def test_leere_results_ueberleben(orch):
    """Leere Ergebnisliste darf nie crashen — liefert Struktur zurück."""
    r = _run(orch, "leere query", [])
    assert r.get("pipeline_success") is True, f"leer crashte: {r}"


def test_nur_titel_ueberlebt(orch):
    """Dict mit NUR title (alle anderen Keys fehlen) darf nie crashen."""
    r = _run(orch, "test nur titel", [{"title": "Nur Titel"}])
    assert r.get("pipeline_success") is True


def test_int_statt_str_title_ueberlebt(orch):
    """Titel als int (12345) statt str — darf nicht crashen."""
    r = _run(orch, "test int titel",
             [{"title": 12345, "citations": "10"}])
    assert r.get("pipeline_success") is True


def test_none_values_ueberleben(orch):
    """None in title/doi/url/citations/authors — darf nicht crashen."""
    r = _run(orch, "test none values", [
        {"title": None, "doi": None, "url": None,
         "citations": None, "authors": None}])
    assert r.get("pipeline_success") is True


def test_nicht_numerische_citations_ueberleben(orch):
    """citations='abc' statt Zahl — der gefundene Crash (ValueError)."""
    r = _run(orch, "test abc citations", [{"title": "ok", "citations": "abc"}])
    assert r.get("pipeline_success") is True


def test_dict_statt_int_citations_ueberleben(orch):
    """citations als Dict statt int — darf nicht crashen."""
    r = _run(orch, "test dict citations",
             [{"title": "ok", "citations": {"x": 1}}])
    assert r.get("pipeline_success") is True


def test_nicht_dict_eintrag_ueberlebt(orch):
    """Eintrag als String statt Dict in der Liste — darf nicht crashen."""
    r = _run(orch, "test string eintrag",
             ["nur-ein-string", {"title": "ok"}])
    assert r.get("pipeline_success") is True
