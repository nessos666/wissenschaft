#!/usr/bin/env bash
# /wissenschaft — Einrichtung in einem Schritt.
#
# Für Dritte: klont das Repo (oder entpackt es), dann dieses Skript aufrufen.
#
#   git clone <repo-url> wissenschaft-tool
#   cd wissenschaft-tool
#   ./setup.sh
#
# Das Skript ist idempotent — mehrfaches Ausführen ist gefahrlos.
set -uo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

echo "════════════════════════════════════════════════"
echo " /wissenschaft — Einrichtung"
echo "════════════════════════════════════════════════"
echo

FEHLER=0

# ── 1. Python pruefen ──────────────────────────────────────────
echo "1) Python"
if command -v python3 >/dev/null 2>&1; then
    PYV="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null)"
    echo "   ✓ python3 $PYV"
    case "$PYV" in
        3.1[0-9]|3.[2-9][0-9]) : ;;
        *) echo "   !  Empfohlen: Python 3.10+ (gefunden: $PYV)";;
    esac
else
    echo "   ✗ python3 fehlt — bitte installieren"; FEHLER=1
fi

# ── 2. venv anlegen ────────────────────────────────────────────
echo
echo "2) Virtuelle Umgebung"
if [ -x .venv/bin/python ]; then
    echo "   ✓ .venv vorhanden"
else
    echo "   → lege .venv an …"
    python3 -m venv .venv || { echo "   ✗ venv-Anlage fehlgeschlagen"; FEHLER=1; }
fi

# ── 3. Abhaengigkeiten ─────────────────────────────────────────
echo
echo "3) Abhängigkeiten"
if [ -x .venv/bin/pip ] && [ -f requirements.txt ]; then
    echo "   → installiere (kann 1-2 Minuten dauern) …"
    .venv/bin/pip install -q --upgrade pip >/dev/null 2>&1
    if .venv/bin/pip install -q -r requirements.txt; then
        echo "   ✓ installiert"
    else
        echo "   ✗ Installation fehlgeschlagen"; FEHLER=1
    fi
else
    echo "   ✗ .venv/bin/pip oder requirements.txt fehlt"; FEHLER=1
fi

# ── 4. Funktionstest ───────────────────────────────────────────
echo
echo "4) Funktionstest"
if [ -x .venv/bin/python ]; then
    N=$(.venv/bin/python -c "import sys;sys.path.insert(0,'.');from sources.papersearch import ALL_SOURCES as A;print(len(A))" 2>/dev/null || echo 0)
    if [ "${N:-0}" -ge 100 ] 2>/dev/null; then
        echo "   ✓ $N Quellen geladen"
    else
        echo "   ✗ nur ${N:-0} Quellen — Installation prüfen"; FEHLER=1
    fi
fi

# ── 5. Hermes-Skill (Slash-Befehl /wissenschaft) ───────────────
echo
echo "5) Slash-Befehl /wissenschaft"
if [ -d "$HOME/.hermes" ]; then
    if [ -x ./install.sh ]; then
        ./install.sh >/dev/null 2>&1 && echo "   ✓ Skill installiert (Symlink ins Repo, update-fest)" \
            || { echo "   !  install.sh fehlgeschlagen — './install.sh' manuell ausführen"; }
        echo "     Hermes-Session neu starten, dann ist /wissenschaft verfügbar."
    else
        echo "   !  install.sh fehlt — Skill manuell kopieren (siehe SICHERUNG.md)"
    fi
else
    echo "   – kein ~/.hermes gefunden (Hermes nicht installiert?) — übersprungen"
    echo "     Das Tool läuft trotzdem direkt über die Kommandozeile."
fi

# ── Ergebnis ───────────────────────────────────────────────────
echo
echo "════════════════════════════════════════════════"
if [ "$FEHLER" -eq 0 ]; then
    echo " FERTIG — so startest du eine Recherche:"
    echo
    echo "   cd $REPO"
    echo "   .venv/bin/python wissenschaft_cli.py \"DEIN THEMA\" --dossier --tiefe standard"
    echo
    echo " Oder in Hermes:   /wissenschaft DEIN THEMA"
    echo
    echo " Health-Check jederzeit:  ./check.sh"
else
    echo " ACHTUNG — $FEHLER Schritt(e) fehlgeschlagen (siehe oben)"
fi
echo "════════════════════════════════════════════════"
exit "$FEHLER"
