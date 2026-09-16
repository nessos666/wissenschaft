"""Extra-Quellen Runde 3 (Block 2: Finance, Regional, Bio-Vertiefung, Archive).

Alle live verifiziert (2026-09). Liefert Dicts im _norm-Format.
  FINANCE/ÖKONOMIE : World Bank, NBER, RePEc, CFTC COT
  REGIONAL         : Redalyc (LatAm), J-STAGE (JP), CiNii (JP), AJOL (Afrika)
  BIO/LABOR        : PDB, Reactome, Gene Ontology, GBIF, Protein Atlas
  BÜCHER/ARCHIVE   : DOAB, ORCID, ROR
"""
import re

import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:wissenschaft-tool@example.org)"}


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


def _eintrag(titel, url, source, jahr="", doi="", abstract="", authors="",
             zitate=0):
    return {"title": (titel or "")[:500], "year": jahr, "doi": doi,
            "url": url or "", "pdf_url": "", "source": source,
            "citations": zitate, "abstract": (abstract or "")[:800],
            "authors": (authors or "")[:300]}


# ══════════ FINANCE / ÖKONOMIE ══════════

@_safe
def suche_worldbank(query, max_results=5):
    """World Bank Open Knowledge Repository."""
    r = requests.get("https://search.worldbank.org/api/v2/wds",
                     params={"qterm": query, "format": "json", "rows": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    docs = (r.json().get("documents") or {})
    out = []
    for d in (docs.values() if isinstance(docs, dict) else []):
        if not isinstance(d, dict):
            continue
        titel = d.get("docna") or d.get("title") or ""
        if not titel:
            continue
        out.append(_eintrag(titel, d.get("url") or d.get("pdfurl") or "",
                            "World Bank", _jahr(d.get("docdt")),
                            abstract=d.get("abstracts", {}).get("cdata", "")
                            if isinstance(d.get("abstracts"), dict) else ""))
    return out[:max_results]


@_safe
def suche_nber(query, max_results=5):
    """NBER Working Papers (Ökonomie)."""
    r = requests.get("https://www.nber.org/api/v1/working_page_listing/"
                     "contentType/working_paper/_/_/search",
                     params={"q": query, "page": 1, "perPage": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("results") or []):
        titel = (d.get("title") or "").strip()
        if not titel:
            continue
        out.append(_eintrag(titel, "https://www.nber.org" + (d.get("url") or ""),
                            "NBER", _jahr(d.get("displaydate")),
                            authors=", ".join(a.get("name", "") for a in (d.get("authors") or []))))
    return out[:max_results]


@_safe
def suche_repec(query, max_results=5):
    """RePEc/IDEAS — Wirtschaftswissenschaften."""
    r = requests.get("https://ideas.repec.org/cgi-bin/htsearch",
                     params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    # HTML — grob parsen (Titel in <a> nach Ergebnisliste)
    titel = re.findall(r'<a href="/p/[^"]+">([^<]{10,200})</a>', r.text)
    return [_eintrag(t, f"https://ideas.repec.org/p/{i}.html", "RePEc")
            for i, t in enumerate(titel[:max_results])]


@_safe
def suche_cftc(query, max_results=5):
    """CFTC Commitments of Traders (Marktdaten — für Trading-Themen)."""
    r = requests.get("https://publicreporting.cftc.gov/resource/6dca-aqww.json",
                     params={"$limit": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json() or []):
        markt = d.get("market_and_exchange_names") or ""
        if not markt:
            continue
        out.append(_eintrag(f"COT: {markt} ({d.get('report_date_as_yyyy_mm_dd', '')[:10]})",
                            "https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm",
                            "CFTC COT", _jahr(d.get("report_date_as_yyyy_mm_dd"))))
    return out[:max_results]


# ══════════ REGIONAL ══════════

@_safe
def suche_redalyc(query, max_results=5):
    """Redalyc — Lateinamerika (Open Access)."""
    r = requests.get("https://www.redalyc.org/busquedaArticuloFiltros.oa",
                     params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<h3[^>]*>\s*<a[^>]*>([^<]{10,250})</a>', r.text)
    return [_eintrag(t, "https://www.redalyc.org/", "Redalyc")
            for t in titel[:max_results]]


@_safe
def suche_jstage(query, max_results=5):
    """J-STAGE — japanische Journale."""
    r = requests.get("https://www.jstage.jst.go.jp/result/global/-char/en",
                     params={"_search": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'class="search-result-title[^"]*"[^>]*>\s*<a[^>]*>([^<]{8,250})', r.text)
    return [_eintrag(t, "https://www.jstage.jst.go.jp/", "J-STAGE")
            for t in titel[:max_results]]


@_safe
def suche_cinii(query, max_results=5):
    """CiNii Research (Japan) — OpenSearch-JSON."""
    r = requests.get("https://cir.nii.ac.jp/opensearch/all",
                     params={"q": query, "format": "json", "count": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for it in (r.json().get("items") or []):
        titel = str(it.get("title") or "").strip()
        if not titel:
            continue
        out.append(_eintrag(titel, str(it.get("link") or it.get("@id") or ""),
                            "CiNii", _jahr(it.get("date"))))
    return out[:max_results]


@_safe
def suche_ajol(query, max_results=5):
    """AJOL — African Journals Online."""
    r = requests.get("https://www.ajol.info/index.php/index/search/search",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'class="title"[^>]*>\s*<a[^>]*>([^<]{10,250})', r.text)
    return [_eintrag(t, "https://www.ajol.info/", "AJOL")
            for t in titel[:max_results]]


# ══════════ BIO / LABOR ══════════

@_safe
def suche_pdb(query, max_results=5):
    """RCSB Protein Data Bank (Strukturbiologie)."""
    r = requests.post("https://search.rcsb.org/rcsbsearch/v2/query",
                      json={"query": {"type": "terminal", "service": "full_text",
                                      "parameters": {"value": query}},
                            "return_type": "entry",
                            "request_options": {"paginate": {"start": 0, "rows": max_results}}},
                      headers=HEADERS, timeout=TIMEOUT)
    out = []
    for e in (r.json().get("result_set") or []):
        pid = e.get("identifier") or ""
        if not pid:
            continue
        out.append(_eintrag(f"PDB-Struktur {pid} — {query}", f"https://www.rcsb.org/structure/{pid}",
                            "PDB", abstract=f"Struktur-Eintrag für '{query}'"))
    return out[:max_results]


@_safe
def suche_reactome(query, max_results=5):
    """Reactome — biologische Pathways."""
    r = requests.get("https://reactome.org/ContentService/search/query",
                     params={"query": query, "cluster": "true"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for res in (r.json().get("results") or []):
        for entry in (res.get("entries") or []):
            name = entry.get("name") or ""
            if not name:
                continue
            sid = entry.get("stId") or ""
            out.append(_eintrag(f"Reactome: {name}", f"https://reactome.org/content/detail/{sid}",
                                "Reactome", abstract=f"Typ: {entry.get('exactType', '')}"))
            if len(out) >= max_results:
                return out
    return out[:max_results]


@_safe
def suche_geneontology(query, max_results=5):
    """Gene Ontology (QuickGO) — Funktionsannotation."""
    r = requests.get("https://www.ebi.ac.uk/QuickGO/services/ontology/go/search",
                     params={"query": query, "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for g in (r.json().get("results") or []):
        goid = g.get("id") or ""
        name = g.get("name") or ""
        if not name:
            continue
        out.append(_eintrag(f"GO:{goid} — {name}", f"https://www.ebi.ac.uk/QuickGO/term/{goid}",
                            "Gene Ontology", abstract=g.get("definition", {}).get("text", "")[:400]
                            if isinstance(g.get("definition"), dict) else ""))
    return out[:max_results]


@_safe
def suche_gbif(query, max_results=5):
    """GBIF — Biodiversitäts-Daten (Vorkommen/Arten)."""
    r = requests.get("https://api.gbif.org/v1/occurrence/search",
                     params={"q": query, "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for o in (r.json().get("results") or []):
        name = o.get("scientificName") or ""
        if not name:
            continue
        out.append(_eintrag(f"GBIF-Vorkommen: {name}" + (f" ({o.get('country')})" if o.get("country") else ""),
                            f"https://www.gbif.org/occurrence/{o.get('key', '')}",
                            "GBIF", _jahr(o.get("year")),
                            abstract=f"Ort: {o.get('locality') or '–'}, Basis: {o.get('basisOfRecord') or '–'}"))
    return out[:max_results]


@_safe
def suche_proteinatlas(query, max_results=5):
    """Human Protein Atlas (Expression)."""
    r = requests.get("https://www.proteinatlas.org/api/search_download.php",
                     params={"search": query, "format": "json", "columns": "g,gs", "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    out = []
    for row in (r.json() if isinstance(r.json(), list) else []):
        gen = row.get("Gene") or row.get("g") or ""
        if not gen:
            continue
        out.append(_eintrag(f"Protein Atlas: {gen} — {row.get('Gene description') or row.get('gs') or ''}",
                            f"https://www.proteinatlas.org/{gen}", "Protein Atlas"))
    return out[:max_results]


# ══════════ BÜCHER / ARCHIVE / REGISTER ══════════

@_safe
def suche_doab(query, max_results=5):
    """DOAB — Directory of Open Access Books."""
    r = requests.get("https://directory.doabooks.org/rest/search",
                     params={"query": query, "expand": "metadata"},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    out = []
    for b in (r.json() if isinstance(r.json(), list) else []):
        meta = {m.get("key"): m.get("value") for m in (b.get("metadata") or [])
                if isinstance(m, dict)} if isinstance(b.get("metadata"), list) else {}
        titel = (b.get("name") or meta.get("dc.title") or "").strip()
        if not titel:
            continue
        out.append(_eintrag(titel, b.get("handle") or "",
                            "DOAB", _jahr(meta.get("dc.date.issued")), doi=meta.get("dc.identifier.doi", "")))
    return out[:max_results]


@_safe
def suche_orcid(query, max_results=5):
    """ORCID — Forscher-Register (Personen/Profile)."""
    r = requests.get("https://pub.orcid.org/v3.0/expanded-search/",
                     params={"q": query},
                     headers={**HEADERS, "Accept": "application/json"}, timeout=TIMEOUT)
    out = []
    for p in (r.json().get("expanded-result") or [])[:max_results]:
        name = " ".join(x for x in [p.get("given-names"), p.get("family-names")] if x)
        if not name:
            continue
        oid = p.get("orcid-id") or ""
        out.append(_eintrag(f"{name} — {', '.join((p.get('institution-name') or [])[:2])}",
                            f"https://orcid.org/{oid}", "ORCID"))
    return out[:max_results]


@_safe
def suche_ror(query, max_results=5):
    """ROR — Research Organization Registry (Institutionen)."""
    r = requests.get("https://api.ror.org/organizations",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for o in (r.json().get("items") or [])[:max_results]:
        name = o.get("name") or ""
        if not name:
            continue
        out.append(_eintrag(f"{name} ({o.get('country', {}).get('country_name', '')})",
                            o.get("id") or "", "ROR",
                            abstract=f"Typ: {', '.join(o.get('types') or [])}"))
    return out[:max_results]


EXTRA_QUELLEN_3 = {
    # Finance/Ökonomie
    "worldbank": suche_worldbank, "nber": suche_nber,
    "repec": suche_repec, "cftc": suche_cftc,
    # Regional
    "redalyc": suche_redalyc, "jstage": suche_jstage,
    "cinii": suche_cinii, "ajol": suche_ajol,
    # Bio/Labor
    "pdb": suche_pdb, "reactome": suche_reactome,
    "geneontology": suche_geneontology, "gbif": suche_gbif,
    "proteinatlas": suche_proteinatlas,
    # Bücher/Register
    "doab": suche_doab, "orcid": suche_orcid, "ror": suche_ror,
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "clay mineral"
    for name, fn in EXTRA_QUELLEN_3.items():
        tr = fn(thema, 3)
        print(f"[{name}] {len(tr)}")
