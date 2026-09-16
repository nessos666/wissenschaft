# Sicherung & Update-Schutz — /wissenschaft

**Ziel (David):** Das Tool darf durch kein Hermes-Update und keinen Ausfall
verloren gehen und muss jederzeit wiederherstellbar sein.

## Die 4 Schutz-Ebenen

| Ebene | Was | Prüfen mit |
|---|---|---|
| **1. Symlink-Skill** | `~/.hermes/skills/research/wissenschaft` zeigt auf **das Repo** | `./check.sh` |
| **2. Eigenes Git-Repo** | Code + Doku, 48+ Commits, eigenes `.venv` | `git log --oneline` |
| **3. Git-Bundle** | komplettes Repo in 1 Datei (`99_BACKUPS/`) | `./check.sh` |
| **4. Hermes-Backup vor Update** | `updates.pre_update_backup: true` | `hermes config get updates.pre_update_backup` |

### Warum der Symlink (Ebene 1) der Kern ist

Früher lag eine **Kopie** des Skills in `~/.hermes/` — ein `hermes update`
konnte sie überschreiben. Jetzt zeigt ein **Symlink direkt ins Repo**:
der Skill ist damit Teil des Git-Repos, versioniert und update-fest.

```bash
./install.sh     # setzt den Symlink (sichert die alte Kopie vorher)
./sync-skill.sh  # prüft/repariert ihn nach einem Update
```

## Nach jedem `hermes update`

```bash
cd ~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool
./check.sh
```

Prüft in einem Lauf: venv · 149 Quellen · Tests · Skill-Kette · CLI-Start ·
Backup · Git-Status. Exit-Code 1 bei Problemen.

## Wiederherstellen

**Fall 1 — Skill durch `hermes update` weg oder Symlink entfernt:**

```bash
./install.sh
```

**Fall 2 — Repo kaputt/gelöscht:**

```bash
git clone ~/HAUPTLAGER/99_BACKUPS/wissenschaft_<datum>.bundle wissenschaft_tool
cd wissenschaft_tool
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./install.sh
./check.sh
```

**Fall 3 — Neue Maschine / externer Rechner:**
Bundle kopieren (~320 KB) und wie Fall 2 vorgehen.

## Backup erneuern

```bash
./backup.sh
```

Erzeugt `~/HAUPTLAGER/99_BACKUPS/wissenschaft_<zeitstempel>.bundle`.

## Was NICHT im Repo ist (bewusst)

- `.venv/` — per `requirements.txt` reproduzierbar
- Dossiers (`XX_WissenschaftSkill/`) — Ergebnisse, nicht Code
- Der Fremdprojekt-Ordner `vendor/` bleibt; MIT-Lizenz + ATTRIBUTION sind drin

## Offen (auf Davids Wunsch später)

- Externe Kopie weit weg von dieser Maschine (privates GitHub-Repo).
  Bis dahin: Bundle regelmäßig auf USB/zweite Platte kopieren.
