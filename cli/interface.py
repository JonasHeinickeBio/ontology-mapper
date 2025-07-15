"""
CLI interface for the ontology mapping tool.
"""

import os
import sys
import json
import argparse
from typing import Dict, List

from services import BioPortalLookup, OLSLookup
from core import OntologyParser, ConceptLookup, OntologyGenerator
from config import ONTOLOGY_CONFIGS, ONTOLOGY_COMBINATIONS


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
        parser.add_argument('ttl_file', nargs='?', help='Path to TTL ontology file (optional with --single-word)')
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
                          help='Query a single word/term instead of processing a TTL file')
        parser.add_argument('--list-ontologies', action='store_true',
                          help='Show available ontologies and exit')
        parser.add_argument('--max-results', type=int, default=5,
                          help='Maximum number of results per search (default: 5)')
        parser.add_argument('--terminal-only', action='store_true',
                          help='Only print results to terminal, do not generate output files')
        
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

    def run(self):
        """Main CLI entry point"""
        args = self.parser.parse_args()
        
        # Handle list ontologies
        if args.list_ontologies:
            self._list_available_ontologies()
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
        
        # Initialize components
        bioportal = BioPortalLookup(args.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols, args.ontologies)
        generator = OntologyGenerator()
        
        # Show ontologies being used
        if args.ontologies:
            print(f"🎯 Using ontologies: {args.ontologies}")
        else:
            print("🎯 Using default ontology selection strategy")
        
        # Handle single word mode
        if args.single_word:
            self._single_word_mode(args, lookup, generator)
            return
        
        # Original TTL processing mode
        ontology = OntologyParser(args.ttl_file)
        
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
                generator.generate_improved_ontology(ontology, selections, args.output, args.report)
        else:
            print("❌ No selections made. Exiting.")

    def _single_word_mode(self, args, lookup: ConceptLookup, generator: OntologyGenerator):
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
                        generator.generate_single_word_ontology(concept, selections, args.output, args.report)
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
