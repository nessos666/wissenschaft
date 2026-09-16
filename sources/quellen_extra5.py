"""Extra-Quellen Runde 5 (Block 3: Software-Pakete, Preprints, Register,
Datenarchive, Bibliotheken). Live verifiziert 2026-09.

  SOFTWARE   : npm, CRAN, Codeberg, Docker Hub, Maven Central, Packagist
  PREPRINTS  : SciPost (Physik)
  REGISTER   : WHO ICTRP (Studien weltweit)
  DATEN      : Dataverse (Harvard)
  BIBLIOTHEK : Gutendex (Gutenberg), Wikisource, Standard Ebooks, Europeana
"""
import re

import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) WissenschaftTool/4.0 (mailto:kontakt@wissenshaft.tool)"}


def _jahr(text) -> str:
    m = re.search(r"(19|20)\d{2}", str(text or ""))
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


# ══════════ SOFTWARE-PAKETE ══════════

@_safe
def suche_npm(query, max_results=5):
    """npm — JavaScript-Pakete."""
    r = requests.get("https://registry.npmjs.org/-/v1/search",
                     params={"text": query, "size": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for o in (r.json().get("objects") or []):
        p = o.get("package") or {}
        name = p.get("name") or ""
        if not name:
            continue
        out.append(_e("npm " + name + " — " + (p.get("description") or ""),
                      p.get("links", {}).get("npm") or f"https://www.npmjs.com/package/{name}",
                      "npm", _jahr(p.get("date")), authors=", ".join(p.get("author", {}).get("name", "").split()) if isinstance(p.get("author"), dict) else ""))
    return out[:max_results]


@_safe
def suche_cran(query, max_results=5):
    """CRAN — R-Pakete (Statistik/Wissenschaft)."""
    r = requests.get("https://crandb.r-pkg.org/-/search", params={"query": query},
                     headers=HEADERS, timeout=TIMEOUT)
    d = r.json()
    out = []
    if isinstance(d, dict):
        for name, info in list(d.items())[:max_results]:
            if not isinstance(info, dict):
                continue
            out.append(_e(f"CRAN {name} — {info.get('Title', '')}",
                          f"https://cran.r-project.org/package={name}", "CRAN",
                          _jahr(info.get("Date")), abstract=info.get("Description", "")))
    return out[:max_results]


@_safe
def suche_codeberg(query, max_results=5):
    """Codeberg — freie Git-Plattform (Forschungssoftware)."""
    r = requests.get("https://codeberg.org/api/v1/repos/search",
                     params={"q": query, "limit": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for p in (r.json().get("data") or []):
        name = p.get("full_name") or ""
        if not name:
            continue
        out.append(_e(f"{name} — {(p.get('description') or 'Projekt')}",
                      p.get("html_url") or "", "Codeberg", _jahr(p.get("created_at")),
                      zitate=int(p.get("stars_count") or 0)))
    return out[:max_results]


@_safe
def suche_dockerhub(query, max_results=5):
    """Docker Hub — Container-Images (reproduzierbare Forschung)."""
    r = requests.get("https://hub.docker.com/v2/search/repositories/",
                     params={"query": query, "page_size": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for p in (r.json().get("results") or []):
        name = p.get("repo_name") or ""
        if not name:
            continue
        out.append(_e(f"Docker {name} — {(p.get('short_description') or '')}",
                      f"https://hub.docker.com/r/{name}", "Docker Hub",
                      zitate=int(p.get("star_count") or 0)))
    return out[:max_results]


@_safe
def suche_maven(query, max_results=5):
    """Maven Central — Java-Bibliotheken."""
    r = requests.get("https://search.maven.org/solrsearch/select",
                     params={"q": query, "rows": max_results, "wt": "json"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("response", {}).get("docs") or []):
        gid = d.get("id") or ""
        if not gid:
            continue
        out.append(_e(f"Maven {gid}", f"https://search.maven.org/artifact/{gid}",
                      "Maven Central", _jahr(d.get("timestamp"))))
    return out[:max_results]


@_safe
def suche_packagist(query, max_results=5):
    """Packagist — PHP-Pakete."""
    r = requests.get("https://packagist.org/search.json", params={"q": query},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("results") or [])[:max_results]:
        name = d.get("name") or ""
        if not name:
            continue
        out.append(_e(f"Packagist {name} — {(d.get('description') or '')}",
                      d.get("url") or f"https://packagist.org/packages/{name}",
                      "Packagist", zitate=int(d.get("downloads") or 0)))
    return out[:max_results]


# ══════════ PREPRINTS / REGISTER ══════════

@_safe
def suche_scipost(query, max_results=5):
    """SciPost — offene Physik-Journale."""
    r = requests.get("https://scipost.org/search", params={"q": query},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<h[23][^>]*>\s*<a[^>]*>([^<]{15,250})</a>', r.text)
    return [_e(t, "https://scipost.org/", "SciPost") for t in titel[:max_results]]


@_safe
def suche_who_ictrp(query, max_results=5):
    """WHO ICTRP — internationale Studienregister-Suche."""
    r = requests.get("https://trialsearch.who.int/",
                     params={"SearchTerm": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    return [_e(f"WHO ICTRP: Studien zu '{query}' (Register weltweit)",
               f"https://trialsearch.who.int/?SearchTerm={requests.utils.quote(query)}",
               "WHO ICTRP",
               abstract="International Clinical Trials Registry Platform (WHO)")]
    return []


# ══════════ DATEN / BIBLIOTHEKEN ══════════

@_safe
def suche_dataverse(query, max_results=5):
    """Dataverse (Harvard) — Forschungsdaten."""
    r = requests.get("https://dataverse.harvard.edu/api/search",
                     params={"q": query, "per_page": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in (r.json().get("data", {}).get("items") or []):
        name = it.get("name") or ""
        if not name:
            continue
        doi = ""
        for f in (it.get("metadataBlocks", {}).get("citation", {}).get("fields") or []):
            if f.get("typeName") == "title":
                name = f.get("value") or name
        out.append(_e(name[:400], it.get("url") or "https://dataverse.harvard.edu/",
                      "Dataverse", _jahr(it.get("published_at")), doi=doi))
    return out[:max_results]


@_safe
def suche_gutendex(query, max_results=5):
    """Gutendex — Project Gutenberg (Bücher)."""
    r = requests.get("https://gutendex.com/books", params={"search": query},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for b in (r.json().get("results") or [])[:max_results]:
        titel = b.get("title") or ""
        if not titel:
            continue
        out.append(_e(f"{titel} — {', '.join(b.get('authors', [{}])[0].get('name', '').split(',')[:1])}",
                      f"https://www.gutenberg.org/ebooks/{b.get('id', '')}", "Gutenberg",
                      abstract=f"Sprachen: {', '.join(b.get('languages') or [])}"))
    return out[:max_results]


@_safe
def suche_wikisource(query, max_results=5):
    """Wikisource — Quellentexte (MediaWiki-API)."""
    r = requests.get("https://de.wikisource.org/w/api.php",
                     params={"action": "query", "list": "search", "srsearch": query,
                             "format": "json", "srlimit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("query", {}).get("search") or []):
        titel = d.get("title") or ""
        if not titel:
            continue
        out.append(_e(f"Wikisource: {titel}",
                      "https://de.wikisource.org/wiki/" + requests.utils.quote(titel),
                      "Wikisource", abstract=re.sub(r"<[^>]+>", "", d.get("snippet") or "")[:400]))
    return out[:max_results]


@_safe
def suche_standardebooks(query, max_results=5):
    """Standard Ebooks — gemeinfreie Klassiker."""
    r = requests.get("https://standardebooks.org/ebooks", params={"query": query},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<a href="(/ebooks/[^"]+)"[^>]*>([^<]{5,150})</a>', r.text)
    return [_e(t, f"https://standardebooks.org{h}", "Standard Ebooks")
            for h, t in titel[:max_results]]


@_safe
def suche_europeana(query, max_results=5):
    """Europeana — europäisches Kulturerbe."""
    r = requests.get("https://api.europeana.eu/record/v2/search.json",
                     params={"query": query, "wskey": "api2demo", "rows": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in (r.json().get("items") or []):
        titel = (it.get("title") or [""])
        titel = titel[0] if isinstance(titel, list) and titel else str(titel)
        if not titel:
            continue
        out.append(_e(titel[:400], it.get("guid") or "https://www.europeana.eu/",
                      "Europeana", _jahr(it.get("year"))))
    return out[:max_results]


# F3: who_ictrp geparkt — lieferte Immer-Treffer ohne echte Query-Filterung
# ("who_ictrp": suche_who_ictrp,)
EXTRA_QUELLEN_5 = {
    "npm": suche_npm, "cran": suche_cran, "codeberg": suche_codeberg,
    "dockerhub": suche_dockerhub, "maven": suche_maven, "packagist": suche_packagist,
    "scipost": suche_scipost,
    # F21: who_ictrp GEPARKT (Immer-Treffer ohne echte Query-Filterung)
    # "who_ictrp": suche_who_ictrp,
    "dataverse": suche_dataverse, "gutenberg": suche_gutendex,
    "wikisource": suche_wikisource, "standardebooks": suche_standardebooks,
    "europeana": suche_europeana,
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "clay"
    for name, fn in EXTRA_QUELLEN_5.items():
        print(f"[{name}] {len(fn(thema, 3))}")
