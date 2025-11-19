"""
Core module for ontology mapping operations.
"""

from .parser import OntologyParser
from .schema_parser import SchemaParser
from .lookup import ConceptLookup
from .generator import OntologyGenerator

__all__ = ['OntologyParser', 'SchemaParser', 'ConceptLookup', 'OntologyGenerator']
