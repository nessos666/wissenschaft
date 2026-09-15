---
name: wissenschaft
description: "Akademische Recherche: 28 Quellen, PRISMA-Dossier, PDFs, Snowballing."
version: 4.0.0
trigger_keywords:
  - wissenschaft
  - recherchieren
  - Paper suchen
  - Research
  - Studie finden
  - akademisch
  - Literatur
  - Dossier
---

# /wissenschaft V4 — Multi-Quellen-Recherche mit PRISMA-Dossier

**61 key-freie Quellen** (CrossRef, PubMed, Europe PMC, Semantic Scholar,
OpenAlex, PMC, CORE, DOAJ, OpenAIRE, Zenodo, DBLP, HAL, SSRN, CiteSeerX,
arXiv, bioRxiv, medRxiv, IACR, ChemRxiv, DataCite, INSPIRE-HEP, COD,
Figshare, PsyArXiv, engrXiv, EarthArXiv, SocArXiv, AfricArXiv,
ClinicalTrials.gov, UniProt, ChEMBL, NCBI Gene, Ensembl, EBI BioStudies,
OpenReview, HuggingFace Papers, GitHub, GitLab, PyPI, zbMATH, OEIS,
Dryad, Wikidata, Open Library, Internet Archive,
World Bank, NBER, RePEc, CFTC, Redalyc, J-STAGE, CiNii, AJOL,
PDB, Reactome, Gene Ontology, GBIF, Protein Atlas, DOAB, ORCID, ROR)
+ 4-Agenten-Pipeline (Researcher → Verifier → Synthesis → Reviewer)
+ PRISMA-Statistik + Dossier (README + BibTeX + optional PDFs).
Läuft komplett lokal, ohne API-Keys. Code: `12_Wissenschaft_Tool/` (Git).

## Ablauf

### 1. Komplett-Recherche (Standard — das ist der Weg)
```bash
cd ~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool
.venv/bin/python wissenschaft_cli.py "THEMA" --dossier --tiefe standard
```
→ Echte Multi-Quellen-Suche → Dedup → Relevanz-Ranking → Verifier (DOI/URL)
→ Evidence → Synthesis → Reviewer → **fertiges Dossier**.

**Wichtig:** IMMER `.venv/bin/python` nutzen (dort liegen die 28 Quellen).
Mit `python3` läuft nur der 2-Quellen-Fallback (CrossRef+arXiv).

### Tiefe
- `--tiefe schnell` = 5 Treffer · `standard` = 15 · `tief` = 25 + **Zitations-Snowballing**

### Optionen (alle kombinierbar)
| Flag | Wirkung |
|---|---|
| `--download` | OA-PDFs der Treffer ins Dossier laden (pdf_url + Unpaywall) |
| `--jahr-von 2020 --jahr-bis 2025` | Zeitraum-Filter |
| `--quellen "openalex,semantic"` | Delta-Folgelauf: nur fehlende Quellen nachsuchen |

### 2. Ergebnis
Dossier unter `~/HAUPTLAGER/XX_WissenschaftSkill/<THEMA>_Dossier/`:
- `README.md` — PRISMA-Flowchart, Qualitäts-Tabelle (DOI ✓ / PDF / Zit. / Trust),
  Quellen-Transparenz („X von 61 aktiv"), Quellen ohne Antwort
- `*_Evidenz.bib` — BibTeX
- `pdfs/` — falls `--download`

### 3. Faktencheck
Bei „prüfe nochmal" → kritische Aussagen gegen die gelisteten Quellen prüfen
(Trust-Score + DOI-Verifikation stehen in der Dossier-Tabelle).

## PITFALLS
- **Kein venv → nur 2 Quellen** (Fallback). Immer `.venv/bin/python`.
- **Quellen-Rate-Limits** sind normal (OpenAlex-Budget, Semantic 429):
  der Searcher überspringt tote Quellen automatisch — Transparenz im Dossier.
- **Lange Läufe sind ok** (kein Timeout-Abschneiden): lieber vollständig
  als abgebrochen. Teilwissen steckt im Cache.
- **google_scholar/BASE/acm/ieee** sind absichtlich NICHT aktiv
  (Bot-Block bzw. Key-Pflicht).

## Update-Schutz (wichtig)
- Code + Doku liegen in **`12_Wissenschaft_Tool/`** (eigenes Git-Repo, 32+ Commits)
- Dieser Skill ist zusätzlich **im Repo kopiert**: `skills/wissenschaft/SKILL.md`
- Backup: `./backup.sh` erzeugt ein Git-Bundle (komplettes Repo in 1 Datei)
  → wiederherstellbar mit `git clone <bundle>`
- Bei `hermes update` verloren? → Skill aus dem Repo zurückkopieren:
  `cp ~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool/skills/wissenschaft/SKILL.md \
      ~/.hermes/skills/research/wissenschaft/SKILL.md`
