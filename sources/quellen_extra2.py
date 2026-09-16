"""Extra-Quellen Runde 2 (Davids Registry-Abgleich, 105 Quellen).

Alle live verifiziert (2026-09): Medizin/Bio/Labor, CS/Software, Mathematik,
Bücher/Archive. Liefern Dicts im _norm-Format von sources/papersearch.

Domänen-Anbindung (Davids Wunsch: 'ärztliche Wissenschaft, Biologie,
Bio-Chemie, Labore überall anknüpfen'):
  MEDIZIN/BIOLOGIE : ClinicalTrials.gov, UniProt, ChEMBL, NCBI Gene,
                     Ensembl, EBI BioStudies, PubChem
  CS/SOFTWARE      : OpenReview, HuggingFace Papers, GitHub, GitLab, PyPI
  MATHEMATIK       : zbMATH, OEIS
  DATEN/WISSEN     : Dryad, Wikidata
  BÜCHER/ARCHIVE   : Open Library, Internet Archive
"""
import re

import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:wissenschaft-tool@example.org)"}


def _jahr(text) -> str:
    m = re.search(r"(19|20)\d{2}", str(text or ""))
    return m.group(0) if m else ""


def _safe(fn):
    """Nie crashen: leere Liste bei Fehler."""
    def wrapper(query, max_results=5):
        try:
            return fn(query, max_results)
        except Exception:
            return []
    wrapper.__name__ = fn.__name__
    return wrapper


# ══════════════ MEDIZIN / BIOLOGIE / LABOR ══════════════

