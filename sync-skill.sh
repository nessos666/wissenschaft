#!/usr/bin/env bash
# /wissenschaft-Hermes-Skill wiederherstellen — nach 'hermes update'.
#
# Windows-Regel: Erst SYMLINK versuchen (update-fest), sonst Kopie.
# Der Symlink zeigt direkt ins Repo — ein Update kann den Inhalt dann nicht
# ersetzen. Nur wenn kein Symlink moeglich ist, wird kopiert.
#
# Nutzung:  ./sync-skill.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
QUELLE="$REPO/skills/wissenschaft/SKILL.md"
ZIEL_DIR="$HOME/.hermes/skills/research/wissenschaft"

if [ ! -f "$QUELLE" ]; then
    echo "FEHLER: $QUELLE nicht gefunden" >&2
    exit 1
fi

mkdir -p "$(dirname "$ZIEL_DIR")"

# Fall 1: Symlink fehlt/zeigt woandershin -> neu setzen (= update-fest)
if [ ! -L "$ZIEL_DIR" ]; then
    echo "→ Symlink fehlt — setze update-feste Verknuepfung …"
    "$REPO/install.sh"
    exit 0
fi

# Fall 2: Symlink vorhanden -> pruefen ob er noch auf dieses Repo zeigt
AKTUELL="$(readlink "$ZIEL_DIR")"
if [ "$AKTUELL" != "$REPO/skills/wissenschaft" ]; then
    echo "→ Symlink zeigt auf '$AKTUELL' — korrigiere …"
    "$REPO/install.sh"
    exit 0
fi

echo "✓ Skill-Kette in Ordnung (Symlink, update-fest)"
echo "    $ZIEL_DIR -> $AKTUELL"
