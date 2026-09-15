# Sicherung & Wiederherstellung — /wissenschaft

**Ziel (David):** Das Tool darf durch kein Hermes-Update und keinen Ausfall
verloren gehen.

## Wo alles liegt (3 Ebenen)

| Ebene | Ort | Inhalt |
|---|---|---|
| **Code (Quelle der Wahrheit)** | `~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool/` | Git-Repo, 35+ Commits |
| **Hermes-Skill (Slash-Befehl)** | `~/.hermes/skills/research/wissenschaft/SKILL.md` | dünne Anleitung → ruft den Code |
| **Skill-Kopie im Repo** | `12_Wissenschaft_Tool/skills/wissenschaft/SKILL.md` | versioniert, update-sicher |
| **Backup** | `~/HAUPTLAGER/99_BACKUPS/wissenschaft_<datum>.bundle` | KOMPLETTES Repo in 1 Datei |

## Wiederherstellen

**Fall 1 — Skill durch `hermes update` weg:**
```bash
~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool/sync-skill.sh
```

**Fall 2 — Repo kaputt/gelöscht:**
```bash
git clone ~/HAUPTLAGER/99_BACKUPS/wissenschaft_<datum>.bundle wissenschaft_tool
cd wissenschaft_tool
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**Fall 3 — Neue Maschine / externer Rechner:**
Bundle kopieren (260 KB) und wie Fall 2 vorgehen.

## Backup erneuern
```bash
~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool/backup.sh
```

## Was NICHT im Repo ist (bewusst)
- `.venv/` — per `requirements.txt` reproduzierbar
- Dossiers (`XX_WissenschaftSkill/`) — Ergebnisse, nicht Code
- Der Fremdprojekt-Testordner bleibt; MIT-Lizenz + ATTRIBUTION sind drin

## Offen (auf Davids Wunsch später)
- Externe Kopie weit weg von dieser Maschine (privates GitHub-Repo).
  Bis dahin: Bundle regelmäßig auf USB/zweite Platte kopieren.
