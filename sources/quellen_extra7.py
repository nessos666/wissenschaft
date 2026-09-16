"""Extra-Quellen Runde 7 (Block 5+6: Förderdatenbanken, EBI-Vertiefung,
Interaktionen, Ökologie, Technik, Wikimedia). Live verifiziert 2026-09.

  FÖRDERUNG  : NIH RePORTER, CORDIS (EU), NSF Awards
  EBI-2      : AlphaFold DB, MGnify (Mikrobiom)
               [PRIDE, InterPro, Expression Atlas, BioModels, KEGG sind in
                quellen_extra9.py implementiert — siehe F2 im Review]
  INTERAKTION: STRING-DB (Protein-Netzwerke)
  ÖKOLOGIE   : iNaturalist, DataONE, DSpace@MIT
  TECHNIK    : IETF Datatracker, ACL Anthology, Bioconductor, SourceForge
  MEDIEN     : Wikipedia, Wikimedia Commons, Wikibooks, Wikiversity,
               OpenEdition, Dialnet
"""
import re

import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) WissenschaftTool/4.0 (mailto:wissenschaft-tool@example.org)"}


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


def _wiki(domain: str, label: str):
    @_safe
    def suche(query, max_results=5):
        r = requests.get(f"https://{domain}/w/api.php",
                         params={"action": "query", "list": "search", "srsearch": query,
                                 "format": "json", "srlimit": max_results},
                         headers=HEADERS, timeout=TIMEOUT)
        out = []
        for d in (r.json().get("query", {}).get("search") or []):
            t = d.get("title") or ""
            if not t:
                continue
            out.append(_e(f"{label}: {t}", f"https://{domain}/wiki/" + requests.utils.quote(t),
                          label, abstract=re.sub(r"<[^>]+>", "", d.get("snippet") or "")[:400]))
        return out[:max_results]
    return suche


