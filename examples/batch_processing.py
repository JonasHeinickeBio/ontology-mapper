#!/usr/bin/env python3
"""
Example: Batch processing of concepts
"""

import json
import sys

from config.logging_config import get_logger, setup_logging
from core.lookup import ConceptLookup
from services.bioportal import BioPortalLookup
from services.ols import OLSLookup

sys.path.append("..")

# Setup logging for the example
setup_logging(level="INFO", console=True)
logger = get_logger(__name__)


def main():
    # Initialize services
    bioportal = BioPortalLookup()
    ols = OLSLookup()
    lookup = ConceptLookup(bioportal, ols)

    # Read concepts from file
    with open("sample_concepts.txt") as f:
        concepts = [line.strip() for line in f if line.strip()]

    results = {}

    for concept in concepts:
        logger.info(f"Processing: {concept}")
        try:
            # Create concept dict for lookup
            concept_dict = {
                "key": concept.replace(" ", "_"),
                "label": concept,
                "type": "Term",
                "category": "general",
            }
            concept_results, comparison = lookup.lookup_concept(concept_dict)
            results[concept] = {"results": concept_results, "comparison": comparison}
        except Exception as e:
            logger.error(f"Error processing {concept}: {e}")
            results[concept] = {"error": str(e)}

    # Save results
    with open("batch_results.json", "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Processed {len(concepts)} concepts")
    logger.info("Results saved to batch_results.json")


if __name__ == "__main__":
    main()
