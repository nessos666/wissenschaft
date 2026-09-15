#!/usr/bin/env bash
# Stellt den /wissenschaft-Hermes-Skill aus DIESEM Repo wieder her.
#
# Nötig falls `hermes update` den Skill in ~/.hermes überschreibt/entfernt.
# Nutzung:  ./sync-skill.sh
set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
ZIEL_DIR="$HOME/.hermes/skills/research/wissenschaft"
mkdir -p "$ZIEL_DIR"
cp "$REPO/skills/wissenschaft/SKILL.md" "$ZIEL_DIR/SKILL.md"
echo "✓ Skill wiederhergestellt: $ZIEL_DIR/SKILL.md"
echo "  (Hermes-Session neu starten, damit /wissenschaft die neue Fassung lädt)"
