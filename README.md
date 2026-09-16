# /wissenschaft — Multi-Quellen-Recherche mit PRISMA-Dossier

> **Ein Slash-Command:** `/wissenschaft <Thema>` → durchsucht **148 key-freie
> Quellen**, erstellt ein fertiges Dossier (README + BibTeX + optional PDFs).
> Eigenständiges Tool mit eigenem Git — **überlebt jedes `hermes update`**.

## Schnellstart

```bash
cd ~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool
.venv/bin/python wissenschaft_cli.py "THEMA" --dossier --tiefe standard
```

⚠️ **Immer `.venv/bin/python`** — mit `python3` läuft nur der 2-Quellen-Fallback.

| Tiefe | Treffer |
|---|---|
| `--tiefe schnell` | 5 |
| `--tiefe standard` | 15 |
| `--tiefe tief` | 25 + **Zitations-Snowballing** |

Weitere Flags: `--download` (OA-PDFs) · `--jahr-von 2020 --jahr-bis 2025` ·
`--quellen "openalex,semantic"` (Delta-Folgelauf)

## Die wichtigsten Dateien

| Datei | Zweck |
|---|---|
| **`check.sh`** | **Health-Check — prüft alles mit einem Befehl** |
| `install.sh` | Skill update-fest machen (Symlink ins Repo) |
| `sync-skill.sh` | prüft/repariert die Skill-Kette (nach Updates) |
| `backup.sh` | Git-Bundle erzeugen (komplettes Repo in 1 Datei) |
| `QUELLEN.md` | alle 148 Quellen nach Kategorie |
| `ERWEITERN.md` | **neue Quellen hinzufügen (Schritt für Schritt)** |
| `SICHERUNG.md` | Update-/Backup-Konzept |
| `wissenschaft_cli.py` | Kommandozeile |
| `orchestrator.py` | die 4-Agenten-Pipeline |
| `sources/` | alle Quellen-Connectoren |
| `tests/` | 157 Tests |
| `legacy/` | alte Fassungen (nie gelöscht) |

## Pipeline

```
Researcher → Verifier → Evidence → Synthesis → Cluster → Reviewer → PRISMA → Dossier
   ↓            ↓                                          ↓
148 Quellen   DOI/URL                              Quellen-Status
(Dedup→Ranking) Trust-Score                    (offen / ohne Treffer / Fehler)
```

**Ehrliche Transparenz:** Das Tool zeigt live, welche Quellen liefern, welche
noch rechnen und welche zum Thema nichts hatten — alles kein Fehler.

## Update-Schutz (wichtig)

| Ebene | Schutz |
|---|---|
| **Skill** | **Symlink** ins Repo → `hermes update` kann ihn nicht ersetzen |
| **Code** | eigenes Git-Repo, `.venv` unabhängig von Hermes |
| **Backup** | Git-Bundle in `~/HAUPTLAGER/99_BACKUPS/` |
| **Wiederherstellen** | `./install.sh` (Skill) · `git clone <bundle>` (Repo) |

Nach `hermes update`: **`./check.sh`** laufen lassen — es sagt dir sofort,
ob alles noch sitzt.

## Daten bleiben lokal

Dossiers (`*_Dossier/`, `Dossiers/`) sind in `.gitignore` — sie enthalten
Recherche-Ergebnisse, keinen Code.
