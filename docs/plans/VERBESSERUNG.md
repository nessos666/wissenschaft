# /wissenschaft — Verbesserungs-Plan (V3 → V4)

**Datum:** 07.09.2026 · **Basis:** Eigene Code-Analyse + OpenCode-Review
**Methode:** Davids Build-Regeln — Checken → Forschen → Bauen, Block für Block,
RED-Test zuerst, 1 Block = 1 Commit.

---

## Befund (Ist-Zustand, gemessen)

- ✅ 30 Tests grün, Kernmodule laufen, Standardbibliothek-only (keine Pflicht-Deps)
- ✅ CLI + Routing + Dedup + Verifier-Heuristiken solide
- ❌ **KEIN Git** (jetzt behoben — Repo initialisiert)
- ⚠️ Researcher-Agent führt **KEINE echte Suche** aus — nur Source-Routing
- ⚠️ Orchestrator braucht externe `raw_results`-JSON (Suche passiert außerhalb)
- ⚠️ Export-/Trust-/PRISMA-Logik teils toter Code
- ⚠️ Kein einheitliches Datenmodell an Pipeline-Grenzen
- ⚠️ Tests decken nur 4 Module ab (dedup/formatter/query_analyzer/verifier)

---

## Blöcke (priorisiert nach Impact/Aufwand)

### Block 1 — Git-Hygiene + Struktur (⭐ Basis, gering) ✅ ERLEDIGT
- [x] Git-Repo initialisiert (main, .gitignore, requirements.txt, README)
- [x] `docs/`-Struktur angelegt (plans/)
- [x] Commit-Regel: jede Verbesserung = eigener Block-Commit
- **Ziel erreicht:** sauberer, nachvollziehbarer Ausgangspunkt

### Block 2 — Echter Such-Client (✅ ERLEDIGT — ⭐⭐⭐ Kernfunktion, mittel-hoch)
- **Problem:** Researcher führt keine Suche aus; Tool ist auf externe JSON angewiesen
- **Lösung:** Neues Modul `sources/searcher.py` — nutzt SUCHER-1000 (16 Studien-
  Quellen: OpenAlex/PubMed/arXiv/EuropePMC/…) als Subprozess ODER direkte
  HTTP-Adapter (arXiv-API, PubMed E-utilities, OpenAlex — alle key-frei)
- [ ] RED-Test: `searcher.search("query")` liefert echte Ergebnisse
- [ ] Researcher-Agent ruft Searcher statt nur Routing
- [ ] CLI: `--suche`-Flag = kompletter Durchlauf ohne externe JSON
- **Ziel:** `/wissenschaft <Thema>` liefert aus EINEM Befehl ein Dossier

### Block 3 — Robustheit (✅ ERLEDIGT — ⭐⭐⭐, mittel)
- **Problem:** Pipeline zerbricht an unsauberen Daten (leere/fehlende Felder)
- **Lösung:** Defensive Normalisierung an allen Pipeline-Grenzen (Muster aus
  SUCHER-OpenAIRE-Fix: `_norm_list`, Feld-Typ-Guards)
- [ ] RED-Tests: leere results, fehlende Keys, int statt str → kein Crash
- **Ziel:** Pipeline liefert immer etwas (Ergebnis-Garantie)

### Block 4 — Export reparieren + Dossier-Writer (✅ ERLEDIGT — ⭐⭐, mittel)
- **Problem:** `save_exports`-Pfad unsicher; kein Dossier-Writer-Modul
- **Lösung:** `writer.py` — Pipeline-JSON → `Dossiers/<Thema>/README.md` im
  Format der bestehenden Dossiers; Pfad-Override per Env/Argument
- [ ] RED-Tests: Dossier-Struktur korrekt, .bib valide
- **Ziel:** Phase 5 automatisiert (PDFs + README + .bib)

### Block 5 — Dedup + PRISMA echt verdrahten (✅ ERLEDIGT — ⭐⭐, mittel)
- **Problem:** `deduplicate()` wird nie vor Verifier aufgerufen; PRISMA-Zahlen
  nicht aus echten Stufen
- **Lösung:** Pipeline-Reihenfolge: Suche → Dedup → Verifier → Evidence →
  PRISMA (Zahlen aus tatsächlichen Stufen)
- [ ] RED-Test: PRISMA-Zahlen = echte Stufen-Zählungen
- **Ziel:** Wissenschaftliche Integrität (nachvollziehbare Zahlen)

### Block 6 — Einheitliches Datenmodell (✅ ERLEDIGT — ⭐, mittel)
- **Problem:** `verified_results` reicht nur title/doi/source/trust durch —
  year/authors/citations/abstract gehen verloren
- **Lösung:** `SearchResult` vollständig durch die Pipeline reichen
- [ ] RED-Test: Feld-Erhalt über alle Stufen
- **Ziel:** Evidence nutzt echte Trust-Werte + Metadaten

### Block 7 — Dead Code + Hygiene (✅ ERLEDIGT — ⭐, gering)
- **Problem:** ranker, async_dispatcher, direct_client, skills/engine teils
  ungenutzt; orchestrator.py:58-62 toter Code
- **Lösung:** entweder verdrahten oder ehrlich entfernen (SUCHER-Regel:
  Funktionen nie halb-kaputt behalten)
- **Ziel:** Code = was läuft

### Block 8 — Test-Abdeckung + Integrationstests (⭐⭐, mittel)
- **Problem:** nur 4 Module getestet; keine Pipeline-Integrationstests
- **Lösung:** Tests für prisma/evidence/clusterer/cache/source_router;
  Orchestrator+Agents mit Fixtures; Netz mocken
- [ ] Ziel: 60+ Tests, Pipeline-Integration grün
- **Ziel:** CI-fähig, Vertrauen für weitere Ausbauten

---

## Reihenfolge-Empfehlung

1. **Block 1** (Basis — teils erledigt)
2. **Block 3** (Robustheit — schnell, verhindert Frust)
3. **Block 2** (Such-Client — der Funktionssprung)
4. **Block 4+5** (Export + PRISMA — Dossier-Qualität)
5. **Block 6+7** (Datenmodell + Hygiene)
6. **Block 8** (Tests — laufend, nach jedem Block erweitern)

*Jeder Block: RED-Test → Implementierung → Gate (pytest) → Commit → STOP.*
*Nach Blöcken 2+3: OpenCode-Review (10-fach) als feste Praxis.*
