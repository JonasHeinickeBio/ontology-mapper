"""
Fuzzy matching and similarity algorithms for concept matching.

Provides string similarity functions (Levenshtein distance, Jaro-Winkler),
confidence scoring, configurable thresholds, and result ranking to improve
concept matching when exact matches are not available.
"""

from typing import List, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Low-level similarity functions (pure Python, no external dependencies)
# ---------------------------------------------------------------------------

def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute the Levenshtein (edit) distance between two strings.

    Returns the minimum number of single-character edits (insertions,
    deletions, substitutions) required to transform *s1* into *s2*.
    """
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    # Use a single-row DP approach to keep memory O(min(len(s1), len(s2)))
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        current_row = [i]
        for j, c2 in enumerate(s2, 1):
            insertions = previous_row[j] + 1
            deletions = current_row[j - 1] + 1
            substitutions = previous_row[j - 1] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Return a normalised similarity score in [0, 1] based on Levenshtein distance.

    Score of 1.0 means identical strings; 0.0 means completely different.
    """
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    return 1.0 - levenshtein_distance(s1, s2) / max_len


def jaro_similarity(s1: str, s2: str) -> float:
    """Compute the Jaro similarity between two strings.

    Returns a value in [0, 1] where 1.0 means identical.
    """
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    len1, len2 = len(s1), len(s2)
    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    s1_matches = [False] * len1
    s2_matches = [False] * len2
    matches = 0
    transpositions = 0

    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)
        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    return (matches / len1 + matches / len2 + (matches - transpositions / 2) / matches) / 3


def jaro_winkler_similarity(s1: str, s2: str, prefix_weight: float = 0.1) -> float:
    """Compute the Jaro-Winkler similarity between two strings.

    Jaro-Winkler boosts the Jaro score for strings that share a common prefix,
    making it well-suited for ontology label matching where prefixes tend to carry
    high semantic weight.

    Args:
        s1: First string.
        s2: Second string.
        prefix_weight: How much weight to give to matching prefixes (default 0.1,
            max 0.25 per the original Winkler specification).

    Returns:
        Similarity score in [0, 1].
    """
    jaro = jaro_similarity(s1, s2)
    if jaro < 0.7:
        return jaro

    prefix = 0
    for c1, c2 in zip(s1[:4], s2[:4]):
        if c1 == c2:
            prefix += 1
        else:
            break

    return jaro + prefix * prefix_weight * (1 - jaro)


# ---------------------------------------------------------------------------
# FuzzyMatcher class
# ---------------------------------------------------------------------------

ALGORITHMS = {
    'levenshtein': levenshtein_similarity,
    'jaro_winkler': jaro_winkler_similarity,
    'jaro': jaro_similarity,
}


