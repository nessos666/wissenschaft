"""Zitations-Snowballing (Verbesserung 5) — klassische + neue Schlüsselwerke.

Rückwärts (Referenzen): CrossRef /works/{doi} → reference-Liste (funktioniert
key-frei). Vorwärts (zitiert von): Semantic Scholar /citations (Fallback —
klappt nicht für alle DOIs; schlägt still fehl).

Nur bei Tiefe 'tief' für die Top-N-Treffer. Ergebnisse werden im
_norm-Format zurückgegeben (wie sources/papersearch).
"""
import re
import urllib.parse

import requests

TIMEOUT = 25
HEADERS = {"User-Agent": "WissenschaftTool/4.0 (+https://github.com/nessos666; mailto:kontakt@wissenshaft.tool)"}


def _doi_sauber(doi: str) -> str:
    return (doi or "").replace("https://doi.org/", "").strip()


def hole_referenzen(doi: str, max_refs: int = 8) -> list:
    """Rückwärts: Referenzen eines Papers (CrossRef). Nie crashen."""
    doi = _doi_sauber(doi)
    if not doi:
        return []
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}",
                         headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return []
        refs = (r.json().get("message") or {}).get("reference") or []
        out = []
        for x in refs:
            if not isinstance(x, dict):
                continue
            ref_doi = _doi_sauber(x.get("DOI") or "")
            titel = (x.get("article-title") or x.get("unstructured")
                     or x.get("volume-title") or "").strip()
            if not titel and not ref_doi:
                continue
            out.append({
                "title": titel[:400] or f"Referenz {ref_doi}",
                "year": str(x.get("year") or "")[:4],
                "doi": ref_doi,
                "url": f"https://doi.org/{ref_doi}" if ref_doi else "",
                "pdf_url": "", "source": "CrossRef-Snowball",
                "citations": 0, "abstract": "", "authors": "",
            })
            if len(out) >= max_refs:
                break
        return out
    except Exception:
        return []


def hole_citing(doi: str, max_citing: int = 8, arxiv_id: str = "") -> list:
    """Vorwärts: Paper die dieses zitieren (Semantic Scholar). Nie crashen.

    Versucht DOI- und arXiv-ID-Format; gibt leere Liste zurück wenn die
    API das Paper nicht kennt (z.B. Buchkapitel).
    """
    ids = []
    d = _doi_sauber(doi)
    if d:
        ids.append(f"DOI:{urllib.parse.quote(d, safe='')}")
    if arxiv_id:
        ids.append(f"arXiv:{arxiv_id}")
    for paper_id in ids:
        try:
            r = requests.get(
                f"https://api.semanticscholar.org/graph/v1/paper/"
                f"{paper_id}/citations",
                params={"fields": "title,doi,year,abstract,authors,externalIds",
                        "limit": max_citing},
                headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            out = []
            for x in (r.json().get("data") or []):
                p = x.get("citingPaper") or {}
                titel = (p.get("title") or "").strip()
                if not titel:
                    continue
                doi_c = _doi_sauber((p.get("externalIds") or {}).get("DOI") or "")
                autoren = ", ".join(a.get("name", "") for a in
                                    (p.get("authors") or [])[:10])
                out.append({
                    "title": titel[:400],
                    "year": str(p.get("year") or "")[:4],
                    "doi": doi_c,
                    "url": f"https://doi.org/{doi_c}" if doi_c else "",
                    "pdf_url": "", "source": "S2-Snowball",
                    "citations": 0,
                    "abstract": (p.get("abstract") or "")[:1000],
                    "authors": autoren[:300],
                })
            if out:
                return out
        except Exception:
            continue
    return []


def snowball(treffer: list, max_seeds: int = 3, pro_seed: int = 6) -> list:
    """Für die Top-N-Treffer Referenzen (rückwärts) + Citing (vorwärts) holen.

    Liefert zusätzliche Papers im _norm-Format. Nie crashen.
    """
    zusatz = []
    for t in (treffer or [])[:max_seeds]:
        if not isinstance(t, dict):
            continue
        doi = t.get("doi") or ""
        if not doi:
            continue
        zusatz.extend(hole_referenzen(doi, max_refs=pro_seed))
        # arXiv-ID aus url ableiten (falls vorhanden) — für S2
        arxiv_id = ""
        url = t.get("url") or ""
        m = re.search(r"arxiv\.org/abs/([\d.]+)", url)
        if m:
            arxiv_id = m.group(1)
        zusatz.extend(hole_citing(doi, max_citing=pro_seed, arxiv_id=arxiv_id))
    return zusatz


if __name__ == "__main__":
    import sys
    doi = sys.argv[1] if len(sys.argv) > 1 else "10.1093/oxfordhb/9780192898357.013.38"
    refs = hole_referenzen(doi)
    print(f"Referenzen (rückwärts): {len(refs)}")
    for r in refs[:5]:
        print(f"  - {r['title'][:65]} ({r['year']})")
    cit = hole_citing(doi)
    print(f"Zitierend (vorwärts): {len(cit)}")
    for c in cit[:5]:
        print(f"  - {c['title'][:65]} ({c['year']})")
