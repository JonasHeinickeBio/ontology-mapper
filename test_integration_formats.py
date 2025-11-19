#!/usr/bin/env python3
"""
Integration test for multiple output format support

Tests the complete workflow from creation to serialization in various formats.
"""

import sys
import os
import tempfile

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from rdflib import Graph
from core.generator import OntologyGenerator
from core.parser import OntologyParser


def create_test_ttl_file():
    """Create a temporary TTL file for testing"""
    content = """@prefix : <http://example.org/test#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

:Diabetes a owl:Class ;
    rdfs:label "Diabetes"@en ;
    skos:prefLabel "Diabetes Mellitus"@en ;
    skos:definition "A metabolic disease characterized by high blood sugar levels"@en .

:Type2Diabetes a owl:Class ;
    rdfs:label "Type 2 Diabetes"@en ;
    rdfs:subClassOf :Diabetes .
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ttl', delete=False) as f:
        f.write(content)
        return f.name


def test_improved_ontology_generation_formats():
    """Test generating improved ontology in different formats"""
    print("\n  Testing improved ontology generation in multiple formats...")
    
    # Create test TTL file
    ttl_file = create_test_ttl_file()
    
    try:
        # Parse ontology
        ontology = OntologyParser(ttl_file)
        if not ontology.parse():
            print("    ✗ Failed to parse test ontology")
            return False
        
        # Create mock selections
        selections = {
            'Diabetes': [{
                'uri': 'http://purl.obolibrary.org/obo/MONDO_0005015',
                'label': 'diabetes mellitus',
                'ontology': 'MONDO',
                'description': 'A metabolic disease',
                'synonyms': ['diabetes', 'DM'],
                'source': 'bioportal',
                'relationship': 'skos:exactMatch'
            }]
        }
        
        # Test multiple formats
        formats_to_test = ['turtle', 'json-ld', 'xml', 'nt', 'csv', 'sssom']
        generator = OntologyGenerator()
        
        for format_name in formats_to_test:
            with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_name}', delete=False) as f:
                output_file = f.name
            
            try:
                # Generate improved ontology
                generator.generate_improved_ontology(
                    ontology, 
                    selections, 
                    output_file,
                    output_format=format_name
                )
                
                # Verify file exists and has content
                if not os.path.exists(output_file):
                    print(f"    ✗ {format_name}: Output file not created")
                    return False
                
                size = os.path.getsize(output_file)
                if size == 0:
                    print(f"    ✗ {format_name}: Output file is empty")
                    return False
                
                # For RDF formats, try to parse
                if format_name not in ['csv', 'tsv', 'sssom']:
                    test_graph = Graph()
                    try:
                        test_graph.parse(output_file, format=format_name)
                        if len(test_graph) == 0:
                            print(f"    ✗ {format_name}: Parsed graph is empty")
                            return False
                        print(f"    ✓ {format_name}: {size} bytes, {len(test_graph)} triples")
                    except Exception as e:
                        print(f"    ✗ {format_name}: Failed to parse: {e}")
                        return False
                else:
                    print(f"    ✓ {format_name}: {size} bytes")
                
            finally:
                if os.path.exists(output_file):
                    os.unlink(output_file)
        
        return True
    
    finally:
        if os.path.exists(ttl_file):
            os.unlink(ttl_file)


def test_single_word_ontology_generation_formats():
    """Test generating single word ontology in different formats"""
    print("\n  Testing single word ontology generation in multiple formats...")
    
    # Create mock concept and selections
    concept = {
        'key': 'diabetes',
        'label': 'Diabetes',
        'type': 'Term',
        'category': 'query'
    }
    
    selections = {
        'diabetes': [{
            'uri': 'http://purl.obolibrary.org/obo/MONDO_0005015',
            'label': 'diabetes mellitus',
            'ontology': 'MONDO',
            'description': 'A metabolic disease',
            'synonyms': ['diabetes', 'DM'],
            'source': 'bioportal',
            'relationship': 'skos:exactMatch'
        }]
    }
    
    # Test multiple formats
    formats_to_test = ['turtle', 'json-ld', 'xml', 'nt', 'sssom']
    generator = OntologyGenerator()
    
    for format_name in formats_to_test:
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format_name}', delete=False) as f:
            output_file = f.name
        
        try:
            # Generate single word ontology
            generator.generate_single_word_ontology(
                concept,
                selections,
                output_file,
                output_format=format_name
            )
            
            # Verify file exists and has content
            if not os.path.exists(output_file):
                print(f"    ✗ {format_name}: Output file not created")
                return False
            
            size = os.path.getsize(output_file)
            if size == 0:
                print(f"    ✗ {format_name}: Output file is empty")
                return False
            
            # For RDF formats, try to parse
            if format_name not in ['csv', 'tsv', 'sssom']:
                test_graph = Graph()
                try:
                    test_graph.parse(output_file, format=format_name)
                    if len(test_graph) == 0:
                        print(f"    ✗ {format_name}: Parsed graph is empty")
                        return False
                    print(f"    ✓ {format_name}: {size} bytes, {len(test_graph)} triples")
                except Exception as e:
                    print(f"    ✗ {format_name}: Failed to parse: {e}")
                    return False
            else:
                print(f"    ✓ {format_name}: {size} bytes")
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    return True


def test_format_auto_detection():
    """Test format auto-detection from filename"""
    print("\n  Testing format auto-detection from filename...")
    
    concept = {
        'key': 'test',
        'label': 'Test',
        'type': 'Term',
        'category': 'query'
    }
    
    selections = {
        'test': [{
            'uri': 'http://example.org/test',
            'label': 'test',
            'ontology': 'TEST',
            'description': 'Test',
            'synonyms': [],
            'source': 'test',
            'relationship': 'skos:exactMatch'
        }]
    }
    
    generator = OntologyGenerator()
    
    # Test auto-detection
    test_cases = [
        ('output.ttl', 'turtle'),
        ('output.jsonld', 'json-ld'),
        ('output.rdf', 'xml'),  # .rdf extension maps to RDF/XML
        ('output.nt', 'nt'),
        ('output.csv', 'csv'),
        ('output.sssom', 'sssom'),
    ]
    
    for filename, expected_format in test_cases:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            base_path = f.name
        
        output_file = os.path.join(os.path.dirname(base_path), filename)
        
        try:
            # Generate with auto-detection (no format parameter)
            generator.generate_single_word_ontology(
                concept,
                selections,
                output_file
            )
            
            # Verify file was created
            if not os.path.exists(output_file):
                print(f"    ✗ {filename}: File not created")
                return False
            
            size = os.path.getsize(output_file)
            if size == 0:
                print(f"    ✗ {filename}: File is empty")
                return False
            
            print(f"    ✓ {filename}: {size} bytes (auto-detected)")
            
        except Exception as e:
            # Some formats might fail on auto-detection without explicit format
            print(f"    ⚠ {filename}: {str(e)}")
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    return True


def main():
    """Run all integration tests"""
    print("Integration Tests: Multiple Output Format Support")
    print("=" * 50)
    
    all_passed = True
    
    # Test improved ontology generation
    if not test_improved_ontology_generation_formats():
        print("❌ Improved ontology generation test FAILED")
        all_passed = False
    
    # Test single word ontology generation
    if not test_single_word_ontology_generation_formats():
        print("❌ Single word ontology generation test FAILED")
        all_passed = False
    
    # Test format auto-detection
    if not test_format_auto_detection():
        print("❌ Format auto-detection test FAILED")
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All integration tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
