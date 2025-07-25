"""
Modular ontology mapping tool for BioPortal and OLS integration.
"""

__version__ = "1.0.0"
__author__ = "Jonas Immanuel Heinicke"

# Import handling for both package and direct execution
import sys
from pathlib import Path

# Ensure the current and parent directory are in the Python path for flexible imports
current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    # Try relative imports first (for package usage)
    from .cli import main
    from .config import ONTOLOGY_COMBINATIONS, ONTOLOGY_CONFIGS
    from .config.logging_config import get_logger
    from .core import ConceptLookup, OntologyGenerator, OntologyParser
    from .services import BioPortalLookup, OLSLookup, ResultComparator
    from .utils import LoadingBar, clean_description, deduplicate_synonyms

    logger = get_logger(__name__)
except ImportError:
    try:
        # Fallback to absolute imports
        from cli import main
        from config import ONTOLOGY_COMBINATIONS, ONTOLOGY_CONFIGS
        from config.logging_config import get_logger
        from core import ConceptLookup, OntologyGenerator, OntologyParser
        from services import BioPortalLookup, OLSLookup, ResultComparator
        from utils import LoadingBar, clean_description, deduplicate_synonyms

        logger = get_logger(__name__)
    except ImportError as e:
        # As a last resort, try importing from ontology_mapper if available
        try:
            from ontology_mapper.cli import main
            from ontology_mapper.config import ONTOLOGY_COMBINATIONS, ONTOLOGY_CONFIGS
            from ontology_mapper.config.logging_config import get_logger
            from ontology_mapper.core import ConceptLookup, OntologyGenerator, OntologyParser
            from ontology_mapper.services import BioPortalLookup, OLSLookup, ResultComparator
            from ontology_mapper.utils import LoadingBar, clean_description, deduplicate_synonyms

            logger = get_logger(__name__)
        except ImportError:
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
