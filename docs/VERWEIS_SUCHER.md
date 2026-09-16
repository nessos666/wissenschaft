# Verweis: SUCHER-1000

Wenn für ein Thema auch Web-Quellen (nicht nur Papers) gebraucht werden,
ergänzt das Schwester-Tool **SUCHER-1000** die akademische Suche:

- Repo: https://github.com/nessos666/sucher-1000
- durchsucht 40+ Web- und Wissenschaftsquellen parallel, key-frei
- eigene lokale Archiv-Suche (SQLite/FTS5)

Im Repo des Sucher-Tools:

```bash
.venv/bin/python sucher.py "dein-begriff" 12 --modus alle --out ergebnisse/slug
```

Ergebnisse landen unter `ergebnisse/` (bzw. `sucher_results/`).

**Abgrenzung:** `wissenschaft` = akademische Papers + PRISMA-Dossier.
`sucher-1000` = breite Web- + Quellensuche mit lokalem Archiv.
