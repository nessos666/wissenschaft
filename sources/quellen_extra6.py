"""Extra-Quellen Runde 6 (Block 4: Paket-Register, Standards, Chemie,
Zitationen, Physik, Medizin-Register). Live verifiziert 2026-09.

  PAKETE    : crates.io (Rust), NuGet (.NET), RubyGems, Hackage, Go modules
  STANDARDS : NIST Chemistry WebBook, RFC Editor, W3C TR
  CHEMIE    : PubChem (Verbindungen)
  ZITATION  : OpenCitations (Zitationsdaten)
  MATHE     : EuDML
  PHYSIK    : CERN CDS, DESY
  MEDIZIN   : NCI PDQ, EU-CTR
"""
import re

import requests

TIMEOUT = 25
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


# ══════════ PAKET-REGISTER ══════════

@_safe
def suche_crates(query, max_results=5):
    r = requests.get("https://crates.io/api/v1/crates",
                     params={"q": query, "per_page": max_results}, headers=HEADERS, timeout=TIMEOUT)
    return [_e(f"crate {c.get('name', '')} — {c.get('description') or ''}",
               f"https://crates.io/crates/{c.get('name', '')}", "crates.io",
               _jahr(c.get("created_at")), zitate=int(c.get("downloads") or 0))
            for c in (r.json().get("crates") or [])][:max_results]


@_safe
def suche_nuget(query, max_results=5):
    r = requests.get("https://azuresearch-usnc.nuget.org/query",
                     params={"q": query, "take": max_results}, headers=HEADERS, timeout=TIMEOUT)
    return [_e(f"NuGet {d.get('id', '')} — {d.get('description') or ''}",
               d.get("projectUrl") or f"https://www.nuget.org/packages/{d.get('id', '')}",
               "NuGet", zitate=int(d.get("totalDownloads") or 0))
            for d in (r.json().get("data") or [])][:max_results]


