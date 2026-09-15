"""Block 8 — Test-Abdeckung: prisma, evidence_scorer, clusterer (bisher 0).

Diese Module sind reine Logik (offline testbar) — sie verdienen Tests.
Signaturen geprüft: compute_prisma(counts), score_evidence(SearchResult-Liste)
mit trust_score-Feld, generate_cluster_report(SearchResult-Liste).
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from prisma import PrismaFlow, compute_prisma, generate_prisma_ascii, generate_prisma_markdown
from evidence_scorer import score_evidence, evidence_summary
from clusterer import generate_cluster_report
from deduplicator import SearchResult


# ---------- PRISMA ----------

def test_prisma_flow_defaults():
    f = PrismaFlow()
    assert f.identified == 0 and f.included == 0


def test_compute_prisma_logik():
    f = compute_prisma(10, 8, 5, 6)
    assert f.identified == 10
    assert f.screened == 8
    assert f.fulltext_sought == 5
    assert f.included == 6


def test_prisma_ascii_enthalt_zahlen():
    f = PrismaFlow(identified=10, duplicates_removed=2, screened=8,
                   fulltext_sought=5, fulltext_assessed=5, included=3)
    out = generate_prisma_ascii(f)
    assert "IDENTIFICATION" in out or "IDENTIFIZIERT" in out
    assert "10" in out or "8" in out


def test_prisma_markdown_nicht_leer():
    f = PrismaFlow(identified=5, screened=4, included=2)
    md = generate_prisma_markdown(f)
    assert isinstance(md, str) and len(md) > 20


# ---------- Evidence Scorer ----------

def test_score_evidence_hohes_vertrauen():
    """Paper mit hohem Trust → hoher combined_score."""
    r = SearchResult(title="Randomized controlled trial of therapy",
                     doi="10.1/x", source="PubMed", citations=100,
                     is_oa=True)
    r.trust_score = 0.9
    scored = score_evidence([r])
    assert len(scored) == 1
    assert scored[0]["combined_score"] >= 0.5
    assert scored[0]["evidence_level"] != "unknown"  # RCT erkannt


def test_score_evidence_niedriges_vertrauen():
    """Paper mit niedrigem Trust → niedriger combined_score."""
    r = SearchResult(title="Blog post ohne Quelle", doi="", source="Unbekannt")
    r.trust_score = 0.1
    scored = score_evidence([r])
    assert scored[0]["combined_score"] < 0.5


def test_evidence_summary_aggregiert():
    papiere = []
    for i in range(3):
        r = SearchResult(title=f"Paper {i}", source="OpenAlex")
        r.trust_score = 0.8
        papiere.append(r)
    s = evidence_summary(score_evidence(papiere))
    assert s.get("distribution")  # Verteilung ist gefüllt
    assert sum(s.get("distribution", {}).values()) == 3


def test_evidence_summary_leer():
    assert evidence_summary([]) == {}


# ---------- Clusterer ----------

def test_clusterer_erzeugt_bericht():
    results = [
        SearchResult(title="Bentonite water retention soil", source="A"),
        SearchResult(title="Bentonite clay barrier", source="B"),
    ]
    md = generate_cluster_report(results)
    assert isinstance(md, str)


def test_clusterer_leere_liste_kein_crash():
    out = generate_cluster_report([])
    assert isinstance(out, str) or out is None


# ---------- Verbesserung 6: Query-Erweiterung ----------

def test_erweitere_query_abkuerzung():
    """EMDR → Langform in Original-Wortstellung."""
    from query_analyzer import erweitere_query
    v = erweitere_query("posttraumatic growth EMDR")
    assert len(v) == 1
    assert "eye movement desensitization and reprocessing" in v[0]
    assert v[0].startswith("posttraumatic growth")


def test_erweitere_query_ohne_abkuerzung():
    from query_analyzer import erweitere_query
    assert erweitere_query("bentonite clay water retention") == []


def test_erweitere_query_leer():
    from query_analyzer import erweitere_query
    assert erweitere_query("") == []


def test_erweitere_query_ptbs_deutsch():
    from query_analyzer import erweitere_query
    v = erweitere_query("PTBS Therapie")
    assert v and "posttraumatic stress disorder" in v[0]
