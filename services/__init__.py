"""
Services module for external API integrations.
"""

from .bioportal import BioPortalLookup
from .ols import OLSLookup
from .comparator import ResultComparator
from .fuzzy_matcher import FuzzyMatcher

__all__ = ['BioPortalLookup', 'OLSLookup', 'ResultComparator', 'FuzzyMatcher']