@_safe
def suche_rubygems(query, max_results=5):
    r = requests.get("https://rubygems.org/api/v1/search.json",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    d = r.json()
    if not isinstance(d, list):
        return []
    return [_e(f"RubyGem {g.get('name', '')} — {g.get('info') or ''}",
               g.get("project_uri") or "", "RubyGems",
               zitate=int(g.get("downloads") or 0))
            for g in d[:max_results]]


@_safe
def suche_hackage(query, max_results=5):
    r = requests.get("https://hackage.haskell.org/packages/search",
                     params={"terms": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<a href="/package/([^"]+)">([^<]+)</a>', r.text)
    return [_e(f"Hackage {name}", f"https://hackage.haskell.org/package/{pfad}",
               "Hackage") for pfad, name in titel[:max_results]]


@_safe
def suche_gomodules(query, max_results=5):
    r = requests.get("https://pkg.go.dev/search",
                     params={"q": query, "m": "package"}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'href="/([a-z0-9./\-]+)"[^>]*>\s*<span[^>]*>([^<]{5,120})</span>', r.text)
    return [_e(f"Go {name}", f"https://pkg.go.dev/{pfad}", "Go modules")
            for pfad, name in titel[:max_results]]


# ══════════ STANDARDS ══════════

@_safe
def suche_nist_webbook(query, max_results=5):
    """NIST Chemistry WebBook — Referenzdaten für Substanzen (Labor)."""
    r = requests.get("https://webbook.nist.gov/cgi/cbook.cgi",
                     params={"Name": query, "Units": "SI"}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    namen = re.findall(r'<strong>([A-Za-z0-9\-\s,()]{3,60})</strong>', r.text)
    out = [_e(f"NIST: {n.strip()}", f"https://webbook.nist.gov/cgi/cbook.cgi?Name={requests.utils.quote(n.strip())}&Units=SI",
              "NIST WebBook") for n in namen[:max_results]]
    return out or [_e(f"NIST Chemistry WebBook — Daten zu '{query}'",
                      f"https://webbook.nist.gov/cgi/cbook.cgi?Name={requests.utils.quote(query)}",
                      "NIST WebBook", abstract="Referenzspektren/Thermodynamik")]


@_safe
def suche_rfc(query, max_results=5):
    """RFC Editor — Internet-Standards (Technik)."""
    r = requests.get("https://www.rfc-editor.org/search/rfc_search_detail.php",
                     params={"title": query, "pubstatus[]": "Any"}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    rfc_nrs = re.findall(r"RFC (\d{3,5})", r.text)[:max_results]
    return [_e(f"RFC {nr} — {query}", f"https://www.rfc-editor.org/rfc/rfc{nr}.html",
               "RFC Editor") for nr in rfc_nrs]


@_safe
def suche_w3c(query, max_results=5):
    """W3C — Web-Standards (Technical Reports)."""
    r = requests.get("https://www.w3.org/TR/", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<a href="(/TR/[^"]+)">([^<]{8,120})</a>', r.text)
    q = query.lower()
    treffer = [(h, t) for h, t in titel if q in t.lower()][:max_results]
    return [_e(f"W3C: {t}", f"https://www.w3.org{h}", "W3C") for h, t in treffer]


# ══════════ CHEMIE / ZITATION / MATHE / PHYSIK / MEDIZIN ══════════

@_safe
def suche_pubchem(query, max_results=5):
    """PubChem — chemische Verbindungen (Stoffdaten)."""
    r = requests.get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                     f"{requests.utils.quote(query.split()[0])}/property/"
                     f"MolecularFormula,MolecularWeight,IUPACName/JSON",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    out = []
    for p in (r.json().get("PropertyTable", {}).get("Properties") or []):
        cid = p.get("CID")
        out.append(_e(f"PubChem CID {cid}: {p.get('IUPACName') or query} "
                      f"({p.get('MolecularFormula', '')}, {p.get('MolecularWeight', '')} g/mol)",
                      f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
                      "PubChem", abstract=f"Summenformel: {p.get('MolecularFormula', '')}"))
    return out[:max_results]


@_safe
def suche_opencitations(query, max_results=5):
    """OpenCitations — Zitationsdaten (COCI)."""
    r = requests.get(f"https://opencitations.net/index/coci/api/v1/citation-count/"
                     f"{requests.utils.quote(query)}", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    d = r.json()
    if not isinstance(d, list):
        return []
    return [_e(f"OpenCitations: {x.get('count', 0)} Zitationen für DOI {query}",
               f"https://opencitations.net/index/coci/api/v1/citations/{query}",
               "OpenCitations", abstract=f"Zitationszahl: {x.get('count', 0)}")
            for x in d[:max_results]]


@_safe
def suche_eudml(query, max_results=5):
    """EuDML — European Digital Mathematics Library."""
    r = requests.get("https://eudml.org/search", params={"q": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<a[^>]+href="(/doc/[^"]+)"[^>]*>([^<]{10,200})</a>', r.text)
    return [_e(t, f"https://eudml.org{h}", "EuDML") for h, t in titel[:max_results]]


@_safe
def suche_cern_cds(query, max_results=5):
    """CERN Document Server (Physik)."""
    r = requests.get("https://cds.cern.ch/search",
                     params={"p": query, "of": "xm", "rg": max_results}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r"<title>([^<]{10,250})</title>", r.text)
    return [_e(t, "https://cds.cern.ch/", "CERN CDS") for t in titel[1:max_results + 1]]


@_safe
def suche_desy(query, max_results=5):
    """DESY Publication Database (Teilchenphysik)."""
    r = requests.get("https://bib-pubdb1.desy.de/search", params={"p": query, "of": "xm"},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r"<title>([^<]{10,250})</title>", r.text)
    return [_e(t, "https://bib-pubdb1.desy.de/", "DESY") for t in titel[1:max_results + 1]]


@_safe
def suche_nci_pdq(query, max_results=5):
    """NCI PDQ — Krebs-Informationsdatenbank (Medizin)."""
    r = requests.get("https://www.cancer.gov/search/results",
                     params={"swKeyword": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<h3[^>]*>\s*<a[^>]*>([^<]{10,250})</a>', r.text)
    return [_e(t, "https://www.cancer.gov/", "NCI PDQ") for t in titel[:max_results]]


@_safe
def suche_eu_ctr(query, max_results=5):
    """EU Clinical Trials Register (Medizin)."""
    r = requests.get("https://www.clinicaltrialsregister.eu/ctr-search/search",
                     params={"query": query}, headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    titel = re.findall(r'<td[^>]*class="[^"]*title[^"]*"[^>]*>\s*<a[^>]*>([^<]{10,250})', r.text)
    return [_e(t, "https://www.clinicaltrialsregister.eu/", "EU-CTR") for t in titel[:max_results]]


@_safe
def suche_metabolights(query, max_results=5):
    """MetaboLights (EBI) — Metabolomik-Studien (Labor)."""
    r = requests.get("https://www.ebi.ac.uk/metabolights/ws/studies/",
                     headers={**HEADERS, "Accept": "application/json"}, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    d = r.json()
    studies = d.get("content", d) if isinstance(d, dict) else d
    return [_e(f"MetaboLights-Studie: {x.get('studyIdentifier') or x.get('study_id') or query}",
               f"https://www.ebi.ac.uk/metabolights/{x.get('studyIdentifier') or ''}",
               "MetaboLights", abstract=str(x.get("title") or x.get("description") or "")[:300])
            for x in (studies or [])[:max_results]]


EXTRA_QUELLEN_6 = {
    "metabolights": suche_metabolights,
    "crates": suche_crates, "nuget": suche_nuget, "rubygems": suche_rubygems,
    "hackage": suche_hackage, "gomodules": suche_gomodules,
    "nist_webbook": suche_nist_webbook, "rfc": suche_rfc, "w3c": suche_w3c,
    "pubchem": suche_pubchem, "opencitations": suche_opencitations,
    "eudml": suche_eudml, "cern_cds": suche_cern_cds, "desy": suche_desy,
    "nci_pdq": suche_nci_pdq, "eu_ctr": suche_eu_ctr,
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "clay"
    for name, fn in EXTRA_QUELLEN_6.items():
        print(f"[{name}] {len(fn(thema, 3))}")
