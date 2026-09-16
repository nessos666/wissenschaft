#!/usr/bin/env bash
# /wissenschaft UPDATE-FEST installieren.
#
# Statt einer Kopie wird ein SYMLINK gesetzt: der Hermes-Skill zeigt dann
# immer direkt auf dieses Repo. Ein `hermes update` kann den Inhalt damit
# nicht mehr ersetzen — der Skill ist Teil des Git-Repos und versioniert.
#
# Nutzung:  ./install.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
QUELLE="$REPO/skills/wissenschaft"
ZIEL="$HOME/.hermes/skills/research/wissenschaft"

if [ ! -f "$QUELLE/SKILL.md" ]; then
    echo "FEHLER: $QUELLE/SKILL.md nicht gefunden — bist du im Repo?" >&2
    exit 1
fi

mkdir -p "$(dirname "$ZIEL")"

# Vorhandene Installation sichern (NIE einfach loeschen)
if [ -e "$ZIEL" ] && [ ! -L "$ZIEL" ]; then
    SICHER="$ZIEL.bak.$(date +%Y%m%d_%H%M%S)"
    mv "$ZIEL" "$SICHER"
    echo "  alte Kopie gesichert: $SICHER"
elif [ -L "$ZIEL" ]; then
    rm -f "$ZIEL"
fi

ln -s "$QUELLE" "$ZIEL"

# Verifizieren, dass der Link wirklich funktioniert (sonst bringt er nichts)
if [ ! -r "$ZIEL/SKILL.md" ]; then
    echo "FEHLER: Symlink gesetzt, aber $ZIEL/SKILL.md nicht lesbar" >&2
    exit 1
fi

echo "✓ Update-fest installiert:"
echo "    $ZIEL  ->  $QUELLE"
echo
echo "  Der Skill zeigt jetzt aufs Repo. Aenderungen im Repo sind sofort aktiv"
echo "  (Hermes-Session neu starten). 'hermes update' kann ihn nicht ersetzen."
echo "  Falls ein Update den Symlink entfernt:  ./install.sh  erneut ausfuehren."
