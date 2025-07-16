"""
Services module for external API integrations.
"""

from .bioportal import BioPortalLookup
from .comparator import ResultComparator
from .ols import OLSLookup

__all__ = ["BioPortalLookup", "OLSLookup", "ResultComparator"]
