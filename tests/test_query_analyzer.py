"""Tests für query_analyzer.py V2 — Boolean-Suche"""
import sys; sys.path.insert(0, '/home/boobi/HAUPTLAGER/03_PROJEKTE/XX_WissenschaftSkill')
from query_analyzer import analyze_query, parse_boolean

def test_boolean_and():
    clean, excl, struct = parse_boolean("FVG AND microstructure")
    assert "FVG" in clean and "microstructure" in clean
    assert struct == "and"
    assert "AND" not in clean.upper()

def test_boolean_or():
    clean, excl, struct = parse_boolean("FVG OR microstructure OR bitcoin")
    assert struct == "or"

def test_boolean_not():
    clean, excl, struct = parse_boolean("FVG AND microstructure NOT bitcoin")
    assert "bitcoin" in excl
    assert struct == "and"

def test_boolean_minus():
    clean, excl, struct = parse_boolean("FVG microstructure -bitcoin")
    assert "bitcoin" in excl

def test_domain_stochastic():
    q = analyze_query("stochastic processes mathematics")
    assert q.domain_guess == "mathematics", f"Got {q.domain_guess}"

def test_domain_black_holes():
    q = analyze_query("black holes physics")
    assert q.domain_guess == "physics", f"Got {q.domain_guess}"

def test_boolean_excluded_terms_in_query():
    q = analyze_query("trading FVG NOT cryptocurrency")
    assert "cryptocurrency" in q.excluded_terms
    assert q.boolean_structure == "and"

if __name__ == "__main__":
    tests = [test_boolean_and, test_boolean_or, test_boolean_not, test_boolean_minus,
             test_domain_stochastic, test_domain_black_holes, test_boolean_excluded_terms_in_query]
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
