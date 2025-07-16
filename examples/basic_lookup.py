#!/usr/bin/env python3
"""
Example: Basic concept lookup
"""

import sys

from core.lookup import ConceptLookup

sys.path.append("..")


def main():
    # Initialize the lookup service
    lookup = ConceptLookup()

    # Search for a concept
    concept = "breast cancer"
    print(f"Searching for: {concept}")

    # Perform lookup
    results = lookup.search(concept)

    # Display results
    if results:
        print(f"\nFound {len(results)} results:")
        for i, result in enumerate(results[:5], 1):  # Show top 5
            print(f"{i}. {result['label']} ({result['id']})")
            print(f"   Source: {result['source']}")
            print(f"   Definition: {result.get('definition', 'N/A')[:100]}...")
            print()
    else:
        print("No results found")


if __name__ == "__main__":
    main()
