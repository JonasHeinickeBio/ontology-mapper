"""
CLI interface for the ontology mapping tool.
"""

import argparse
import json
import os
import sys
from typing import Any

from config import ONTOLOGY_COMBINATIONS, ONTOLOGY_CONFIGS
from config.logging_config import get_logger
from core import ConceptLookup, OntologyGenerator, OntologyParser
from services import BioPortalLookup, OLSLookup

logger = get_logger(__name__)


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
            """,
        )

        # Make ttl_file optional when using single-word mode
        parser.add_argument(
            "ttl_file", nargs="?", help="Path to TTL ontology file (optional with --single-word)"
        )
        parser.add_argument(
            "--output",
            "-o",
            default="improved_ontology.ttl",
            help="Output file for improved ontology (default: improved_ontology.ttl)",
        )
        parser.add_argument(
            "--api-key", help="BioPortal API key (or set BIOPORTAL_API_KEY env var)"
        )
        parser.add_argument(
            "--batch-mode", help="JSON file with pre-selected choices for batch processing"
        )
        parser.add_argument(
            "--report", help="Output file for alignment report (only generated if specified)"
        )
        parser.add_argument(
            "--disable-ols", action="store_true", help="Disable OLS lookups (use only BioPortal)"
        )
        parser.add_argument(
            "--disable-bioportal",
            action="store_true",
            help="Disable BioPortal lookups (use only OLS)",
        )
        parser.add_argument(
            "--comparison-only",
            action="store_true",
            help="Run comparison analysis without generating improved ontology",
        )

        # New arguments for ontology selection and single word queries
        parser.add_argument(
            "--ontologies",
            "-ont",
            help="Comma-separated list of ontologies to search (e.g., HP,NCIT,MONDO)",
        )
        parser.add_argument(
            "--single-word", "-sw", help="Query a single word/term instead of processing a TTL file"
        )
        parser.add_argument(
            "--list-ontologies", action="store_true", help="Show available ontologies and exit"
        )
        parser.add_argument(
            "--max-results",
            type=int,
            default=5,
            help="Maximum number of results per search (default: 5)",
        )
        parser.add_argument(
            "--terminal-only",
            action="store_true",
            help="Only print results to terminal, do not generate output files",
        )

        return parser

    def _list_available_ontologies(self):
        """Display available ontologies and their descriptions"""
        # Output to both logger (for unit tests) and stderr (for E2E tests)
        logger.info("Available Ontologies")
        print("Available Ontologies", file=sys.stderr)

        separator = "=" * 50
        logger.info(separator)
        print(separator, file=sys.stderr)

        logger.info("\nIndividual Ontologies:")
        print("\nIndividual Ontologies:", file=sys.stderr)
        for ont, desc in ONTOLOGY_CONFIGS.items():
            msg = f"  {ont:12s} - {desc}"
            logger.info(msg)
            print(msg, file=sys.stderr)

        logger.info("\nRecommended Combinations:")
        print("\nRecommended Combinations:", file=sys.stderr)
        for category, onts in ONTOLOGY_COMBINATIONS.items():
            msg = f"  {category:15s} - {onts}"
            logger.info(msg)
            print(msg, file=sys.stderr)

        logger.info("\nUsage Examples:")
        print("\nUsage Examples:", file=sys.stderr)
        examples = [
            "  --ontologies 'HP,NCIT'           # Phenotypes and clinical terms",
            "  --ontologies 'MONDO,DOID'        # Disease ontologies",
            "  --ontologies 'CHEBI,RXNORM'      # Chemical and drug terms",
            "  --ontologies 'GO,PRO'            # Gene/protein related",
        ]
        for example in examples:
            logger.info(example)
            print(example, file=sys.stderr)

        logger.info("")
        print("", file=sys.stderr)

    def run(self):
        """Main CLI entry point"""
        args = self.parser.parse_args()

        # Handle list ontologies
        if args.list_ontologies:
            self._list_available_ontologies()
            return

        # Validate arguments
        if not args.single_word and not args.ttl_file:
            logger.error("Either provide a TTL file or use --single-word option")
            self.parser.print_help()
            sys.exit(1)

        if args.ttl_file and not os.path.exists(args.ttl_file):
            logger.error(f"File {args.ttl_file} not found")
            sys.exit(1)

        logger.info("BioPortal & OLS Ontology Alignment CLI")
        logger.info("=" * 45)

        # Initialize components
        bioportal = BioPortalLookup(args.api_key)
        ols = OLSLookup()
        lookup = ConceptLookup(bioportal, ols, args.ontologies)
        generator = OntologyGenerator()

        # Show ontologies being used
        if args.ontologies:
            print(f"Using ontologies: {args.ontologies}", file=sys.stderr)
        else:
            print("Using default ontology selection strategy", file=sys.stderr)

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
            logger.error("No priority concepts found in ontology")
            sys.exit(1)

        logger.info(f"Found {len(concepts)} priority concepts to improve")

        # Handle batch mode
        if args.batch_mode:
            selections = self._load_batch_selections(args.batch_mode)
        else:
            selections = self._interactive_selection(concepts, lookup)

        # Generate improved ontology
        if selections:
            if args.terminal_only:
                logger.info("TERMINAL-ONLY MODE: Selections processed")
                logger.info(f"Concepts aligned: {len(selections)}")
                total_alignments = sum(len(alignments) for alignments in selections.values())
                logger.info(f"Total alignments: {total_alignments}")
                for concept_key, alignments in selections.items():
                    logger.info(f"{concept_key}:")
                    for alignment in alignments:
                        source_icon = "🌐" if alignment["source"] == "bioportal" else "🔬"
                        logger.info(
                            f"  {source_icon} {alignment['label']} ({alignment['ontology']})"
                        )
                        logger.info(f"    URI: {alignment['uri']}")
                        if alignment.get("description"):
                            logger.info(f"    Description: {alignment['description'][:100]}...")
            else:
                generator.generate_improved_ontology(ontology, selections, args.output, args.report)
        else:
            logger.error("No selections made. Exiting.")

    def _single_word_mode(self, args, lookup: ConceptLookup, generator: OntologyGenerator):
        """Handle single word query mode"""
        # Output to both logger (for unit tests) and stderr (for E2E tests)
        logger.info("Single Word Query Mode")
        print("Single Word Query Mode", file=sys.stderr)

        query_msg = f"Query: '{args.single_word}'"
        logger.info(query_msg)
        print(query_msg, file=sys.stderr)

        separator = "=" * 40
        logger.info(separator)
        print(separator, file=sys.stderr)

        # Create a mock concept for the single word
        concept = {
            "key": args.single_word.replace(" ", "_"),
            "label": args.single_word,
            "type": "Term",
            "category": "query",
        }

        # Perform lookup
        options, comparison = lookup.lookup_concept(concept)

        if not options:
            logger.error(f"No results found for '{args.single_word}'")
            return

        # Display comparison summary
        if comparison["discrepancies"]:
            logger.warning("Service Comparison Alert:")
            for discrepancy in comparison["discrepancies"]:
                logger.warning(f"• {discrepancy}")
            logger.warning(f"BioPortal: {comparison['bioportal_count']} results")
            logger.warning(f"OLS: {comparison['ols_count']} results")

        # Display options
        logger.info(f"Found {len(options)} standardized terms:")
        for j, result in enumerate(options, 1):
            source_indicator = (
                "🌐"
                if result["source"] == "bioportal"
                else "🔬"
                if result["source"] == "ols"
                else "🎭"
            )
            ols_only_indicator = " (OLS-only)" if result.get("ols_only") else ""

            logger.info(f"{j:2d}. {source_indicator} {result['label']}{ols_only_indicator}")
            logger.info(f"     Ontology: {result['ontology']} | Source: {result['source']}")
            logger.info(f"     URI: {result['uri'][:70]}{'...' if len(result['uri']) > 70 else ''}")

            # Show description if available
            if result.get("description") and result["description"].strip():
                desc = (
                    result["description"][:120] + "..."
                    if len(result["description"]) > 120
                    else result["description"]
                )
                logger.info(f"     Description: {desc}")

            # Show synonyms if available
            if result.get("synonyms") and len(result["synonyms"]) > 0:
                synonyms_str = ", ".join(result["synonyms"][:3])  # Show max 3 synonyms
                if len(result["synonyms"]) > 3:
                    synonyms_str += f" (+ {len(result['synonyms']) - 3} more)"
                logger.info(f"     Synonyms: {synonyms_str}")

            logger.info("")

        # Get user selection
        while True:
            try:
                choice = input(
                    f"Choose option(s) for '{args.single_word}' (1-{len(options)}, multiple with commas, 0 to skip): "
                ).strip()

                if choice == "0":
                    print(f"⏭️  Skipped {args.single_word}")
                    return

                # Parse multiple selections
                selected_indices = [int(x.strip()) for x in choice.split(",") if x.strip()]
                valid_selections = []

                for idx in selected_indices:
                    if 1 <= idx <= len(options):
                        result = options[idx - 1]
                        valid_selections.append(
                            {
                                "uri": result["uri"],
                                "label": result["label"],
                                "ontology": result["ontology"],
                                "description": result.get("description", ""),
                                "synonyms": result.get("synonyms", []),
                                "source": result["source"],
                                "relationship": "skos:exactMatch",
                            }
                        )
                    else:
                        print(f"⚠️  Invalid choice: {idx}")

                if valid_selections:
                    selections = {concept["key"]: valid_selections}
                    print(
                        f"✅ Selected {len(valid_selections)} alignment(s) for {args.single_word}"
                    )

                    # Show selected items
                    for sel in valid_selections:
                        source_icon = "🌐" if sel["source"] == "bioportal" else "🔬"
                        print(f"   {source_icon} {sel['label']} ({sel['ontology']})")

                    # Generate simple ontology for the single word
                    if args.terminal_only:
                        print("\n🎉 TERMINAL-ONLY MODE: Single word query processed")
                        print(f"  Query: {args.single_word}")
                        print(f"  Alignments found: {len(valid_selections)}")
                        for sel in valid_selections:
                            source_icon = "🌐" if sel["source"] == "bioportal" else "🔬"
                            print(f"    {source_icon} {sel['label']} ({sel['ontology']})")
                            print(f"      URI: {sel['uri']}")
                            if sel.get("description"):
                                print(f"      Description: {sel['description'][:100]}...")
                    else:
                        generator.generate_single_word_ontology(
                            concept, selections, args.output, args.report
                        )
                    break
                else:
                    print("❌ No valid selections. Try again.")

            except ValueError:
                print("❌ Invalid input. Please enter numbers separated by commas.")
            except KeyboardInterrupt:
                print("\n\n⏹️  Interrupted. Exiting...")
                sys.exit(0)

    def _load_batch_selections(self, batch_file: str) -> dict[str, Any]:
        """Load pre-made selections from JSON file"""
        try:
            with open(batch_file) as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            print(f"❌ Error loading batch file {batch_file}: {e}")
            return {}

    def _interactive_selection(self, concepts: list[dict], lookup: ConceptLookup) -> dict:
        """Interactive concept selection process with enhanced metadata and comparison"""
        all_selections = {}
        all_comparisons = {}

        for i, concept in enumerate(concepts, 1):
            print(f"\n{'=' * 60}")
            print(f"🔍 Step {i}/{len(concepts)}: {concept['label']} ({concept['type']})")
            print(f"{'=' * 60}")

            # Perform lookup across both services
            options, comparison = lookup.lookup_concept(concept)
            all_comparisons[concept["key"]] = comparison

            if not options:
                print(f"❌ No results found for '{concept['label']}'")
                continue

            # Display comparison summary
            if comparison["discrepancies"]:
                print("\n⚠️  Service Comparison Alert:")
                for discrepancy in comparison["discrepancies"]:
                    print(f"   • {discrepancy}")
                print(f"   BioPortal: {comparison['bioportal_count']} results")
                print(f"   OLS: {comparison['ols_count']} results")
                print()

            # Display options with enhanced metadata
            print(f"✅ Found {len(options)} standardized terms:")
            for j, result in enumerate(options, 1):
                source_indicator = (
                    "🌐"
                    if result["source"] == "bioportal"
                    else "🔬"
                    if result["source"] == "ols"
                    else "🎭"
                )
                ols_only_indicator = " (OLS-only)" if result.get("ols_only") else ""

                print(f"{j:2d}. {source_indicator} {result['label']}{ols_only_indicator}")
                print(f"     Ontology: {result['ontology']} | Source: {result['source']}")
                print(f"     URI: {result['uri'][:70]}{'...' if len(result['uri']) > 70 else ''}")

                # Show description if available
                if result.get("description") and result["description"].strip():
                    desc = (
                        result["description"][:120] + "..."
                        if len(result["description"]) > 120
                        else result["description"]
                    )
                    print(f"     Description: {desc}")

                # Show synonyms if available
                if result.get("synonyms") and len(result["synonyms"]) > 0:
                    synonyms_str = ", ".join(result["synonyms"][:3])  # Show max 3 synonyms
                    if len(result["synonyms"]) > 3:
                        synonyms_str += f" (+ {len(result['synonyms']) - 3} more)"
                    print(f"     Synonyms: {synonyms_str}")

                print()

            # Get user selection
            while True:
                try:
                    choice = input(
                        f"Choose option(s) for '{concept['label']}' (1-{len(options)}, multiple with commas, 0 to skip): "
                    ).strip()

                    if choice == "0":
                        print(f"⏭️  Skipped {concept['label']}")
                        break

                    # Parse multiple selections
                    selected_indices = [int(x.strip()) for x in choice.split(",") if x.strip()]
                    valid_selections = []

                    for idx in selected_indices:
                        if 1 <= idx <= len(options):
                            result = options[idx - 1]
                            valid_selections.append(
                                {
                                    "uri": result["uri"],
                                    "label": result["label"],
                                    "ontology": result["ontology"],
                                    "description": result.get("description", ""),
                                    "synonyms": result.get("synonyms", []),
                                    "source": result["source"],
                                    "relationship": (
                                        "owl:sameAs"
                                        if concept["category"] == "instance"
                                        else "rdfs:seeAlso"
                                    ),
                                }
                            )
                        else:
                            print(f"⚠️  Invalid choice: {idx}")

                    if valid_selections:
                        all_selections[concept["key"]] = valid_selections
                        print(
                            f"✅ Selected {len(valid_selections)} alignment(s) for {concept['label']}"
                        )

                        # Show selected items
                        for sel in valid_selections:
                            source_icon = "🌐" if sel["source"] == "bioportal" else "🔬"
                            print(f"   {source_icon} {sel['label']} ({sel['ontology']})")
                        break
                    else:
                        print("❌ No valid selections. Try again.")

                except ValueError:
                    print("❌ Invalid input. Please enter numbers separated by commas.")
                except KeyboardInterrupt:
                    print("\n\n⏹️  Interrupted. Exiting...")
                    sys.exit(0)

        # Save comparison report
        if all_comparisons:
            with open("service_comparison_report.json", "w") as f:
                json.dump(all_comparisons, f, indent=2)
            print("\n📊 Service comparison report saved: service_comparison_report.json")

        return all_selections