class FuzzyMatcher:
    """Fuzzy string matcher for ontology concept results.

    Attributes:
        algorithm: Name of the default similarity algorithm to use.
            One of ``'levenshtein'``, ``'jaro_winkler'``, ``'jaro'``.
        threshold: Minimum similarity score (in [0, 1]) for a result to be
            considered a match.  Results below this threshold are filtered out
            unless *apply_threshold* is ``False``.
    """

    SUPPORTED_ALGORITHMS = list(ALGORITHMS.keys())
    DEFAULT_ALGORITHM = 'jaro_winkler'
    DEFAULT_THRESHOLD = 0.7

    def __init__(
        self,
        algorithm: str = DEFAULT_ALGORITHM,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        if algorithm not in ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. "
                f"Supported: {self.SUPPORTED_ALGORITHMS}"
            )
        if not (0.0 <= threshold <= 1.0):
            raise ValueError("threshold must be a float in [0, 1].")

        self.algorithm = algorithm
        self.threshold = threshold
        self._similarity_fn = ALGORITHMS[algorithm]

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def similarity(self, s1: str, s2: str) -> float:
        """Return the similarity score between two strings using the configured algorithm."""
        return self._similarity_fn(s1.lower(), s2.lower())

    def similarity_with_algorithm(self, s1: str, s2: str, algorithm: str) -> float:
        """Return the similarity score between two strings using a specific algorithm."""
        if algorithm not in ALGORITHMS:
            raise ValueError(
                f"Unknown algorithm '{algorithm}'. "
                f"Supported: {self.SUPPORTED_ALGORITHMS}"
            )
        return ALGORITHMS[algorithm](s1.lower(), s2.lower())

    def find_best_match(
        self,
        query: str,
        candidates: List[str],
        threshold: Optional[float] = None,
    ) -> Optional[Tuple[str, float]]:
        """Find the best-matching string from *candidates* for *query*.

        Args:
            query: The search term.
            candidates: A list of candidate strings to compare against.
            threshold: Override the instance threshold for this call.

        Returns:
            A ``(best_candidate, score)`` tuple, or ``None`` if no candidate
            meets the threshold.
        """
        if not candidates:
            return None

        effective_threshold = threshold if threshold is not None else self.threshold
        best: Optional[Tuple[str, float]] = None

        for candidate in candidates:
            score = self.similarity(query, candidate)
            if score >= effective_threshold:
                if best is None or score > best[1]:
                    best = (candidate, score)

        return best

    def score_results(
        self,
        query: str,
        results: List[Dict],
        threshold: Optional[float] = None,
        apply_threshold: bool = True,
    ) -> List[Dict]:
        """Add a ``'similarity_score'`` key to each result and optionally filter.

        Each result dict is expected to have at least a ``'label'`` key.
        The method also checks ``'synonyms'`` when present, using the highest
        synonym score as the confidence when it exceeds the label score.

        Args:
            query: The original search query.
            results: List of result dicts from BioPortal or OLS.
            threshold: Override the instance threshold for this call.
            apply_threshold: When ``True`` (default), results below the
                threshold are removed from the output.

        Returns:
            A new list of result dicts with ``'similarity_score'`` added, sorted
            by score (highest first).
        """
        effective_threshold = threshold if threshold is not None else self.threshold
        scored: List[Dict] = []

        for result in results:
            label = result.get('label', '')
            label_score = self.similarity(query, label)

            # Also check synonyms if present
            synonyms = result.get('synonyms', [])
            synonym_score = 0.0
            best_synonym: Optional[str] = None
            for syn in synonyms:
                s = self.similarity(query, syn)
                if s > synonym_score:
                    synonym_score = s
                    best_synonym = syn

            confidence = max(label_score, synonym_score)

            if apply_threshold and confidence < effective_threshold:
                continue

            enriched = dict(result)
            enriched['similarity_score'] = round(confidence, 4)
            enriched['similarity_algorithm'] = self.algorithm
            if best_synonym and synonym_score > label_score:
                enriched['matched_synonym'] = best_synonym
            scored.append(enriched)

        scored.sort(key=lambda r: r['similarity_score'], reverse=True)
        return scored

    def rank_results(
        self,
        query: str,
        results: List[Dict],
    ) -> List[Dict]:
        """Rank results by similarity score without filtering any out.

        Convenience wrapper around :meth:`score_results` with
        ``apply_threshold=False``.
        """
        return self.score_results(query, results, apply_threshold=False)

    def filter_by_threshold(
        self,
        results: List[Dict],
        threshold: Optional[float] = None,
    ) -> List[Dict]:
        """Return only results whose ``'similarity_score'`` meets the threshold.

        Assumes :meth:`score_results` has already been called so each result
        already has a ``'similarity_score'`` key.

        Args:
            results: Pre-scored result dicts.
            threshold: Override the instance threshold for this call.

        Returns:
            Filtered list of result dicts.
        """
        effective_threshold = threshold if threshold is not None else self.threshold
        return [r for r in results if r.get('similarity_score', 0.0) >= effective_threshold]
