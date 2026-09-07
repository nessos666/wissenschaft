"""Tests für formatter.py V2 — alle Export-Formate + DOI-Verifikation"""
import sys, os, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from formatter import (format_results, save_report, save_exports, export_bibtex,
                       export_ris, export_json, verify_doi, generate_next_searches)
from deduplicator import SearchResult

def test_export_bibtex():
    results = [SearchResult(title="Test Paper", authors="Chen et al.", year="2025", doi="10.1234/test", source="OpenAlex")]
    bib = export_bibtex(results)
    assert "@article" in bib
    assert "Test Paper" in bib
    assert "10.1234/test" in bib

def test_export_ris():
    results = [SearchResult(title="Test Paper", authors="Chen et al.", year="2025", doi="10.1234/test", source="OpenAlex")]
    ris = export_ris(results)
    assert "TY  - JOUR" in ris
    assert "TI  - Test Paper" in ris
    assert "ER  -" in ris

def test_export_json():
    results = [SearchResult(title="Test Paper", year="2025", doi="10.1234/test", citations=10)]
    js = export_json(results)
    data = __import__('json').loads(js)
    assert data[0]["title"] == "Test Paper"
    assert data[0]["citations"] == 10

def test_save_exports():
    results = [SearchResult(title="Export Test", year="2025", source="Test")]
    with tempfile.TemporaryDirectory() as tmp:
        paths = save_exports("Export Test Query", results, base_dir=tmp)
        assert "Markdown" in paths
        assert "BibTeX" in paths
        assert "RIS" in paths
        assert "JSON" in paths
        for p in paths.values():
            assert os.path.exists(p), f"Missing: {p}"

def test_verify_doi_fake():
    result = verify_doi("10.9999/doesnotexist12345", timeout=3)
    assert not result["valid"]

def test_verify_doi_no_doi():
    result = verify_doi("")
    assert not result["valid"]

def test_format_shows_verified():
    r = SearchResult(title="Test", doi="10.1234/x", source="OA")
    r.doi_verified = True
    md = format_results("test", "schnell", ["OA"], [r])
    assert "verifiziert" in md

def test_format_shows_unverified():
    r = SearchResult(title="Test", doi="10.1234/x", source="OA")
    r.doi_verified = False
    md = format_results("test", "schnell", ["OA"], [r])
    assert "UNVERIFIED" in md

if __name__ == "__main__":
    tests = [test_export_bibtex, test_export_ris, test_export_json, test_save_exports,
             test_verify_doi_fake, test_verify_doi_no_doi, test_format_shows_verified, test_format_shows_unverified]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"💥 {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} Tests bestanden")
