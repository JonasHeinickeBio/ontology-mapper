"""
Ontology configuration constants and mappings.
"""

from typing import Dict, Any

# Ontology descriptions and configurations
ONTOLOGY_CONFIGS: Dict[str, str] = {
    'MONDO': 'Monarch Disease Ontology - Human diseases and disorders',
    'HP': 'Human Phenotype Ontology - Phenotypic abnormalities',
    'NCIT': 'NCI Thesaurus - Cancer terminology and biomedical concepts',
    'GO': 'Gene Ontology - Biological processes, molecular functions, cellular components',
    'DOID': 'Disease Ontology - Human diseases',
    'CHEBI': 'Chemical Entities of Biological Interest - Chemical compounds',
    'PRO': 'Protein Ontology - Protein-related entities',
    'SYMP': 'Symptom Ontology - Symptoms and clinical findings',
    'EFO': 'Experimental Factor Ontology - Experimental variables',
    'ORDO': 'Orphanet Rare Disease Ontology - Rare diseases',
    'ICD10': 'International Classification of Diseases, 10th Revision',
    'ICD11': 'International Classification of Diseases, 11th Revision',
    'SNOMEDCT': 'SNOMED Clinical Terms - Healthcare terminology',
    'MESH': 'Medical Subject Headings - Biomedical literature indexing',
    'LOINC': 'Logical Observation Identifiers Names and Codes',
    'RXNORM': 'RxNorm - Normalized drug names',
    'CPT': 'Current Procedural Terminology - Medical procedures',
    'HGNC': 'HUGO Gene Nomenclature Committee - Gene names',
    'SO': 'Sequence Ontology - Biological sequences',
    'CL': 'Cell Ontology - Cell types',
    'UBERON': 'Uberon - Anatomical structures',
    'FMA': 'Foundational Model of Anatomy - Human anatomy',
    'GARD': 'Genetic and Rare Diseases Information Center',
    'OMIM': 'Online Mendelian Inheritance in Man - Genetic disorders'
}

# Common ontology combinations for different research domains
ONTOLOGY_COMBINATIONS: Dict[str, str] = {
    'Disease Research': 'MONDO,HP,DOID,NCIT,ORDO',
    'Symptom/Phenotype': 'HP,SYMP,NCIT',
    'Chemical/Drug': 'CHEBI,RXNORM,NCIT',
    'Gene/Protein': 'GO,PRO,HGNC,SO',
    'Anatomy': 'UBERON,FMA,CL',
    'Clinical': 'SNOMEDCT,ICD10,ICD11,LOINC,CPT',
    'General Medical': 'NCIT,HP,MONDO,MESH'
}

# Search strategies for different concept types
SEARCH_STRATEGIES: Dict[str, Dict[str, Any]] = {
    'Disease': {
        'variants': ['disease', 'medical condition', 'disorder'],
        'ontologies': 'MONDO,HP,DOID,NCIT'
    },
    'Symptom': {
        'variants': ['symptom', 'clinical sign', 'phenotype'],
        'ontologies': 'HP,NCIT,SYMP'
    },
    'BiologicalProcess': {
        'variants': ['biological process', 'physiological process'],
        'ontologies': 'GO,NCIT'
    },
    'MolecularEntity': {
        'variants': ['molecular entity', 'chemical entity', 'biomarker'],
        'ontologies': 'CHEBI,PRO,NCIT'
    },
    'Treatment': {
        'variants': ['treatment', 'therapy', 'intervention'],
        'ontologies': 'NCIT,DRON'
    },
    'long_covid': {
        'variants': ['long covid', 'post-covid', 'post covid syndrome', 'covid-19 sequelae'],
        'ontologies': 'MONDO,HP,NCIT,DOID'
    },
    'fatigue': {
        'variants': ['fatigue', 'chronic fatigue', 'tiredness', 'exhaustion', 'post-exertional malaise'],
        'ontologies': 'HP,NCIT,SYMP'
    },
    'immune_dysfunction': {
        'variants': ['immune dysfunction', 'immune system disorder', 'immune response abnormality'],
        'ontologies': 'GO,HP,NCIT'
    }
}

# BioPortal to OLS ontology mapping
BIOPORTAL_TO_OLS_MAPPING: Dict[str, str] = {
    'MONDO': 'mondo',
    'HP': 'hp',
    'GO': 'go',
    'CHEBI': 'chebi',
    'NCIT': 'ncit',
    'DOID': 'doid',
    'SYMP': 'symp',
    'PRO': 'pr'
}
