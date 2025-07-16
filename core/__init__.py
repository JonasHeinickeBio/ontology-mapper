"""
Core module for ontology mapping operations.
"""

from .generator import OntologyGenerator
from .lookup import ConceptLookup
from .parser import OntologyParser

__all__ = ["OntologyParser", "ConceptLookup", "OntologyGenerator"]
