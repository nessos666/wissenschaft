# Plan: Quellen auf 130+ ausbauen (Stück für Stück, mit Checkpoints)

Stand: 2026-09-08 · **Aktuell: 45 Quellen** · Ziel: **≥ 130**

## Ausgangslage

- Davids Registry: **105 dokumentierte Quellen** (21 Kategorien)
- Davon angebunden: **45**
- Lücke: 60 aus der Registry + weitere neue Quellen, um 130+ zu erreichen

## Methode (jeder Block = 1 Checkpoint)

1. **Testen** — Kandidaten live gegen die API prüfen (key-frei? liefert es?)
2. **Bauen** — Connector in `sources/quellen_extraN.py` (nie crashen, _norm-Format)
3. **Testen (Suite)** — Unit-Tests für die neue Gruppe, `pytest` grün
4. **Validieren** — `/wissenschaft`-CLI-Lauf mit echtem Thema, Quellen-Zahl prüfen
5. **Committen + Backup** — eigener Commit + `./backup.sh`
6. **Melden** — Quellen-Stand + was der Block gebracht hat

## Blöcke

### ✅ Block 0 (fertig): 45 Quellen
Kern (CrossRef, PubMed, arXiv …) + Extra 1 (Chemie/Physik/OSF) + Extra 2
(Medizin/Bio/Labor, CS/Software, Mathe, Bücher).

### Block 1 — Patente + Standards (teilweise)
- ERGEBNIS: Patente brauchen ALLE Keys/Accounts (PatentsView tot, EPO 403,
  Lens 401, Google Patents 503, WIPO kein API) → NICHT key-frei machbar
- ✅ NIST + RFC Editor machbar (Block 5)

### Block 1b — Finance/Regional/Bio/Archive ✅ ERLEDIGT (+16 = 61 Quellen)
World Bank, NBER, RePEc, CFTC, Redalyc, J-STAGE, CiNii, AJOL, PDB, Reactome,
Gene Ontology, GBIF, Protein Atlas, DOAB, ORCID, ROR

### Block 1-alt — Patente + Standards + Technik (Ziel: ~55)
- [ ] Google Patents (via SerpAPI? sonst PatentsView)
- [ ] USPTO PatentsView (key-frei API!)
- [ ] EPO OPS (Key nötig — dokumentieren)
- [ ] WIPO Patentscope (HTML/kein API)
- [ ] NIST (key-frei)
- [ ] RFC Editor (key-frei, statisch)
- [ ] ISO / DIN (paid — dokumentieren)
- [ ] NASA ADS (Key nötig)
- [ ] IOPscience (prüfen)

### Block 2 — Finance/Ökonomie + Regional (Ziel: ~70)
- [ ] World Bank Open Knowledge (key-frei API)
- [ ] IMF eLibrary (key-frei API)
- [ ] OECD iLibrary (key-frei API)
- [ ] NBER (key-frei)
- [ ] RePEc/IDEAS (HTML)
- [ ] BIS, ECB, Federal Reserve (key-frei)
- [ ] CFTC COT (Trading-Daten — David!)
- [ ] SciELO, Redalyc, Dialnet (Lateinamerika)
- [ ] J-STAGE, CiNii, KCI, AJOL (Asien/Afrika)
- [ ] CyberLeninka, Shodhganga (RU/IN)

### Block 3 — Bio/Labor vertiefen + Daten (Ziel: ~85)
- [ ] PDB (Protein Data Bank — erneut)
- [ ] KEGG, Reactome (Pathways)
- [ ] Gene Ontology, BioModels
- [ ] GBIF (Biodiversität — key-frei!)
- [ ] Dataverse, Kaggle
- [ ] Protein Atlas, ArrayExpress/ENA
- [ ] NIST Chemistry WebBook (Labor)

### Block 4 — Uni-Archive + Bücher + Repositorien (Ziel: ~100)
- [ ] DOAB (Open Access Books — key-frei!)
- [ ] Gutenberg, HathiTrust, OpenEdition
- [ ] ROAR, OpenDOAR, DSpace-Beispiele, EPrints
- [ ] NDLTD (Dissertationen weltweit)
- [ ] ORCID, ROR (Forscher/Institutionen)

### Block 5 — Restliche Registry + Lücken (Ziel: ~115)
- [ ] ACL Anthology (key-frei, statisch)
- [ ] AlphaXiv, MathOverflow, EuDML
- [ ] WorldCat, Paper Ladder, DSpace
- [ ] Trove, DigitalNZ, Europeana, DPLA (Bibliotheken)
- [ ] GESIS, ICPSR (Sozialdaten)
- [ ] Scinapse, Lens.org (prüfen)

### Block 6 — Reserve auf 130+ (Ziel: ≥ 130)
- [ ] Weitere key-freie APIs nach Bedarf (OpenAIRE-Erweiterungen,
      NCBI-Suite, EBI-Suite, arXiv-Varianten)
- [ ] Bilanz + Aufräumen + Skill/README auf Endzahl

## Validierung des Slash-Befehls (PFLICHT, jeder Block)

```bash
hermes skills list | grep wissenschaft          # Skill enabled?
.venv/bin/python wissenschaft_cli.py "THEMA" --dossier --tiefe standard
# → prüfen: "X von N Quellen" (N = aktueller Stand)
```
Zusätzlich: `sync-skill.sh` (Skill-Kopie im Repo = Quelle der Wahrheit).

## Nicht machbar ohne Keys/Accounts (ehrlich dokumentieren)
Lens.org, Dimensions, JSTOR, IEEE, ACM, Embase, Cochrane, ResearchGate,
Google Scholar, BASE, WHO IRIS, Preprints.org, Scilit, Scopus, Web of Science.

## Sicherung
Nach jedem Block: `./backup.sh` (Git-Bundle) → `~/HAUPTLAGER/99_BACKUPS/`
