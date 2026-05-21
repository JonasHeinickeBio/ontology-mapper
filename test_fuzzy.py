#!/usr/bin/env python3
"""
Test script for fuzzy matching and similarity algorithms.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from services.fuzzy_matcher import (
    levenshtein_distance,
    levenshtein_similarity,
    jaro_similarity,
    jaro_winkler_similarity,
    FuzzyMatcher,
)


# ---------------------------------------------------------------------------
# Levenshtein distance
# ---------------------------------------------------------------------------

def test_levenshtein_distance_identical():
    print("Testing levenshtein_distance: identical strings...")
    assert levenshtein_distance("", "") == 0
    assert levenshtein_distance("abc", "abc") == 0
    print("✓ Identical strings → distance 0")


def test_levenshtein_distance_empty():
    print("Testing levenshtein_distance: empty string...")
    assert levenshtein_distance("", "abc") == 3
    assert levenshtein_distance("abc", "") == 3
    print("✓ Empty string → distance = len(other)")


def test_levenshtein_distance_basic():
    print("Testing levenshtein_distance: basic edits...")
    assert levenshtein_distance("kitten", "sitting") == 3
    assert levenshtein_distance("sunday", "saturday") == 3
    print("✓ Basic edit distance computed correctly")


def test_levenshtein_similarity():
    print("Testing levenshtein_similarity...")
    assert levenshtein_similarity("diabetes", "diabetes") == 1.0
    score = levenshtein_similarity("diabetes", "diabetis")
    assert 0.7 < score < 1.0, f"Expected high similarity, got {score}"
    assert levenshtein_similarity("abc", "xyz") < 0.5
    print("✓ Normalised Levenshtein similarity works")


# ---------------------------------------------------------------------------
# Jaro similarity
# ---------------------------------------------------------------------------

def test_jaro_identical():
    print("Testing jaro_similarity: identical strings...")
    assert jaro_similarity("hello", "hello") == 1.0
    print("✓ Identical strings → 1.0")


def test_jaro_empty():
    print("Testing jaro_similarity: empty strings...")
    # Both empty: same strings, so score is 1.0
    assert jaro_similarity("", "") == 1.0
    # One empty, one non-empty: no matching characters → 0.0
    assert jaro_similarity("abc", "") == 0.0
    assert jaro_similarity("", "abc") == 0.0
    print("✓ Empty string edge cases handled correctly")


def test_jaro_known_values():
    print("Testing jaro_similarity: known values...")
    # "MARTHA" vs "MARHTA" → 0.944
    score = jaro_similarity("MARTHA", "MARHTA")
    assert abs(score - 0.9444) < 0.01, f"Got {score}"
    print(f"✓ MARTHA / MARHTA → {score:.4f}")


# ---------------------------------------------------------------------------
# Jaro-Winkler similarity
# ---------------------------------------------------------------------------

def test_jaro_winkler_identical():
    print("Testing jaro_winkler_similarity: identical strings...")
    assert jaro_winkler_similarity("fatigue", "fatigue") == 1.0
    print("✓ Identical strings → 1.0")


def test_jaro_winkler_prefix_boost():
    print("Testing jaro_winkler_similarity: prefix boost...")
    jaro = jaro_similarity("diabetes", "diabetis")
    jw = jaro_winkler_similarity("diabetes", "diabetis")
    assert jw >= jaro, "Jaro-Winkler should be >= Jaro for strings sharing a prefix"
    print(f"✓ Jaro={jaro:.4f} <= Jaro-Winkler={jw:.4f}")


def test_jaro_winkler_range():
    print("Testing jaro_winkler_similarity: scores in [0, 1]...")
    pairs = [
        ("", ""),
        ("fatigue", ""),
        ("", "fatigue"),
        ("covid", "covid-19"),
        ("hypertension", "hypotension"),
        ("abc", "xyz"),
    ]
    for s1, s2 in pairs:
        score = jaro_winkler_similarity(s1, s2)
        assert 0.0 <= score <= 1.0, f"Score {score} out of range for ({s1!r}, {s2!r})"
    print("✓ All scores in [0, 1]")


# ---------------------------------------------------------------------------
# FuzzyMatcher class
# ---------------------------------------------------------------------------

def test_fuzzy_matcher_init():
    print("Testing FuzzyMatcher initialisation...")
    matcher = FuzzyMatcher()
    assert matcher.algorithm == 'jaro_winkler'
    assert matcher.threshold == 0.7

    matcher2 = FuzzyMatcher(algorithm='levenshtein', threshold=0.8)
    assert matcher2.algorithm == 'levenshtein'
    assert matcher2.threshold == 0.8
    print("✓ Default and custom initialisation works")


def test_fuzzy_matcher_invalid_algorithm():
    print("Testing FuzzyMatcher: invalid algorithm raises ValueError...")
    try:
        FuzzyMatcher(algorithm='unknown')
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    print("✓ Invalid algorithm raises ValueError")


def test_fuzzy_matcher_invalid_threshold():
    print("Testing FuzzyMatcher: invalid threshold raises ValueError...")
    for bad_threshold in [-0.1, 1.1, 2.0]:
        try:
            FuzzyMatcher(threshold=bad_threshold)
            assert False, f"Should have raised ValueError for threshold={bad_threshold}"
        except ValueError:
            pass
    print("✓ Invalid threshold raises ValueError")


def test_fuzzy_matcher_similarity():
    print("Testing FuzzyMatcher.similarity...")
    matcher = FuzzyMatcher(algorithm='jaro_winkler')
    score = matcher.similarity("Diabetes", "diabetes")
    assert score == 1.0, f"Case-insensitive identical → 1.0, got {score}"

    score2 = matcher.similarity("fatigue", "chronic fatigue")
    assert 0.0 <= score2 <= 1.0
    print(f"✓ similarity('fatigue', 'chronic fatigue') = {score2:.4f}")


def test_fuzzy_matcher_find_best_match():
    print("Testing FuzzyMatcher.find_best_match...")
    matcher = FuzzyMatcher(threshold=0.8)
    candidates = ["diabetes", "hypertension", "fatigue", "cancer"]
    result = matcher.find_best_match("diabetis", candidates)
    assert result is not None, "Should find a match above threshold"
    assert result[0] == "diabetes"
    print(f"✓ Best match for 'diabetis' → {result}")


def test_fuzzy_matcher_find_best_match_no_match():
    print("Testing FuzzyMatcher.find_best_match: no match above threshold...")
    matcher = FuzzyMatcher(threshold=0.99)
    result = matcher.find_best_match("xyz", ["abc", "def", "ghi"])
    assert result is None, "Should return None when no candidate meets threshold"
    print("✓ Returns None when no candidate meets threshold")


def test_fuzzy_matcher_score_results():
    print("Testing FuzzyMatcher.score_results...")
    matcher = FuzzyMatcher(threshold=0.5)

    results = [
        {'label': 'Diabetes Mellitus', 'uri': 'http://ex.org/1', 'source': 'bioportal', 'ontology': 'MONDO'},
        {'label': 'Hypertension', 'uri': 'http://ex.org/2', 'source': 'bioportal', 'ontology': 'HP'},
        {'label': 'Diabetic Neuropathy', 'uri': 'http://ex.org/3', 'source': 'ols', 'ontology': 'DOID'},
    ]

    scored = matcher.score_results("diabetes", results)

    # All returned results should have similarity_score
    for r in scored:
        assert 'similarity_score' in r, f"Missing similarity_score in {r}"
        assert 0.0 <= r['similarity_score'] <= 1.0

    # Results should be sorted by score descending
    scores = [r['similarity_score'] for r in scored]
    assert scores == sorted(scores, reverse=True), "Results not sorted by score"

    print(f"✓ Scored {len(scored)} results, top: {scored[0]['label']} ({scored[0]['similarity_score']:.4f})")


def test_fuzzy_matcher_score_results_with_synonyms():
    print("Testing FuzzyMatcher.score_results: synonym matching...")
    matcher = FuzzyMatcher(threshold=0.5)

    results = [
        {
            'label': 'Post-exertional Malaise',
            'uri': 'http://ex.org/4',
            'source': 'bioportal',
            'ontology': 'HP',
            'synonyms': ['fatigue', 'exhaustion', 'tiredness'],
        }
    ]

    scored = matcher.score_results("fatigue", results)
    assert len(scored) == 1
    assert scored[0]['similarity_score'] == 1.0  # exact match via synonym
    assert scored[0].get('matched_synonym') == 'fatigue'
    print(f"✓ Synonym match detected: matched_synonym={scored[0]['matched_synonym']!r}")


def test_fuzzy_matcher_rank_results():
    print("Testing FuzzyMatcher.rank_results (no threshold filtering)...")
    matcher = FuzzyMatcher(threshold=0.99)  # very high threshold

    results = [
        {'label': 'Hypertension', 'uri': 'http://ex.org/1', 'source': 'bioportal', 'ontology': 'HP'},
        {'label': 'Diabetes', 'uri': 'http://ex.org/2', 'source': 'bioportal', 'ontology': 'MONDO'},
    ]

    # rank_results should return all results regardless of threshold
    ranked = matcher.rank_results("diabetis", results)
    assert len(ranked) == len(results), "rank_results should not filter results"
    print(f"✓ rank_results returned all {len(ranked)} results")


def test_fuzzy_matcher_filter_by_threshold():
    print("Testing FuzzyMatcher.filter_by_threshold...")
    matcher = FuzzyMatcher(threshold=0.8)

    pre_scored = [
        {'label': 'Diabetes', 'similarity_score': 0.95},
        {'label': 'Hypertension', 'similarity_score': 0.4},
        {'label': 'Diabetic Complication', 'similarity_score': 0.82},
    ]

    filtered = matcher.filter_by_threshold(pre_scored)
    assert len(filtered) == 2
    labels = [r['label'] for r in filtered]
    assert 'Diabetes' in labels
    assert 'Diabetic Complication' in labels
    assert 'Hypertension' not in labels
    print(f"✓ Filtered to {len(filtered)} results above threshold 0.8")


def test_fuzzy_matcher_all_algorithms():
    print("Testing FuzzyMatcher: all supported algorithms produce valid scores...")
    for algo in FuzzyMatcher.SUPPORTED_ALGORITHMS:
        matcher = FuzzyMatcher(algorithm=algo)
        score = matcher.similarity("fatigue", "chronic fatigue syndrome")
        assert 0.0 <= score <= 1.0, f"{algo}: score {score} out of range"
        print(f"  {algo}: similarity('fatigue', 'chronic fatigue syndrome') = {score:.4f}")
    print("✓ All algorithms produce scores in [0, 1]")


# ---------------------------------------------------------------------------
# Integration with ConceptLookup
# ---------------------------------------------------------------------------

def test_concept_lookup_accepts_fuzzy_matcher():
    """Verify ConceptLookup accepts a FuzzyMatcher without errors."""
    print("Testing ConceptLookup + FuzzyMatcher integration...")
    from core.lookup import ConceptLookup

    class _StubService:
        def search(self, *args, **kwargs):
            return []

    matcher = FuzzyMatcher(algorithm='levenshtein', threshold=0.6)
    lookup = ConceptLookup(
        bioportal=_StubService(),
        ols=_StubService(),
        fuzzy_matcher=matcher,
    )
    assert lookup.fuzzy_matcher is matcher
    print("✓ ConceptLookup stores FuzzyMatcher correctly")


def test_concept_lookup_without_fuzzy_matcher():
    """Verify ConceptLookup works without a FuzzyMatcher (default behaviour)."""
    print("Testing ConceptLookup without FuzzyMatcher...")
    from core.lookup import ConceptLookup

    class _StubService:
        def search(self, *args, **kwargs):
            return []

    lookup = ConceptLookup(bioportal=_StubService(), ols=_StubService())
    assert lookup.fuzzy_matcher is None
    print("✓ ConceptLookup.fuzzy_matcher defaults to None")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main():
    print("Testing Fuzzy Matching Functionality")
    print("=" * 50)

    tests = [
        test_levenshtein_distance_identical,
        test_levenshtein_distance_empty,
        test_levenshtein_distance_basic,
        test_levenshtein_similarity,
        test_jaro_identical,
        test_jaro_empty,
        test_jaro_known_values,
        test_jaro_winkler_identical,
        test_jaro_winkler_prefix_boost,
        test_jaro_winkler_range,
        test_fuzzy_matcher_init,
        test_fuzzy_matcher_invalid_algorithm,
        test_fuzzy_matcher_invalid_threshold,
        test_fuzzy_matcher_similarity,
        test_fuzzy_matcher_find_best_match,
        test_fuzzy_matcher_find_best_match_no_match,
        test_fuzzy_matcher_score_results,
        test_fuzzy_matcher_score_results_with_synonyms,
        test_fuzzy_matcher_rank_results,
        test_fuzzy_matcher_filter_by_threshold,
        test_fuzzy_matcher_all_algorithms,
        test_concept_lookup_accepts_fuzzy_matcher,
        test_concept_lookup_without_fuzzy_matcher,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            print(f"❌ {test_fn.__name__} FAILED: {exc}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 50)
    if failed == 0:
        print(f"✅ All {passed} fuzzy matching tests passed!")
        return True
    else:
        print(f"❌ {failed} test(s) failed, {passed} passed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
