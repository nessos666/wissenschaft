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
MAIL = "wissenschaft-tool@example.org"
HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:wissenschaft-tool@example.org)"}


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


# ---------- COD (Crystallography Open Database — Material/Kristalle) ----------

@_kaputt_abfangen
def suche_cod(query: str, max_results: int = 5) -> list:
    """Kristallstrukturen (Materialwissenschaft). Nur sinnvoll bei
    Mineral-/Kristall-Themen (z.B. 'zeolite', 'quartz')."""
    r = requests.get(
        "https://www.crystallography.net/cod/result",
        params={"format": "json", "text": query}, headers=HEADERS,
        timeout=TIMEOUT)
    out = []
    for d in (r.json() if isinstance(r.json(), list) else []):
        if len(out) >= max_results:
            break
        name = d.get("chemname") or d.get("formula") or "Kristall"
        cod_id = str(d.get("file") or "")
        out.append({
            "title": f"{name} (COD {cod_id})",
            "year": "", "doi": "",
            "url": f"https://www.crystallography.net/cod/{cod_id}.html" if cod_id else "",
            "pdf_url": "", "source": "COD",
            "citations": 0,
            "abstract": (d.get("mineral") or d.get("formula") or "")[:200],
            "authors": "",
        })
    return out[:max_results]


# ---------- Figshare (Forschungsdaten/-artikel, generisch) ----------

@_kaputt_abfangen
def suche_figshare(query: str, max_results: int = 5) -> list:
    r = requests.get(
        "https://api.figshare.com/v2/articles",
        params={"search_for": query, "page_size": max_results},
        headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json() or []):
        if not isinstance(d, dict):
            continue
        title = (d.get("title") or "")[:500]
        if not title:
            continue
        autoren = ", ".join(
            f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()
            for a in (d.get("authors") or []) if isinstance(a, dict))[:300]
        out.append({
            "title": title,
            "year": str(d.get("published_date") or "")[:4],
            "doi": (d.get("doi") or "").replace("https://doi.org/", ""),
            "url": d.get("url_public_api") or d.get("url_public_html") or "",
            "pdf_url": "", "source": "Figshare",
            "citations": int(d.get("metrics", {}).get("total_views") or 0),
            "abstract": (d.get("description") or "")[:800],
            "authors": autoren,
        })
    return out[:max_results]


# ---------- OSF-Preprints (PsyArXiv, engrXiv, EarthArXiv, SocArXiv, AfricArXiv …) ----------

_OSF_NAMEN = {
    "psyarxiv": "PsyArXiv", "engrxiv": "engrXiv", "eartharxiv": "EarthArXiv",
    "socarxiv": "SocArXiv", "africarxiv": "AfricArXiv",
    # Weitere OSF-Communities (jede ist ein eigener Preprint-Server)
    "medarxiv": "medRxiv-OSF", "edarxiv": "EdArXiv",
    "nutrixiv": "NutriXiv", "sportrxiv": "SportRxiv",
    "lawarxiv": "LawArXiv", "paleorxiv": "PaleoArXiv",
    "arabixiv": "Arabixiv", "marxiv": "MarXiv", "inarxiv": "INA-Rxiv",
    "thesiscommons": "Thesis Commons", "ecsarxiv": "ECSarXiv",
}

# Registry: erst die direkt definierten Quellen, dann OSF-Communities
EXTRA_QUELLEN = {
    "chemrxiv": suche_chemrxiv,    # Chemie-Preprints
    "datacite": suche_datacite,    # generisch (Forschungsdaten + Paper)
    "inspirehep": suche_inspirehep,  # Hochenergie-Physik
    "cod": suche_cod,              # Kristalle/Material
    "figshare": suche_figshare,    # Forschungsdaten/-artikel
}


def _suche_osf_provider(provider: str, label: str):
    """Factory: Such-Funktion für EINE OSF-Preprint-Community."""
    @_kaputt_abfangen
    def suche(query: str, max_results: int = 5) -> list:
        r = requests.get(
            "https://api.osf.io/v2/preprints/",
            params={"filter[provider]": provider,
                    "filter[title]": query, "page[size]": max_results},
            headers=HEADERS, timeout=TIMEOUT)
        out = []
        for d in (r.json().get("data") or []):
            att = d.get("attributes") or {}
            title = (att.get("title") or "")[:500]
            if not title:
                continue
            doi = att.get("doi") or ""
            out.append({
                "title": title,
                "year": (att.get("date_published") or "")[:4],
                "doi": (doi or "").replace("https://doi.org/", ""),
                "url": att.get("absolute_url") or (f"https://doi.org/{doi}" if doi else ""),
                "pdf_url": "", "source": label,
                "citations": 0,
                "abstract": "",
                "authors": "",
            })
        return out[:max_results]
    return suche


for _p, _l in _OSF_NAMEN.items():
    EXTRA_QUELLEN[_p] = _suche_osf_provider(_p, _l)


@_kaputt_abfangen
def suche_osf_nodes(query: str, max_results: int = 5) -> list:
    """OSF-Projekte (Forschungsdaten/Projekte, nicht Preprints)."""
    r = requests.get("https://api.osf.io/v2/nodes/",
                     params={"filter[title]": query, "page[size]": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    aus = []
    for d in (r.json().get("data") or []):
        att = d.get("attributes") or {}
        titel = (att.get("title") or "").strip()
        if not titel:
            continue
        aus.append({
            "title": f"OSF-Projekt: {titel}"[:500],
            "year": (att.get("date_created") or "")[:4], "doi": "",
            "url": f"https://osf.io/{d.get('id', '')}/" if d.get("id") else "",
            "pdf_url": "", "source": "OSF Projekte", "citations": 0,
            "abstract": (att.get("description") or "")[:600], "authors": "",
        })
    return aus[:max_results]


EXTRA_QUELLEN["osf_nodes"] = suche_osf_nodes


# ---------- Registry für die Brücke ----------

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "bentonite clay"
    for name, fn in EXTRA_QUELLEN.items():
        treffer = fn(thema, 3)
        print(f"[{name}] {len(treffer)} Treffer")
        for t in treffer[:2]:
            print(f"   - {t['title'][:65]} ({t['year']})")
