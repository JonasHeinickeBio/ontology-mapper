"""
Core module for ontology mapping operations.
"""

from .parser import OntologyParser
from .lookup import ConceptLookup
from .generator import OntologyGenerator

__all__ = ['OntologyParser', 'ConceptLookup', 'OntologyGenerator']
