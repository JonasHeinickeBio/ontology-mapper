"""
Ontology generation utilities.
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, Optional, List

from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef, Literal
from rdflib.namespace import DCTERMS

from utils.helpers import clean_description, deduplicate_synonyms, determine_alignment_type
from .parser import OntologyParser


# Supported output formats
SUPPORTED_FORMATS = {
    # RDF formats (via rdflib)
    'turtle': 'turtle',
    'ttl': 'turtle',
    'json-ld': 'json-ld',
    'jsonld': 'json-ld',
    'xml': 'xml',
    'rdf': 'xml',  # .rdf files use RDF/XML
    'rdf-xml': 'xml',
    'rdfxml': 'xml',
    'nt': 'nt',
    'ntriples': 'nt',
    'n-triples': 'nt',
    'n3': 'n3',
    'trig': 'trig',
    'nquads': 'nquads',
    # Custom formats
    'csv': 'csv',
    'tsv': 'tsv',
    'sssom': 'sssom'
}

# Format descriptions for help text
FORMAT_DESCRIPTIONS = {
    'turtle': 'Turtle (default) - Human-readable RDF format',
    'json-ld': 'JSON-LD - JSON format for linked data',
    'xml': 'RDF/XML - Traditional RDF XML format',
    'nt': 'N-Triples - Simple line-based RDF format',
    'n3': 'Notation3 - Superset of Turtle with rules',
    'trig': 'TriG - Turtle with named graphs',
    'nquads': 'N-Quads - N-Triples with named graphs',
    'csv': 'CSV - Comma-separated values (tabular)',
    'tsv': 'TSV - Tab-separated values (tabular)',
    'sssom': 'SSSOM TSV - Simple Standard for Sharing Ontology Mappings'
}


class OntologyGenerator:
    """Generates improved ontologies with alignments"""
    
    @staticmethod
    def get_supported_formats() -> List[str]:
        """Get list of supported output formats"""
        return sorted(set(SUPPORTED_FORMATS.values()))
    
    @staticmethod
    def get_format_descriptions() -> Dict[str, str]:
        """Get format descriptions for help text"""
        return FORMAT_DESCRIPTIONS.copy()
    
    def _normalize_format(self, format_str: str) -> str:
        """Normalize format string to canonical format name"""
        if not format_str:
            return 'turtle'  # Default format
        
        format_lower = format_str.lower().strip()
        if format_lower in SUPPORTED_FORMATS:
            return SUPPORTED_FORMATS[format_lower]
        
        # Try to extract format from file extension
        if '.' in format_lower:
            ext = format_lower.split('.')[-1]
            if ext in SUPPORTED_FORMATS:
                return SUPPORTED_FORMATS[ext]
        
        raise ValueError(f"Unsupported format: {format_str}. Supported formats: {', '.join(sorted(set(SUPPORTED_FORMATS.values())))}")
    
    def _detect_format_from_filename(self, filename: str) -> Optional[str]:
        """Detect output format from filename extension"""
        if not filename:
            return None
        
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        return SUPPORTED_FORMATS.get(ext)
    
    def _serialize_graph(self, graph: Graph, output_file: str, format_name: str):
        """Serialize RDF graph to file in specified format"""
        if format_name in ['csv', 'tsv', 'sssom']:
            # Custom serialization
            if format_name == 'sssom':
                self._serialize_sssom(graph, output_file)
            else:
                self._serialize_tabular(graph, output_file, format_name)
        else:
            # RDF serialization via rdflib
            graph.serialize(destination=output_file, format=format_name)
    
    def _serialize_tabular(self, graph: Graph, output_file: str, format_name: str):
        """Serialize graph to CSV/TSV format"""
        delimiter = '\t' if format_name == 'tsv' else ','
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=delimiter)
            
            # Write header
            writer.writerow(['Subject', 'Predicate', 'Object', 'Object Type'])
            
            # Write triples
            for s, p, o in graph:
                obj_type = 'URI' if isinstance(o, URIRef) else 'Literal'
                writer.writerow([str(s), str(p), str(o), obj_type])
    
    def _get_entity_label(self, uri: URIRef, graph: Graph) -> Optional[str]:
        """Extract label for an entity from the graph
        
        Args:
            uri: The URI of the entity
            graph: The RDF graph to search
            
        Returns:
            Label string if found, None otherwise
        """
        # Try SKOS prefLabel first (more specific)
        for _, _, label in graph.triples((uri, SKOS.prefLabel, None)):
            return str(label)
        
        # Fall back to RDFS label
        for _, _, label in graph.triples((uri, RDFS.label, None)):
            return str(label)
        
        return None
    
    def _serialize_sssom(self, graph: Graph, output_file: str):
        """Serialize graph to SSSOM (Simple Standard for Sharing Ontology Mappings) format"""
        mappings = []
        
        # Extract mapping information from graph
        for s, p, o in graph:
            if p in [SKOS.exactMatch, SKOS.closeMatch, SKOS.relatedMatch, 
                     SKOS.broadMatch, SKOS.narrowMatch, RDFS.seeAlso]:
                if isinstance(o, URIRef):
                    # Determine mapping predicate
                    if p == SKOS.exactMatch:
                        predicate_id = 'skos:exactMatch'
                    elif p == SKOS.closeMatch:
                        predicate_id = 'skos:closeMatch'
                    elif p == SKOS.relatedMatch:
                        predicate_id = 'skos:relatedMatch'
                    elif p == SKOS.broadMatch:
                        predicate_id = 'skos:broadMatch'
                    elif p == SKOS.narrowMatch:
                        predicate_id = 'skos:narrowMatch'
                    else:
                        predicate_id = 'rdfs:seeAlso'
                    
                    # Get labels using helper method
                    subject_label = self._get_entity_label(s, graph)
                    object_label = self._get_entity_label(o, graph)
                    
                    mappings.append({
                        'subject_id': str(s),
                        'subject_label': subject_label or '',
                        'predicate_id': predicate_id,
                        'object_id': str(o),
                        'object_label': object_label or '',
                        'mapping_justification': 'semapv:ManualMappingCuration',
                        'mapping_date': datetime.now().strftime('%Y-%m-%d')
                    })
        
        # Write SSSOM TSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, delimiter='\t', fieldnames=[
                'subject_id', 'subject_label', 'predicate_id', 'object_id', 
                'object_label', 'mapping_justification', 'mapping_date'
            ])
            writer.writeheader()
            writer.writerows(mappings)
    
    def _determine_output_format(self, output_file: str, output_format: Optional[str]) -> str:
        """Determine the output format from explicit format parameter or filename
        
        Args:
            output_file: Path to output file
            output_format: Optional explicit format specification
            
        Returns:
            Normalized format name
        """
        if output_format:
            return self._normalize_format(output_format)
        else:
            return self._detect_format_from_filename(output_file) or 'turtle'
    
    def generate_improved_ontology(self, ontology: OntologyParser, selections: Dict, 
                                  output_file: str, report_file: Optional[str] = None,
                                  output_format: Optional[str] = None):
        """Generate improved ontology with selected alignments
        
        Args:
            ontology: Parsed ontology object
            selections: Dictionary of concept alignments
            output_file: Path to output file
            report_file: Optional path to report file
            output_format: Output format (turtle, json-ld, xml, nt, csv, tsv, sssom, etc.)
                          If None, auto-detect from filename or use turtle
        """
        # Determine output format
        format_name = self._determine_output_format(output_file, output_format)
        
        print(f"\n💾 Generating Improved Ontology ({format_name})")
        print("=" * 35)
        
        # Create enhanced graph
        improved_graph = Graph()
        
        # Copy original ontology
        for s, p, o in ontology.graph:
            improved_graph.add((s, p, o))
        
        # Add namespace bindings - using standard vocabularies
        improved_graph.bind("", "http://example.org/ontology#")
        improved_graph.bind("owl", OWL)
        improved_graph.bind("skos", SKOS)
        improved_graph.bind("dcterms", DCTERMS)
        improved_graph.bind("prov", "http://www.w3.org/ns/prov#")
        improved_graph.bind("mondo", "http://purl.obolibrary.org/obo/MONDO_")
        improved_graph.bind("hp", "http://purl.obolibrary.org/obo/HP_")
        improved_graph.bind("go", "http://purl.obolibrary.org/obo/GO_")
        improved_graph.bind("ncit", "http://purl.obolibrary.org/obo/NCIT_")
        improved_graph.bind("efo", "http://www.ebi.ac.uk/efo/EFO_")
        improved_graph.bind("doid", "http://purl.obolibrary.org/obo/DOID_")
        
        # Add alignments with standardized properties
        total_alignments = 0
        for concept_key, alignments in selections.items():
            local_uri = URIRef(f"http://example.org/ontology#{concept_key}")
            
            for alignment in alignments:
                external_uri = URIRef(alignment['uri'])
                
                # Determine alignment type and relationship based on confidence
                alignment_type = determine_alignment_type(alignment, concept_key)
                
                # Add standardized alignment relationship
                if alignment_type == 'exact':
                    improved_graph.add((local_uri, SKOS.exactMatch, external_uri))
                elif alignment_type == 'close':
                    improved_graph.add((local_uri, SKOS.closeMatch, external_uri))
                elif alignment_type == 'related':
                    improved_graph.add((local_uri, SKOS.relatedMatch, external_uri))
                elif alignment_type == 'broader':
                    improved_graph.add((local_uri, SKOS.broadMatch, external_uri))
                elif alignment_type == 'narrower':
                    improved_graph.add((local_uri, SKOS.narrowMatch, external_uri))
                else:
                    improved_graph.add((local_uri, RDFS.seeAlso, external_uri))
                
                # Add standard metadata using SKOS and DCTERMS
                improved_graph.add((local_uri, SKOS.inScheme, URIRef(f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}")))
                improved_graph.add((local_uri, DCTERMS.source, URIRef(f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}")))
                
                # Use standard SKOS properties for labels and descriptions
                if alignment.get('label') and alignment['label'].strip():
                    improved_graph.add((local_uri, SKOS.prefLabel, Literal(alignment['label'], lang='en')))
                
                # Add description using standard DCTERMS
                if alignment.get('description') and alignment['description'].strip():
                    clean_desc = clean_description(alignment['description'])
                    if clean_desc:
                        improved_graph.add((local_uri, DCTERMS.description, Literal(clean_desc, lang='en')))
                
                # Add synonyms using SKOS altLabel, avoiding duplicates
                if alignment.get('synonyms'):
                    unique_synonyms = deduplicate_synonyms(alignment['synonyms'], set())
                    for synonym in unique_synonyms[:3]:  # Limit to 3 synonyms
                        improved_graph.add((local_uri, SKOS.altLabel, Literal(synonym, lang='en')))
                
                # Add provenance for this alignment
                prov_node = URIRef(f"http://example.org/ontology#alignment_{concept_key}_{total_alignments}")
                improved_graph.add((prov_node, RDF.type, URIRef("http://www.w3.org/ns/prov#Entity")))
                improved_graph.add((prov_node, URIRef("http://www.w3.org/ns/prov#wasAttributedTo"), 
                                 URIRef(f"http://example.org/ontology#{alignment['source']}_service")))
                improved_graph.add((prov_node, DCTERMS.created, Literal(datetime.now().isoformat())))
                
                total_alignments += 1
                source_icon = "🌐" if alignment['source'] == 'bioportal' else "🔬"
                print(f"✅ {source_icon} {concept_key} → {alignment['label']} ({alignment['ontology']}) [{alignment_type}]")
        
        # Add enhanced provenance using PROV-O vocabulary
        prov_activity = URIRef("http://example.org/ontology#BioPortalCLIAlignment")
        improved_graph.add((prov_activity, RDF.type, URIRef("http://www.w3.org/ns/prov#Activity")))
        improved_graph.add((prov_activity, DCTERMS.title, Literal("Ontology Alignment Activity", lang='en')))
        improved_graph.add((prov_activity, DCTERMS.description, 
                         Literal("Automated ontology alignment using BioPortal and OLS services", lang='en')))
        improved_graph.add((prov_activity, URIRef("http://www.w3.org/ns/prov#startedAtTime"), 
                         Literal(datetime.now().isoformat())))
        improved_graph.add((prov_activity, URIRef("http://www.w3.org/ns/prov#endedAtTime"), 
                         Literal(datetime.now().isoformat())))
        
        # Add tool information
        tool_agent = URIRef("http://example.org/ontology#BioPortalCLITool")
        improved_graph.add((tool_agent, RDF.type, URIRef("http://www.w3.org/ns/prov#SoftwareAgent")))
        improved_graph.add((tool_agent, DCTERMS.title, Literal("BioPortal CLI Alignment Tool", lang='en')))
        improved_graph.add((tool_agent, URIRef("http://www.w3.org/ns/prov#wasAssociatedWith"), prov_activity))
        
        # Add statistics as structured data
        stats_node = URIRef("http://example.org/ontology#AlignmentStatistics")
        improved_graph.add((stats_node, RDF.type, URIRef("http://www.w3.org/ns/prov#Entity")))
        improved_graph.add((stats_node, URIRef("http://www.w3.org/ns/prov#wasGeneratedBy"), prov_activity))
        improved_graph.add((stats_node, URIRef("http://example.org/vocab#alignmentCount"), 
                         Literal(total_alignments, datatype=URIRef("http://www.w3.org/2001/XMLSchema#integer"))))
        improved_graph.add((stats_node, URIRef("http://example.org/vocab#conceptCount"), 
                         Literal(len(selections), datatype=URIRef("http://www.w3.org/2001/XMLSchema#integer"))))
        
        # Save improved ontology using the specified format
        self._serialize_graph(improved_graph, output_file, format_name)
        
        # Generate report only if specified
        if report_file:
            report = {
                'timestamp': datetime.now().isoformat(),
                'input_file': ontology.ttl_file,
                'output_file': output_file,
                'output_format': format_name,
                'original_triples': len(ontology.graph),
                'improved_triples': len(improved_graph),
                'alignments_added': total_alignments,
                'concepts_aligned': len(selections),
                'selections': selections
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n🎉 SUCCESS!")
        print(f"  Input: {ontology.ttl_file}")
        print(f"  Output: {output_file} ({format_name})")
        if report_file:
            print(f"  Report: {report_file}")
        print(f"  Original triples: {len(ontology.graph):,}")
        print(f"  New triples: {len(improved_graph) - len(ontology.graph):,}")
        print(f"  Total triples: {len(improved_graph):,}")
        print(f"  Concepts aligned: {len(selections)}")
        print(f"  Total alignments: {total_alignments}")
        
        # Show file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"  File size: {size:,} bytes")
    
    def generate_single_word_ontology(self, concept: Dict, selections: Dict, 
                                     output_file: str, report_file: Optional[str] = None,
                                     output_format: Optional[str] = None):
        """Generate ontology for single word query
        
        Args:
            concept: Concept dictionary with label and key
            selections: Dictionary of concept alignments
            output_file: Path to output file
            report_file: Optional path to report file
            output_format: Output format (turtle, json-ld, xml, nt, csv, tsv, sssom, etc.)
                          If None, auto-detect from filename or use turtle
        """
        # Determine output format
        format_name = self._determine_output_format(output_file, output_format)
        
        print(f"\n💾 Generating Ontology for Single Word Query ({format_name})")
        print("=" * 45)
        
        # Create new graph
        graph = Graph()
        
        # Add namespace bindings
        graph.bind("", "http://example.org/query#")
        graph.bind("owl", OWL)
        graph.bind("skos", SKOS)
        graph.bind("dcterms", DCTERMS)
        graph.bind("prov", "http://www.w3.org/ns/prov#")
        
        # Create local concept
        local_uri = URIRef(f"http://example.org/query#{concept['key']}")
        graph.add((local_uri, RDF.type, OWL.Class))
        graph.add((local_uri, RDFS.label, Literal(concept['label'], lang='en')))
        graph.add((local_uri, SKOS.prefLabel, Literal(concept['label'], lang='en')))
        
        # Add alignments
        total_alignments = 0
        for concept_key, alignments in selections.items():
            for alignment in alignments:
                external_uri = URIRef(alignment['uri'])
                
                # Determine alignment type
                alignment_type = determine_alignment_type(alignment, concept_key)
                
                # Add standardized alignment relationship
                if alignment_type == 'exact':
                    graph.add((local_uri, SKOS.exactMatch, external_uri))
                elif alignment_type == 'close':
                    graph.add((local_uri, SKOS.closeMatch, external_uri))
                elif alignment_type == 'related':
                    graph.add((local_uri, SKOS.relatedMatch, external_uri))
                elif alignment_type == 'broader':
                    graph.add((local_uri, SKOS.broadMatch, external_uri))
                elif alignment_type == 'narrower':
                    graph.add((local_uri, SKOS.narrowMatch, external_uri))
                else:
                    graph.add((local_uri, RDFS.seeAlso, external_uri))
                
                # Add metadata
                graph.add((local_uri, SKOS.inScheme, URIRef(f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}")))
                graph.add((local_uri, DCTERMS.source, URIRef(f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}")))
                
                # Add description
                if alignment.get('description') and alignment['description'].strip():
                    clean_desc = clean_description(alignment['description'])
                    if clean_desc:
                        graph.add((local_uri, DCTERMS.description, Literal(clean_desc, lang='en')))
                
                # Add synonyms
                if alignment.get('synonyms'):
                    unique_synonyms = deduplicate_synonyms(alignment['synonyms'], set())
                    for synonym in unique_synonyms[:3]:
                        graph.add((local_uri, SKOS.altLabel, Literal(synonym, lang='en')))
                
                total_alignments += 1
                source_icon = "🌐" if alignment['source'] == 'bioportal' else "🔬"
                print(f"✅ {source_icon} {concept_key} → {alignment['label']} ({alignment['ontology']}) [{alignment_type}]")
        
        # Add provenance
        prov_activity = URIRef("http://example.org/query#SingleWordAlignment")
        graph.add((prov_activity, RDF.type, URIRef("http://www.w3.org/ns/prov#Activity")))
        graph.add((prov_activity, DCTERMS.title, Literal("Single Word Query Alignment", lang='en')))
        graph.add((prov_activity, URIRef("http://www.w3.org/ns/prov#startedAtTime"), 
                 Literal(datetime.now().isoformat())))
        
        # Save ontology using the specified format
        self._serialize_graph(graph, output_file, format_name)
        
        # Generate report only if specified
        if report_file:
            report = {
                'timestamp': datetime.now().isoformat(),
                'query_term': concept['label'],
                'output_file': output_file,
                'output_format': format_name,
                'total_triples': len(graph),
                'alignments_added': total_alignments,
                'selections': selections
            }
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n🎉 SUCCESS!")
        print(f"  Query: {concept['label']}")
        print(f"  Output: {output_file} ({format_name})")
        if report_file:
            print(f"  Report: {report_file}")
        print(f"  Total triples: {len(graph):,}")
        print(f"  Total alignments: {total_alignments}")
        
        # Show file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            print(f"  File size: {size:,} bytes")
