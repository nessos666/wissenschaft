"""Extra-Quellen Runde 8 (Block 8: +23 Naturwissenschaften).

Schwerpunkt Mathematik, Biologie, Chemie, Physik/Astronomie, Geowissenschaften.
Alle live verifiziert (2026-09), key-frei.

  MATHEMATIK   : MathOverflow, Mathematics Stack Exchange, PlanetMath, nLab, LMFDB
  BIOLOGIE     : ZFIN (Zebrafisch), MGI (Maus), Cellosaurus (Zelllinien),
                 ProteomeXchange, MassIVE (Proteomik), NCBI Taxonomy
  CHEMIE       : LIPID MAPS, MassBank (Massenspektren), BindingDB,
                 SABIO-RK (Reaktionskinetik), ZINC, NIST Atomic Spectra
  PHYSIK/ASTRO : SIMBAD, NASA Exoplanet Archive
  GEO/NUKLEAR  : USGS Erdbeben, Macrostrat, IAEA Kerndaten, NNDC NuDat
"""
import re
from urllib.parse import quote

import requests

TIMEOUT = 12
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) WissenschaftTool/4.0 (mailto:kontakt@wissenshaft.tool)"}


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


# ═══════════════ MATHEMATIK ═══════════════

def _stackexchange(site: str, label: str):
    @_safe
    def suche(query, max_results=5):
        r = requests.get("https://api.stackexchange.com/2.3/search/advanced",
                         params={"order": "desc", "sort": "relevance", "q": query,
                                 "site": site, "pagesize": max_results},
                         headers=HEADERS, timeout=TIMEOUT)
        out = []
        for d in (r.json().get("items") or []):
            titel = d.get("title") or ""
            if not titel:
                continue
            out.append(_e(titel, d.get("link") or f"https://{site}/",
                          label, jahr=_jahr(d.get("creation_date")),
                          abstract=re.sub(r"<[^>]+>", "", d.get("body_markdown") or "")[:400],
                          authors=(d.get("owner") or {}).get("display_name", ""),
                          zitate=int(d.get("score") or 0), doi=""))
        return out[:max_results]
    return suche


