"""
Formatter V2 — Markdown, BibTeX, RIS, JSON Export + DOI-Verifikation + UNVERIFIED-Marker
"""
import json, re, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
from deduplicator import SearchResult

def verify_doi(doi: str, timeout: int = 5) -> dict:
    """Prüft DOI gegen CrossRef API. Returns {valid: bool, title: str, error: str}."""
    if not doi:
        return {"valid": False, "title": "", "error": "Kein DOI"}
    try:
        url = f"https://api.crossref.org/works/{doi}"
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes/1.0 (mailto:david@example.com)"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        title = data.get("message", {}).get("title", [""])[0]
        return {"valid": True, "title": title, "error": None}
    except urllib.error.HTTPError as e:
        return {"valid": False, "title": "", "error": f"HTTP {e.code}"}
    except Exception as e:
        return {"valid": False, "title": "", "error": str(e)[:100]}


def format_results(query, depth, sources_used, results, domain_guess="", next_searches=None, source_status=None):
    """Formatiert Ergebnisse als Markdown-Report mit Quellenstatus."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    lines = [
        f"# Wissenschaftliche Recherche: _{query}_",
        "",
        f"**Datum:** {now} | **Modus:** {depth} | **Domain:** {domain_guess}",
        f"**Quellen:** {', '.join(sources_used)}",
        f"**Ergebnisse:** {len(results)} (nach Deduplizierung)",
    ]
    
    if source_status:
        lines.append("")
        lines.append("### 📡 Quellenstatus")
        lines.append("")
        lines.append("| Quelle | Status | Ergebnisse |")
        lines.append("|--------|--------|------------|")
        for src, info in source_status.items():
            if info.get("ok"): icon, label = "✅", "OK"
            elif info.get("degraded"): icon, label = "⚠️", "degraded"
            else: icon, label = "❌", info.get("status", "Fehler")
            lines.append(f"| {src} | {icon} {label} | {info.get('count', 0)} |")
        lines.append("")
    
    lines.extend(["", "---", ""])
    
    if results:
        lines.append("## 📋 Ergebnisübersicht")
        lines.append("")
        for i, r in enumerate(results[:5], 1):
            verified = "✅" if getattr(r, 'doi_verified', False) else ("⚠️" if getattr(r, 'doi', '') else "")
            oa_badge = "🟢 OA" if r.is_oa else "🔒"
            cit_str = f" — {r.citations} Zit." if r.citations > 0 else ""
            lines.append(f"{i}. {verified} **{r.title}** ({r.year}){cit_str} {oa_badge}")
        lines.append("")
    
    lines.extend(["---", "", "## 📄 Detail-Ergebnisse", ""])
    
    for i, r in enumerate(results[:30], 1):
        lines.append(f"### {i}. {r.title}")
        lines.append("")
        if r.authors: lines.append(f"**Autoren:** {r.authors}")
        if r.year: lines.append(f"**Jahr:** {r.year}")
        if r.doi:
            verified_mark = " ✅ verifiziert" if getattr(r, 'doi_verified', False) else " ⚠️ UNVERIFIED"
            lines.append(f"**DOI:** [{r.doi}](https://doi.org/{r.doi}){verified_mark}")
        if r.url and not r.doi: lines.append(f"**URL:** {r.url}")
        if r.citations > 0: lines.append(f"**Zitationen:** {r.citations}")
        if r.is_oa: lines.append("**Open Access:** ✅ Ja")
        if r.pdf_url: lines.append(f"**PDF:** {r.pdf_url}")
        lines.append(f"**Quelle:** {r.source}")
        lines.append("")
        if r.abstract:
            abstract = r.abstract[:500] + ("..." if len(r.abstract) > 500 else "")
            lines.append(f"> {abstract}")
            lines.append("")
        if r.relevance_note:
            lines.append(f"💡 **Relevanz:** {r.relevance_note}")
            lines.append("")
        if r.quality_note:
            lines.append(f"⭐ **Qualität:** {r.quality_note}")
            lines.append("")
        if r.merged_from:
            lines.append(f"_Auch gefunden in: {', '.join(r.merged_from)}_")
            lines.append("")
        lines.append("---")
        lines.append("")
    
    lines.append("## 🔍 Verwendete Quellen")
    lines.append("")
    for s in sources_used: lines.append(f"- {s}")
    lines.append("")
    
    if next_searches:
        lines.append("## 💡 Vorschläge für weitere Suchen")
        lines.append("")
        for ns in next_searches: lines.append(f"- `{ns}`")
        lines.append("")
    
    lines.append("---")
    lines.append(f"_Generiert von Hermes /wissenschaft — {now}_")
    
    return "\n".join(lines)


# === EXPORT-FORMATE ===

def export_bibtex(results: list[SearchResult]) -> str:
    """Exportiert Ergebnisse als BibTeX."""
    entries = []
    for i, r in enumerate(results):
        citekey = f"hermes_{r.year or '0000'}_{r.doi.split('/')[-1] if r.doi else f'ref{i+1}'}"
        citekey = re.sub(r'[^a-zA-Z0-9_]', '_', citekey)[:50]
        entry = [f"@article{{{citekey},"]
        if r.authors: entry.append(f"  author = {{{r.authors}}},")
        entry.append(f"  title = {{{r.title}}},")
        if r.year: entry.append(f"  year = {{{r.year}}},")
        if r.doi: entry.append(f"  doi = {{{r.doi}}},")
        if r.url: entry.append(f"  url = {{{r.url}}},")
        entry.append(f"  note = {{Source: {r.source}}}")
        entry.append("}")
        entries.append("\n".join(entry))
    return "\n\n".join(entries)


def export_ris(results: list[SearchResult]) -> str:
    """Exportiert Ergebnisse als RIS (EndNote/Zotero)."""
    entries = []
    for r in results:
        entry = ["TY  - JOUR"]
        entry.append(f"TI  - {r.title}")
        if r.authors:
            for a in r.authors.split(";"):
                entry.append(f"AU  - {a.strip()}")
        if r.year: entry.append(f"PY  - {r.year}")
        if r.doi: entry.append(f"DO  - {r.doi}")
        if r.url: entry.append(f"UR  - {r.url}")
        if r.abstract: entry.append(f"AB  - {r.abstract[:200]}")
        entry.append(f"N1  - Source: {r.source}")
        entry.append("ER  - ")
        entries.append("\n".join(entry))
    return "\n\n".join(entries)


def export_json(results: list[SearchResult]) -> str:
    """Exportiert Ergebnisse als strukturiertes JSON."""
    data = []
    for r in results:
        data.append({
            "title": r.title,
            "authors": r.authors,
            "year": r.year,
            "doi": r.doi,
            "url": r.url,
            "citations": r.citations,
            "is_oa": r.is_oa,
            "pdf_url": r.pdf_url,
            "source": r.source,
            "abstract": r.abstract[:500] if r.abstract else "",
            "doi_verified": getattr(r, 'doi_verified', False),
        })
    return json.dumps(data, indent=2, ensure_ascii=False)


def save_report(markdown, query):
    out_dir = Path.home() / "HAUPTLAGER" / "07_SYSTEM" / "33_System_Reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query[:50])
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{safe_query.strip().replace(' ', '-')}.md"
    filepath = out_dir / filename
    filepath.write_text(markdown, encoding='utf-8')
    return str(filepath)


def save_exports(query, results, base_dir=None):
    """Speichert Markdown + BibTeX + RIS + JSON."""
    if base_dir is None:
        base_dir = Path.home() / "HAUPTLAGER" / "07_SYSTEM" / "33_System_Reports"
    elif isinstance(base_dir, str):
        base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query[:50])
    date_str = datetime.now().strftime("%Y-%m-%d")
    prefix = f"{date_str}-{safe_query.strip().replace(' ', '-')}"
    
    paths = {}
    for ext, content, label in [
        (".md", format_results(query, "standard", [], results), "Markdown"),
        (".bib", export_bibtex(results), "BibTeX"),
        (".ris", export_ris(results), "RIS"),
        (".json", export_json(results), "JSON"),
    ]:
        path = base_dir / f"{prefix}{ext}"
        path.write_text(content, encoding='utf-8')
        paths[label] = str(path)
    return paths


def generate_next_searches(query, domain, results):
    suggestions = []
    if domain == "trading":
        suggestions.extend([f"{query} machine learning model", f"{query} empirical study", f"{query} systematic review"])
    elif domain == "medicine":
        suggestions.extend([f"{query} meta-analysis", f"{query} clinical trial", f"{query} systematic review"])
    elif domain == "computer_science":
        suggestions.extend([f"{query} benchmark", f"{query} implementation github", f"{query} survey"])
    else:
        suggestions.extend([f"{query} review", f"{query} empirical evidence", f"{query} latest research"])
    return suggestions[:3]


if __name__ == "__main__":
    results = [
        SearchResult(title="FVG Detection in NQ", authors="Chen et al.", year="2025", doi="10.1234/fvg1",
                     citations=87, is_oa=True, source="OpenAlex", abstract="We propose..."),
    ]
    paths = save_exports("FVG test", results)
    for fmt, p in paths.items():
        print(f"{fmt}: {p}")
