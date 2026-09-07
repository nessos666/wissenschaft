# 10 Verbesserungsvorschläge — /wissenschaft (Stand 2026-09-08, 28 Quellen)

Priorisiert nach Impact/Aufwand. Jeder Vorschlag basiert auf einem konkreten
Befund beim Arbeiten (keine Theorie).

## 1. Relevanz-Ranking statt Quellen-Reihenfolge ⭐⭐⭐
**Befund:** Nach Dedup entscheidet die Quellen-Priorität (CrossRef zuerst),
nicht die Relevanz zur Query. `ranker.py` existiert seit Block 7 UNGENUTZT
(Relevanz/Jahr/Citations/OA-Metrik) — verdrahten: Pipeline sortiert nach
ranker-Score statt nach Ankunftsreihenfolge.
**Nutzen:** Die besten Paper einer Query stehen oben, unabhängig davon
welche Quelle sie lieferte.

## 2. Preprint→Published-Merging ⭐⭐⭐
**Befund:** arXiv/bioRxiv-Preprint und die spätere CrossRef-Published-Version
derselben Arbeit zählen als 2 Einträge (Preprint hat oft keinen DOI, der
Titel weicht leicht ab). deduplicator.py macht Fuzzy > 0.70 — Schwelle/Logik
für Preprint-Paare schärfen (z.B. 'arXiv'↔'CrossRef' bei Titel-Ähnlichkeit
+ Autoren-Übereinstimmung mergen, Published gewinnt).
**Nutzen:** Saubere Trefferliste ohne Doppel, korrekte PRISMA-Zahlen.

## 3. PDF-Download ins Dossier ⭐⭐⭐
**Befund:** paper-search-mcp (vendor) hat `download_with_fallback`
(OA-Links + Unpaywall-Fallback) — die Pipeline nutzt nur `pdf_url`-Feld,
lädt aber nie PDFs. Dossier-Writer erweitern: `--download` lädt OA-PDFs der
Top-Paper in `Dossiers/<Thema>/pdfs/`.
**Nutzen:** Dossier = sofort lesbare Volltexte, nicht nur Metadaten.

## 4. Abstract-Anreicherung ⭐⭐
**Befund:** OSF-Communities, DOAJ und teils Zenodo liefern KEINE Abstracts
(Feld leer) → Evidence-Klassifikation (abstract-basiert) und Dossier
verlieren Text. Nachschlag-Schicht: fehlende Abstracts via CrossRef/OpenAlex
(DOI vorhanden → Metadaten nachladen).
**Nutzen:** Vollständigere Dossiers + bessere Evidence-Level.

## 5. Zitations-Snowballing (vorwärts/rückwärts) ⭐⭐
**Befund:** Such-Treffer haben `citations`-Zahl, aber die Pipeline zeigt
keine cited-by/references. Bei `--tief`: für die Top-3-Paper die
Referenzen (rückwärts) + Citing-Works (vorwärts) über CrossRef/OpenAlex
nachladen und als 2. Runde in die Trefferliste mischen.
**Nutzen:** Echte Tiefen-Recherche findet klassische + neue Schlüsselwerke.

## 6. Query-Erweiterung (Synonyme/Abkürzungen) ⭐⭐
**Befund:** 'EMDR' findet in arXiv/bioRxiv wenig, weil die 'Eye Movement
Desensitization and Reprocessing' ausschreiben. query_analyzer erweitern:
Abkürzung↔Langform + Synonym-Erweiterung (je Query 1 Zusatz-Term,
OR-verknüpft an die Quellen).
**Nutzen:** Höhere Ausbeute pro Quelle, weniger Thema-Lücken.

## 7. Qualitäts-Sicht im Dossier ⭐⭐
**Befund:** Dossier listet Treffer, aber ohne Trust/Evidence/OA-Spalte.
Writer erweitern: Tabellen-Spalten 'DOI-verifiziert | OA | Citations |
Evidence-Level' + Quelle je Paper.
**Nutzen:** David sieht sofort, welchen Paper er trauen kann.

## 8. Zeitraum- und Sprach-Filter ⭐
**Befund:** Kein CLI-Flag für Jahr/Sprache. Quellen können das teils
(CrossRef from-pub-date, PubMed). `--jahr-von 2020 --jahr-bis 2024`
als Filter an die Quellen durchreichen + lokal nachfiltern.
**Nutzen:** Aktualitäts-Fokus (z.B. nur letzte 5 Jahre).

## 9. Fehler-Transparenz im Dossier-Footer ⭐
**Befund:** papersearch sammelt `errors` (welche Quellen down/429/Timeout),
aber das Dossier zeigt sie nicht. Writer-Footer: 'Quellen ohne Antwort
heute: OpenAlex (429 Budget), Semantic Scholar (Rate-Limit) …'.
**Nutzen:** Ehrlichkeit + Diagnose wenn eine Quelle dauerhaft fehlt.

## 10. Streaming/Teilwissen + Delta-Folgelauf ⭐
**Befund:** Lange Suche (30s+) liefert erst am Ende alles. Verbesserung:
(a) CLI zeigt Zwischenstand je gelieferter Quelle (live), (b) Cache wird
während des Laufs befüllt — Abbruch/Timeout verliert nichts, (c) Folgelauf
`--delta` sucht nur Quellen nach, die beim letzten Lauf fehlten.
**Nutzen:** 'Geschwindigkeit egal, Teilwissen ok' (Davids Vorgabe) wird
technisch sauber unterstützt.
