"""Extra-Quellen für Chemie/Physik/Generisch (Quellen-Ausbau).

Neue Connectors NACH dem paper-search-Muster, aber schlank (nur requests,
kein Vendor-Patch). Liefern Dicts im _norm-Format von sources/papersearch:
title, year, doi, url, pdf_url, source, citations, abstract, authors.

Quellen (live verifiziert 2026-09-08):
- chemrxiv: Chemie-Preprints via CrossRef prefix:10.26434
- datacite:  Forschungsdaten + Publikationen (generisch, riesig)
- inspirehep: Hochenergie-Physik (CERN/INSPIRE)
"""
import re

import requests

TIMEOUT = 25
MAIL = "kontakt@wissenshaft.tool"
HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:kontakt@wissenshaft.tool)"}


def _clean_year(text) -> str:
    """Jahr aus beliebigem Datums/String extrahieren."""
    m = re.search(r"(19|20)\d{2}", str(text or ""))
    return m.group(0) if m else ""


def _kaputt_abfangen(fn):
    """Decorator: nie crashen, leere Liste bei Fehler."""
    def wrapper(query, max_results):
        try:
            return fn(query, max_results)
        except Exception:
            return []
    wrapper.__name__ = fn.__name__
    return wrapper


# ---------- chemrxiv (Chemie-Preprints, CrossRef prefix 10.26434) ----------

@_kaputt_abfangen
def suche_chemrxiv(query: str, max_results: int = 5) -> list:
    r = requests.get(
        "https://api.crossref.org/works",
        params={"query": query, "rows": max_results,
                "filter": "prefix:10.26434", "sort": "relevance",
                "order": "desc", "mailto": MAIL},
        headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in (r.json().get("message", {}).get("items") or []):
        title = ((it.get("title") or [""])[0] or "")[:500]
        if not title:
            continue
        autoren = ", ".join(
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in (it.get("author") or []) if isinstance(a, dict))[:300]
        jahr = ""
        for k in ("published-print", "published-online", "issued"):
            dp = (it.get(k) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                jahr = str(dp[0][0])
                break
        doi = (it.get("DOI") or "").replace("https://doi.org/", "")
        out.append({
            "title": title, "year": jahr, "doi": doi,
            "url": f"https://doi.org/{doi}" if doi else "",
            "pdf_url": "", "source": "ChemRxiv",
            "citations": int(it.get("is-referenced-by-count") or 0),
            "abstract": (it.get("abstract") or "")[:1000],
            "authors": autoren,
        })
    return out[:max_results]


# ---------- DataCite (generisch: Forschungsdaten + Paper) ----------

@_kaputt_abfangen
def suche_datacite(query: str, max_results: int = 5) -> list:
    r = requests.get(
        "https://api.datacite.org/dois",
        params={"query": query, "page[size]": max_results},
        headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("data") or []):
        att = d.get("attributes") or {}
        title = (((att.get("titles") or [{}])[0] or {}).get("title") or "")[:500]
        if not title:
            continue
        autoren = ", ".join(
            f"{a.get('givenName', '')} {a.get('familyName', '')}".strip()
            for a in (att.get("creators") or []) if isinstance(a, dict))[:300]
        out.append({
            "title": title,
            "year": _clean_year(att.get("publicationYear")),
            "doi": (att.get("doi") or "").replace("https://doi.org/", ""),
            "url": att.get("url") or f"https://doi.org/{att.get('doi', '')}",
            "pdf_url": "", "source": "DataCite",
            "citations": 0,
            "abstract": (att.get("descriptions") or [{}])[0].get(
                "description", "")[:1000] if att.get("descriptions") else "",
            "authors": autoren,
        })
    return out[:max_results]


# ---------- INSPIRE-HEP (Hochenergie-Physik, CERN) ----------

@_kaputt_abfangen
def suche_inspirehep(query: str, max_results: int = 5) -> list:
    r = requests.get(
        "https://inspirehep.net/api/literature",
        params={"q": query, "size": max_results},
        headers=HEADERS, timeout=TIMEOUT)
    out = []
    for h in (r.json().get("hits", {}).get("hits") or []):
        md = h.get("metadata") or {}
        title = (((md.get("titles") or [{}])[0] or {}).get("title") or "")[:500]
        if not title:
            continue
        autoren = ", ".join(
            f"{a.get('given_name', '')} {a.get('full_name', '')}".strip()
            for a in (md.get("authors") or []) if isinstance(a, dict))[:300]
        doi = (md.get("dois") or [""])[0] if md.get("dois") else ""
        arx = (md.get("arxiv_eprints") or [{}])[0].get("value", "") if md.get("arxiv_eprints") else ""
        out.append({
            "title": title,
            "year": _clean_year(md.get("earliest_date") or md.get("imprints")),
            "doi": (doi or "").replace("https://doi.org/", ""),
            "url": (f"https://doi.org/{doi}" if doi
                    else f"https://arxiv.org/abs/{arx}" if arx
                    else f"https://inspirehep.net/literature/{h.get('id', '')}"),
            "pdf_url": "", "source": "INSPIRE-HEP",
            "citations": int(md.get("citation_count") or 0),
            "abstract": (md.get("abstracts") or [{}])[0].get(
                "value", "")[:1000] if md.get("abstracts") else "",
            "authors": autoren,
        })
    return out[:max_results]


# ---------- Registry für die Brücke ----------

EXTRA_QUELLEN = {
    "chemrxiv": suche_chemrxiv,    # Chemie-Preprints
    "datacite": suche_datacite,    # generisch (Forschungsdaten + Paper)
    "inspirehep": suche_inspirehep,  # Hochenergie-Physik
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "bentonite clay"
    for name, fn in EXTRA_QUELLEN.items():
        treffer = fn(thema, 3)
        print(f"[{name}] {len(treffer)} Treffer")
        for t in treffer[:2]:
            print(f"   - {t['title'][:65]} ({t['year']})")
