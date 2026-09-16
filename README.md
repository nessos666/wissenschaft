# /wissenschaft — Multi-Quellen-Recherche mit PRISMA-Dossier

[![skills.sh](https://skills.sh/b/nessos666/wissenschaft)](https://skills.sh/nessos666/wissenschaft)

> **Ein Slash-Command:** `/wissenschaft <Thema>` → durchsucht **148 key-freie
> Quellen**, erstellt ein fertiges Dossier (README + BibTeX + optional PDFs).
> Eigenständiges Tool mit eigenem Git — **überlebt jedes `hermes update`**.
>
> Läuft komplett lokal, **ohne API-Keys**. Lizenz: MIT.

## Installation (3 Befehle)

```bash
git clone https://github.com/nessos666/wissenschaft.git wissenschaft-tool
cd wissenschaft-tool
./setup.sh
```

`setup.sh` ist idempotent und erledigt alles: Python prüfen, `.venv` anlegen,
Abhängigkeiten installieren, Funktionstest (148 Quellen) und — falls Hermes
installiert ist — den Slash-Befehl `/wissenschaft` einrichten.

Danach in Hermes: **`/wissenschaft dein thema`**
oder direkt auf der Kommandozeile (siehe Schnellstart).

**Voraussetzungen:** Python 3.10+ · Linux/macOS · optional Hermes Agent
(für den Slash-Befehl; das Tool selbst läuft auch ohne).

## Schnellstart

```bash
cd wissenschaft-tool
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

### Zitations-Snowballing (`--tiefe tief`)

Bei `standard` und `schnell` sucht das Tool nur nach Stichworten. Bei `tief`
kommt ein zweiter Schritt dazu: Es nimmt die drei besten Treffer und holt sich
deren Nachbarschaft im Zitationsnetz.

**Rückwärts (Referenzen).** Über CrossRef werden die Literaturverweise der
Top-Treffer geladen. So tauchen die Grundlagenarbeiten auf, die eine Suchmaschine
über Stichworte nicht findet, weil sie älter sind oder anders benannt wurden.

**Vorwärts (zitiert von).** Über Semantic Scholar wird geladen, wer diese Arbeit
zitiert hat. Das findet neuere Arbeiten, die auf dem Treffer aufbauen.

Umfang: drei Seeds, je sechs Referenzen und sechs Zitierende. Diese Zusatztreffer
laufen durch dieselbe Dedup- und Ranking-Stufe wie alles andere.

**Grenzen, ehrlich:**
- Der Rückwärts-Schritt braucht einen DOI. Treffer ohne DOI (manche Bücher,
  Konferenzbeiträge) werden übersprungen.
- Der Vorwärts-Schritt hängt an Semantic Scholar. Die API kennt nicht jedes
  Paper und drosselt gelegentlich (HTTP 429). Dann kommt für diesen Seed nichts
  zurück — der Rest des Laufs läuft normal weiter.
- Beides ist ein Bonus, kein Pflichtteil. Scheitert es, bleibt das Ergebnis
  vollständig, nur ohne die Zusatztreffer.

Im Dossier erkennt man Snowball-Treffer an der Quelle: `CrossRef-Snowball`
beziehungsweise `S2-Snowball`.

## Die wichtigsten Dateien

| Datei | Zweck |
|---|---|
| **`setup.sh`** | **Einrichtung in einem Schritt (für Dritte)** |
| **`check.sh`** | **Health-Check — prüft alles mit einem Befehl** |
| **`nach-update.sh`** | **nach `hermes update` ausführen — repariert + prüft** |
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

Nach `hermes update`: **`./check.sh`** laufen lassen — es sagt sofort,
ob alles noch sitzt.

## Herkunft / Danksagung

Die Such-Schicht bündelt Code aus
[paper-search-mcp](https://github.com/openags/paper-search-mcp) (MIT) —
siehe `vendor/paper_search_mcp/LICENSE` und `ATTRIBUTION.md`.
Die Verarbeitungs-Pipeline (Dedup, Ranking, Verifier, PRISMA, Dossier)
ist eigenständig.

## Daten bleiben lokal

Dossiers (`*_Dossier/`, `Dossiers/`) sind in `.gitignore` — sie enthalten
Recherche-Ergebnisse, keinen Code.

---

## Verwandte Tools

🔬 **Search the web too** → [SUCHER-1000](https://github.com/nessos666/sucher-1000) · 🧠 **Keep what you learn** → [Extraktor](https://github.com/nessos666/extraktor)

Alle drei sind key-frei und laufen lokal.
