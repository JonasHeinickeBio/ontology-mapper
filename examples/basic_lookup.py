#!/usr/bin/env python3
"""
Example: Basic concept lookup
"""

import sys

from config.logging_config import get_logger, setup_logging
from core.lookup import ConceptLookup

sys.path.append("..")

# Setup logging for the example
setup_logging(level="INFO", console=True)
logger = get_logger(__name__)


def main():
    # Initialize the lookup service
    from services import BioPortalLookup, OLSLookup

    bioportal = BioPortalLookup()
    ols = OLSLookup()
    lookup = ConceptLookup(bioportal, ols)

    # Search for a concept
    concept = {
        "key": "breast_cancer",
        "label": "breast cancer",
        "type": "Disease",
        "category": "clinical",
    }

    logger.info(f"Searching for: {concept['label']}")

    # Perform lookup
    results, comparison = lookup.lookup_concept(concept)

    # Display results
    if results:
        logger.info(f"Found {len(results)} results:")
        for i, result in enumerate(results[:5], 1):  # Show top 5
            logger.info(f"{i}. {result['label']} ({result['uri']})")
            logger.info(f"   Source: {result['source']}")
            logger.info(f"   Definition: {result.get('description', 'N/A')[:100]}...")
            logger.info("")
    else:
        logger.info("No results found")


if __name__ == "__main__":
    main()
