"""
Schema parser for YAML, JSON, and Markdown formats with ontology mappings.
"""

import os
import json
import re
from typing import List, Dict, Optional, Tuple
from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef, Literal
from rdflib.namespace import DCTERMS


class SchemaParser:
    """Parses schema files (YAML, JSON, Markdown) and extracts ontology mappings"""
    
    def __init__(self, input_file: str, input_format: Optional[str] = None):
        """Initialize schema parser
        
        Args:
            input_file: Path to schema file
            input_format: Optional format specification (yaml, json, md)
                         If None, auto-detect from filename
        """
        self.input_file = input_file
        self.input_format = input_format or self._detect_format(input_file)
        self.schema_data = None
        self.classes: List[Dict] = []
        self.graph = Graph()
        
    def _detect_format(self, filename: str) -> str:
        """Detect format from file extension"""
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        if ext in ['yaml', 'yml']:
            return 'yaml'
        elif ext == 'json':
            return 'json'
        elif ext in ['md', 'markdown']:
            return 'markdown'
        return 'yaml'  # default
    
    def parse(self) -> bool:
        """Parse the schema file and extract ontology mappings"""
        try:
            if self.input_format == 'yaml':
                return self._parse_yaml()
            elif self.input_format == 'json':
                return self._parse_json()
            elif self.input_format == 'markdown':
                return self._parse_markdown()
            else:
                print(f"❌ Unsupported schema format: {self.input_format}")
                return False
        except Exception as e:
            print(f"❌ Error parsing schema file {self.input_file}: {e}")
            return False
    
    def _parse_yaml(self) -> bool:
        """Parse YAML schema file"""
        try:
            import yaml
        except ImportError:
            print("❌ PyYAML not installed. Install with: pip install pyyaml")
            return False
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.schema_data = yaml.safe_load(f)
        
        return self._extract_classes_from_dict(self.schema_data)
    
    def _parse_json(self) -> bool:
        """Parse JSON schema file"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            self.schema_data = json.load(f)
        
        return self._extract_classes_from_dict(self.schema_data)
    
    def _extract_classes_from_dict(self, data: Dict) -> bool:
        """Extract class definitions from dictionary structure"""
        if 'classes' not in data:
            print("❌ No 'classes' section found in schema")
            return False
        
        classes_data = data['classes']
        
        # Handle both dict and list formats
        if isinstance(classes_data, dict):
            for class_name, class_info in classes_data.items():
                self._process_class(class_name, class_info)
        elif isinstance(classes_data, list):
            for class_info in classes_data:
                if 'name' in class_info:
                    self._process_class(class_info['name'], class_info)
        
        print(f"✅ Loaded {len(self.classes)} classes from {self.input_file}")
        print(f"📊 Found {sum(len(c.get('ontology_mappings', [])) for c in self.classes)} total ontology mappings")
        
        return True
    
    def _process_class(self, class_name: str, class_info: Dict):
        """Process a single class definition"""
        class_dict = {
            'name': class_name,
            'definition': class_info.get('definition', ''),
            'properties': class_info.get('properties', []),
            'relations': class_info.get('relations', []),
            'examples': class_info.get('examples', []),
            'ontology_mappings': []
        }
        
        # Extract ontology mappings
        if 'ontology_mappings' in class_info:
            mappings = class_info['ontology_mappings']
            if isinstance(mappings, list):
                for mapping in mappings:
                    if isinstance(mapping, dict):
                        class_dict['ontology_mappings'].append({
                            'curie': mapping.get('curie', ''),
                            'iri': mapping.get('iri', ''),
                            'prefix': mapping.get('prefix', '')
                        })
                    elif isinstance(mapping, str):
                        # Handle CURIE-only format
                        class_dict['ontology_mappings'].append({
                            'curie': mapping,
                            'iri': self._curie_to_iri(mapping),
                            'prefix': mapping.split(':')[0] if ':' in mapping else ''
                        })
        
        self.classes.append(class_dict)
    
    def _parse_markdown(self) -> bool:
        """Parse Markdown schema file"""
        with open(self.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract classes from markdown
        # Look for headers and extract information
        current_class = None
        current_section = None
        
        for line in content.split('\n'):
            # Check for class headers (### ClassName or - ClassName)
            if line.strip().startswith('###'):
                if current_class:
                    self.classes.append(current_class)
                class_name = line.replace('###', '').strip()
                current_class = {
                    'name': class_name,
                    'definition': '',
                    'ontology_mappings': [],
                    'properties': [],
                    'relations': [],
                    'examples': []
                }
                current_section = None
            elif line.strip().startswith('- ') and current_class is None:
                # Top-level class definition
                if current_class:
                    self.classes.append(current_class)
                class_name = line.replace('-', '').strip()
                current_class = {
                    'name': class_name,
                    'definition': '',
                    'ontology_mappings': [],
                    'properties': [],
                    'relations': [],
                    'examples': []
                }
                current_section = None
            elif current_class:
                # Extract ontology mappings
                if '**Ontology Mappings**:' in line:
                    current_section = 'mappings'
                    # Extract IRIs from the same line
                    iris = re.findall(r'http[s]?://[^\s;]+', line)
                    for iri in iris:
                        current_class['ontology_mappings'].append({
                            'curie': '',
                            'iri': iri.rstrip(');'),
                            'prefix': ''
                        })
                elif 'Definition:' in line or '- Definition:' in line:
                    current_section = 'definition'
                    definition = line.split('Definition:')[-1].strip()
                    current_class['definition'] = definition
                elif 'Examples:' in line or '- Examples:' in line:
                    current_section = 'examples'
                    examples_text = line.split('Examples:')[-1].strip()
                    if examples_text:
                        current_class['examples'].append(examples_text)
                elif 'Properties:' in line or '- Properties:' in line:
                    current_section = 'properties'
                elif 'Relations:' in line or '- Relations:' in line:
                    current_section = 'relations'
                elif current_section == 'properties' and line.strip().startswith('-'):
                    prop = line.strip().lstrip('- ').strip()
                    if prop:
                        current_class['properties'].append(prop)
                elif current_section == 'relations' and line.strip().startswith('-'):
                    rel = line.strip().lstrip('- ').strip()
                    if rel and not rel.startswith('#'):
                        current_class['relations'].append(rel)
        
        # Add last class
        if current_class:
            self.classes.append(current_class)
        
        print(f"✅ Loaded {len(self.classes)} classes from {self.input_file}")
        print(f"📊 Found {sum(len(c.get('ontology_mappings', [])) for c in self.classes)} total ontology mappings")
        
        return True
    
    def _curie_to_iri(self, curie: str) -> str:
        """Convert CURIE to IRI"""
        if ':' not in curie:
            return curie
        
        prefix, local_id = curie.split(':', 1)
        
        # Common prefix mappings
        prefix_map = {
            'NCIT': 'http://purl.obolibrary.org/obo/NCIT_',
            'HP': 'http://purl.obolibrary.org/obo/HP_',
            'MONDO': 'http://purl.obolibrary.org/obo/MONDO_',
            'DOID': 'http://purl.obolibrary.org/obo/DOID_',
            'ICO': 'http://purl.obolibrary.org/obo/ICO_',
            'SIO': 'http://semanticscience.org/resource/SIO_',
            'OMIT': 'http://purl.obolibrary.org/obo/OMIT_',
            'SCDO': 'http://purl.obolibrary.org/obo/SCDO_',
        }
        
        base = prefix_map.get(prefix, f'http://purl.obolibrary.org/obo/{prefix}_')
        return f"{base}{local_id}"
    
    def get_concepts_for_mapping(self) -> List[Dict]:
        """Get concepts that need ontology mapping validation/enhancement"""
        concepts = []
        
        for class_def in self.classes:
            if class_def['ontology_mappings']:
                concepts.append({
                    'key': class_def['name'],
                    'label': class_def['name'],
                    'type': 'Class',
                    'category': 'schema_class',
                    'definition': class_def['definition'],
                    'existing_mappings': class_def['ontology_mappings'],
                    'properties': class_def['properties'],
                    'relations': class_def['relations']
                })
        
        return concepts
    
    def to_rdf_graph(self) -> Graph:
        """Convert schema to RDF graph"""
        # Add namespace bindings
        self.graph.bind("", "http://example.org/schema#")
        self.graph.bind("owl", OWL)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("skos", SKOS)
        self.graph.bind("dcterms", DCTERMS)
        
        for class_def in self.classes:
            class_uri = URIRef(f"http://example.org/schema#{class_def['name']}")
            
            # Add class
            self.graph.add((class_uri, RDF.type, OWL.Class))
            self.graph.add((class_uri, RDFS.label, Literal(class_def['name'], lang='en')))
            
            # Add definition
            if class_def['definition']:
                self.graph.add((class_uri, SKOS.definition, Literal(class_def['definition'], lang='en')))
            
            # Add ontology mappings
            for mapping in class_def['ontology_mappings']:
                if mapping['iri']:
                    mapped_uri = URIRef(mapping['iri'])
                    self.graph.add((class_uri, SKOS.exactMatch, mapped_uri))
        
        return self.graph
