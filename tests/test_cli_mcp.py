"""F16: Tests für die bisher ungetesteten Pfade wissenschaft_cli.py und mcp_server.py.

Diese Tests hätten die Review-Findings F12-F15 aufgedeckt.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = str(REPO / "wissenschaft_cli.py")


def _python():
    """Das Python, das die Tests ausführt — funktioniert lokal (venv) UND in der CI.

    Wichtig: NICHT .venv/bin/python hartkodieren — in der CI (GitHub-Runner)
    existiert kein venv und der Test bricht mit FileNotFoundError ab.
    """
    venv = REPO / ".venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


PY = _python()


def _run(*args, timeout=60):
    return subprocess.run([PY, CLI, *args], capture_output=True, text=True,
                          timeout=timeout, cwd=str(REPO))


def test_cli_help_funktioniert():
    r = _run("--help")
    assert r.returncode == 0
    for flag in ("--tiefe", "--dossier", "--download", "--input", "--quellen"):
        assert flag in r.stdout, f"{flag} fehlt in --help"


def test_f14_input_fehlende_datei_kein_traceback():
    """F14: fehlende Eingabedatei -> saubere Meldung, kein Traceback."""
    r = _run("--orchestrate", "--input", "/nonexistent/datei.json", "test")
    assert "Traceback" not in r.stderr, "F14: ungeschuetzter Crash"
    assert "nicht gefunden" in (r.stdout + r.stderr).lower() or r.returncode != 0


def test_f14_input_kaputtes_json():
    """F14: ungültiges JSON -> saubere Meldung."""
    kaputt = REPO / "tests" / "_tmp_kaputt.json"
    kaputt.write_text("{nicht json")
    try:
        r = _run("--orchestrate", "--input", str(kaputt), "test")
        assert "Traceback" not in r.stderr, "F14: ungeschuetzter Crash bei kaputtem JSON"
    finally:
        kaputt.unlink(missing_ok=True)


def test_f15_mcp_bindet_nicht_an_alle_interfaces():
    """F15: MCP-Server darf nicht 0.0.0.0 binden."""
    src = (REPO / "mcp_server.py").read_text()
    assert 'host = "0.0.0.0"' not in src, "F15: 0.0.0.0 noch vorhanden"
    assert "127.0.0.1" in src


def test_f12_export_nutzt_existierende_felder():
    """F12: der Export-Zweig darf keine nicht-existierenden Felder lesen."""
    src = (REPO / "wissenschaft_cli.py").read_text()
    assert 'get("top10_count"' not in src, "F12: top10_count existiert nicht"
    assert 'synthesis", {}).get("verified_results"' not in src, "F12: Feld existiert nicht"


def test_cli_plan_ohne_registry_kein_crash():
    """F13: --plan darf ohne Registry nicht crashen."""
    r = _run("--plan", "test query")
    assert "Traceback" not in r.stderr, "F13: Registry-Fehlen crasht"