def _html_liste(url_tmpl, source, params_key="q", regex=r'<a[^>]+href="([^"]+)"[^>]*>([^<]{10,200})</a>'):
    @_safe
    def suche(query, max_results=5):
        r = requests.get(url_tmpl.format(q=requests.utils.quote(query)),
                         headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        treffer = re.findall(regex, r.text)
        return [_e(t, h if h.startswith("http") else f"https://{source.lower()}.org{h}", source)
                for h, t in treffer[:max_results]]
    return suche


# ══════════ FÖRDERDATENBANKEN ══════════

@_safe
def suche_nih_reporter(query, max_results=5):
    """NIH RePORTER — geförderte Forschungsprojekte (USA)."""
    r = requests.post("https://api.reporter.nih.gov/v2/projects/search",
                      json={"criteria": {"advanced_text_search": {
                          "operator": "and", "search_field": "projecttitle",
                          "search_text": query}}, "limit": max_results},
                      headers={**HEADERS, "Content-Type": "application/json"}, timeout=TIMEOUT)
    out = []
    for p in (r.json().get("results") or []):
        titel = p.get("project_title") or ""
        if not titel:
            continue
        pid = p.get("project_num") or ""
        out.append(_e(titel, f"https://reporter.nih.gov/project-details/{p.get('appl_id', '')}",
                      "NIH RePORTER", _jahr(p.get("project_start_date")),
                      abstract=f"Projektnummer: {pid}, Förderjahr: {_jahr(p.get('fiscal_year'))}",
                      zitate=int(p.get("award_amount") or 0) // 1000))
    return out[:max_results]


@_safe
def suche_cordis(query, max_results=5):
    """CORDIS — EU-Forschungsprojekte."""
    r = requests.post("https://api.tech.ec.europa.eu/search-api/prod/rest/search",
                      params={"apiKey": "SEDIA", "text": query, "pageSize": max_results},
                      headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("results") or []):
        titel = d.get("title") or ""
        if not titel:
            continue
        out.append(_e(titel, d.get("url") or "https://cordis.europa.eu/",
                      "CORDIS", _jahr(d.get("startDate")),
                      abstract=str(d.get("teaser") or "")[:400]))
    return out[:max_results]


@_safe
def suche_nsf(query, max_results=5):
    """NSF Awards — geförderte Projekte (USA)."""
    r = requests.get("https://api.nsf.gov/services/v1/awards.json",
                     params={"keyword": query, "printFields": "id,title,startDate,awardeeName,abstractText"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for a in ((r.json().get("response") or {}).get("award") or []):
        titel = a.get("title") or ""
        if not titel:
            continue
        out.append(_e(titel, f"https://www.nsf.gov/awardsearch/showAward?AWD_ID={a.get('id', '')}",
                      "NSF Awards", _jahr(a.get("startDate")),
                      abstract=a.get("abstractText", ""), authors=a.get("awardeeName", "")))
    return out[:max_results]


# ══════════ EBI-2 / INTERAKTIONEN / ÖKOLOGIE ══════════

@_safe
def suche_alphafold(query, max_results=5):
    """AlphaFold DB — KI-Proteinstruktur-Vorhersagen."""
    r = requests.get(f"https://alphafold.ebi.ac.uk/api/prediction/"
                     f"{requests.utils.quote(query.split()[0])}", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    d = r.json()
    daten = d if isinstance(d, list) else [d]
    return [_e(f"AlphaFold {x.get('uniprotAccession', '')} — {x.get('uniprotDescription', '')}",
               x.get("entryId") or "https://alphafold.ebi.ac.uk/", "AlphaFold DB",
               abstract=f"Organismus: {x.get('organismScientificName', '')}")
            for x in daten][:max_results]


@_safe
def suche_mgnify(query, max_results=5):
    """MGnify (EBI) — Mikrobiom-Analysen."""
    r = requests.get("https://www.ebi.ac.uk/metagenomics/api/v1/studies",
                     params={"search": query}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("data") or []):
        att = d.get("attributes") or {}
        titel = att.get("study-name") or att.get("study_name") or ""
        if not titel:
            continue
        out.append(_e(f"MGnify: {titel}", d.get("links", {}).get("self") or "https://www.ebi.ac.uk/metagenomics/",
                      "MGnify", abstract=(att.get("study-abstract") or "")[:500],
                      authors=att.get("centre-name", "")))
    return out[:max_results]


@_safe
def suche_stringdb(query, max_results=5):
    """STRING-DB — Protein-Protein-Interaktionen."""
    r = requests.get("https://string-db.org/api/json/network",
                     params={"identifiers": query.split()[0], "species": 9606},
                     headers=HEADERS, timeout=TIMEOUT)
    d = r.json() if r.status_code == 200 else []
    if not isinstance(d, list):
        return []
    return [_e(f"STRING: {x.get('preferredName_A', '')} ↔ {x.get('preferredName_B', '')} "
               f"(Score {round(float(x.get('score', 0)), 2)})",
               "https://string-db.org/network/" + str(x.get("stringId_A", "")), "STRING-DB",
               abstract=f"Interaktionsscore: {x.get('score')}, Quelle: {x.get('ncbiTaxonIdentifiers')}")
            for x in d[:max_results]]


@_safe
def suche_inaturalist(query, max_results=5):
    """iNaturalist — Artenbeobachtungen (Biodiversität)."""
    r = requests.get("https://api.inaturalist.org/v1/observations",
                     params={"q": query, "per_page": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for o in (r.json().get("results") or []):
        taxon = (o.get("taxon") or {}).get("name") or o.get("species_guess") or ""
        if not taxon:
            continue
        out.append(_e(f"iNaturalist-Beobachtung: {taxon}",
                      f"https://www.inaturalist.org/observations/{o.get('id', '')}",
                      "iNaturalist", _jahr(o.get("observed_on")),
                      abstract=f"Ort: {o.get('place_guess') or '–'}"))
    return out[:max_results]


@_safe
def suche_dataone(query, max_results=5):
    """DataONE — Umwelt-/Ökologiedaten."""
    r = requests.get("https://cn.dataone.org/cn/v2/query/solr/",
                     params={"q": query, "rows": max_results, "wt": "json"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in ((r.json().get("response") or {}).get("docs") or []):
        titel = (d.get("title") or "")
        if isinstance(titel, list):
            titel = titel[0] if titel else ""
        if not titel:
            continue
        out.append(_e(str(titel)[:400], f"https://search.dataone.org/#view/{d.get('id', '')}",
                      "DataONE", _jahr(d.get("dateUploaded")))
        )
    return out[:max_results]


@_safe
def suche_dspace_mit(query, max_results=5):
    """DSpace@MIT — institutionelles Repositorium."""
    r = requests.get("https://dspace.mit.edu/server/api/discover/search/objects",
                     params={"query": query, "size": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for o in (((r.json().get("_embedded") or {}).get("searchResult") or {})
              .get("_embedded") or {}).get("objects") or []:
        md = ((o.get("_embedded") or {}).get("indexableObject") or {}).get("metadata") or {}
        titel = ""
        for k in ("dc.title", "title"):
            if md.get(k):
                titel = md[k][0].get("value", "")
                break
        if not titel:
            continue
        out.append(_e(titel, f"https://dspace.mit.edu/handle/{o.get('id', '')}",
                      "DSpace@MIT", _jahr(md.get("dc.date.issued", [{}])[0].get("value")
                                          if md.get("dc.date.issued") else "")))
    return out[:max_results]


# ══════════ TECHNIK / MEDIEN ══════════

@_safe
def suche_ietf(query, max_results=5):
    """IETF Datatracker — Internet-Drafts/Standards."""
    r = requests.get("https://datatracker.ietf.org/api/v1/doc/document/",
                     params={"title__icontains": query, "limit": max_results},
                     headers={**HEADERS, "Accept": "application/json"}, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("objects") or []):
        titel = d.get("title") or ""
        name = d.get("name") or ""
        if not titel:
            continue
        out.append(_e(f"IETF {name}: {titel}", f"https://datatracker.ietf.org/doc/{name}/",
                      "IETF", _jahr(d.get("time"))))
    return out[:max_results]


@_safe
def suche_acl_anthology(query, max_results=5):
    """ACL Anthology — NLP/Computational Linguistics."""
    r = requests.get("https://aclanthology.org/search/",
                     params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    treffer = re.findall(r'<a[^>]+href="(/[A-Z0-9][^"]*)"[^>]*>\s*<strong>([^<]{10,250})</strong>', r.text)
    return [_e(t, f"https://aclanthology.org{h}", "ACL Anthology")
            for h, t in treffer[:max_results]]


@_safe
def suche_bioconductor(query, max_results=5):
    """Bioconductor — R-Pakete für Bioinformatik."""
    r = requests.get("https://bioconductor.org/packages/json/3.19/bioc/packages.json",
                     headers=HEADERS, timeout=TIMEOUT)
    d = r.json().get("packages", {}) if isinstance(r.json(), dict) else {}
    q = query.lower()
    out = []
    for name, info in (d.items() if isinstance(d, dict) else []):
        titel = info.get("Title", "") if isinstance(info, dict) else ""
        if q in name.lower() or q in titel.lower():
            out.append(_e(f"Bioconductor {name} — {titel}",
                          f"https://bioconductor.org/packages/{name}/", "Bioconductor",
                          abstract=info.get("Description", "") if isinstance(info, dict) else ""))
        if len(out) >= max_results:
            break
    return out


@_safe
def suche_sourceforge(query, max_results=5):
    """SourceForge — Open-Source-Projekte (Forschung)."""
    r = requests.get(f"https://sourceforge.net/directory/?q={requests.utils.quote(query)}",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    treffer = re.findall(r'<a[^>]+href="(/projects/[^"]+)"[^>]*>\s*<h3[^>]*>([^<]{5,150})', r.text)
    return [_e(t, f"https://sourceforge.net{h}", "SourceForge") for h, t in treffer[:max_results]]


@_safe
def suche_openedition(query, max_results=5):
    """OpenEdition — Geistes-/Sozialwissenschaften (EU)."""
    r = requests.get("https://search.openedition.org/search",
                     params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    treffer = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>\s*([^<]{15,200})</a>', r.text)
    return [_e(t, h, "OpenEdition") for h, t in treffer[:max_results]]


@_safe
def suche_dialnet(query, max_results=5):
    """Dialnet — spanischsprachige Wissenschaft."""
    r = requests.get("https://dialnet.unirioja.es/buscar/documentos",
                     params={"querysDismax.DOCUMENTAL_TODO": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    treffer = re.findall(r'<a[^>]+href="(/servlet/articulo[^"]+)"[^>]*>([^<]{15,200})', r.text)
    return [_e(t, f"https://dialnet.unirioja.es{h}", "Dialnet") for h, t in treffer[:max_results]]


# ══════════ REGISTRY ══════════

EXTRA_QUELLEN_7 = {
    # Förderdatenbanken
    "nih_reporter": suche_nih_reporter, "cordis": suche_cordis, "nsf": suche_nsf,
    # EBI-2 / Interaktionen / Ökologie
    "alphafold": suche_alphafold, "mgnify": suche_mgnify,
    "stringdb": suche_stringdb, "inaturalist": suche_inaturalist,
    "dataone": suche_dataone, "dspace_mit": suche_dspace_mit,
    # Technik
    "ietf": suche_ietf, "acl_anthology": suche_acl_anthology,
    "bioconductor": suche_bioconductor, "sourceforge": suche_sourceforge,
    # Medien/Wikipedia-Familie
    "wikipedia": _wiki("de.wikipedia.org", "Wikipedia"),
    "wikimedia_commons": _wiki("commons.wikimedia.org", "Wikimedia Commons"),
    "wikibooks": _wiki("de.wikibooks.org", "Wikibooks"),
    "wikiversity": _wiki("de.wikiversity.org", "Wikiversity"),
    "openedition": suche_openedition, "dialnet": suche_dialnet,
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "clay"
    for name, fn in EXTRA_QUELLEN_7.items():
        print(f"[{name}] {len(fn(thema, 3))}")
