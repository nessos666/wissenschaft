"""Tests für deduplicator.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deduplicator import deduplicate, SearchResult, title_similarity, normalize_title

def test_doi_dedup():
    r1 = SearchResult(title="FVG Detection in NQ", doi="10.1234/fvg1", source="OpenAlex", citations=10)
    r2 = SearchResult(title="FVG Detection in NQ Futures", doi="10.1234/fvg1", source="CrossRef", citations=87)
    results = deduplicate([r1, r2])
    assert len(results) == 1, f"Erwartet 1, bekam {len(results)}"
    assert results[0].citations == 87, "Citations wurden nicht gemerged"
    assert "CrossRef" in results[0].merged_from

def test_title_fuzzy_dedup():
    r1 = SearchResult(title="Fair Value Gap Detection in NASDAQ-100 Futures", doi="", source="OpenAlex")
    r2 = SearchResult(title="Detection of Fair Value Gaps in NASDAQ Futures", doi="", source="Semantic Scholar")
    results = deduplicate([r1, r2])
    assert len(results) == 1, f"Erwartet 1, bekam {len(results)}"

def test_no_dedup_different_papers():
    r1 = SearchResult(title="FVG Detection", doi="10.1", source="OpenAlex")
    r2 = SearchResult(title="Market Microstructure Theory", doi="10.2", source="CrossRef")
    r3 = SearchResult(title="Machine Learning in Finance", doi="10.3", source="Semantic Scholar")
    results = deduplicate([r1, r2, r3])
    assert len(results) == 3

def test_title_similarity_identical():
    assert title_similarity("Fair Value Gap Detection", "Fair Value Gap Detection") > 0.95

def test_title_similarity_different():
    assert title_similarity("Fair Value Gap Detection", "Machine Learning Basics") < 0.5

def test_normalize_title():
    assert normalize_title("Fair Value Gap: Detection!") == "fair value gap detection"

def test_merge_keeps_longer_abstract():
    r1 = SearchResult(title="Test", doi="10.x", source="A", abstract="Short")
    r2 = SearchResult(title="Test", doi="10.x", source="B", abstract="Much longer abstract with more details")
    results = deduplicate([r1, r2])
    assert len(results[0].abstract) > 10

if __name__ == "__main__":
    tests = [
        test_doi_dedup, test_title_fuzzy_dedup, test_no_dedup_different_papers,
        test_title_similarity_identical, test_title_similarity_different,
        test_normalize_title, test_merge_keeps_longer_abstract,
    ]
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
