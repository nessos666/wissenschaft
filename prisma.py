"""
PRISMA Formatter — Generiert PRISMA-Flussdiagramme für systematische Reviews.
"""
from dataclasses import dataclass, field

@dataclass
class PrismaFlow:
    identified: int = 0       # Alle Roh-Ergebnisse
    duplicates_removed: int = 0  # Duplikate entfernt
    screened: int = 0         # Nach Dedup
    fulltext_sought: int = 0  # Volltext verfügbar
    fulltext_assessed: int = 0  # Volltext geprüft
    included: int = 0         # Final eingeschlossen
    excluded_reasons: dict = field(default_factory=dict)  # {grund: anzahl}

def generate_prisma_ascii(flow: PrismaFlow) -> str:
    """Erzeugt ASCII PRISMA-Diagramm."""
    return f"""
┌─────────────────────────────────────────────────┐
│                IDENTIFICATION                    │
│  Records identified from:                       │
│  Databases (n = {flow.identified})              │
│  Registers (n = 0)                              │
├─────────────────────────────────────────────────┤
│                                                 │
│  Records removed BEFORE screening:              │
│  Duplicate records removed (n = {flow.duplicates_removed})  │
│                                                 │
├─────────────────────────────────────────────────┤
│                SCREENING                        │
│  Records screened (n = {flow.screened})         │
│                                                 │
├─────────────────────────────────────────────────┤
│  Reports sought for retrieval (n = {flow.fulltext_sought})  │
│  Reports not retrieved (n = {flow.screened - flow.fulltext_sought})    │
│                                                 │
├─────────────────────────────────────────────────┤
│  Reports assessed for eligibility (n = {flow.fulltext_assessed})     │
│  Reports excluded:                              │
{chr(10).join(f'    Reason: {k} (n = {v})' for k,v in flow.excluded_reasons.items()) if flow.excluded_reasons else '    None'}
│                                                 │
├─────────────────────────────────────────────────┤
│                INCLUDED                         │
│  Studies included in review (n = {flow.included})│
│  Reports of included studies (n = {flow.included})│
└─────────────────────────────────────────────────┘
"""

def generate_prisma_markdown(flow: PrismaFlow) -> str:
    """PRISMA als Markdown-Tabelle."""
    lines = [
        "## PRISMA 2020 Flow Diagram",
        "",
        "| Phase | Count | Description |",
        "|-------|-------|-------------|",
        f"| 🔍 Identified | {flow.identified} | Records from all sources |",
        f"| 🗑️ Duplicates | {flow.duplicates_removed} | Removed before screening |",
        f"| 📋 Screened | {flow.screened} | After deduplication |",
        f"| 📄 Full-text sought | {flow.fulltext_sought} | Open Access available |",
        f"| ✅ Assessed | {flow.fulltext_assessed} | Full-text eligibility checked |",
        f"| ⭐ Included | {flow.included} | Final selection |",
        "",
    ]
    if flow.excluded_reasons:
        lines.append("### Exclusion Reasons")
        lines.append("")
        lines.append("| Reason | Count |")
        lines.append("|--------|-------|")
        for reason, count in flow.excluded_reasons.items():
            lines.append(f"| {reason} | {count} |")
        lines.append("")
    return "\n".join(lines)

def compute_prisma(results_count: int, dedup_count: int, oa_count: int, final_count: int,
                   exclusion_reasons: dict = None) -> PrismaFlow:
    """Berechnet PRISMA-Zahlen aus Pipeline-Ergebnissen."""
    duplicates = results_count - dedup_count if results_count > dedup_count else 0
    return PrismaFlow(
        identified=results_count,
        duplicates_removed=duplicates,
        screened=dedup_count,
        fulltext_sought=oa_count,
        fulltext_assessed=oa_count,  # Vereinfacht: alle OA werden bewertet
        included=final_count,
        excluded_reasons=exclusion_reasons or {},
    )

if __name__ == "__main__":
    flow = PrismaFlow(
        identified=127, duplicates_removed=38, screened=89,
        fulltext_sought=23, fulltext_assessed=20, included=20,
        excluded_reasons={"Kein Volltext": 3, "Nicht relevant": 15, "Paywall": 20},
    )
    print(generate_prisma_ascii(flow))
    print(generate_prisma_markdown(flow))
