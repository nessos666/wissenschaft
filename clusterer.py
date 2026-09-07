"""
Paper Clusterer — Gruppiert ähnliche Papers via Titel-Embedding.
Nutzt sentence-transformers für semantische Ähnlichkeit.
"""
from collections import defaultdict
from deduplicator import SearchResult

def cluster_by_title_similarity(results: list[SearchResult], threshold: float = 0.6) -> list[dict]:
    """Gruppiert Papers nach Titel-Ähnlichkeit (einfache Heuristik)."""
    from difflib import SequenceMatcher
    import re
    
    def normalize(t):
        return re.sub(r'[^a-z0-9\s]', '', t.lower()).strip()
    
    clusters = []
    assigned = set()
    
    for i, r1 in enumerate(results):
        if i in assigned:
            continue
        
        cluster = [{"title": r1.title, "source": r1.source, "year": r1.year}]
        assigned.add(i)
        
        for j, r2 in enumerate(results):
            if j in assigned:
                continue
            sim = SequenceMatcher(None, normalize(r1.title), normalize(r2.title)).ratio()
            if sim > threshold:
                cluster.append({"title": r2.title, "source": r2.source, "year": r2.year})
                assigned.add(j)
        
        clusters.append({
            "topic": r1.title[:60],
            "size": len(cluster),
            "papers": cluster,
        })
    
    clusters.sort(key=lambda x: x["size"], reverse=True)
    return clusters

def cluster_by_domain(results: list[SearchResult]) -> dict:
    """Gruppiert Papers nach Quelle/Domain."""
    by_source = defaultdict(list)
    for r in results:
        by_source[r.source or "Unknown"].append(r.title[:60])
    return dict(by_source)

def cluster_by_year(results: list[SearchResult]) -> dict:
    """Gruppiert Papers nach Jahr."""
    by_year = defaultdict(list)
    for r in results:
        year = r.year or "Unknown"
        by_year[year].append(r.title[:60])
    return dict(sorted(by_year.items(), reverse=True))

def generate_cluster_report(results: list[SearchResult]) -> str:
    """Erstellt Cluster-Report als Markdown."""
    by_source = cluster_by_domain(results)
    by_year = cluster_by_year(results)
    clusters = cluster_by_title_similarity(results)
    
    lines = ["## 📊 Paper Clustering", ""]
    
    # Topic-Clusters
    if clusters:
        lines.append("### Thematische Cluster")
        lines.append("")
        for i, c in enumerate(clusters[:5], 1):
            lines.append(f"**Cluster {i}** ({c['size']} Papers): _{c['topic']}..._")
            for p in c['papers'][:3]:
                lines.append(f"- {p['title'][:80]}")
            if c['size'] > 3:
                lines.append(f"- ... und {c['size']-3} weitere")
            lines.append("")
    
    # Nach Quelle
    lines.append("### Nach Quelle")
    lines.append("")
    lines.append("| Quelle | Papers |")
    lines.append("|--------|--------|")
    for src, papers in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
        lines.append(f"| {src} | {len(papers)} |")
    lines.append("")
    
    # Nach Jahr
    years = list(by_year.items())[:5]
    if years:
        lines.append("### Nach Jahr")
        lines.append("")
        for year, papers in years:
            lines.append(f"**{year}**: {len(papers)} Papers")
        lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    results = [
        SearchResult(title="Fair Value Gap Detection in NQ Futures", source="SSRN", year="2025"),
        SearchResult(title="Detecting Fair Value Gaps Using Machine Learning", source="arXiv", year="2025"),
        SearchResult(title="Market Microstructure of E-mini Futures", source="OpenAlex", year="2023"),
        SearchResult(title="Reinforcement Learning for Trading", source="OpenAlex", year="2024"),
        SearchResult(title="Deep RL in Financial Markets", source="arXiv", year="2024"),
    ]
    print(generate_cluster_report(results))
