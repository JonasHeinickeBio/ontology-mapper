#!/usr/bin/env python3
"""
Test script for multiple output format support
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from rdflib import Graph, RDF, RDFS, OWL, SKOS, URIRef, Literal
from rdflib.namespace import DCTERMS
from core.generator import OntologyGenerator
from core.parser import OntologyParser


def create_test_graph():
    """Create a simple test graph with alignments"""
    graph = Graph()
    
    # Add namespace bindings
    graph.bind("", "http://example.org/test#")
    graph.bind("owl", OWL)
    graph.bind("skos", SKOS)
    graph.bind("dcterms", DCTERMS)
    
    # Create a simple ontology
    concept = URIRef("http://example.org/test#Diabetes")
    graph.add((concept, RDF.type, OWL.Class))
    graph.add((concept, RDFS.label, Literal("Diabetes", lang='en')))
    graph.add((concept, SKOS.prefLabel, Literal("Diabetes Mellitus", lang='en')))
    graph.add((concept, DCTERMS.description, Literal("A metabolic disease", lang='en')))
    
    # Add alignment
    external = URIRef("http://purl.obolibrary.org/obo/MONDO_0005015")
    graph.add((concept, SKOS.exactMatch, external))
    graph.add((concept, SKOS.inScheme, URIRef("http://bioportal.bioontology.org/ontologies/MONDO")))
    
    return graph


def test_rdf_serialization(format_name):
    """Test RDF format serialization"""
    print(f"\n  Testing {format_name} format...")
    
    graph = create_test_graph()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_name}', delete=False) as f:
        output_file = f.name
    
    try:
        generator = OntologyGenerator()
        generator._serialize_graph(graph, output_file, format_name)
        
        # Verify file was created and has content
        if not os.path.exists(output_file):
            print(f"    ✗ File not created")
            return False
        
        size = os.path.getsize(output_file)
        if size == 0:
            print(f"    ✗ File is empty")
            return False
        
        # For RDF formats, try to parse it back
        if format_name not in ['csv', 'tsv', 'sssom']:
            test_graph = Graph()
            try:
                test_graph.parse(output_file, format=format_name)
                if len(test_graph) == 0:
                    print(f"    ✗ Parsed graph is empty")
                    return False
                print(f"    ✓ {format_name}: {size} bytes, {len(test_graph)} triples")
            except Exception as e:
                print(f"    ✗ Failed to parse: {e}")
                return False
        else:
            print(f"    ✓ {format_name}: {size} bytes (tabular format)")
        
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_tabular_export():
    """Test CSV/TSV export"""
    print(f"\n  Testing tabular exports...")
    
    graph = create_test_graph()
    generator = OntologyGenerator()
    
    for format_name in ['csv', 'tsv']:
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_name}', delete=False) as f:
            output_file = f.name
        
        try:
            generator._serialize_tabular(graph, output_file, format_name)
            
            if not os.path.exists(output_file):
                print(f"    ✗ {format_name}: File not created")
                return False
            
            size = os.path.getsize(output_file)
            if size == 0:
                print(f"    ✗ {format_name}: File is empty")
                return False
            
            # Read and verify content
            with open(output_file, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:  # Header + at least one row
                    print(f"    ✗ {format_name}: Too few lines")
                    return False
            
            print(f"    ✓ {format_name}: {size} bytes, {len(lines)-1} triples")
        except Exception as e:
            print(f"    ✗ {format_name}: Error: {e}")
            return False
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    return True


def test_sssom_export():
    """Test SSSOM export"""
    print(f"\n  Testing SSSOM export...")
    
    graph = create_test_graph()
    generator = OntologyGenerator()
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sssom.tsv', delete=False) as f:
        output_file = f.name
    
    try:
        generator._serialize_sssom(graph, output_file)
        
        if not os.path.exists(output_file):
            print(f"    ✗ File not created")
            return False
        
        size = os.path.getsize(output_file)
        if size == 0:
            print(f"    ✗ File is empty")
            return False
        
        # Read and verify SSSOM format
        with open(output_file, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:  # Header + at least one mapping
                print(f"    ✗ Too few lines")
                return False
            
            # Check header
            header = lines[0].strip().split('\t')
            required_fields = ['subject_id', 'predicate_id', 'object_id']
            for field in required_fields:
                if field not in header:
                    print(f"    ✗ Missing required field: {field}")
                    return False
        
        print(f"    ✓ SSSOM: {size} bytes, {len(lines)-1} mappings")
        return True
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def test_format_detection():
    """Test format detection from filename"""
    print(f"\n  Testing format detection from filename...")
    
    generator = OntologyGenerator()
    
    test_cases = [
        ('output.ttl', 'turtle'),
        ('output.jsonld', 'json-ld'),
        ('output.rdf', 'xml'),  # .rdf maps to xml (RDF/XML)
        ('output.xml', 'xml'),
        ('output.nt', 'nt'),
        ('output.csv', 'csv'),
        ('output.tsv', 'tsv'),
        ('output.sssom', 'sssom'),
    ]
    
    for filename, expected in test_cases:
        result = generator._detect_format_from_filename(filename)
        if result == expected:
            print(f"    ✓ {filename} -> {result}")
        else:
            print(f"    ✗ {filename} -> {result} (expected {expected})")
            return False
    
    return True


def test_format_validation():
    """Test format validation"""
    print(f"\n  Testing format validation...")
    
    generator = OntologyGenerator()
    
    # Valid formats
    valid_formats = ['turtle', 'ttl', 'json-ld', 'xml', 'nt', 'csv', 'tsv', 'sssom']
    for fmt in valid_formats:
        try:
            normalized = generator._normalize_format(fmt)
            print(f"    ✓ Valid format: {fmt} -> {normalized}")
        except ValueError as e:
            print(f"    ✗ Unexpected error for valid format {fmt}: {e}")
            return False
    
    # Invalid format
    try:
        generator._normalize_format('invalid_format')
        print(f"    ✗ Should have raised ValueError for invalid format")
        return False
    except ValueError:
        print(f"    ✓ Invalid format properly rejected")
    
    return True


def main():
    """Run all format tests"""
    print("Testing Multiple Output Format Support")
    print("=" * 50)
    
    all_passed = True
    
    # Test format validation
    if not test_format_validation():
        print("❌ Format validation test FAILED")
        all_passed = False
    
    # Test format detection
    if not test_format_detection():
        print("❌ Format detection test FAILED")
        all_passed = False
    
    # Test RDF formats
    rdf_formats = ['turtle', 'json-ld', 'xml', 'nt', 'n3']
    for fmt in rdf_formats:
        if not test_rdf_serialization(fmt):
            print(f"❌ {fmt} serialization test FAILED")
            all_passed = False
    
    # Test tabular export
    if not test_tabular_export():
        print("❌ Tabular export test FAILED")
        all_passed = False
    
    # Test SSSOM export
    if not test_sssom_export():
        print("❌ SSSOM export test FAILED")
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All format tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
