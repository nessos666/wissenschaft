"""
Deduplicator — Entfernt Duplikate per DOI-Match und Titel-Fuzzy-Match.
"""
import re
from difflib import SequenceMatcher
from dataclasses import dataclass, field

@dataclass
class SearchResult:
    title: str = ""
    authors: str = ""
    year: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    source: str = ""
    citations: int = 0
    is_oa: bool = False
    pdf_url: str = ""
    relevance_note: str = ""
    quality_note: str = ""
    merged_from: list[str] = field(default_factory=list)
    trust_score: float = 0.5


def _as_str(value, default: str = "") -> str:
    """Wert robust in str wandeln — None/int/Dict → default oder str()."""
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _as_int(value, default: int = 0) -> int:
    """Wert robust in int wandeln — 'abc'/Dict/None → default."""
    if value is None:
        return default
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def searchresult_from_dict(r) -> SearchResult:
    """Dict → SearchResult mit defensiver Normalisierung (Block 3).

    Die Pipeline-Grenzen (orchestrator, verifier_agent) bekommen rohe externe
    Daten — Einträge können Nicht-Dict sein (String), Felder int/None/Dict
    statt str, Zitationen nicht-numerisch. NIE crashen (Muster: SUCHER-
    OpenAIRE-Fix). Nicht-Dict-Einträge → None (Aufrufer überspringt).
    """
    if not isinstance(r, dict):
        return None
    return SearchResult(
        title=_as_str(r.get("title"))[:500],
        authors=_as_str(r.get("authors")),
        year=_as_str(r.get("year"))[:20],
        doi=_as_str(r.get("doi")),
        url=_as_str(r.get("url")),
        pdf_url=_as_str(r.get("pdf_url")),
        source=_as_str(r.get("source"), "Unknown")[:50],
        citations=_as_int(r.get("citations")),
        is_oa=bool(r.get("is_oa", False)),
        abstract=_as_str(r.get("abstract"))[:2000],
    )


def normalize_title(title: str) -> str:
    """Normalisiert Titel für Vergleich."""
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def title_similarity(t1: str, t2: str) -> float:
    """Berechnet Ähnlichkeit zweier Titel."""
    return SequenceMatcher(None, normalize_title(t1), normalize_title(t2)).ratio()

def _merge_duplikat(ziel: "SearchResult", dup: "SearchResult") -> None:
    """Füllt leere Felder aus dem Duplikat (first-non-empty je Feld).

    Abschluss-Review F2: vorher gingen pdf_url/url/authors/year/is_oa der
    späteren (oft reicheren) Quelle verloren — nur abstract+citations wurden
    gemerged. Jetzt: alle Felder, je Feld das erste Nicht-Leere gewinnt.
    """
    ziel.merged_from.append(dup.source)
    if len(dup.abstract) > len(ziel.abstract):
        ziel.abstract = dup.abstract
    if dup.citations > ziel.citations:
        ziel.citations = dup.citations
    for feld in ("pdf_url", "url", "authors", "year", "doi"):
        if not getattr(ziel, feld) and getattr(dup, feld):
            setattr(ziel, feld, getattr(dup, feld))
    if dup.is_oa and not ziel.is_oa:
        ziel.is_oa = True


# Preprint-Server (Verbesserung 2): deren Einträge sind oft die Vorab-Version
# eines veröffentlichten Papers (CrossRef/PubMed) — beim Merge verliert der
# Preprint, der Verlagseintrag gewinnt (behält Felder, übernimmt pdf_url).
_PREPRINT_SERVER = {
    "arXiv", "bioRxiv", "medRxiv", "ChemRxiv", "PsyArXiv", "engrXiv",
    "EarthArXiv", "SocArXiv", "AfricArXiv", "SSRN", "Figshare", "Zenodo",
}


def _ist_preprint(r: SearchResult) -> bool:
    return r.source in _PREPRINT_SERVER


