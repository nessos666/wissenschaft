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
./nach-update.sh
```

Das repariert automatisch, was ein Update kaputtmachen kann:
1. Skill-Symlink weg? → wiederherstellen (`install.sh`)
2. Skill ist eine Kopie statt Symlink? → update-fest machen
3. venv fehlt? → neu anlegen + Requirements installieren
4. Danach läuft der komplette Health-Check (`./check.sh`)

**Nur prüfen** (ohne Reparatur): `./check.sh`
Prüft: venv · 148 Quellen · Tests · Skill-Kette · CLI-Start · Backup · Git-Status.
Exit-Code 1 bei Problemen.

### Automatik (optional, nicht aktiv)

Ein Cronjob ist **bewusst nicht eingerichtet** (Davids Cron-System bleibt unangetastet).
Auf Wunsch aktivierbar mit:

```bash
hermes cron create "10 10 * * *" \
  --name "Wissenschaft-Check" \
  --script check.sh \
  --workdir "$HOME/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool" \
  --no-agent --deliver telegram
```

Meldet dann täglich um 10:10 nur, wenn etwas nicht stimmt. Entfernen mit
`hermes cron remove <id>` (ID aus `hermes cron list`).

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
Bundle kopieren (~330 KB) und wie Fall 2 vorgehen.

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
