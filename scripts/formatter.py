"""
Formatter — Erzeugt Markdown-Report aus Suchergebnissen.
Teil des /wissenschaft Tools.
"""
import json
from datetime import datetime
from pathlib import Path


def format_results(query, depth, sources_used, results, domain_guess="", next_searches=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Wissenschaftliche Recherche: _{query}_", "",
        f"**Datum:** {now} | **Modus:** {depth} | **Domain:** {domain_guess}",
        f"**Quellen:** {', '.join(sources_used)}",
        f"**Ergebnisse:** {len(results)} (nach Deduplizierung)", "",
        "---", "",
    ]
    
    if results:
        lines.append("## 📋 Ergebnisuebersicht")
        lines.append("")
        for i, r in enumerate(results[:5], 1):
            title = r.get("title", "Ohne Titel")
            year = r.get("year", "")
            citations = r.get("citations", 0)
            cit_str = f" — {citations} Zit." if citations > 0 else ""
            lines.append(f"{i}. **{title}** ({year}){cit_str}")
        lines.append("")
    
    lines.extend(["---", "", "## 📄 Detail-Ergebnisse", ""])
    
    for i, r in enumerate(results, 1):
        title = r.get("title", "Ohne Titel")
        lines.append(f"### {i}. {title}")
        lines.append("")
        if r.get("authors"): lines.append(f"**Autoren:** {r['authors']}")
        if r.get("year"): lines.append(f"**Jahr:** {r['year']}")
        if r.get("doi"): lines.append(f"**DOI:** [{r['doi']}](https://doi.org/{r['doi']})")
        if r.get("url") and not r.get("doi"): lines.append(f"**URL:** {r['url']}")
        if r.get("citations", 0) > 0: lines.append(f"**Zitationen:** {r['citations']}")
        lines.append(f"**Quelle:** {r.get('source', 'unbekannt')}")
        lines.append("")
        snippet = r.get("snippet", r.get("abstract", ""))
        if snippet:
            short = snippet[:500] + ("..." if len(snippet) > 500 else "")
            lines.append(f"> {short}")
            lines.append("")
        lines.extend(["---", ""])
    
    lines.append("## 🔍 Verwendete Quellen")
    lines.append("")
    for s in sources_used: lines.append(f"- {s}")
    lines.append("")
    
    if next_searches:
        lines.append("## 💡 Vorschlaege fuer weitere Suchen")
        lines.append("")
        for ns in next_searches: lines.append(f"- `{ns}`")
        lines.append("")
    
    lines.extend(["---", f"_Generiert vom /wissenschaft Tool — {now}_"])
    return "\n".join(lines)


def save_report(markdown, query, output_dir=None):
    """Save report to output directory."""
    if output_dir is None:
        output_dir = Path.cwd() / "output"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    safe_query = "".join(c if c.isalnum() or c in " -_" else "_" for c in query[:50])
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}-{safe_query.strip().replace(' ', '-')}.md"
    filepath = output_dir / filename
    filepath.write_text(markdown, encoding='utf-8')
    return str(filepath)


def generate_next_searches(query, domain, results):
    suggestions = []
    if domain == "trading":
        suggestions = [f"{query} machine learning model", f"{query} empirical study", f"{query} systematic review"]
    elif domain == "medical":
        suggestions = [f"{query} meta-analysis", f"{query} clinical trial", f"{query} systematic review"]
    elif domain == "ai":
        suggestions = [f"{query} benchmark", f"{query} implementation github", f"{query} survey"]
    else:
        suggestions = [f"{query} review", f"{query} empirical evidence", f"{query} latest research"]
    return suggestions[:3]
