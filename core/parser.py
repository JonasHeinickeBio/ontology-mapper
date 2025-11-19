"""
Ontology parser for multiple RDF formats.
"""

import os
from typing import List, Dict, Optional
from rdflib import Graph, RDF, RDFS


# Supported input formats
SUPPORTED_INPUT_FORMATS = {
    # RDF formats (via rdflib)
    'turtle': 'turtle',
    'ttl': 'turtle',
    'json-ld': 'json-ld',
    'jsonld': 'json-ld',
    'xml': 'xml',
    'rdf': 'xml',
    'rdf-xml': 'xml',
    'rdfxml': 'xml',
    'nt': 'nt',
    'ntriples': 'nt',
    'n-triples': 'nt',
    'n3': 'n3',
    'trig': 'trig',
    'nquads': 'nquads',
}

# Format descriptions for help text
INPUT_FORMAT_DESCRIPTIONS = {
    'turtle': 'Turtle - Human-readable RDF format',
    'json-ld': 'JSON-LD - JSON format for linked data',
    'xml': 'RDF/XML - Traditional RDF XML format',
    'nt': 'N-Triples - Simple line-based RDF format',
    'n3': 'Notation3 - Superset of Turtle with rules',
    'trig': 'TriG - Turtle with named graphs',
    'nquads': 'N-Quads - N-Triples with named graphs'
}


class OntologyParser:
    """Parses and analyzes ontology files in multiple RDF formats"""
    
    def __init__(self, input_file: str, input_format: Optional[str] = None):
        """Initialize parser
        
        Args:
            input_file: Path to ontology file
            input_format: Optional format specification (turtle, json-ld, xml, nt, etc.)
                         If None, auto-detect from filename or use turtle as default
        """
        self.ttl_file = input_file  # Keep for backward compatibility
        self.input_file = input_file
        self.graph = Graph()
        self.classes: List[str] = []
        self.instances: List[Dict] = []
        
        # Determine input format
        self.input_format = self._determine_input_format(input_file, input_format)
        
    def _detect_format_from_filename(self, filename: str) -> Optional[str]:
        """Detect input format from filename extension"""
        if not filename:
            return None
        
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        return SUPPORTED_INPUT_FORMATS.get(ext)
    
    def _normalize_format(self, format_str: str) -> str:
        """Normalize format string to canonical format name"""
        if not format_str:
            return 'turtle'  # Default format
        
        format_lower = format_str.lower().strip()
        if format_lower in SUPPORTED_INPUT_FORMATS:
            return SUPPORTED_INPUT_FORMATS[format_lower]
        
        raise ValueError(f"Unsupported input format: {format_str}. Supported formats: {', '.join(sorted(set(SUPPORTED_INPUT_FORMATS.values())))}")
    
    def _determine_input_format(self, input_file: str, input_format: Optional[str]) -> str:
        """Determine the input format from explicit parameter or filename
        
        Args:
            input_file: Path to input file
            input_format: Optional explicit format specification
            
        Returns:
            Normalized format name
        """
        if input_format:
            return self._normalize_format(input_format)
        else:
            return self._detect_format_from_filename(input_file) or 'turtle'
    
    @staticmethod
    def get_supported_input_formats() -> List[str]:
        """Get list of supported input formats"""
        return sorted(set(SUPPORTED_INPUT_FORMATS.values()))
    
    @staticmethod
    def get_input_format_descriptions() -> Dict[str, str]:
        """Get format descriptions for help text"""
        return INPUT_FORMAT_DESCRIPTIONS.copy()
        
    def parse(self) -> bool:
        """Parse the ontology file and extract concepts"""
        try:
            self.graph.parse(self.input_file, format=self.input_format)
            print(f"✅ Loaded {len(self.graph)} triples from {self.input_file} ({self.input_format} format)")
            
            # Extract classes
            for s, p, o in self.graph.triples((None, RDF.type, RDFS.Class)):
                class_name = str(s).split("#")[-1]
                if class_name != 'Entity':  # Skip base class
                    self.classes.append(class_name)
            
            # Extract instances
            for s, p, o in self.graph.triples((None, RDF.type, None)):
                if str(o).startswith("http://example.org/ontology#") and str(o).split("#")[-1] in self.classes:
                    instance_name = str(s).split("#")[-1]
                    class_type = str(o).split("#")[-1]
                    self.instances.append({
                        'name': instance_name,
                        'type': class_type,
                        'label': instance_name.replace('_', ' ')
                    })
            
            print(f"📊 Found {len(self.classes)} classes and {len(self.instances)} instances")
            return True
            
        except Exception as e:
            print(f"❌ Error parsing {self.input_file} as {self.input_format}: {e}")
            return False
    
    def get_priority_concepts(self) -> List[Dict]:
        """Get priority concepts for BioPortal lookup"""
        concepts = []
        
        # Add priority instances
        priority_instances = ['long_covid', 'fatigue', 'immune_dysfunction']
        for instance in self.instances:
            if instance['name'] in priority_instances:
                concepts.append({
                    'key': instance['name'],
                    'label': instance['label'],
                    'type': instance['type'],
                    'category': 'instance'
                })
        
        # Add core classes
        priority_classes = ['Disease', 'Symptom', 'BiologicalProcess', 'MolecularEntity', 'Treatment']
        for class_name in self.classes:
            if class_name in priority_classes:
                concepts.append({
                    'key': class_name,
                    'label': class_name,
                    'type': 'Class',
                    'category': 'class'
                })
        
        return concepts