@_safe
def suche_clinicaltrials(query: str, max_results: int = 5) -> list:
    """Klinische Studien (Medizin) — ClinicalTrials.gov API v2."""
    r = requests.get("https://clinicaltrials.gov/api/v2/studies",
                     params={"query.term": query, "pageSize": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for st in (r.json().get("studies") or []):
        ps = st.get("protocolSection") or {}
        idm = ps.get("identificationModule") or {}
        titel = (idm.get("briefTitle") or "").strip()
        if not titel:
            continue
        nct = idm.get("nctId") or ""
        status = (ps.get("statusModule") or {}).get("overallStatus") or ""
        out.append({
            "title": f"{titel} [{nct}]"[:500],
            "year": _jahr((ps.get("statusModule") or {}).get("startDateStruct", {}).get("date")),
            "doi": "", "url": f"https://clinicaltrials.gov/study/{nct}" if nct else "",
            "pdf_url": "", "source": "ClinicalTrials.gov", "citations": 0,
            "abstract": f"Status: {status}",
            "authors": "",
        })
    return out[:max_results]


@_safe
def suche_uniprot(query: str, max_results: int = 5) -> list:
    """UniProt — Protein-Datenbank (Biologie)."""
    r = requests.get("https://rest.uniprot.org/uniprotkb/search",
                     params={"query": query, "size": max_results, "format": "json"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for e in (r.json().get("results") or []):
        acc = e.get("primaryAccession") or ""
        desc = ((e.get("proteinDescription") or {}).get("recommendedName") or {}).get("fullName") or {}
        name = desc.get("value") or e.get("uniProtkbId") or acc
        organism = ((e.get("organism") or {}).get("scientificName") or "")
        out.append({
            "title": f"{name} ({acc}) — {organism}"[:500],
            "year": _jahr((e.get("entryAudit") or {}).get("firstPublicDate")),
            "doi": "", "url": f"https://www.uniprot.org/uniprotkb/{acc}" if acc else "",
            "pdf_url": "", "source": "UniProt", "citations": 0,
            "abstract": f"Protein-Eintrag, Organismus: {organism}",
            "authors": "",
        })
    return out[:max_results]


@_safe
def suche_chembl(query: str, max_results: int = 5) -> list:
    """ChEMBL — Bioaktivitäts-Datenbank (Bio-Chemie)."""
    r = requests.get("https://www.ebi.ac.uk/chembl/api/data/molecule.json",
                     params={"limit": max_results, "pref_name__isnull": "false",
                             "molecule_chembl_id__startswith": "CHEMBL"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for m in (r.json().get("molecules") or []):
        cid = m.get("molecule_chembl_id") or ""
        name = (m.get("pref_name") or cid)
        out.append({
            "title": f"{name} ({cid}) — bioaktive Verbindung"[:500],
            "year": "", "doi": "",
            "url": f"https://www.ebi.ac.uk/chembl/compound_report_card/{cid}" if cid else "",
            "pdf_url": "", "source": "ChEMBL", "citations": 0,
            "abstract": f"Max. klinische Phase: {m.get('max_phase') or '–'}",
            "authors": "",
        })
    return out[:max_results]


@_safe
def suche_ncbi_gene(query: str, max_results: int = 5) -> list:
    """NCBI Gene — Gen-Datenbank (Genomik)."""
    r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                     params={"db": "gene", "term": query, "retmode": "json",
                             "retmax": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    ids = (r.json().get("esearchresult") or {}).get("idlist") or []
    return [{
        "title": f"NCBI Gene ID {gid} — {query}"[:300],
        "year": "", "doi": "",
        "url": f"https://www.ncbi.nlm.nih.gov/gene/{gid}",
        "pdf_url": "", "source": "NCBI Gene", "citations": 0,
        "abstract": "", "authors": "",
    } for gid in ids][:max_results]


@_safe
def suche_ensembl(query: str, max_results: int = 5) -> list:
    """Ensembl REST — Genom-Datenbank (Genomik)."""
    r = requests.get("https://rest.ensembl.org/lookup/symbol/homo_sapiens/"
                     + requests.utils.quote(query.split()[0] if query else "BRCA1"),
                     params={"content-type": "application/json"},
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    d = r.json()
    gid = d.get("id") or ""
    return [{
        "title": f"Ensembl {gid} — {d.get('display_name', '')} ({d.get('biotype', '')})"[:400],
        "year": "", "doi": "", "url": f"https://www.ensembl.org/id/{gid}" if gid else "",
        "pdf_url": "", "source": "Ensembl", "citations": 0,
        "abstract": f"Chromosom {d.get('seq_region_name', '?')}", "authors": "",
    }][:max_results]


@_safe
def suche_biostudies(query: str, max_results: int = 5) -> list:
    """EBI BioStudies — Labor-/Studiendaten (Life Sciences)."""
    r = requests.get("https://www.ebi.ac.uk/biostudies/api/v1/search",
                     params={"query": query, "pageSize": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for h in (r.json().get("hits") or []):
        titel = (h.get("title") or "").strip()
        if not titel:
            continue
        acc = h.get("accession") or ""
        out.append({
            "title": titel[:500], "year": _jahr(h.get("releaseTime")),
            "doi": "", "url": f"https://www.ebi.ac.uk/biostudies/studies/{acc}" if acc else "",
            "pdf_url": "", "source": "EBI BioStudies", "citations": 0,
            "abstract": "", "authors": (h.get("author") or "")[:300],
        })
    return out[:max_results]


# ══════════════ CS / SOFTWARE ══════════════

@_safe
def suche_openreview(query: str, max_results: int = 5) -> list:
    """OpenReview — AI/ML-Konferenz-Papers (NeurIPS, ICLR …)."""
    r = requests.get("https://api2.openreview.net/notes/search",
                     params={"term": query, "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for n in (r.json().get("notes") or []):
        c = n.get("content") or {}
        titel = (c.get("title") or {}).get("value") or ""
        if not titel:
            continue
        out.append({
            "title": titel[:500],
            "year": _jahr(c.get("pdate") or c.get("cdate")),
            "doi": (c.get("doi") or {}).get("value", "") if isinstance(c.get("doi"), dict) else "",
            "url": f"https://openreview.net/forum?id={n.get('id', '')}",
            "pdf_url": "", "source": "OpenReview", "citations": 0,
            "abstract": ((c.get("abstract") or {}).get("value") or "")[:1000],
            "authors": ", ".join((c.get("authors") or {}).get("value") or [])[:300],
        })
    return out[:max_results]


@_safe
def suche_huggingface(query: str, max_results: int = 5) -> list:
    """HuggingFace Daily Papers — aktuelle AI-Forschung."""
    r = requests.get("https://huggingface.co/api/daily_papers",
                     params={"limit": max_results}, headers=HEADERS, timeout=TIMEOUT)
    out = []
    for p in (r.json() or []):
        paper = p.get("paper") or {}
        titel = (paper.get("title") or p.get("title") or "").strip()
        if not titel:
            continue
        if query.lower() not in titel.lower() and query.lower() not in (paper.get("summary") or "").lower():
            continue  # Filter (API hat keine Suche)
        out.append({
            "title": titel[:500], "year": _jahr(p.get("publishedAt")),
            "doi": (paper.get("doi") or "").replace("https://doi.org/", ""),
            "url": f"https://huggingface.co/papers/{paper.get('id', '')}",
            "pdf_url": "", "source": "HuggingFace Papers", "citations": 0,
            "abstract": (paper.get("summary") or "")[:1000],
            "authors": ", ".join(a.get("name", "") for a in (paper.get("authors") or [])[:10])[:300],
        })
    return out[:max_results]


@_safe
def suche_github(query: str, max_results: int = 5) -> list:
    """GitHub — Forschungs-Software/Code (Davids Wunsch: 'Geachhab dabei')."""
    r = requests.get("https://api.github.com/search/repositories",
                     params={"q": query, "per_page": max_results, "sort": "stars"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for repo in (r.json().get("items") or []):
        name = repo.get("full_name") or ""
        if not name:
            continue
        out.append({
            "title": f"{name} — {repo.get('description') or 'Repository'}"[:500],
            "year": _jahr(repo.get("created_at")),
            "doi": "", "url": repo.get("html_url") or "",
            "pdf_url": "", "source": "GitHub",
            "citations": int(repo.get("stargazers_count") or 0),
            "abstract": (repo.get("description") or "")[:500],
            "authors": (repo.get("owner") or {}).get("login", ""),
        })
    return out[:max_results]


@_safe
def suche_gitlab(query: str, max_results: int = 5) -> list:
    """GitLab — Forschungs-Software (offene Instanz)."""
    r = requests.get("https://gitlab.com/api/v4/projects",
                     params={"search": query, "per_page": max_results,
                             "order_by": "star_count"},
                     headers=HEADERS, timeout=TIMEOUT)
    d = r.json()
    if not isinstance(d, list):
        return []
    return [{
        "title": f"{p.get('path_with_namespace', '')} — {(p.get('description') or 'Projekt')}"[:500],
        "year": _jahr(p.get("created_at")), "doi": "",
        "url": p.get("web_url") or "", "pdf_url": "", "source": "GitLab",
        "citations": int(p.get("star_count") or 0),
        "abstract": (p.get("description") or "")[:500], "authors": "",
    } for p in d][:max_results]


@_safe
def suche_pypi(query: str, max_results: int = 5) -> list:
    """PyPI — Python-Pakete (Forschungs-Software)."""
    r = requests.get(f"https://pypi.org/pypi/{requests.utils.quote(query.split()[0])}/json",
                     headers=HEADERS, timeout=TIMEOUT)
    if r.status_code != 200:
        return []
    info = r.json().get("info") or {}
    return [{
        "title": f"{info.get('name', '')} {info.get('version', '')} — {(info.get('summary') or '')}"[:400],
        "year": "", "doi": "", "url": info.get("package_url") or "",
        "pdf_url": "", "source": "PyPI", "citations": 0,
        "abstract": (info.get("description") or "")[:500],
        "authors": (info.get("author") or "")[:200],
    }][:max_results]


# ══════════════ MATHEMATIK ══════════════

@_safe
def suche_zbmath(query: str, max_results: int = 5) -> list:
    """zbMATH Open — Mathematik-Literatur."""
    r = requests.get("https://api.zbmath.org/v1/document/_search",
                     params={"search_string": query, "results_per_page": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("result") or []):
        titel = ((d.get("title") or {}).get("title") or "").strip()
        if not titel:
            continue
        out.append({
            "title": titel[:500], "year": _jahr(d.get("year")),
            "doi": (d.get("doi") or "").replace("https://doi.org/", ""),
            "url": f"https://zbmath.org/{d.get('identifier', '')}",
            "pdf_url": "", "source": "zbMATH", "citations": 0,
            "abstract": "", "authors": ", ".join(
                a.get("name", "") for a in (d.get("contributors") or {}).get("authors", [])[:10])[:300],
        })
    return out[:max_results]


@_safe
def suche_oeis(query: str, max_results: int = 5) -> list:
    """OEIS — Zahlenfolgen (Mathematik)."""
    r = requests.get("https://oeis.org/search",
                     params={"q": query, "fmt": "json"}, headers=HEADERS, timeout=TIMEOUT)
    data = r.json()
    results = data.get("results") if isinstance(data, dict) else data
    out = []
    for e in (results or [])[:max_results]:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        anum = e.get("number") or e.get("id") or ""
        out.append({
            "title": f"A{anum}: {name}"[:400], "year": _jahr(e.get("created")),
            "doi": "", "url": f"https://oeis.org/A{anum}" if anum else "",
            "pdf_url": "", "source": "OEIS", "citations": 0,
            "abstract": (e.get("data") or "")[:300], "authors": "",
        })
    return out[:max_results]


# ══════════════ DATEN / WISSEN / BÜCHER ══════════════

@_safe
def suche_dryad(query: str, max_results: int = 5) -> list:
    """Dryad — Forschungsdaten (Ökologie/Evolution)."""
    r = requests.get("https://datadryad.org/api/v2/search",
                     params={"q": query, "per_page": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in ((r.json().get("_embedded") or {}).get("stash:datasets") or []):
        titel = (d.get("title") or "").strip()
        if not titel:
            continue
        doi = (d.get("identifier") or "").replace("doi:", "")
        out.append({
            "title": titel[:500], "year": _jahr(d.get("publicationDate")),
            "doi": doi, "url": f"https://doi.org/{doi}" if doi else "",
            "pdf_url": "", "source": "Dryad", "citations": 0,
            "abstract": (d.get("abstract") or "")[:800],
            "authors": ", ".join(a.get("familyName", "") for a in
                                 (d.get("authors") or [])[:10])[:300],
        })
    return out[:max_results]


@_safe
def suche_wikidata(query: str, max_results: int = 5) -> list:
    """Wikidata — strukturiertes Weltwissen (Fakten/Entitäten)."""
    r = requests.get("https://www.wikidata.org/w/api.php",
                     params={"action": "wbsearchentities", "search": query,
                             "language": "de", "uselang": "de",
                             "format": "json", "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for e in (r.json().get("search") or []):
        label = (e.get("label") or "").strip()
        if not label:
            continue
        qid = e.get("id") or ""
        out.append({
            "title": f"{label} ({qid}) — {(e.get('description') or '')}"[:400],
            "year": "", "doi": "", "url": f"https://www.wikidata.org/wiki/{qid}",
            "pdf_url": "", "source": "Wikidata", "citations": 0,
            "abstract": (e.get("description") or "")[:300], "authors": "",
        })
    return out[:max_results]


@_safe
def suche_openlibrary(query: str, max_results: int = 5) -> list:
    """Open Library — Bücher (Standardwerk-Suche)."""
    r = requests.get("https://openlibrary.org/search.json",
                     params={"q": query, "limit": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("docs") or []):
        titel = (d.get("title") or "").strip()
        if not titel:
            continue
        out.append({
            "title": f"{titel} — {', '.join((d.get('author_name') or [])[:3])}"[:400],
            "year": str(d.get("first_publish_year") or ""),
            "doi": "", "url": f"https://openlibrary.org{d.get('key', '')}",
            "pdf_url": "", "source": "Open Library", "citations": 0,
            "abstract": "", "authors": ", ".join((d.get("author_name") or [])[:5])[:300],
        })
    return out[:max_results]


@_safe
def suche_internetarchive(query: str, max_results: int = 5) -> list:
    """Internet Archive — Bücher/Archive/Medien."""
    r = requests.get("https://archive.org/advancedsearch.php",
                     params={"q": query, "fl[]": ["identifier", "title", "year"],
                             "rows": max_results, "output": "json"},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in ((r.json().get("response") or {}).get("docs") or []):
        ident = d.get("identifier") or ""
        titel = d.get("title")
        if isinstance(titel, list):
            titel = titel[0] if titel else ""
        if not titel:
            continue
        out.append({
            "title": f"{titel} — {ident}"[:400],
            "year": _jahr(d.get("year")), "doi": "",
            "url": f"https://archive.org/details/{ident}" if ident else "",
            "pdf_url": "", "source": "Internet Archive", "citations": 0,
            "abstract": "", "authors": "",
        })
    return out[:max_results]


# ══════════════ REGISTRY ══════════════

EXTRA_QUELLEN_2 = {
    # Medizin / Biologie / Labor
    "clinicaltrials": suche_clinicaltrials,
    "uniprot": suche_uniprot,
    "chembl": suche_chembl,
    "ncbi_gene": suche_ncbi_gene,
    "ensembl": suche_ensembl,
    "biostudies": suche_biostudies,
    # CS / Software
    "openreview": suche_openreview,
    "huggingface": suche_huggingface,
    "github": suche_github,
    "gitlab": suche_gitlab,
    "pypi": suche_pypi,
    # Mathematik
    "zbmath": suche_zbmath,
    "oeis": suche_oeis,
    # Daten / Wissen / Bücher
    "dryad": suche_dryad,
    "wikidata": suche_wikidata,
    "openlibrary": suche_openlibrary,
    "internetarchive": suche_internetarchive,
}

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "bentonite clay"
    for name, fn in EXTRA_QUELLEN_2.items():
        treffer = fn(thema, 3)
        print(f"[{name}] {len(treffer)} Treffer")
        for t in treffer[:2]:
            print(f"   - {t['title'][:62]}")
