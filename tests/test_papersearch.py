"""Fusion Option A — tests für sources/papersearch.py (Brücke zu 17 Quellen).

Offline testbar: Dedup-Logik + Feld-Normalisierung (kein Netz nötig).
Die Live-Suche selbst ist in Live-Smokes verifiziert (24 Treffer/8 Quellen).
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import pytest

papersearch = pytest.importorskip("sources.papersearch")


def test_dedupe_doi():
    """Gleiche DOI → ein Treffer."""
    p1 = {"doi": "10.1/x", "title": "A"}
    p2 = {"doi": "10.1/x", "title": "A Kopie"}
    out = papersearch._dedupe([p1, p2])
    assert len(out) == 1


def test_dedupe_titel():
    """Ohne DOI: gleicher Titel+Autors → dedupliziert."""
    p1 = {"title": "Water retention in bentonite", "authors": "Muster"}
    p2 = {"title": "Water retention in bentonite", "authors": "Muster"}
    p3 = {"title": "Anderes Paper", "authors": "Anders"}
    assert len(papersearch._dedupe([p1, p2, p3])) == 2


def test_norm_feld_mapping():
    """paper-search-Felder → unser Schema (title/doi/url/source/year)."""
    roh = {"title": "Titel X", "doi": "https://doi.org/10.1/y",
           "url": "https://x.de", "pdf_url": "https://x.de/pdf",
           "source": "crossref", "published_date": "2024-03-01T00:00:00Z",
           "authors": "A; B", "citations": 42, "abstract": "Abstrakt"}
    n = papersearch._norm(roh)
    assert n["doi"] == "10.1/y"  # doi.org-Präfix gestrippt
    assert n["year"] == "2024"  # aus published_date
    assert n["source"] == "CrossRef"  # humanisiert
    assert n["citations"] == 42


def test_norm_fehltoleranz():
    """Kaputte Einträge crashen nicht."""
    n = papersearch._norm({})
    assert n["title"] == ""
    assert n["doi"] == ""
    assert n["citations"] == 0


def test_search_leere_query():
    erg = papersearch.search_papers("   ")
    assert erg["total"] == 0
    assert erg["papers"] == []


def test_search_unbekannte_quelle():
    erg = papersearch.search_papers("test", sources="gibt_es_nicht")
    assert erg["total"] == 0
    assert "keine valide Quelle" in str(erg["errors"])


def test_search_quellen_auswahl():
    """Nur ausgewählte Quelle suchen (kein Netz — wird gemockt)."""
    import sources.papersearch as ps

    def fake_eine(cls, query, max_results):
        return [{"title": "Paper", "doi": "10.1/a", "url": "u",
                 "source": "arxiv", "published_date": "2020"}]

    ps._search_eine = fake_eine
    erg = ps.search_papers("test", sources="arxiv", timeout_s=5)
    assert erg["total"] >= 1
    assert erg["sources_used"] == ["arxiv"]


# ---------- Quellen-Ausbau: Extra-Connectors ----------

def test_extra_quellen_registriert():
    """Die neuen Domänen-Quellen sind in der Brücke aktiv."""
    assert "chemrxiv" in papersearch.SEARCHER_MAP  # Chemie
    assert "datacite" in papersearch.SEARCHER_MAP  # generisch
    assert "inspirehep" in papersearch.SEARCHER_MAP  # Physik


def test_quellen_anzahl_gestiegen():
    """20+ Quellen registriert (ursprünglich 17)."""
    assert len(papersearch.ALL_SOURCES) >= 20


def test_reihenfolge_kuratierte_zuerst():
    """CrossRef (kuratiert) vor arXiv (Preprint) — Qualitäts-Priorität."""
    assert papersearch.ALL_SOURCES.index("crossref") < \
        papersearch.ALL_SOURCES.index("arxiv")


# ---------- Quellen-Ausbau Teil 2: +10 neue ----------

def test_zehn_neue_quellen_aktiv():
    """Die 10 neuen Quellen (seit Fusion) sind registriert."""
    neue = {"chemrxiv", "datacite", "inspirehep", "cod", "figshare",
            "psyarxiv", "engrxiv", "eartharxiv", "socarxiv", "africarxiv"}
    assert neue.issubset(papersearch.SEARCHER_MAP), \
        f"fehlen: {neue - set(papersearch.SEARCHER_MAP)}"


def test_gesamt_28_quellen():
    assert len(papersearch.ALL_SOURCES) >= 28


# ---------- Verbesserung 4: Abstract-Anreicherung ----------

def test_abstract_anreicherung_ueberspringt_vorhandene():
    """Treffer MIT Abstract werden nicht angefasst (kein Netz)."""
    p = [{"doi": "10.1/x", "abstract": "Schon da", "title": "A"}]
    out = papersearch._reichere_abstracts_an(p, timeout_s=0.1)
    assert out[0]["abstract"] == "Schon da"


def test_abstract_anreicherung_ohne_doi_kein_netz():
    """Ohne DOI → kein Nachschlag, bleibt leer (kein Crash)."""
    p = [{"doi": "", "abstract": "", "title": "Kein DOI"}]
    out = papersearch._reichere_abstracts_an(p, timeout_s=0.1)
    assert out[0]["abstract"] == ""


# ---------- Runde 2: Medizin/Bio/Labor + CS/Mathe/Bücher ----------

def test_medizin_bio_labor_angebunden():
    """Davids Kernwunsch: Medizin/Bio/Chemie/Labor-Quellen aktiv."""
    medizin_bio = {"clinicaltrials", "uniprot", "chembl", "ncbi_gene",
                   "ensembl", "biostudies"}
    assert medizin_bio.issubset(set(papersearch.SEARCHER_MAP)), \
        f"fehlen: {medizin_bio - set(papersearch.SEARCHER_MAP)}"


def test_github_angebunden():
    """Davids 'Geachhab': GitHub + GitLab + PyPI aktiv."""
    assert {"github", "gitlab", "pypi"}.issubset(set(papersearch.SEARCHER_MAP))


def test_mathe_und_buecher():
    assert {"zbmath", "oeis", "openlibrary", "internetarchive"}.issubset(
        set(papersearch.SEARCHER_MAP))


def test_gesamt_mindestens_45_quellen():
    assert len(papersearch.ALL_SOURCES) >= 45


# ---------- Runde 3: Finance/Regional/Bio-Vertiefung/Archive ----------

def test_runde3_quellen():
    neue = {"worldbank", "nber", "repec", "cftc", "redalyc", "jstage",
            "cinii", "ajol", "pdb", "reactome", "geneontology", "gbif",
            "proteinatlas", "doab", "orcid", "ror"}
    assert neue.issubset(set(papersearch.SEARCHER_MAP)), \
        f"fehlen: {neue - set(papersearch.SEARCHER_MAP)}"


def test_gesamt_mindestens_60_quellen():
    assert len(papersearch.ALL_SOURCES) >= 60


# ---------- Runde 4: NCBI- + EBI-Suite (Labor) ----------

def test_runde4_ncbi_ebi():
    neue = {"nucleotide", "protein", "sra", "assembly", "bioproject",
            "biosample", "chebi", "pdbe", "ena", "ols4"}
    assert neue.issubset(set(papersearch.SEARCHER_MAP)), \
        f"fehlen: {neue - set(papersearch.SEARCHER_MAP)}"


def test_gesamt_mindestens_70_quellen():
    assert len(papersearch.ALL_SOURCES) >= 70
