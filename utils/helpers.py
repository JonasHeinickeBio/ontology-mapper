"""
Helper functions for ontology mapping operations.
"""


def clean_description(description: str) -> str:
    """Clean and normalize description text"""
    if not description:
        return ""

    # Remove extra whitespace and normalize
    cleaned = " ".join(description.split())

    # Remove common prefixes that add no value
    prefixes_to_remove = [
        "A ",
        "An ",
        "The ",
        "This is a ",
        "This is an ",
        "This is the ",
        "Definition: ",
        "Description: ",
    ]

    for prefix in prefixes_to_remove:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix) :]
            break

    # Ensure first letter is capitalized
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    # Limit length to reasonable size
    if len(cleaned) > 200:
        cleaned = cleaned[:197] + "..."

    return cleaned


def deduplicate_synonyms(synonyms: list[str], existing_labels: set[str]) -> list[str]:
    """Remove duplicate and low-quality synonyms"""
    if not synonyms:
        return []

    unique_synonyms = []
    seen_normalized: set[str] = set()

    for synonym in synonyms:
        if not synonym or not synonym.strip():
            continue

        # Normalize for comparison
        normalized = synonym.lower().strip()

        # Skip if already seen or in existing labels
        if normalized in seen_normalized or normalized in existing_labels:
            continue

        # Skip very short synonyms (likely not meaningful)
        if len(normalized) < 3:
            continue

        # Skip synonyms that are just case variations
        if any(normalized == existing.lower() for existing in seen_normalized):
            continue

        # Add to unique list
        unique_synonyms.append(synonym.strip())
        seen_normalized.add(normalized)

    # Sort by length and relevance (shorter, more specific terms first)
    unique_synonyms.sort(key=lambda x: (len(x), x.lower()))

    return unique_synonyms


def determine_alignment_type(alignment: dict, concept_key: str) -> str:
    """Determine the type of alignment based on concept and external term characteristics"""
    label_match = alignment.get("label", "").lower()
    concept_label = concept_key.lower().replace("_", " ")

    # Exact match criteria
    if label_match == concept_label:
        return "exact"

    # Check for exact match in synonyms
    synonyms = [s.lower() for s in alignment.get("synonyms", [])]
    if concept_label in synonyms:
        return "exact"

    # Close match criteria (similar terms)
    if concept_label in label_match or label_match in concept_label:
        return "close"

    # Check for semantic relationships
    broader_indicators = ["disease", "disorder", "condition", "syndrome"]
    narrower_indicators = ["symptom", "sign", "manifestation"]

    if any(
        indicator in label_match for indicator in broader_indicators
    ) and concept_key.lower() in ["symptom", "sign"]:
        return "broader"

    if any(
        indicator in label_match for indicator in narrower_indicators
    ) and concept_key.lower() in ["disease", "disorder"]:
        return "narrower"

    # Default to related match
    return "related"
