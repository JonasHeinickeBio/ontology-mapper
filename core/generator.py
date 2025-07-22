"""
Ontology generation utilities.
"""

import json
import os
from datetime import datetime

from rdflib import OWL, RDF, RDFS, SKOS, Graph, Literal, URIRef
from rdflib.namespace import DCTERMS

from config.logging_config import get_logger
from utils.helpers import clean_description, deduplicate_synonyms, determine_alignment_type

from .parser import OntologyParser

logger = get_logger(__name__)


class OntologyGenerator:
    """Generates improved ontologies with alignments"""

    def generate_improved_ontology(
        self,
        ontology: OntologyParser,
        selections: dict,
        output_file: str,
        report_file: str | None = None,
    ):
        """Generate improved ontology with selected alignments"""
        logger.info("Generating Improved Ontology")

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
                external_uri = URIRef(alignment["uri"])

                # Determine alignment type and relationship based on confidence
                alignment_type = determine_alignment_type(alignment, concept_key)

                # Add standardized alignment relationship
                if alignment_type == "exact":
                    improved_graph.add((local_uri, SKOS.exactMatch, external_uri))
                elif alignment_type == "close":
                    improved_graph.add((local_uri, SKOS.closeMatch, external_uri))
                elif alignment_type == "related":
                    improved_graph.add((local_uri, SKOS.relatedMatch, external_uri))
                elif alignment_type == "broader":
                    improved_graph.add((local_uri, SKOS.broadMatch, external_uri))
                elif alignment_type == "narrower":
                    improved_graph.add((local_uri, SKOS.narrowMatch, external_uri))
                else:
                    improved_graph.add((local_uri, RDFS.seeAlso, external_uri))

                # Add standard metadata using SKOS and DCTERMS
                improved_graph.add(
                    (
                        local_uri,
                        SKOS.inScheme,
                        URIRef(
                            f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}"
                        ),
                    )
                )
                improved_graph.add(
                    (
                        local_uri,
                        DCTERMS.source,
                        URIRef(
                            f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}"
                        ),
                    )
                )

                # Use standard SKOS properties for labels and descriptions
                if alignment.get("label") and alignment["label"].strip():
                    improved_graph.add(
                        (local_uri, SKOS.prefLabel, Literal(alignment["label"], lang="en"))
                    )

                # Add description using standard DCTERMS
                if alignment.get("description") and alignment["description"].strip():
                    clean_desc = clean_description(alignment["description"])
                    if clean_desc:
                        improved_graph.add(
                            (local_uri, DCTERMS.description, Literal(clean_desc, lang="en"))
                        )

                # Add synonyms using SKOS altLabel, avoiding duplicates
                if alignment.get("synonyms"):
                    unique_synonyms = deduplicate_synonyms(alignment["synonyms"], set())
                    for synonym in unique_synonyms[:3]:  # Limit to 3 synonyms
                        improved_graph.add((local_uri, SKOS.altLabel, Literal(synonym, lang="en")))

                # Add provenance for this alignment
                prov_node = URIRef(
                    f"http://example.org/ontology#alignment_{concept_key}_{total_alignments}"
                )
                improved_graph.add(
                    (prov_node, RDF.type, URIRef("http://www.w3.org/ns/prov#Entity"))
                )
                improved_graph.add(
                    (
                        prov_node,
                        URIRef("http://www.w3.org/ns/prov#wasAttributedTo"),
                        URIRef(f"http://example.org/ontology#{alignment['source']}_service"),
                    )
                )
                improved_graph.add(
                    (prov_node, DCTERMS.created, Literal(datetime.now().isoformat()))
                )

                total_alignments += 1
                source_icon = "🌐" if alignment["source"] == "bioportal" else "🔬"
                logger.info(
                    f"{source_icon} {concept_key} → {alignment['label']} ({alignment['ontology']}) [{alignment_type}]"
                )

        # Add enhanced provenance using PROV-O vocabulary
        prov_activity = URIRef("http://example.org/ontology#BioPortalCLIAlignment")
        improved_graph.add((prov_activity, RDF.type, URIRef("http://www.w3.org/ns/prov#Activity")))
        improved_graph.add(
            (prov_activity, DCTERMS.title, Literal("Ontology Alignment Activity", lang="en"))
        )
        improved_graph.add(
            (
                prov_activity,
                DCTERMS.description,
                Literal("Automated ontology alignment using BioPortal and OLS services", lang="en"),
            )
        )
        improved_graph.add(
            (
                prov_activity,
                URIRef("http://www.w3.org/ns/prov#startedAtTime"),
                Literal(datetime.now().isoformat()),
            )
        )
        improved_graph.add(
            (
                prov_activity,
                URIRef("http://www.w3.org/ns/prov#endedAtTime"),
                Literal(datetime.now().isoformat()),
            )
        )

        # Add tool information
        tool_agent = URIRef("http://example.org/ontology#BioPortalCLITool")
        improved_graph.add(
            (tool_agent, RDF.type, URIRef("http://www.w3.org/ns/prov#SoftwareAgent"))
        )
        improved_graph.add(
            (tool_agent, DCTERMS.title, Literal("BioPortal CLI Alignment Tool", lang="en"))
        )
        improved_graph.add(
            (tool_agent, URIRef("http://www.w3.org/ns/prov#wasAssociatedWith"), prov_activity)
        )

        # Add statistics as structured data
        stats_node = URIRef("http://example.org/ontology#AlignmentStatistics")
        improved_graph.add((stats_node, RDF.type, URIRef("http://www.w3.org/ns/prov#Entity")))
        improved_graph.add(
            (stats_node, URIRef("http://www.w3.org/ns/prov#wasGeneratedBy"), prov_activity)
        )
        improved_graph.add(
            (
                stats_node,
                URIRef("http://example.org/vocab#alignmentCount"),
                Literal(
                    total_alignments, datatype=URIRef("http://www.w3.org/2001/XMLSchema#integer")
                ),
            )
        )
        improved_graph.add(
            (
                stats_node,
                URIRef("http://example.org/vocab#conceptCount"),
                Literal(
                    len(selections), datatype=URIRef("http://www.w3.org/2001/XMLSchema#integer")
                ),
            )
        )

        # Save improved ontology
        improved_graph.serialize(destination=output_file, format="turtle")

        # Generate report only if specified
        if report_file:
            report = {
                "timestamp": datetime.now().isoformat(),
                "input_file": ontology.ttl_file,
                "output_file": output_file,
                "original_triples": len(ontology.graph),
                "improved_triples": len(improved_graph),
                "alignments_added": total_alignments,
                "concepts_aligned": len(selections),
                "selections": selections,
            }

            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

        # Print summary
        logger.info("SUCCESS!")
        logger.info(f"Input: {ontology.ttl_file}")
        logger.info(f"Output: {output_file}")
        if report_file:
            logger.info(f"Report: {report_file}")
        logger.info(f"Original triples: {len(ontology.graph):,}")
        logger.info(f"New triples: {len(improved_graph) - len(ontology.graph):,}")
        logger.info(f"Total triples: {len(improved_graph):,}")
        logger.info(f"Concepts aligned: {len(selections)}")
        logger.info(f"Total alignments: {total_alignments}")

        # Show file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            logger.info(f"File size: {size:,} bytes")

    def generate_single_word_ontology(
        self, concept: dict, selections: dict, output_file: str, report_file: str | None = None
    ):
        """Generate ontology for single word query"""
        logger.info("Generating Ontology for Single Word Query")

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
        graph.add((local_uri, RDFS.label, Literal(concept["label"], lang="en")))
        graph.add((local_uri, SKOS.prefLabel, Literal(concept["label"], lang="en")))

        # Add alignments
        total_alignments = 0
        for concept_key, alignments in selections.items():
            for alignment in alignments:
                external_uri = URIRef(alignment["uri"])

                # Determine alignment type
                alignment_type = determine_alignment_type(alignment, concept_key)

                # Add standardized alignment relationship
                if alignment_type == "exact":
                    graph.add((local_uri, SKOS.exactMatch, external_uri))
                elif alignment_type == "close":
                    graph.add((local_uri, SKOS.closeMatch, external_uri))
                elif alignment_type == "related":
                    graph.add((local_uri, SKOS.relatedMatch, external_uri))
                elif alignment_type == "broader":
                    graph.add((local_uri, SKOS.broadMatch, external_uri))
                elif alignment_type == "narrower":
                    graph.add((local_uri, SKOS.narrowMatch, external_uri))
                else:
                    graph.add((local_uri, RDFS.seeAlso, external_uri))

                # Add metadata
                graph.add(
                    (
                        local_uri,
                        SKOS.inScheme,
                        URIRef(
                            f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}"
                        ),
                    )
                )
                graph.add(
                    (
                        local_uri,
                        DCTERMS.source,
                        URIRef(
                            f"http://bioportal.bioontology.org/ontologies/{alignment['ontology']}"
                        ),
                    )
                )

                # Add description
                if alignment.get("description") and alignment["description"].strip():
                    clean_desc = clean_description(alignment["description"])
                    if clean_desc:
                        graph.add((local_uri, DCTERMS.description, Literal(clean_desc, lang="en")))

                # Add synonyms
                if alignment.get("synonyms"):
                    unique_synonyms = deduplicate_synonyms(alignment["synonyms"], set())
                    for synonym in unique_synonyms[:3]:
                        graph.add((local_uri, SKOS.altLabel, Literal(synonym, lang="en")))

                total_alignments += 1
                source_icon = "🌐" if alignment["source"] == "bioportal" else "🔬"
                logger.info(
                    f"{source_icon} {concept_key} → {alignment['label']} ({alignment['ontology']}) [{alignment_type}]"
                )

        # Add provenance
        prov_activity = URIRef("http://example.org/query#SingleWordAlignment")
        graph.add((prov_activity, RDF.type, URIRef("http://www.w3.org/ns/prov#Activity")))
        graph.add((prov_activity, DCTERMS.title, Literal("Single Word Query Alignment", lang="en")))
        graph.add(
            (
                prov_activity,
                URIRef("http://www.w3.org/ns/prov#startedAtTime"),
                Literal(datetime.now().isoformat()),
            )
        )

        # Save ontology
        graph.serialize(destination=output_file, format="turtle")

        # Generate report only if specified
        if report_file:
            report = {
                "timestamp": datetime.now().isoformat(),
                "query_term": concept["label"],
                "output_file": output_file,
                "total_triples": len(graph),
                "alignments_added": total_alignments,
                "selections": selections,
            }

            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

        # Print summary
        logger.info("SUCCESS!")
        logger.info(f"Query: {concept['label']}")
        logger.info(f"Output: {output_file}")
        if report_file:
            logger.info(f"Report: {report_file}")
        logger.info(f"Total triples: {len(graph):,}")
        logger.info(f"Total alignments: {total_alignments}")

        # Show file size
        if os.path.exists(output_file):
            size = os.path.getsize(output_file)
            logger.info(f"File size: {size:,} bytes")
