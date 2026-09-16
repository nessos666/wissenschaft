#!/usr/bin/env bash
# Nach jedem 'hermes update' ausfuehren — repariert was verloren ging.
#
# Nutzung:  ./nach-update.sh
#
# Prueft die Skill-Kette, repariert sie bei Bedarf und laeuft den
# kompletten Health-Check.
set -uo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

echo "══════════════════════════════════════════"
echo " /wissenschaft — WIEDERHERSTELLUNG nach Update"
echo "══════════════════════════════════════════"
echo

# 1 — Skill-Kette pruefen und ggf. reparieren
ZIEL="$HOME/.hermes/skills/research/wissenschaft"
if [ ! -e "$ZIEL" ]; then
    echo "→ Skill fehlt (Update hat ihn entfernt) — stelle ihn wieder her …"
    ./install.sh
elif [ -L "$ZIEL" ]; then
    echo "✓ Skill-Symlink noch da"
else
    echo "→ Skill ist eine Kopie (kein Symlink) — mache ihn update-fest …"
    ./install.sh
fi

# 2 — venv pruefen
if [ ! -x .venv/bin/python ]; then
    echo "→ venv fehlt — lege es neu an …"
    python3 -m venv .venv
    .venv/bin/pip install -q -r requirements.txt
fi

echo
# 3 — vollstaendiger Health-Check
./check.sh
RC=$?

echo
if [ "$RC" -eq 0 ]; then
    echo "FERTIG: /wissenschaft laeuft wieder einwandfrei."
else
    echo "ACHTUNG: es gibt noch Probleme — siehe oben."
fi
exit "$RC"
