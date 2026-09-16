#!/usr/bin/env bash
# /wissenschaft HEALTH-CHECK — ein Befehl, der alles prueft.
# Nutzung:  ./check.sh
REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"
FEHLER=0

echo "══════════════════════════════════════════"
echo " /wissenschaft — HEALTH-CHECK"
echo "══════════════════════════════════════════"

# 1 — venv (ohne = nur 2 statt 149 Quellen)
echo
if [ -x .venv/bin/python ]; then
    echo "✓ venv .............. .venv/bin/python vorhanden"
else
    echo "✗ venv .............. FEHLT — 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'"
    FEHLER=1
fi

# 2 — Quellen
if [ -x .venv/bin/python ]; then
    N=$(cd . && .venv/bin/python -c "import sys;sys.path.insert(0,'.');from sources.papersearch import ALL_SOURCES as A;print(len(A))" 2>/dev/null || echo 0)
    if [ "$N" -ge 145 ] 2>/dev/null; then
        echo "✓ Quellen ........... $N aktiv (Sollwert 148)"
    else
        echo "✗ Quellen ........... nur $N aktiv (erwartet ≥145 / Soll 148)"
        FEHLER=1
    fi
fi

# 3 — Tests
if [ -x .venv/bin/python ]; then
    OUT=$(timeout 300 .venv/bin/python -m pytest tests/ -q 2>&1); RC=$?
    T=$(printf '%s\n' "$OUT" | tail -1)
    if [ "$RC" -ne 0 ]; then
        echo "✗ Tests ............. $T (rc=$RC — Timeout oder Fehler)"; FEHLER=1
    elif printf '%s' "$T" | grep -q "passed"; then
        echo "✓ Tests ............. $T"
    else
        echo "? Tests ............. unerwartete Ausgabe: $T"; FEHLER=1
    fi
fi

# 4 — Skill-Kette (Repo → Hermes)
ZIEL="$HOME/.hermes/skills/research/wissenschaft"
if [ -L "$ZIEL" ]; then
    ZIEL_REAL="$(readlink -f "$ZIEL" 2>/dev/null || echo "")"
    ERWARTET="$REPO/skills/wissenschaft"
    if [ -n "$ZIEL_REAL" ] && [ "$ZIEL_REAL" = "$ERWARTET" ] && [ -r "$ZIEL/SKILL.md" ]; then
        echo "✓ Skill-Kette ....... Symlink (update-fest) -> $ZIEL_REAL"
    else
        echo "✗ Skill-Kette ....... Symlink KAPUTT/FALSCH (zeigt auf: ${ZIEL_REAL:-nichts}) — './install.sh'"
        FEHLER=1
    fi
elif [ -f "$ZIEL/SKILL.md" ]; then
    if diff -q "$ZIEL/SKILL.md" skills/wissenschaft/SKILL.md >/dev/null 2>&1; then
        echo "✓ Skill-Kette ....... Hermes-Kopie identisch (Tipp: ./install.sh für Symlink)"
    else
        echo "✗ Skill-Kette ....... Hermes-Kopie WEICHT AB — './install.sh' oder './sync-skill.sh'"
        FEHLER=1
    fi
else
    echo "✗ Skill-Kette ....... Skill fehlt in ~/.hermes — './install.sh' ausführen"
    FEHLER=1
fi

# 5 — CLI startet
if [ -x .venv/bin/python ]; then
    if timeout 60 .venv/bin/python wissenschaft_cli.py --help >/dev/null 2>&1; then
        echo "✓ CLI ............... startet"
    else
        echo "✗ CLI ............... startet NICHT"; FEHLER=1
    fi
fi

# 6 — Backup
LETZTES=$(ls -t "$HOME/HAUPTLAGER/99_BACKUPS"/wissenschaft_*.bundle 2>/dev/null | head -1)
if [ -n "$LETZTES" ]; then
    echo "✓ Backup ............ $(basename "$LETZTES") ($(du -h "$LETZTES" | cut -f1))"
else
    echo "! Backup ............ keins gefunden — './backup.sh' ausführen"
fi

# 7 — Git
if [ ! -d .git ]; then
    echo "✗ Git ............... kein Git-Repo (hier erwartet)"; FEHLER=1
elif [ -z "$(git status --short 2>/dev/null)" ]; then
    echo "✓ Git ............... Arbeitsbaum sauber ($(git log --oneline 2>/dev/null | wc -l) Commits)"
else
    echo "! Git ............... $(git status --short | wc -l) uncommittete Änderungen"
fi

# timeout verfuegbar? (sonst laufen die Zeitbegrenzungen ins Leere)
if ! command -v timeout >/dev/null 2>&1; then
    echo "! timeout ........... nicht verfuegbar — Zeitbegrenzungen inaktiv"
fi

echo
if [ "$FEHLER" -eq 0 ]; then
    echo "ERGEBNIS: ✓ alles in Ordnung"
else
    echo "ERGEBNIS: ✗ $FEHLER Problem(e) — siehe oben"
fi
echo "══════════════════════════════════════════"
exit "$FEHLER"
