"""Searcher — echter Such-Zugang für den Researcher-Agent (Block 2).

Fragt key-freie wissenschaftliche APIs direkt ab (keine externe JSON-Datei
nötig). Quellen: OpenAlex (breiteste Abdeckung) + arXiv (Preprints/CS/ML).
Muster aus SUCHER-1000: harte Timeouts, defensive Parser, nie crashen.

Feld-Standard (Pipeline-Vertrag):
  title, year, doi (nackt, ohne https://doi.org/), url, pdf_url,
  source, citations, abstract, authors
"""
import json
import os
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


# ---------- CrossRef (Primärquelle, DOI-Registrierung) ----------

def _parse_crossref(data: dict) -> list[dict]:
    """CrossRef /works-Antwort → standardisierte Dicts (Block: OpenAlex-Ersatz).

    OpenAlex hat 2025 ein Budget-System eingeführt (freier Pool oft erschöpft,
    HTTP 429 '$0 remaining'); CrossRef ist die DOI-Registrierungsstelle —
    key-frei, großzügige Limits, relevanz-sortierte query-Suche.
    """
    out = []
    for r in ((data.get("message") or {}).get("items") or []):
        if not isinstance(r, dict):
            continue
        title = _as_str((r.get("title") or [""])[0])[:500]
        if not title:
            continue
        authors = ", ".join(
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in (r.get("author") or [])
            if isinstance(a, dict)
        )[:300]
        jahr = None
        for k in ("published-print", "published-online", "issued"):
            dp = (r.get(k) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                jahr = dp[0][0]
                break
        # Abstract liegt als JATS-XML vor — nur grob säubern, Rohtext-Bestand
        abstr = _as_str(r.get("abstract"))[:1000]
        out.append({
            "title": title,
            "year": jahr,
            "doi": _norm_doi(r.get("DOI")),
            "url": _as_str(r.get("URL")) or f"https://doi.org/{r.get('DOI', '')}",
            "pdf_url": "",
            "source": "CrossRef",
            "citations": _as_int(r.get("is-referenced-by-count")),
            "abstract": abstr,
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
    log_hinweise = []

    # 1) CrossRef (Primärquelle — DOI-Registrierung, key-frei, relevanz-sortiert)
    try:
        mail = os.environ.get("WISSENSCHAFT_MAIL", "kontakt@wissenshaft.tool")
        url = (f"https://api.crossref.org/works?query={q}"
               f"&rows={max_results}&select=DOI,title,author,issued,abstract,URL,is-referenced-by-count"
               f"&mailto={urllib.parse.quote(mail)}")
        with _open(url) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        ergebnisse.extend(_parse_crossref(data))
    except Exception as e:
        # Nie crashen — aber Fehler sichtbar machen (nicht mehr still verschlucken)
        log_hinweise.append(f"CrossRef-Fehler: {type(e).__name__}: {e}")

    # 2) arXiv (Preprints, CS/ML/Physik) — nur auffüllen, wenn CrossRef zu wenig
    if len(ergebnisse) < max_results:
        try:
            url = (f"http://export.arxiv.org/api/query?search_query="
                   f"all:{q}&start=0&max_results={max_results}")
            with _open(url) as resp:
                xml_text = resp.read().decode("utf-8")
            arxiv_treffer = _parse_arxiv(xml_text)
            # arXiv nicht über CrossRef-Ergebnisse legen (die sind relevanter)
            vorhandene_dois = {e.get("doi") for e in ergebnisse}
            for t in arxiv_treffer:
                if len(ergebnisse) >= max_results:
                    break
                if t.get("doi") and t.get("doi") in vorhandene_dois:
                    continue
                ergebnisse.append(t)
        except Exception as e:
            log_hinweise.append(f"arXiv-Fehler: {type(e).__name__}: {e}")

    ergebnisse[:] = ergebnisse[:max_results]
    if log_hinweise:
        import logging
        logging.getLogger("sucher").warning(" | ".join(log_hinweise))
    return ergebnisse


if __name__ == "__main__":
    import sys
    thema = sys.argv[1] if len(sys.argv) > 1 else "quantum computing"
    treffer = search(thema, max_results=5)
    print(f"Suche '{thema}': {len(treffer)} Treffer")
    for t in treffer:
        print(f"  [{t['source']}] {t['title'][:70]} ({t['year']})")
