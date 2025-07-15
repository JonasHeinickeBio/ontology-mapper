"""
Services module for external API integrations.
"""

from .bioportal import BioPortalLookup
from .ols import OLSLookup
from .comparator import ResultComparator

__all__ = ['BioPortalLookup', 'OLSLookup', 'ResultComparator']