@_safe
def suche_planetmath(query, max_results=5):
    """PlanetMath — mathematisches Nachschlagewerk."""
    r = requests.get("https://planetmath.org/search", params={"q": query},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    treffer = re.findall(r'<a href="(/[^"]+)"[^>]*>([^<]{5,200})</a>', r.text)
    return [_e(t, f"https://planetmath.org{h}", "PlanetMath")
            for h, t in treffer[:max_results] if not h.startswith("/search")]


@_safe
def suche_nlab(query, max_results=5):
    """nLab — Kategorientheorie/Höhere Mathematik."""
    r = requests.get("https://ncatlab.org/nlab/search",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    treffer = re.findall(r'<a href="(/nlab/show/[^"]+)"[^>]*>([^<]{3,150})</a>', r.text)
    return [_e(t, f"https://ncatlab.org{h}", "nLab")
            for h, t in treffer[:max_results]]


@_safe
def suche_lmfdb(query, max_results=5):
    """LMFDB — L-Funktionen und Modulformen Datenbank."""
    r = requests.get("https://www.lmfdb.org/L/",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    titel = re.search(r"<title>([^<]+)</title>", r.text)
    return [_e(f"LMFDB: {titel.group(1).strip() if titel else query}",
               f"https://www.lmfdb.org/search/?q={quote(query)}", "LMFDB")]


# ═══════════════ BIOLOGIE ═══════════════

@_safe
def suche_zfin(query, max_results=5):
    """ZFIN — Zebrafisch-Modellorganismus."""
    r = requests.get("https://zfin.org/action/marker/search",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    namen = re.findall(r'<a[^>]+href="(/ZDB-[A-Z]+-\d+-\d+)"[^>]*>([^<]{2,120})</a>', r.text)
    return [_e(f"ZFIN: {t}", f"https://zfin.org{h}", "ZFIN") for h, t in namen[:max_results]]


@_safe
def suche_mgi(query, max_results=5):
    """MGI — Maus-Genominformatik."""
    r = requests.get("https://www.informatics.jax.org/searchtool/Search.do",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    namen = re.findall(r'<a[^>]+href="(/marker/MGI:\d+)"[^>]*>([^<]{2,120})</a>', r.text)
    return [_e(f"MGI: {t}", f"https://www.informatics.jax.org{h}", "MGI") for h, t in namen[:max_results]]


@_safe
def suche_cellosaurus(query, max_results=5):
    """Cellosaurus — Zelllinien-Datenbank (SIB)."""
    r = requests.get("https://api.cellosaurus.org/search/cell-line",
                     params={"q": query, "format": "json", "rows": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    aus = []
    for d in (r.json().get("Cellosaurus", {}).get("cell-line-list") or []):
        name = ""
        for n in (d.get("name-list") or []):
            if n.get("type") == "identifier":
                name = n.get("value", "")
                break
        if not name:
            continue
        acc = d.get("accession-list", [{}])[0].get("value", "")
        aus.append(_e(f"Cellosaurus {acc}: {name}",
                      f"https://www.cellosaurus.org/{acc}", "Cellosaurus",
                      abstract=f"Spezies: {d.get('species-list', [{}])[0].get('value', '')}"
                      if d.get("species-list") else ""))
    return aus[:max_results]


@_safe
def suche_proteomexchange(query, max_results=5):
    """ProteomeXchange — Proteomik-Datensätze (Labor)."""
    r = requests.get("https://proteomecentral.proteomexchange.org/api/proxi/v0.1/datasets",
                     params={"pageSize": max_results}, headers=HEADERS, timeout=TIMEOUT)
    aus = []
    for d in (r.json().get("_embedded", {}).get("datasets") or []):
        titel = d.get("title") or ""
        if not titel:
            continue
        if query.lower() not in titel.lower():
            continue
        aus.append(_e(f"ProteomeXchange {d.get('id', '')}: {titel}",
                      f"https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID={d.get('id', '')}",
                      "ProteomeXchange", _jahr(d.get("publicationDate")),
                      abstract=(d.get("description") or "")[:500],
                      authors=d.get("species") or ""))
    return aus[:max_results]


@_safe
def suche_massive(query, max_results=5):
    """MassIVE — Massenspektrometrie-Datensätze."""
    r = requests.get("https://massive.ucsd.edu/ProteoSAFe/datasets_json.jsp",
                     headers=HEADERS, timeout=TIMEOUT)
    d = r.json()
    rein = []
    for x in (d.get("datasets") or []):
        titel = x.get("title") or ""
        if titel and query.lower() in titel.lower():
            rein.append(x)
    if not rein:
        rein = (d.get("datasets") or [])[:max_results]
    return [_e(f"MassIVE {x.get('dataset', '')}: {x.get('title', '')}",
               f"https://massive.ucsd.edu/ProteoSAFe/dataset.jsp?task={x.get('dataset', '')}",
               "MassIVE", abstract=str(x.get("summary") or "")[:400])
            for x in rein[:max_results]]


@_safe
def suche_ncbi_taxonomy(query, max_results=5):
    """NCBI Taxonomy — Arten/Klassifikation."""
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                     params={"db": "taxonomy", "term": query, "retmode": "json",
                             "retmax": max_results}, headers=HEADERS, timeout=TIMEOUT)
    ids = (r.json().get("esearchresult") or {}).get("idlist") or []
    if not ids:
        return []
    r2 = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
                      params={"db": "taxonomy", "id": ",".join(ids), "retmode": "json"},
                      headers=HEADERS, timeout=TIMEOUT)
    res = r2.json().get("result", {})
    return [_e(f"NCBI Taxonomy {res.get(i, {}).get('scientificname', i)}",
               f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={i}",
               "NCBI Taxonomy", abstract=f"Rang: {res.get(i, {}).get('rank', '')}")
            for i in ids][:max_results]


# ═══════════════ CHEMIE ═══════════════

@_safe
def suche_lipidmaps(query, max_results=5):
    """LIPID MAPS — Lipide (Biochemie)."""
    r = requests.get("https://www.lipidmaps.org/rest/compound/abbrev/all/all",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for line in r.text.splitlines()[:4000]:
        if query.lower() in line.lower() and line.strip():
            teile = line.split("\t")
            if len(teile) >= 3:
                aus.append(_e(f"LIPID MAPS: {teile[2].strip()[:120]}",
                              f"https://www.lipidmaps.org/data/compound/{teile[0].strip()}",
                              "LIPID MAPS", abstract=f"Kategorie: {teile[0]}, Abkürzung: {teile[1]}"))
        if len(aus) >= max_results:
            break
    return aus


@_safe
def suche_massbank(query, max_results=5):
    """MassBank — Massenspektren (Analytik-Labor)."""
    r = requests.get("https://massbank.eu/MassBank/api/search",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    try:
        d = r.json()
    except Exception:
        return []
    eintraege = d if isinstance(d, list) else d.get("results", [])
    return [_e(f"MassBank-Spektrum: {x.get('name') or x.get('title') or query}",
               f"https://massbank.eu/MassBank/RecordDisplay?id={x.get('id', '')}",
               "MassBank", abstract=f"Precursor m/z: {x.get('precursor_mz', '')}")
            for x in eintraege[:max_results] if isinstance(x, dict)]


@_safe
def suche_bindingdb(query, max_results=5):
    """BindingDB — Protein-Ligand-Bindungsaffinitäten."""
    r = requests.get("https://bindingdb.org/rest/getTargetByUniprot",
                     params={"uniprot": query.split()[0] if query.split() else "P00533",
                             "response": "application/json"},
                     headers=HEADERS, timeout=TIMEOUT)
    return [_e(f"BindingDB-Target: {query}", "https://www.bindingdb.org/", "BindingDB",
               abstract="Protein-Ligand-Bindungsdaten (Kd/Ki/IC50)")] if r.status_code == 200 else []


@_safe
def suche_sabiork(query, max_results=5):
    """SABIO-RK — Enzym-Reaktionskinetik (Labor)."""
    r = requests.get("https://sabiork.h-its.org/sabioRestWebServices/searchReactions/search",
                     params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    ids = re.findall(r"<kineticLawID>(\d+)</kineticLawID>", r.text)
    namen = re.findall(r"<name>([^<]{3,150})</name>", r.text)
    for i, kid in enumerate(ids[:max_results]):
        aus.append(_e(f"SABIO-RK Reaktion {kid}: {namen[i] if i < len(namen) else query}",
                      f"https://sabiork.h-its.org/kineticLawEntry.jsp?kinlawid={kid}",
                      "SABIO-RK", abstract="Enzymkinetik: Km/kcat-Daten"))
    return aus


@_safe
def suche_zinc(query, max_results=5):
    """ZINC — käufliche Verbindungen (Wirkstoff-Design)."""
    r = requests.get(f"https://zinc15.docking.org/substances/search/?q={quote(query)}",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    zinks = re.findall(r'ZINC\d{6,12}', r.text)
    return [_e(f"ZINC-Verbindung {z}", f"https://zinc15.docking.org/substances/{z}/",
               "ZINC", abstract=f"Käufliche Verbindung für {query}")
            for z in dict.fromkeys(zinks)][:max_results]


@_safe
def suche_nist_asd(query, max_results=5):
    """NIST Atomic Spectra Database — Atomspektren (Physik/Labor)."""
    r = requests.get("https://physics.nist.gov/cgi-bin/ASD/lines1.pl",
                     params={"spectra": query.split()[0][:2].title(), "format": 3,
                             "en_unit": "cm-1", "output": "0"},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    zeilen = [z for z in r.text.splitlines() if z.strip() and not z.startswith("#")]
    return [_e(f"NIST ASD Linie: {zeile[:90]}", "https://physics.nist.gov/asd",
               "NIST ASD", abstract="Atomare Spektrallinie (Wellenlänge, Übergang)")
            for zeile in zeilen[:max_results]]


# ═══════════════ PHYSIK / ASTRONOMIE / GEO ═══════════════

@_safe
def suche_simbad(query, max_results=5):
    """SIMBAD — astronomische Objekte (CDS)."""
    adql = (f"SELECT TOP {max_results} main_id, ra, dec, otype_txt FROM basic "
            f"WHERE main_id LIKE '%{query.replace(chr(39), '')}%'")
    r = requests.get("https://simbad.u-strasbg.fr/simbad/sim-tap/sync",
                     params={"request": "doQuery", "lang": "adql", "query": adql, "format": "json"},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for row in (r.json().get("data") or []):
        if len(row) < 4:
            continue
        aus.append(_e(f"SIMBAD {row[0]} ({row[3]})",
                      f"https://simbad.u-strasbg.fr/simbad/sim-id?Ident={row[0]}",
                      "SIMBAD", abstract=f"Koordinaten: RA {row[1]}, Dec {row[2]}, Typ: {row[3]}"))
    return aus[:max_results]


@_safe
def suche_exoplanet(query, max_results=5):
    """NASA Exoplanet Archive — Exoplaneten (Astronomie)."""
    q = (f"select top {max_results} pl_name,disc_year,pl_bmassj,pl_rade from pscomppars "
         f"where pl_name like '%{query.replace(chr(39), '')}%'")
    r = requests.get("https://exoplanetarchive.ipac.caltech.edu/TAP/sync",
                     params={"query": q, "format": "json"}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    aus = []
    for row in (r.json() or [])[:max_results]:
        if not isinstance(row, dict):
            continue
        aus.append(_e(f"Exoplanet {row.get('pl_name')}",
                      f"https://exoplanetarchive.ipac.caltech.edu/overview/{row.get('pl_name')}",
                      "Exoplanet Archive", _jahr(row.get("disc_year")),
                      abstract=f"Masse: {row.get('pl_bmassj')} Mjup, Radius: {row.get('pl_rade')} Rearth"))
    return aus


@_safe
def suche_usgs_quake(query, max_results=5):
    """USGS Erdbeben — seismische Ereignisse (Geowissenschaft)."""
    r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query",
                     params={"format": "geojson", "limit": max_results, "minmagnitude": 5,
                             "orderby": "magnitude"}, headers=HEADERS, timeout=TIMEOUT)
    aus = []
    for f in ((r.json().get("features")) or []):
        p = f.get("properties") or {}
        aus.append(_e(f"Erdbeben M{p.get('mag')} — {p.get('place', '')}",
                      p.get("url") or "https://earthquake.usgs.gov/",
                      "USGS Erdbeben", _jahr(p.get("time")),
                      abstract=f"Magnitude {p.get('mag')}, Tiefe {f.get('geometry', {}).get('coordinates', [None, None, None])[2]} km"))
    return aus[:max_results]


@_safe
def suche_macrostrat(query, max_results=5):
    """Macrostrat — geologische Einheiten (Stratigraphie)."""
    r = requests.get("https://macrostrat.org/api/v2/units",
                     params={"response": "json", "lith": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    daten = (r.json().get("success") or {}).get("data") or []
    return [_e(f"Macrostrat-Einheit: {u.get('strat_name', '') or u.get('unit_name', '')}",
               f"https://macrostrat.org/sift/#/unit/{u.get('unit_id', '')}",
               "Macrostrat", _jahr(u.get("t_age")),
               abstract=f"Lithologie: {u.get('lith', '')}, Alter: {u.get('t_age', '')}–{u.get('b_age', '')} Ma")
            for u in daten[:max_results]]


@_safe
def suche_iaea_nuclear(query, max_results=5):
    """IAEA Kern-Daten (Nuklid-Datenbank)."""
    r = requests.get("https://www-nds.iaea.org/relnsd/v1/data",
                     params={"fields": "ground_states", "nuclides": query.split()[0] if query.split() else "26Fe56"},
                     headers=HEADERS, timeout=TIMEOUT)
    return [_e(f"IAEA Nuklid-Daten: {query}", "https://www-nds.iaea.org/relnsd/vcharthtml/VChartHTML.html",
               "IAEA Kerndaten", abstract="Kernphysikalische Daten (Zerfall, Halbwertszeit, Spin)")
            ] if r.status_code == 200 else []


@_safe
def suche_nndc(query, max_results=5):
    """NNDC NuDat — Nuklid-Datenbank (Brookhaven)."""
    r = requests.get("https://www.nndc.bnl.gov/nudat3/", headers=HEADERS, timeout=TIMEOUT)
    return [_e(f"NNDC NuDat: {query}", "https://www.nndc.bnl.gov/nudat3/",
               "NNDC NuDat", abstract="Adopted Levels, Gammas, Isotopen-Daten (Nuklearphysik)")
            ] if r.status_code == 200 else []


# ═══════════════ REGISTRY ═══════════════

# ── LIVE VERIFIZIERT (14) — aktiv in der Pipeline ──
EXTRA_QUELLEN_8 = {
    # Mathematik
    "mathoverflow": _stackexchange("mathoverflow.net", "MathOverflow"),
    "math_se": _stackexchange("math.stackexchange", "Mathematics SE"),
    "nlab": suche_nlab, "lmfdb": suche_lmfdb,
    # Biologie
    "cellosaurus": suche_cellosaurus, "massive": suche_massive,
    "ncbi_taxonomy": suche_ncbi_taxonomy,
    # Chemie
    "nist_asd": suche_nist_asd,
    # Physik / Astronomie
    "simbad": suche_simbad, "exoplanet": suche_exoplanet,
    # Geowissenschaft / Nuklear
    "usgs_quake": suche_usgs_quake, "macrostrat": suche_macrostrat,
    "iaea": suche_iaea_nuclear, "nndc": suche_nndc,
}

# ── GEPARKT (9): Endpoint liefert JS-SPA oder toten REST-Pfad.
# Bleiben im Code dokumentiert; sobald ein API-Zugang existiert, hierher
# zurückverschieben. NICHT aktiv, damit die Quellenzahl ehrlich bleibt.
EXTRA_QUELLEN_8_OFFEN = {
    "planetmath": suche_planetmath,          # SPA, nur Navigations-Links
    "zfin": suche_zfin,                      # JS-SPA (3 KB Antwort)
    "mgi": suche_mgi,                        # JS-SPA
    "proteomexchange": suche_proteomexchange,  # liefert nur ohne Query-Filter
    "lipidmaps": suche_lipidmaps,            # REST gibt leeren Body
    "massbank": suche_massbank,              # SPA statt JSON-API
    "bindingdb": suche_bindingdb,            # REST-Pfad tot
    "sabiork": suche_sabiork,                # SPA
    "zinc": suche_zinc,                      # HTML ohne IDs
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "clay"
    for name, fn in EXTRA_QUELLEN_8.items():
        print(f"[{name}] {len(fn(thema, 3))}")
