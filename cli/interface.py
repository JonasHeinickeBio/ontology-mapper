"""
CLI interface for the ontology mapping tool.
"""

import os
import sys
import json
import argparse
from typing import Dict, List

from services import BioPortalLookup, OLSLookup
from core import OntologyParser, SchemaParser, ConceptLookup, OntologyGenerator
from config import ONTOLOGY_CONFIGS, ONTOLOGY_COMBINATIONS
from cache import CacheManager, CacheConfig


class SchemaGraphWrapper:
    """Wrapper for schema parser graph to maintain compatibility with OntologyParser interface"""
    
    def __init__(self, graph, ttl_file):
        self.graph = graph
        self.ttl_file = ttl_file


class CLIInterface:
    """Command-line interface for the tool"""
    
    def __init__(self):
        self.parser = self._create_parser()
        
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser"""
        parser = argparse.ArgumentParser(
            description="BioPortal Ontology Alignment CLI Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m ontology_mapping.cli ontology.ttl
  python -m ontology_mapping.cli ontology.ttl --output improved.ttl --api-key YOUR_KEY
  python -m ontology_mapping.cli ontology.ttl --batch-mode selections.json
  python -m ontology_mapping.cli --single-word "fatigue" --ontologies "HP,NCIT"
  python -m ontology_mapping.cli --single-word "covid" --ontologies "MONDO,DOID" --output covid_alignments.ttl
            """
        )
        
        # Make ttl_file optional when using single-word mode
        parser.add_argument('ttl_file', nargs='?', help='Path to ontology/schema file (RDF, YAML, JSON, or Markdown)')
        parser.add_argument('--output', '-o', default='improved_ontology.ttl',
                          help='Output file for improved ontology (default: improved_ontology.ttl)')
        parser.add_argument('--api-key', help='BioPortal API key (or set BIOPORTAL_API_KEY env var)')
        parser.add_argument('--batch-mode', help='JSON file with pre-selected choices for batch processing')
        parser.add_argument('--report', 
                          help='Output file for alignment report (only generated if specified)')
        parser.add_argument('--disable-ols', action='store_true',
                          help='Disable OLS lookups (use only BioPortal)')
        parser.add_argument('--disable-bioportal', action='store_true',
                          help='Disable BioPortal lookups (use only OLS)')
        parser.add_argument('--comparison-only', action='store_true',
                          help='Run comparison analysis without generating improved ontology')
        
        # New arguments for ontology selection and single word queries
        parser.add_argument('--ontologies', '-ont', 
                          help='Comma-separated list of ontologies to search (e.g., HP,NCIT,MONDO)')
        parser.add_argument('--single-word', '-sw',
                          help='Query a single word/term instead of processing an ontology file')
        parser.add_argument('--list-ontologies', action='store_true',
                          help='Show available ontologies and exit')
        parser.add_argument('--max-results', type=int, default=5,
                          help='Maximum number of results per search (default: 5)')
        parser.add_argument('--terminal-only', action='store_true',
                          help='Only print results to terminal, do not generate output files')
        
        # Format arguments
        parser.add_argument('--input-format', '--if',
                          help='Input format: turtle/ttl, json-ld, xml/rdf-xml, nt/ntriples, n3, trig, nquads, yaml, json, markdown (auto-detected from extension if not specified)')
        parser.add_argument('--format', '-f',
                          help='Output format: turtle/ttl (default), json-ld, xml/rdf-xml, nt/ntriples, n3, trig, nquads, csv, tsv, sssom')
        parser.add_argument('--list-formats', action='store_true',
                          help='Show available input and output formats and exit')
        parser.add_argument('--list-input-formats', action='store_true',
                          help='Show available input formats and exit')
        parser.add_argument('--schema-mode', action='store_true',
                          help='Parse as schema file (YAML/JSON/Markdown) with ontology mappings instead of RDF')
        
        # Cache management arguments
        parser.add_argument('--clear-cache', action='store_true',
                          help='Clear all cached API responses')
        parser.add_argument('--cache-stats', action='store_true',
                          help='Show cache statistics')
        parser.add_argument('--no-cache', action='store_true',
                          help='Disable cache for this run')
        
        return parser
    
    def _list_available_ontologies(self):
        """Display available ontologies and their descriptions"""
        print("\n🔍 Available Ontologies")
        print("=" * 50)
        
        print("\n📋 Individual Ontologies:")
        for ont, desc in ONTOLOGY_CONFIGS.items():
            print(f"  {ont:12s} - {desc}")
        
        print("\n🎯 Recommended Combinations:")
        for category, onts in ONTOLOGY_COMBINATIONS.items():
            print(f"  {category:15s} - {onts}")
        
        print("\n💡 Usage Examples:")
        print("  --ontologies 'HP,NCIT'           # Phenotypes and clinical terms")
        print("  --ontologies 'MONDO,DOID'        # Disease ontologies")
        print("  --ontologies 'CHEBI,RXNORM'      # Chemical and drug terms")
        print("  --ontologies 'GO,PRO'            # Gene/protein related")
        print("\n")
    
    def _list_available_input_formats(self):
        """Display available input formats and their descriptions"""
        from core.parser import OntologyParser
        
        print("\n📥 Available Input Formats")
        print("=" * 50)
        
        print("\n📊 RDF Formats (via rdflib):")
        descriptions = OntologyParser.get_input_format_descriptions()
        for fmt in sorted(descriptions.keys()):
            print(f"  {fmt:12s} - {descriptions[fmt]}")
        
        print("\n📋 Schema Formats (with ontology_mappings):")
        print(f"  yaml         - YAML schema files with ontology mappings")
        print(f"  json         - JSON schema files with ontology mappings")
        print(f"  markdown     - Markdown documentation with ontology mappings")
        
        print("\n💡 Usage Examples:")
        print("  --input-format json-ld           # Parse JSON-LD RDF input")
        print("  --input-format xml               # Parse RDF/XML input")
        print("  --input-format yaml --schema-mode  # Parse YAML schema")
        print("  python main.py schema.yaml --schema-mode")
        print("  python main.py ontology.jsonld   # Auto-detect RDF format")
        print("\n")
    
    def _list_available_formats(self):
        """Display available input and output formats and their descriptions"""
        from core.generator import OntologyGenerator
        from core.parser import OntologyParser
        
        print("\n📄 Available Input and Output Formats")
        print("=" * 50)
        
        print("\n📥 INPUT FORMATS")
        print("\nRDF Formats (via rdflib):")
        input_descriptions = OntologyParser.get_input_format_descriptions()
        for fmt in sorted(input_descriptions.keys()):
            print(f"  {fmt:12s} - {input_descriptions[fmt]}")
        
        print("\nSchema Formats (with ontology_mappings):")
        print(f"  yaml         - YAML schema files")
        print(f"  json         - JSON schema files")
        print(f"  markdown     - Markdown documentation")
        
        print("\n📤 OUTPUT FORMATS")
        print("\n📊 RDF Formats (via rdflib):")
        rdf_formats = ['turtle', 'json-ld', 'xml', 'nt', 'n3', 'trig', 'nquads']
        output_descriptions = OntologyGenerator.get_format_descriptions()
        for fmt in rdf_formats:
            if fmt in output_descriptions:
                print(f"  {fmt:12s} - {output_descriptions[fmt]}")
        
        print("\n📋 Tabular Formats (custom export):")
        tabular_formats = ['csv', 'tsv', 'sssom']
        for fmt in tabular_formats:
            if fmt in output_descriptions:
                print(f"  {fmt:12s} - {output_descriptions[fmt]}")
        
        print("\n💡 Usage Examples:")
        print("  # Input format")
        print("  python main.py data.jsonld --input-format json-ld")
        print("  python main.py ontology.rdf        # Auto-detect input format")
        print()
        print("  # Output format")
        print("  python main.py data.ttl --format json-ld --output result.jsonld")
        print("  python main.py data.jsonld --format sssom --output mappings.sssom.tsv")
        print("\n")

    def run(self):
        """Main CLI entry point"""
        args = self.parser.parse_args()
        
        # Handle list ontologies
        if args.list_ontologies:
            self._list_available_ontologies()
            return
        
        # Handle list input formats
        if args.list_input_formats:
            self._list_available_input_formats()
            return
        
        # Handle list formats (both input and output)
        if args.list_formats:
            self._list_available_formats()
            return
        
        # Initialize cache
        cache_config = CacheConfig()
        if args.no_cache:
            cache_config.enabled = False
        cache = CacheManager(cache_config)
        
        # Handle cache commands
        if args.clear_cache:
            count = cache.clear()
            print(f"🗑️  Cleared {count} cached entries")
            return
        
        if args.cache_stats:
            self._show_cache_stats(cache)
            return
        
        # Validate arguments
        if not args.single_word and not args.ttl_file:
            print("❌ Error: Either provide a TTL file or use --single-word option")
            self.parser.print_help()
            sys.exit(1)
        
        if args.ttl_file and not os.path.exists(args.ttl_file):
            print(f"❌ Error: File {args.ttl_file} not found")
            sys.exit(1)
        
        print(f"\n🔧 BioPortal & OLS Ontology Alignment CLI")
        print("=" * 45)
        
        # Show cache status
        if cache_config.enabled:
            print(f"💾 Cache: Enabled (TTL: {cache_config.ttl}s, Persistent: {cache_config.persistent})")
        else:
            print(f"💾 Cache: Disabled")
        
        # Initialize components with shared cache
        bioportal = BioPortalLookup(args.api_key, cache)
        ols = OLSLookup(cache)
        lookup = ConceptLookup(bioportal, ols, args.ontologies)
        generator = OntologyGenerator()
        
        # Show ontologies being used
        if args.ontologies:
            print(f"🎯 Using ontologies: {args.ontologies}")
        else:
            print("🎯 Using default ontology selection strategy")
        
        # Handle single word mode
        if args.single_word:
            self._single_word_mode(args, lookup, generator, cache, cache_config)
            return
        
        # Determine if we're in schema mode
        schema_mode = args.schema_mode or (args.input_format and args.input_format.lower() in ['yaml', 'json', 'markdown', 'md'])
        
        if schema_mode:
            # Schema file processing mode
            print("\n📋 Schema File Processing Mode")
            schema_parser = SchemaParser(args.ttl_file, args.input_format)
            
            # Parse schema
            if not schema_parser.parse():
                sys.exit(1)
            
            # Get concepts that have ontology mappings
            concepts = schema_parser.get_concepts_for_mapping()
            if not concepts:
                print("❌ No classes with ontology mappings found in schema")
                sys.exit(1)
            
            print(f"\n🎯 Found {len(concepts)} classes with ontology mappings to validate/enhance")
            
            # Show existing mappings for each concept
            for concept in concepts:
                print(f"\n📌 {concept['label']}:")
                print(f"   Definition: {concept['definition'][:100]}..." if len(concept['definition']) > 100 else f"   Definition: {concept['definition']}")
                print(f"   Existing mappings: {len(concept['existing_mappings'])}")
                for mapping in concept['existing_mappings']:
                    curie = mapping.get('curie', '')
                    iri = mapping.get('iri', '')
                    if curie:
                        print(f"     - {curie} ({iri})")
                    else:
                        print(f"     - {iri}")
        else:
            # RDF ontology file processing mode
            ontology = OntologyParser(args.ttl_file, args.input_format)
            
            # Parse ontology
            if not ontology.parse():
                sys.exit(1)
            
            # Get concepts to improve
            concepts = ontology.get_priority_concepts()
            if not concepts:
                print("❌ No priority concepts found in ontology")
                sys.exit(1)
            
            print(f"\n🎯 Found {len(concepts)} priority concepts to improve")
        
        # Handle batch mode
        if args.batch_mode:
            selections = self._load_batch_selections(args.batch_mode)
        else:
            selections = self._interactive_selection(concepts, lookup)
        
        # Generate improved ontology
        if selections:
            if args.terminal_only:
                print(f"\n🎉 TERMINAL-ONLY MODE: Selections processed")
                print(f"  Concepts aligned: {len(selections)}")
                total_alignments = sum(len(alignments) for alignments in selections.values())
                print(f"  Total alignments: {total_alignments}")
                for concept_key, alignments in selections.items():
                    print(f"\n  {concept_key}:")
                    for alignment in alignments:
                        source_icon = "🌐" if alignment['source'] == 'bioportal' else "🔬"
                        print(f"    {source_icon} {alignment['label']} ({alignment['ontology']})")
                        print(f"      URI: {alignment['uri']}")
                        if alignment.get('description'):
                            print(f"      Description: {alignment['description'][:100]}...")
            else:
                if schema_mode:
                    # For schema mode, convert to RDF graph first
                    print("\n📊 Converting schema to RDF graph...")
                    schema_graph_wrapper = SchemaGraphWrapper(schema_parser.to_rdf_graph(), args.ttl_file)
                    generator.generate_improved_ontology(schema_graph_wrapper, selections, args.output, args.report, args.format)
                else:
                    generator.generate_improved_ontology(ontology, selections, args.output, args.report, args.format)
        else:
            print("❌ No selections made. Exiting.")
        
        # Show cache stats at the end
        if cache_config.enabled:
            self._show_cache_stats(cache)

    def _show_cache_stats(self, cache: CacheManager):
        """Display cache statistics"""
        stats = cache.get_stats()
        print(f"\n📊 Cache Statistics")
        print("=" * 45)
        print(f"Status: {'Enabled' if stats['enabled'] else 'Disabled'}")
        print(f"Hit Rate: {stats['hit_rate']} ({stats['hits']} hits, {stats['misses']} misses)")
        print(f"Memory Entries: {stats['memory_entries']}")
        print(f"Persistent Cache: {'Enabled' if stats['persistent_enabled'] else 'Disabled'}")
        print(f"TTL: {stats['ttl_seconds']}s")
        print(f"Operations: {stats['sets']} sets, {stats['deletes']} deletes")
        if stats['errors'] > 0:
            print(f"⚠️  Errors: {stats['errors']}")
        print()
        
    def _single_word_mode(self, args, lookup: ConceptLookup, generator: OntologyGenerator, 
                          cache: CacheManager, cache_config):
        """Handle single word query mode"""
        print(f"\n🔍 Single Word Query Mode")
        print(f"Query: '{args.single_word}'")
        print("=" * 40)
        
        # Create a mock concept for the single word
        concept = {
            'key': args.single_word.replace(' ', '_'),
            'label': args.single_word,
            'type': 'Term',
            'category': 'query'
        }
        
        # Perform lookup
        options, comparison = lookup.lookup_concept(concept)
        
        if not options:
            print(f"❌ No results found for '{args.single_word}'")
            return
        
        # Display comparison summary
        if comparison['discrepancies']:
            print(f"\n⚠️  Service Comparison Alert:")
            for discrepancy in comparison['discrepancies']:
                print(f"   • {discrepancy}")
            print(f"   BioPortal: {comparison['bioportal_count']} results")
            print(f"   OLS: {comparison['ols_count']} results")
            print()
        
        # Display options
        print(f"✅ Found {len(options)} standardized terms:")
        for j, result in enumerate(options, 1):
            source_indicator = "🌐" if result['source'] == 'bioportal' else "🔬" if result['source'] == 'ols' else "🎭"
            ols_only_indicator = " (OLS-only)" if result.get('ols_only') else ""
            
            print(f"{j:2d}. {source_indicator} {result['label']}{ols_only_indicator}")
            print(f"     Ontology: {result['ontology']} | Source: {result['source']}")
            print(f"     URI: {result['uri'][:70]}{'...' if len(result['uri']) > 70 else ''}")
            
            # Show description if available
            if result.get('description') and result['description'].strip():
                desc = result['description'][:120] + "..." if len(result['description']) > 120 else result['description']
                print(f"     Description: {desc}")
            
            # Show synonyms if available
            if result.get('synonyms') and len(result['synonyms']) > 0:
                synonyms_str = ", ".join(result['synonyms'][:3])  # Show max 3 synonyms
                if len(result['synonyms']) > 3:
                    synonyms_str += f" (+ {len(result['synonyms']) - 3} more)"
                print(f"     Synonyms: {synonyms_str}")
            
            print()
        
        # Get user selection
        while True:
            try:
                choice = input(f"Choose option(s) for '{args.single_word}' (1-{len(options)}, multiple with commas, 0 to skip): ").strip()
                
                if choice == '0':
                    print(f"⏭️  Skipped {args.single_word}")
                    return
                
                # Parse multiple selections
                selected_indices = [int(x.strip()) for x in choice.split(',') if x.strip()]
                valid_selections = []
                
                for idx in selected_indices:
                    if 1 <= idx <= len(options):
                        result = options[idx - 1]
                        valid_selections.append({
                            'uri': result['uri'],
                            'label': result['label'],
                            'ontology': result['ontology'],
                            'description': result.get('description', ''),
                            'synonyms': result.get('synonyms', []),
                            'source': result['source'],
                            'relationship': 'skos:exactMatch'
                        })
                    else:
                        print(f"⚠️  Invalid choice: {idx}")
                
                if valid_selections:
                    selections = {concept['key']: valid_selections}
                    print(f"✅ Selected {len(valid_selections)} alignment(s) for {args.single_word}")
                    
                    # Show selected items
                    for sel in valid_selections:
                        source_icon = "🌐" if sel['source'] == 'bioportal' else "🔬"
                        print(f"   {source_icon} {sel['label']} ({sel['ontology']})")
                    
                    # Generate simple ontology for the single word
                    if args.terminal_only:
                        print(f"\n🎉 TERMINAL-ONLY MODE: Single word query processed")
                        print(f"  Query: {args.single_word}")
                        print(f"  Alignments found: {len(valid_selections)}")
                        for sel in valid_selections:
                            source_icon = "🌐" if sel['source'] == 'bioportal' else "🔬"
                            print(f"    {source_icon} {sel['label']} ({sel['ontology']})")
                            print(f"      URI: {sel['uri']}")
                            if sel.get('description'):
                                print(f"      Description: {sel['description'][:100]}...")
                    else:
                        generator.generate_single_word_ontology(concept, selections, args.output, args.report, args.format)
                    
                    # Show cache stats at the end
                    if cache_config.enabled:
                        self._show_cache_stats(cache)
                    
                    break
                else:
                    print("❌ No valid selections. Try again.")
                    
            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas.")
            except KeyboardInterrupt:
                print(f"\n\n⏹️  Interrupted. Exiting...")
                sys.exit(0)

    def _load_batch_selections(self, batch_file: str) -> Dict:
        """Load pre-made selections from JSON file"""
        try:
            with open(batch_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading batch file {batch_file}: {e}")
            return {}

    def _interactive_selection(self, concepts: List[Dict], lookup: ConceptLookup) -> Dict:
        """Interactive concept selection process with enhanced metadata and comparison"""
        all_selections = {}
        all_comparisons = {}
        
        for i, concept in enumerate(concepts, 1):
            print(f"\n{'='*60}")
            print(f"🔍 Step {i}/{len(concepts)}: {concept['label']} ({concept['type']})")
            print(f"{'='*60}")
            
            # Perform lookup across both services
            options, comparison = lookup.lookup_concept(concept)
            all_comparisons[concept['key']] = comparison
            
            if not options:
                print(f"❌ No results found for '{concept['label']}'")
                continue
            
            # Display comparison summary
            if comparison['discrepancies']:
                print(f"\n⚠️  Service Comparison Alert:")
                for discrepancy in comparison['discrepancies']:
                    print(f"   • {discrepancy}")
                print(f"   BioPortal: {comparison['bioportal_count']} results")
                print(f"   OLS: {comparison['ols_count']} results")
                print()
            
            # Display options with enhanced metadata
            print(f"✅ Found {len(options)} standardized terms:")
            for j, result in enumerate(options, 1):
                source_indicator = "🌐" if result['source'] == 'bioportal' else "🔬" if result['source'] == 'ols' else "🎭"
                ols_only_indicator = " (OLS-only)" if result.get('ols_only') else ""
                
                print(f"{j:2d}. {source_indicator} {result['label']}{ols_only_indicator}")
                print(f"     Ontology: {result['ontology']} | Source: {result['source']}")
                print(f"     URI: {result['uri'][:70]}{'...' if len(result['uri']) > 70 else ''}")
                
                # Show description if available
                if result.get('description') and result['description'].strip():
                    desc = result['description'][:120] + "..." if len(result['description']) > 120 else result['description']
                    print(f"     Description: {desc}")
                
                # Show synonyms if available
                if result.get('synonyms') and len(result['synonyms']) > 0:
                    synonyms_str = ", ".join(result['synonyms'][:3])  # Show max 3 synonyms
                    if len(result['synonyms']) > 3:
                        synonyms_str += f" (+ {len(result['synonyms']) - 3} more)"
                    print(f"     Synonyms: {synonyms_str}")
                
                print()
            
            # Get user selection
            while True:
                try:
                    choice = input(f"Choose option(s) for '{concept['label']}' (1-{len(options)}, multiple with commas, 0 to skip): ").strip()
                    
                    if choice == '0':
                        print(f"⏭️  Skipped {concept['label']}")
                        break
                    
                    # Parse multiple selections
                    selected_indices = [int(x.strip()) for x in choice.split(',') if x.strip()]
                    valid_selections = []
                    
                    for idx in selected_indices:
                        if 1 <= idx <= len(options):
                            result = options[idx - 1]
                            valid_selections.append({
                                'uri': result['uri'],
                                'label': result['label'],
                                'ontology': result['ontology'],
                                'description': result.get('description', ''),
                                'synonyms': result.get('synonyms', []),
                                'source': result['source'],
                                'relationship': 'owl:sameAs' if concept['category'] == 'instance' else 'rdfs:seeAlso'
                            })
                        else:
                            print(f"⚠️  Invalid choice: {idx}")
                    
                    if valid_selections:
                        all_selections[concept['key']] = valid_selections
                        print(f"✅ Selected {len(valid_selections)} alignment(s) for {concept['label']}")
                        
                        # Show selected items
                        for sel in valid_selections:
                            source_icon = "🌐" if sel['source'] == 'bioportal' else "🔬"
                            print(f"   {source_icon} {sel['label']} ({sel['ontology']})")
                        break
                    else:
                        print("❌ No valid selections. Try again.")
                        
                except ValueError:
                    print("❌ Invalid input. Please enter numbers separated by commas.")
                except KeyboardInterrupt:
                    print(f"\n\n⏹️  Interrupted. Exiting...")
                    sys.exit(0)
        
        # Save comparison report
        if all_comparisons:
            with open('service_comparison_report.json', 'w') as f:
                json.dump(all_comparisons, f, indent=2)
            print(f"\n📊 Service comparison report saved: service_comparison_report.json")
        
        return all_selections
