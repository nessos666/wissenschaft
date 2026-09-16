"""Extra-Quellen Runde 9 (Block 9: EBI-Vertiefung Bio/Chemie — F2-Fix).

Diese 5 Quellen wurden in Block 5 live verifiziert (PRIDE 3, InterPro 20,
Expression Atlas 4562, BioModels 10, KEGG 9960 Treffer), aber nie gebaut.
OpenCode-Review F2 hat die Lücke aufgedeckt.
"""
import re

import requests

TIMEOUT = 20
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) WissenschaftTool/4.0 (mailto:wissenschaft-tool@example.org)"}


def _safe(fn):
    def wrapper(query, max_results=5):
        try:
            return fn(query, max_results)
        except Exception:
            return []
    wrapper.__name__ = fn.__name__
    return wrapper


def _jahr(t):
    m = re.search(r"(19|20)\d{2}", str(t or ""))
    return m.group(0) if m else ""


def _e(titel, url, source, jahr="", abstract="", authors="", zitate=0, doi=""):
    return {"title": (titel or "")[:500], "year": jahr, "doi": doi, "url": url or "",
            "pdf_url": "", "source": source, "citations": zitate,
            "abstract": (abstract or "")[:800], "authors": (authors or "")[:300]}


@_safe
def suche_pride(query, max_results=5):
    """PRIDE (EBI) — Proteomik-Datensätze (Labor)."""
    r = requests.get("https://www.ebi.ac.uk/pride/ws/archive/v3/search/projects",
                     params={"keyword": query, "pageSize": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    d = r.json()
    if isinstance(d, dict):
        d = (d.get("_embedded", {}).get("compactprojects")
             or d.get("projects") or d.get("_embedded", {}).get("projects") or [])
    aus = []
    for x in (d if isinstance(d, list) else []):
        titel = x.get("title") or ""
        if not titel:
            continue
        acc = x.get("accession") or ""
        aus.append(_e(f"PRIDE {acc}: {titel}",
                      f"https://www.ebi.ac.uk/pride/archive/projects/{acc}",
                      "PRIDE", _jahr(x.get("publicationDate")),
                      abstract=(x.get("projectDescription") or "")[:500],
                      authors=x.get("submissionType") or ""))
    return aus[:max_results]


@_safe
def suche_interpro(query, max_results=5):
    """InterPro (EBI) — Protein-Familien und Domänen."""
    r = requests.get("https://www.ebi.ac.uk/interpro/api/entry/all/protein/",
                     params={"search": query, "page_size": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for x in (r.json().get("results") or []):
        md = x.get("metadata") or {}
        name = (md.get("name") or "").strip()
        acc = md.get("accession") or ""
        if not name and not acc:
            continue
        aus.append(_e(f"InterPro {acc}: {name}",
                      f"https://www.ebi.ac.uk/interpro/entry/InterPro/{acc}/",
                      "InterPro", abstract=f"Typ: {md.get('type', '')}, Quelle: {md.get('source_database', '')}"))
    return aus[:max_results]


@_safe
def suche_expression_atlas(query, max_results=5):
    """Expression Atlas (EBI) — Genexpressions-Experimente."""
    r = requests.get("https://www.ebi.ac.uk/gxa/json/experiments",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    q = query.lower()
    aus = []
    for x in (r.json().get("experiments") or []):
        titel = (x.get("experimentDescription") or x.get("experimentAccession") or "")
        if not titel:
            continue
        if q not in titel.lower() and q not in (x.get("experimentAccession") or "").lower():
            continue
        aus.append(_e(f"Expression Atlas {x.get('experimentAccession', '')}: {titel}",
                      f"https://www.ebi.ac.uk/gxa/experiments/{x.get('experimentAccession', '')}",
                      "Expression Atlas",
                      abstract=f"Spezies: {x.get('species', '')}, Typ: {x.get('experimentType', '')}"))
        if len(aus) >= max_results:
            break
    return aus


@_safe
def suche_biomodels(query, max_results=5):
    """BioModels (EBI) — computergestützte Modelle biologischer Systeme."""
    r = requests.get("https://www.ebi.ac.uk/biomodels/search",
                     params={"query": query, "format": "json", "numResults": max_results, "offset": 0},
                     headers={**HEADERS, "Accept": "application/json"}, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for x in (r.json().get("models") or []):
        name = x.get("name") or x.get("id") or ""
        if not name:
            continue
        aus.append(_e(f"BioModels {x.get('id', '')}: {name}",
                      f"https://www.ebi.ac.uk/biomodels/{x.get('id', '')}",
                      "BioModels", _jahr(x.get("submitDate")),
                      abstract=str(x.get("description") or "")[:500],
                      authors=str(x.get("submitter") or "")))
    return aus[:max_results]


@_safe
def suche_kegg(query, max_results=5):
    """KEGG — Gene, Pathways, Stoffwechsel (Bioinformatik)."""
    r = requests.get(f"https://rest.kegg.jp/find/genes/{requests.utils.quote(query.split()[0] if query.split() else query)}",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for zeile in r.text.splitlines()[:max_results]:
        if not zeile.strip():
            continue
        teile = zeile.split("\t")
        kid = teile[0] if teile else ""
        beschr = teile[1] if len(teile) > 1 else ""
        aus.append(_e(f"KEGG {kid}: {beschr[:150]}",
                      f"https://www.genome.jp/entry/{kid}", "KEGG",
                      abstract="KEGG-Gen/Pathway-Eintrag (Stoffwechsel, Bioinformatik)"))
    return aus


EXTRA_QUELLEN_9 = {
    "pride": suche_pride,
    "interpro": suche_interpro,
    "expression_atlas": suche_expression_atlas,
    "biomodels": suche_biomodels,
    "kegg": suche_kegg,
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "kinase"
    for name, fn in EXTRA_QUELLEN_9.items():
        print(f"[{name}] {len(fn(thema, 3))}")
