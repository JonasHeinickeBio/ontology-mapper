"""
Modular ontology mapping tool for BioPortal and OLS integration.

This package provides a command-line interface for improving ontologies
using BioPortal and OLS standard terminologies.

Usage:
    python -m ontology_mapping.cli <ttl_file> [options]
    python ontology_mapping/main.py <ttl_file> [options]

Modules:
    cli: Command-line interface
    core: Core ontology processing logic
    services: External API integrations
    utils: Utility functions
    config: Configuration constants
"""

__version__ = "1.0.0"
__author__ = "AID-PAIS Research Team"

from .cli import main
from .core import OntologyParser, ConceptLookup, OntologyGenerator
from .services import BioPortalLookup, OLSLookup, ResultComparator
from .utils import LoadingBar, clean_description, deduplicate_synonyms
from .config import ONTOLOGY_CONFIGS, ONTOLOGY_COMBINATIONS

__all__ = [
    'main',
    'OntologyParser',
    'ConceptLookup', 
    'OntologyGenerator',
    'BioPortalLookup',
    'OLSLookup',
    'ResultComparator',
    'LoadingBar',
    'clean_description',
    'deduplicate_synonyms',
    'ONTOLOGY_CONFIGS',
    'ONTOLOGY_COMBINATIONS'
]
