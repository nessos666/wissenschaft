"""Tests für verifier.py"""
import sys; sys.path.insert(0, '/home/boobi/HAUPTLAGER/03_PROJEKTE/XX_WissenschaftSkill')
from verifier import Verifier, VerifiedResult
from deduplicator import SearchResult

def test_verify_valid_doi():
    v = Verifier(timeout=5)
    result = v.check_doi("10.1613/jair.301")
    assert result["valid"], f"Valid DOI failed: {result.get('error')}"
    assert "Reinforcement" in result.get("title", "")

def test_verify_broken_doi():
    v = Verifier(timeout=5)
    result = v.check_doi("10.9999/doesnotexist123456789")
    assert not result["valid"]

def test_verify_no_doi():
    v = Verifier(timeout=5)
    result = v.check_doi("")
    assert not result["valid"]

def test_url_check_google():
    v = Verifier(timeout=5)
    assert v.check_url("https://google.com")

def test_url_check_broken():
    v = Verifier(timeout=5)
    assert not v.check_url("https://thisurldoesnotexist99999.com")

def test_verify_full_paper():
    v = Verifier()
    r = SearchResult(
        title="Reinforcement Learning: A Survey",
        authors="Kaelbling; Littman; Moore",
        year="1996", doi="10.1613/jair.301",
        url="https://doi.org/10.1613/jair.301",
        source="OpenAlex", citations=8836,
    )
    vr = v.verify(r)
    assert vr.doi_verified
    assert vr.trust_score > 0.5

def test_verify_paper_no_doi():
    v = Verifier()
    r = SearchResult(title="Some Paper", authors="Author", year="2020", source="arXiv")
    vr = v.verify(r)
    assert not vr.doi_verified
    assert len(vr.warnings) > 0

def test_summary():
    v = Verifier()
    r = SearchResult(title="Test", doi="10.1613/jair.301", source="OpenAlex")
    summary = v.summary([v.verify(r)])
    assert summary["total"] == 1

if __name__ == "__main__":
    tests = [
        test_verify_valid_doi, test_verify_broken_doi, test_verify_no_doi,
        test_url_check_google, test_url_check_broken,
        test_verify_full_paper, test_verify_paper_no_doi, test_summary,
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
