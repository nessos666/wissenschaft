# Neue Quellen hinzufügen — Schritt für Schritt

Ziel: Das Tool bleibt **offen für Neues**. Eine neue Quelle ist in ~15 Minuten
drin — immer nach demselben Muster (nie abkürzen, sonst kommt Schrott rein).

## Die 6 Schritte

### 1. Kandidat LIVE testen (nicht raten!)
Erst prüfen, ob die Quelle überhaupt key-frei liefert:

```bash
cd ~/HAUPTLAGER/03_PROJEKTE/12_Wissenschaft_Tool
.venv/bin/python -c "
import requests
r = requests.get('https://api.beispiel.org/search', params={'q':'test'}, timeout=10)
print(r.status_code, r.text[:200])
"
```

**Harte Kriterien:** HTTP 200 · echte Daten · kein API-Key · kein Bot-Block.

### 2. Connector schreiben
In `sources/quellen_extraN.py` (neue Runde = neue Datei).

**Jede `quellen_extraN.py` bringt diesen Header selbst mit** (kopieren!):

```python
import re
from urllib.parse import quote

import requests

TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) WissenschaftTool/4.0 "
                         "(mailto:kontakt@wissenshaft.tool)"}


def _jahr(t):
    m = re.search(r"(19|20)\d{2}", str(t or ""))
    return m.group(0) if m else ""


def _safe(fn):
    def wrapper(query, max_results=5):
        try:
            return fn(query, max_results)
        except Exception:
            return []
    wrapper.__name__ = fn.__name__
    return wrapper


def _e(titel, url, source, jahr="", abstract="", authors="", zitate=0, doi=""):
    return {"title": (titel or "")[:500], "year": jahr, "doi": doi, "url": url or "",
            "pdf_url": "", "source": source, "citations": zitate,
            "abstract": (abstract or "")[:800], "authors": (authors or "")[:300]}
```

Dann die Suchfunktion:

```python
@_safe
def suche_beispiel(query, max_results=5):
    """Beispiel-Quelle — was sie liefert."""
    r = requests.get("https://api.beispiel.org/search",
                     params={"q": query, "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for x in (r.json().get("results") or []):
        titel = x.get("title") or ""
        if not titel:
            continue
        aus.append(_e(titel, x.get("url", ""), "Beispiel",
                      _jahr(x.get("year")), abstract=x.get("abstract", "")))
    return aus[:max_results]
```

**Pflicht:** `_safe`-Decorator (nie crashen) · `_e()` für das Schema ·
leere Liste bei Fehler · `max_results` respektieren.

### 3. Registrieren
Unten in der Datei eintragen:

```python
EXTRA_QUELLEN_N = {"beispiel": suche_beispiel}
```

Dann in `sources/papersearch.py` **beides** ergänzen:
1. den Import:  `from sources.quellen_extraN import EXTRA_QUELLEN_N`
2. den Eintrag in der Schleife:
   ```python
   for _extra in (EXTRA_QUELLEN_2, …, EXTRA_QUELLEN_N):
       EXTRA_QUELLEN.update(_extra)
   ```
   Die Zeile `EXTRA_QUELLEN.update(...)` weiter unten baut daraus `SEARCHER_MAP`.

### 4. Tests
In `tests/test_papersearch.py` ergänzen:

```python
def test_rundeN_quellen():
    assert {"beispiel"}.issubset(set(papersearch.SEARCHER_MAP))
```

`pytest tests/ -q` → grün.

### 5. Validieren
```bash
./check.sh                                    # Health-Check
.venv/bin/python wissenschaft_cli.py "test" --dossier --tiefe schnell
```
Erwartung: Quellen-Zahl steigt, Pipeline läuft, Dossier wird erstellt.

### 6. Doku + Zahlen angleichen
```bash
.venv/bin/python tools/quellen_md_generieren.py     # QUELLEN.md neu erzeugen
# Danach die Quellen-Zahl in README.md, SICHERUNG.md und skills/wissenschaft/SKILL.md
# auf den neuen Stand setzen (die Zahl steht dort im Text).
```

### 7. Committen + sichern
```bash
./check.sh                                          # Health-Check
git add -A && git commit -m "Quelle X hinzugefügt (live verifiziert)"
./backup.sh
```

## Wenn eine Quelle NICHT liefert

Nicht mitzählen! Stattdessen ehrlich parken (wie `EXTRA_QUELLEN_8_OFFEN`):

```python
EXTRA_QUELLEN_8_OFFEN = {
    "quelle_x": suche_quelle_x,   # Grund: JS-SPA / toter Endpoint
}
```

Parken heißt: Code bleibt dokumentiert, zählt aber **nicht** als aktive Quelle.
Grund immer als Kommentar dazuschreiben.

## Geparkte Quellen reaktivieren

1. Prüfen ob der Endpoint inzwischen wieder liefert (Schritt 1)
2. Aus `*_OFFEN` nach `EXTRA_QUELLEN_N` verschieben
3. Test anpassen (`test_rundeN_geparkte_quellen_nicht_aktiv`)
4. `./check.sh` → commit

## Qualitäts-Regeln (nicht verhandelbar)

| Regel | Warum |
|---|---|
| Nur live verifizierte Quellen zählen | erfundene Zahlen vermeiden |
| `_safe` um jede Suchfunktion | Pipeline darf nie still crashen |
| Fehlerhafte Quellen parken, nicht löschen | Wiederaktivierung möglich |
| Doppelte Namen vermeiden | `SEARCHER_MAP`-Kollision |
| Nach jedem Block: `./check.sh` + `./backup.sh` | nichts geht verloren |
