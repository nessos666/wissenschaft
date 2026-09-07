"""Searcher — echter Such-Zugang für den Researcher-Agent (Block 2).

Fragt key-freie wissenschaftliche APIs direkt ab (keine externe JSON-Datei
nötig). Quellen: OpenAlex (breiteste Abdeckung) + arXiv (Preprints/CS/ML).
Muster aus SUCHER-1000: harte Timeouts, defensive Parser, nie crashen.

Feld-Standard (Pipeline-Vertrag):
  title, year, doi (nackt, ohne https://doi.org/), url, pdf_url,
  source, citations, abstract, authors
"""
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

TIMEOUT_S = 12


def _open(url: str, timeout: int = TIMEOUT_S):
    """Netz-Zugriff — Test-Hook (Tests ersetzen _open)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Wissenschaft-Recherche/1.0 (akademische Suche)"})
    return urllib.request.urlopen(req, timeout=timeout)


def _as_str(value) -> str:
    if value is None:
        return ""
    return str(value) if not isinstance(value, str) else value


def _as_int(value, default: int = 0) -> int:
    if value is None or isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _norm_doi(doi: str) -> str:
    """Volle DOI-URL → nackte DOI (10.xxxx/...)."""
    d = _as_str(doi).strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if d.lower().startswith(prefix):
            return d[len(prefix):]
    return d


# ---------- OpenAlex ----------

def _parse_openalex(data: dict) -> list[dict]:
    """OpenAlex /works-Antwort → standardisierte Dicts."""
    out = []
    for r in (data.get("results") or []):
        if not isinstance(r, dict):
            continue
        title = _as_str(r.get("title"))[:500]
        if not title:
            continue
        authors = ", ".join(
            a.get("author", {}).get("display_name", "")
            for a in (r.get("authorships") or [])
            if isinstance(a, dict) and isinstance(a.get("author"), dict)
        )[:300]
        loc = r.get("primary_location")
        pdf_url = ""
        landing = ""
        if isinstance(loc, dict):
            pdf_url = _as_str(loc.get("pdf_url"))
            landing = _as_str(loc.get("landing_page_url"))
        out.append({
            "title": title,
            "year": r.get("publication_year"),
            "doi": _norm_doi(r.get("doi")),
            "url": landing or r.get("id", ""),
            "pdf_url": pdf_url,
            "source": "OpenAlex",
            "citations": _as_int(r.get("cited_by_count")),
            "abstract": _as_str(r.get("abstract_inverted_index"))[:0],  # Abstract ist invertiert — Roh nicht nutzbar
            "authors": authors,
        })
    return out


# ---------- arXiv ----------

def _parse_arxiv(xml_text: str) -> list[dict]:
    """arXiv-Atom-XML → standardisierte Dicts."""
    out = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("a:entry", ns):
        title = _as_str(entry.findtext("a:title", "", ns)).strip()
        title = re.sub(r"\s+", " ", title)
        if not title:
            continue
        published = _as_str(entry.findtext("a:published", "", ns))
        year = published[:4] if len(published) >= 4 else ""
        link_id = _as_str(entry.findtext("a:id", "", ns))
        authors = ", ".join(
            _as_str(a.findtext("a:name", "", ns))
            for a in entry.findall("a:author", ns)
        )[:300]
        abstract = _as_str(entry.findtext("a:summary", "", ns))
        abstract = re.sub(r"\s+", " ", abstract).strip()[:2000]
        out.append({
            "title": title[:500],
            "year": year,
            "doi": "",
            "url": link_id,
            "pdf_url": link_id.replace("/abs/", "/pdf/") + ".pdf" if link_id else "",
            "source": "arXiv",
            "citations": 0,
            "abstract": abstract,
            "authors": authors,
        })
    return out


# ---------- Haupt-Suche ----------

def search(query: str, max_results: int = 8) -> list[dict]:
    """Durchsucht key-freie APIs (OpenAlex + arXiv) parallel-sequenziell.

    Liefert IMMER eine Liste (nie None/crash): Quelle down/leer → andere liefert.
    """
    if not query or not query.strip():
        return []
    q = urllib.parse.quote(query.strip())
    ergebnisse = []

    # 1) OpenAlex (breiteste wissenschaftliche Abdeckung)
    try:
        url = (f"https://api.openalex.org/works?search={q}"
               f"&per-page={max_results}&mailto=recherche@example.org")
        with _open(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ergebnisse.extend(_parse_openalex(data))
    except Exception:
        pass  # OpenAlex down → arXiv liefert weiter (nie crashen)

    # 2) arXiv (Preprints, CS/ML/Physik)
    if len(ergebnisse) < max_results:
        try:
            url = (f"http://export.arxiv.org/api/query?search_query="
                   f"all:{q}&start=0&max_results={max_results}")
            with _open(url) as resp:
                xml_text = resp.read().decode("utf-8")
            ergebnisse.extend(_parse_arxiv(xml_text))
        except Exception:
            pass

    return ergebnisse[:max_results]


if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "quantum computing"
    treffer = search(thema, max_results=5)
    print(f"Suche '{thema}': {len(treffer)} Treffer")
    for t in treffer:
        print(f"  [{t['source']}] {t['title'][:70]} ({t['year']})")
