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
__author__ = "Jonas Immanuel Heinicke"

# Import handling for both package and direct execution
import sys
from pathlib import Path

# Ensure the current directory is in the Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    # Try relative imports first (for package usage)
    from .cli import main
    from .config import ONTOLOGY_COMBINATIONS, ONTOLOGY_CONFIGS
    from .core import ConceptLookup, OntologyGenerator, OntologyParser
    from .services import BioPortalLookup, OLSLookup, ResultComparator
    from .utils import LoadingBar, clean_description, deduplicate_synonyms
except ImportError:
    # Fallback to absolute imports (for script usage)
    try:
        from cli import main
        from config import ONTOLOGY_COMBINATIONS, ONTOLOGY_CONFIGS
        from config.logging_config import get_logger
        from core import ConceptLookup, OntologyGenerator, OntologyParser
        from services import BioPortalLookup, OLSLookup, ResultComparator
        from utils import LoadingBar, clean_description, deduplicate_synonyms

        logger = get_logger(__name__)
    except ImportError as e:
        # Use standard logging as a fallback
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Could not import some modules: {e}")
        main = None
        ONTOLOGY_COMBINATIONS = {}
        ONTOLOGY_CONFIGS = {}
        ConceptLookup = None
        OntologyGenerator = None
        OntologyParser = None
        BioPortalLookup = None
        OLSLookup = None
        ResultComparator = None
        LoadingBar = None
        clean_description = None
        deduplicate_synonyms = None

__all__ = [
    "main",
    "OntologyParser",
    "ConceptLookup",
    "OntologyGenerator",
    "BioPortalLookup",
    "OLSLookup",
    "ResultComparator",
    "LoadingBar",
    "clean_description",
    "deduplicate_synonyms",
    "ONTOLOGY_CONFIGS",
    "ONTOLOGY_COMBINATIONS",
]
