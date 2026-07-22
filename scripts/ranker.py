"""
Ranker — Sortiert Ergebnisse nach Relevanz.
Teil des /wissenschaft Tools.
"""
import re


def rank(results: list) -> list:
    """Rank by snippet quality, URL authority, and recency."""
    scored = []
    for r in results:
        score = 0.0
        snippet = r.get("snippet", r.get("abstract", ""))
        title = r.get("title", "")
        url = r.get("url", "")

        score += min(len(snippet) / 500, 1.0)
        if "arxiv" in url: score += 0.3
        if ".edu" in url: score += 0.2
        if ".org" in url: score += 0.1
        if r.get("citations", 0): score += min(r["citations"] / 100, 0.5)

        years = re.findall(r'(20\d{2})', snippet + " " + title)
        if years:
            most_recent = max(int(y) for y in years)
            score += max(0, (most_recent - 2020) / 10)

        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored]
