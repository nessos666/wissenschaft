---
name: wissenschaft
description: "Akademische Recherche: 148 Quellen, PRISMA-Dossier, PDFs, Snowballing."
version: 4.1.0
author: David Miko, Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [wissenschaft, recherche, papers, prisma, dossier, multi-source]
    related_skills: [sucher-1000, forschungs-dossier, grounded-citations]
---

# /wissenschaft — Multi-Quellen-Recherche mit PRISMA-Dossier

Durchsucht bei EINEM Aufruf **148 key-freie Quellen** (CrossRef, PubMed, Europe
PMC, Semantic Scholar, OpenAlex, arXiv, bioRxiv, medRxiv, ChemRxiv, Zenodo,
OpenAIRE, CORE, DOAJ, PDB, UniProt, ChEMBL, GBIF, NCBI- und EBI-Suite,
MathOverflow, SIMBAD, USGS, KEGG, PRIDE …), dedupliziert, rankt nach Relevanz
und erzeugt ein **fertiges Dossier** (README + BibTeX + optional PDFs).

Pipeline: Researcher → Verifier → Evidence → Synthesis → Cluster → Reviewer →
PRISMA. Läuft komplett lokal, **ohne API-Keys**.

Dieser Skill beschreibt BEDIENUNG + Installation, nicht den Bau.

## When to Use

- Nutzer sagt `/wissenschaft <Thema>` oder „recherchier / such Papers / Studien / Literatur zu …"
- Es wird ein **Dossier** mit Quellen, DOI-Check und PRISMA-Statistik gebraucht
- Systematische Übersicht statt einzelner Treffer

Don't use for: breite Web-Suche ohne Papers (→ `sucher-1000`) · Bau oder
Erweiterung des Tools (→ `ERWEITERN.md` im Repo).

## Prerequisites

- **Repo-Pfad ermitteln** (kann umgezogen sein — nie hartkodiert annehmen):
  `search_files(target='files', pattern='wissenschaft_cli.py')`
  Übliche Stelle: `~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool`
- **Einmalig einrichten** (legt venv an und installiert den Slash-Befehl):
  ```bash
  cd <repo> && ./setup.sh
  ```
- **Immer `.venv/bin/python`** verwenden — mit `python3` läuft nur der
  2-Quellen-Fallback (CrossRef+arXiv) statt 148.
- Kein API-Key nötig.

## How to Run

```bash
cd <repo>
.venv/bin/python wissenschaft_cli.py "THEMA" --dossier --tiefe standard
```

Ergebnis: Dossier-Ordner mit `README.md` (PRISMA, Qualitätstabelle,
Quellen-Status) und `*_Evidenz.bib`.

**Nicht durch `| head` pipen**, wenn der volle Lauf durchlaufen soll —
besser in eine Datei umleiten und danach lesen.

### Tiefe

| Flag | Treffer |
|---|---|
| `--tiefe schnell` | 5 |
| `--tiefe standard` | 15 |
| `--tiefe tief` | 25 + **Zitations-Snowballing** |

Bei `tief` holt das Tool zusätzlich die Zitationsnachbarschaft der drei besten
Treffer: rückwärts die Referenzen (CrossRef), vorwärts die zitierenden Arbeiten
(Semantic Scholar). Das findet Grundlagenwerke und neuere Folgearbeiten, die
über Stichworte nicht auftauchen. Im Dossier stehen sie als Quelle
`CrossRef-Snowball` bzw. `S2-Snowball`. Scheitert der Schritt (kein DOI,
API-Drosselung), bleibt das Ergebnis vollständig — es ist ein Bonus, kein
Pflichtteil.

## Quick Reference

```bash
.venv/bin/python wissenschaft_cli.py "Thema" --dossier             # Standard
.venv/bin/python wissenschaft_cli.py "Thema" --dossier --download  # + OA-PDFs
.venv/bin/python wissenschaft_cli.py "Thema" --dossier --tiefe tief
.venv/bin/python wissenschaft_cli.py "Thema" --jahr-von 2020 --jahr-bis 2025
.venv/bin/python wissenschaft_cli.py "Thema" --quellen "openalex,semantic"  # Delta
./check.sh          # Health-Check (venv, Quellen, Tests, Skill-Kette, Backup)
./nach-update.sh    # nach 'hermes update': reparieren + prüfen
```

## Procedure

1. **Repo-Pfad finden** (`search_files pattern='wissenschaft_cli.py'`), dann `cd` dorthin.
2. **Bei Erstnutzung**: `./setup.sh` (venv + Slash-Befehl einrichten).
3. **Thema präzise formulieren** — Fachbegriffe plus englische Begriffe liefern
   deutlich bessere Treffer in den internationalen Quellen.
4. **Tiefe wählen**: `standard` für den Überblick, `tief` mit Snowballing.
5. **Laufen lassen** — langsame Quellen dürfen arbeiten. Live-Meldungen zeigen,
   welche Quelle gerade geliefert hat.
6. **Dossier lesen**: `README.md` (Treffer, Qualität, Quellen-Status) und die
   `.bib` für die Literaturverwaltung.

## Ergebnis verstehen

Das Dossier enthält neben den Treffern einen **Quellen-Status**:

| Status | Bedeutung |
|---|---|
| Treffer | Quelle hat geliefert |
| ohne Treffer | hat geantwortet, aber nichts zum Thema — **kein Fehler** |
| offen | rechnete noch (langsamer) — **kein Fehler**, kommt beim nächsten Lauf |
| Fehler | echte Ausnahme bei der Abfrage |

Bei 148 Spezialquellen ist es **normal**, dass nur ein Teil zum konkreten
Thema etwas beiträgt.

## Pitfalls

- **Kein venv → nur 2 Quellen** (Fallback). Immer `.venv/bin/python`.
- **Rate-Limits sind normal** (Semantic Scholar 429, OpenAlex-Budget): der
  Searcher überspringt tote Quellen automatisch, Transparenz steht im Dossier.
- **Lange Läufe sind gewollt**: lieber vollständig als abgebrochen.
- **Hardware-/Produktthemen** liefern aus akademischen Quellen wenig —
  dafür ist `sucher-1000` (Web) das passendere Werkzeug.
- **google_scholar/BASE/acm/ieee** sind absichtlich NICHT aktiv
  (Bot-Block bzw. Key-Pflicht).

## Verification

- Ausgabe enthält `✅ Pipeline: success | N Treffer aus N von 148 Quellen`
- Dossier-Ordner existiert mit `README.md` + `*_Evidenz.bib`
- Kein `Traceback` in der Ausgabe
- `./check.sh` meldet `ERGEBNIS: ✓ alles in Ordnung`

## Update-Schutz

Der Skill liegt als **Symlink** auf dieses Repo — `hermes update` kann ihn
nicht ersetzen. Nach einem Update: `./nach-update.sh`.
Details in `SICHERUNG.md`.
