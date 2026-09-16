#!/usr/bin/env bash
# Backup des /wissenschaft-Tools (unabhängig von Hermes).
#
# Erzeugt ein Git-Bundle = KOMPLETTES Repo in EINER Datei (alle Commits).
# Wiederherstellen auf jeder Maschine:
#   git clone /pfad/zum/wissenschaft_<datum>.bundle wissenschaft_tool
#
# Nutzung:  ./backup.sh          (Bundle nach ~/HAUPTLAGER/99_BACKUPS/)
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
ZIEL="${1:-$HOME/HAUPTLAGER/99_BACKUPS}"
mkdir -p "$ZIEL"
DATEI="$ZIEL/wissenschaft_$(date +%Y%m%d_%H%M%S).bundle"
cd "$REPO"
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "!  WARNUNG: uncommittete Aenderungen — sie landen NICHT im Bundle!"
    echo "   Erst committen, dann sichern."
fi

git bundle create "$DATEI" --all
echo "✓ Backup: $DATEI ($(du -h "$DATEI" | cut -f1))"
echo "  Wiederherstellen: git clone $DATEI wissenschaft_tool"
