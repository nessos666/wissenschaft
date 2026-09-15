"""Extra-Quellen Runde 4 (Block 2: NCBI- + EBI-Suite, Labor-Datenbanken).

Alle live verifiziert (2026-09):
  NCBI  : Nucleotide (GenBank), Protein, SRA (Sequenzdaten), Assembly, BioProject
  EBI   : ChEBI (Chemie-Ontologie via OLS4), PDBe (Strukturen),
          ENA (Nukleotid-Archiv), OLS4 (Ontologien allgemein)

Davids Wunsch: 'wissenschaftliche Labore überall anknüpfen' — Genomik,
Proteomik, Strukturbiologie, Sequenzdaten.
"""
import re

import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:kontakt@wissenshaft.tool)"}


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


def _eintrag(titel, url, source, jahr="", abstract=""):
    return {"title": (titel or "")[:500], "year": jahr, "doi": "",
            "url": url or "", "pdf_url": "", "source": source,
            "citations": 0, "abstract": (abstract or "")[:800], "authors": ""}


# ══════════ NCBI-Suite (eine Funktion, mehrere Datenbanken) ══════════

_EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# db → (Label, URL-Präfix)
_NCBI_DBS = {
    "nucleotide": ("NCBI Nucleotide", "https://www.ncbi.nlm.nih.gov/nuccore/"),
    "protein": ("NCBI Protein", "https://www.ncbi.nlm.nih.gov/protein/"),
    "sra": ("NCBI SRA", "https://www.ncbi.nlm.nih.gov/sra/"),
    "assembly": ("NCBI Assembly", "https://www.ncbi.nlm.nih.gov/assembly/"),
    "bioproject": ("NCBI BioProject", "https://www.ncbi.nlm.nih.gov/bioproject/"),
    "biosample": ("NCBI BioSample", "https://www.ncbi.nlm.nih.gov/biosample/"),
}


def _ncbi_factory(db: str):
    label, url_prefix = _NCBI_DBS[db]

    @_safe
    def suche(query: str, max_results: int = 5) -> list:
        r = requests.get(_EUTILS, params={"db": db, "term": query,
                                          "retmode": "json", "retmax": max_results},
                         headers=HEADERS, timeout=TIMEOUT)
        ids = (r.json().get("esearchresult") or {}).get("idlist") or []
        return [_eintrag(f"{label} {i} — {query}", f"{url_prefix}{i}", label,
                         abstract=f"{label}-Eintrag (NCBI, Suche: {query})")
                for i in ids][:max_results]
    return suche


# ══════════ EBI-Suite ══════════

@_safe
def suche_chebi(query: str, max_results: int = 5) -> list:
    """ChEBI — chemische Substanzen (via OLS4)."""
    r = requests.get("https://www.ebi.ac.uk/ols4/api/search",
                     params={"q": query, "ontology": "chebi", "rows": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("response", {}).get("docs") or []):
        label = (d.get("label") or "").strip()
        if not label:
            continue
        obo_id = d.get("obo_id") or ""
        out.append(_eintrag(f"ChEBI {obo_id}: {label}",
                            f"https://www.ebi.ac.uk/chebi/searchId.do?chebiId={obo_id}",
                            "ChEBI", abstract=(d.get("description") or [""])[0]
                            if isinstance(d.get("description"), list) else ""))
    return out[:max_results]


@_safe
def suche_pdbe(query: str, max_results: int = 5) -> list:
    """PDBe (EBI) — Protein-Strukturen."""
    r = requests.get("https://www.ebi.ac.uk/pdbe/search/pdb/select",
                     params={"q": query, "wt": "json", "rows": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("response", {}).get("docs") or []):
        pid = (d.get("pdb_id") or "").lower()
        if not pid:
            continue
        titel = d.get("title") or f"PDBe-Struktur {pid}"
        out.append(_eintrag(str(titel)[:400], f"https://www.ebi.ac.uk/pdbe/entry/pdb/{pid}",
                            "PDBe", abstract=f"Struktur {pid.upper()}"))
    return out[:max_results]


@_safe
def suche_ena(query: str, max_results: int = 5) -> list:
    """ENA — European Nucleotide Archive (Sequenzdaten)."""
    r = requests.get("https://www.ebi.ac.uk/ena/portal/api/search",
                     params={"result": "study", "query": f'study_title="{query}"',
                             "limit": max_results, "format": "json"},
                     headers=HEADERS, timeout=TIMEOUT)
    d = r.json()
    rows = d if isinstance(d, list) else []
    return [_eintrag(f"ENA-Studie {x.get('study_accession', '')}: {x.get('study_title', '')}"[:400],
                     f"https://www.ebi.ac.uk/ena/browser/view/{x.get('study_accession', '')}",
                     "ENA") for x in rows][:max_results]


@_safe
def suche_ols4(query: str, max_results: int = 5) -> list:
    """OLS4 — Ontologien allgemein (GO, ChEBI, EFO, …)."""
    r = requests.get("https://www.ebi.ac.uk/ols4/api/search",
                     params={"q": query, "rows": max_results},
                     headers=HEADERS, timeout=TIMEOUT)
    out = []
    for d in (r.json().get("response", {}).get("docs") or []):
        label = (d.get("label") or "").strip()
        if not label:
            continue
        obo_id = d.get("obo_id") or d.get("short_form") or ""
        out.append(_eintrag(f"{d.get('ontology_name', '')}: {label} ({obo_id})",
                            d.get("iri") or "", "OLS4"))
    return out[:max_results]


# ══════════ REGISTRY ══════════

EXTRA_QUELLEN_4 = {db: _ncbi_factory(db) for db in _NCBI_DBS}
EXTRA_QUELLEN_4.update({
    "chebi": suche_chebi,
    "pdbe": suche_pdbe,
    "ena": suche_ena,
    "ols4": suche_ols4,
})

if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "clay mineral"
    for name, fn in EXTRA_QUELLEN_4.items():
        print(f"[{name}] {len(fn(thema, 3))}")
