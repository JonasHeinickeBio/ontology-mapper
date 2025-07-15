#!/usr/bin/env python3
"""
Example: Batch processing of concepts
"""

import sys
import json
sys.path.append('..')

from core.lookup import ConceptLookup
from services.bioportal import BioPortalService
from services.ols import OLSService

def main():
    # Initialize services
    bioportal = BioPortalService()
    ols = OLSService()
    lookup = ConceptLookup(bioportal, ols)
    
    # Read concepts from file
    with open('sample_concepts.txt', 'r') as f:
        concepts = [line.strip() for line in f if line.strip()]
    
    results = {}
    
    for concept in concepts:
        print(f"Processing: {concept}")
        try:
            concept_results = lookup.lookup_concept(concept)
            results[concept] = concept_results
        except Exception as e:
            print(f"Error processing {concept}: {e}")
            results[concept] = {"error": str(e)}
    
    # Save results
    with open('batch_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nProcessed {len(concepts)} concepts")
    print("Results saved to batch_results.json")

if __name__ == "__main__":
    main()