def _preprint_gewichtet_besser(a: SearchResult, b: SearchResult) -> bool:
    """True wenn a der bessere (Verlags-)Eintrag ist als b (Preprint)."""
    return (not _ist_preprint(a)) and _ist_preprint(b)


def deduplicate(results: list[SearchResult]) -> list[SearchResult]:
    """Entfernt Duplikate: DOI-Match, dann Preprint→Published (V2), dann
    Titel-Fuzzy (> 0.70).

    Verbesserung 2: Ein arXiv/bioRxiv-Preprint (DOI 10.48550/…) und die
    spätere Verlags-Version (CrossRef/PubMed, anderer DOI) sind dieselbe
    Arbeit. Erkannt über sehr ähnliche Titel (> 0.85) + mindestens ein
    Preprint → der Verlags-Eintrag gewinnt, der Preprint wandert in
    merged_from (pdf_url bleibt erhalten).
    """
    unique: list[SearchResult] = []
    seen_dois: dict[str, SearchResult] = {}

    def _titel_duplikat_finden(r: SearchResult, schwelle: float,
                               nur_preprint_paar: bool = False):
        """Findet existierenden Eintrag mit ähnlichem Titel (für Merge)."""
        for u in unique:
            if title_similarity(r.title, u.title) > schwelle:
                if nur_preprint_paar:
                    # Nur wenn (r oder u) Preprint — sonst kein Kreuz-DOI-Merge
                    if not (_ist_preprint(r) or _ist_preprint(u)):
                        continue
                    # Gleiche Arbeit nur wenn nicht beide aus derselben Quelle
                    # (zwei verschiedene arXiv-Paper mit ähnlichem Titel)
                    if r.source == u.source:
                        continue
                return u
        return None

    for r in results:
        # Stufe 1: DOI-Match
        if r.doi and r.doi in seen_dois:
            _merge_duplikat(seen_dois[r.doi], r)
            continue

        # Stufe 2 (V2): Preprint→Published — verschiedene DOIs, sehr ähnlicher
        # Titel, mindestens ein Preprint → als eine Arbeit behandeln.
        # Der Verlags-Eintrag gewinnt (Preprint wandert in merged_from).
        if r.doi:
            u = _titel_duplikat_finden(r, schwelle=0.85,
                                       nur_preprint_paar=True)
            if u is not None:
                if _preprint_gewichtet_besser(r, u):
                    # r ist Verlag, u ist Preprint → u durch r ersetzen
                    # (Felder von u übernehmen wo r leer ist)
                    _merge_duplikat(r, u)
                    unique[unique.index(u)] = r
                    seen_dois[r.doi] = r
                else:
                    # r ist Preprint (oder gleichrangig) → in u mergen
                    _merge_duplikat(u, r)
                continue

        if r.doi:
            seen_dois[r.doi] = r
            unique.append(r)
            continue

        # Kein DOI — nach Titel-Duplikaten suchen (Fuzzy)
        is_dup = False
        u = _titel_duplikat_finden(r, schwelle=0.70)
        if u is not None:
            _merge_duplikat(u, r)
            is_dup = True

        if not is_dup:
            unique.append(r)

    return unique

if __name__ == "__main__":
    # Quick test
    r1 = SearchResult(title="Fair Value Gap Detection in NQ Futures", doi="10.1234/fvg1", source="OpenAlex")
    r2 = SearchResult(title="Fair Value Gap Detection in NQ Futures", doi="10.1234/fvg1", source="CrossRef")
    r3 = SearchResult(title="Detection of Fair Value Gaps in NASDAQ Futures", doi="", source="Semantic Scholar")
    r4 = SearchResult(title="Machine Learning for Market Microstructure", doi="10.1234/ml1", source="OpenAlex")
    
    results = deduplicate([r1, r2, r3, r4])
    print(f"Vorher: 4, Nachher: {len(results)}")
    for r in results:
        print(f"  {r.title[:50]}... [from: {r.source}{' + ' + ', '.join(r.merged_from) if r.merged_from else ''}]")
