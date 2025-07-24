"""
CLI workflow scenario tests.
Tests specific user scenarios and workflows that are commonly used.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cli.interface import CLIInterface


@pytest.mark.integration
@pytest.mark.cli
@pytest.mark.e2e
class TestCLIWorkflowScenarios(unittest.TestCase):
    """Tests for common CLI workflow scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

        # Sample realistic TTL content for medical ontology
        self.medical_ontology_ttl = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<http://medical.example.org/ontology> a owl:Ontology ;
    rdfs:label "Medical Conditions Ontology" ;
    rdfs:comment "Sample medical ontology for testing alignment" .

<http://medical.example.org/LongCOVID> a owl:Class ;
    rdfs:label "Long COVID" ;
    rdfs:comment "Post-acute sequelae of SARS-CoV-2 infection" ;
    rdfs:subClassOf <http://medical.example.org/PostViralSyndrome> .

<http://medical.example.org/ChronicFatigue> a owl:Class ;
    rdfs:label "Chronic Fatigue Syndrome" ;
    rdfs:comment "A complex disorder characterized by extreme fatigue" ;
    rdfs:subClassOf <http://medical.example.org/NeurologicalDisorder> .

<http://medical.example.org/ImmuneDisorder> a owl:Class ;
    rdfs:label "Immune System Disorder" ;
    rdfs:comment "Disorders affecting the immune system function" .

<http://medical.example.org/Diabetes> a owl:Class ;
    rdfs:label "Diabetes Mellitus" ;
    rdfs:comment "A group of metabolic disorders characterized by high blood sugar" .

<http://medical.example.org/Hypertension> a owl:Class ;
    rdfs:label "Hypertension" ;
    rdfs:comment "Persistently high blood pressure" .
"""

        self.medical_ttl_file = self.temp_dir_path / "medical_ontology.ttl"
        self.medical_ttl_file.write_text(self.medical_ontology_ttl)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_medical_researcher_scenario(
        self, mock_ols, mock_bioportal, mock_generator, mock_lookup
    ):
        """
        Scenario: Medical researcher wants to standardize disease terms
        using specific medical ontologies (MONDO, HP, NCIT)
        """
        # Setup mocks
        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance

        # Mock realistic medical search results
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0100233",
                    "label": "Post-acute COVID-19 syndrome",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "A condition that occurs in patients with a history of probable or confirmed SARS-CoV-2 infection",
                    "synonyms": ["Long COVID", "PASC", "Post-COVID syndrome"],
                },
                {
                    "uri": "http://purl.bioontology.org/ontology/SNOMEDCT/1119303003",
                    "label": "Post-acute sequelae of COVID-19",
                    "source": "bioportal",
                    "ontology": "SNOMEDCT",
                    "description": "Condition following acute COVID-19",
                    "synonyms": ["Long COVID-19", "Chronic COVID-19"],
                },
            ],
            {"discrepancies": [], "bioportal_count": 1, "ols_count": 1},
        )

        cli = CLIInterface()

        # Test single word query for medical term
        test_args = cli.parser.parse_args(
            [
                "--single-word",
                "Long COVID",
                "--ontologies",
                "MONDO,HP,NCIT",
                "--max-results",
                "5",
                "--terminal-only",
            ]
        )

        # Simulate user selecting the first option
        with patch("builtins.input", return_value="1"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                cli.run()

        # Verify the medical ontologies were used
        mock_lookup.assert_called_once()
        lookup_call_args = mock_lookup.call_args
        # Check that ontologies were passed as the third argument (default_ontologies)
        self.assertEqual(lookup_call_args[0][2], "MONDO,HP,NCIT")

        # Verify concept lookup was performed
        mock_lookup_instance.lookup_concept.assert_called_once()
        concept_arg = mock_lookup_instance.lookup_concept.call_args[0][0]
        self.assertEqual(concept_arg["label"], "Long COVID")

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("os.path.exists")
    def test_bioinformatics_pipeline_scenario(
        self, mock_exists, mock_ols, mock_bioportal, mock_parser, mock_generator, mock_lookup
    ):
        """
        Scenario: Bioinformatics pipeline needs to process ontology file
        with batch selections for automated processing
        """
        mock_exists.return_value = True

        # Create realistic batch selections for medical terms
        batch_selections = {
            "long_covid": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0100233",
                    "label": "Post-acute COVID-19 syndrome",
                    "ontology": "MONDO",
                    "description": "Post-acute sequelae of SARS-CoV-2 infection",
                    "synonyms": ["Long COVID", "PASC"],
                    "source": "ols",
                    "relationship": "skos:exactMatch",
                }
            ],
            "chronic_fatigue_syndrome": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0005395",
                    "label": "Chronic fatigue syndrome",
                    "ontology": "MONDO",
                    "description": "A disorder characterized by persistent fatigue",
                    "synonyms": ["CFS", "Myalgic encephalomyelitis"],
                    "source": "ols",
                    "relationship": "skos:exactMatch",
                }
            ],
            "immune_system_disorder": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0005046",
                    "label": "Immune system disorder",
                    "ontology": "MONDO",
                    "description": "A disorder of the immune system",
                    "synonyms": ["Immunological disorder"],
                    "source": "ols",
                    "relationship": "skos:exactMatch",
                }
            ],
        }

        batch_file = self.temp_dir_path / "pipeline_batch.json"
        batch_file.write_text(json.dumps(batch_selections, indent=2))

        output_file = self.temp_dir_path / "pipeline_output.ttl"
        report_file = self.temp_dir_path / "pipeline_report.json"

        # Setup mocks
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = True
        mock_parser_instance.get_priority_concepts.return_value = [
            {"key": "long_covid", "label": "Long COVID", "type": "class", "category": "class"},
            {
                "key": "chronic_fatigue_syndrome",
                "label": "Chronic Fatigue Syndrome",
                "type": "class",
                "category": "class",
            },
            {
                "key": "immune_system_disorder",
                "label": "Immune System Disorder",
                "type": "class",
                "category": "class",
            },
        ]

        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance

        cli = CLIInterface()

        test_args = cli.parser.parse_args(
            [
                str(self.medical_ttl_file),
                "--batch-mode",
                str(batch_file),
                "--output",
                str(output_file),
                "--report",
                str(report_file),
                "--ontologies",
                "MONDO,HP",
            ]
        )

        with patch.object(cli.parser, "parse_args", return_value=test_args):
            cli.run()

        # Verify batch processing workflow
        mock_parser.assert_called_once_with(str(self.medical_ttl_file))
        mock_parser_instance.parse.assert_called_once()
        mock_generator_instance.generate_improved_ontology.assert_called_once()

        # Verify correct arguments were passed to generator
        call_args = mock_generator_instance.generate_improved_ontology.call_args
        self.assertEqual(call_args[0][2], str(output_file))  # output file
        self.assertEqual(call_args[0][3], str(report_file))  # report file

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_clinical_terminology_scenario(
        self, mock_ols, mock_bioportal, mock_generator, mock_lookup
    ):
        """
        Scenario: Clinical terminologist exploring different disease
        ontologies and comparing results between services
        """
        # Setup mocks
        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance

        # Mock results with discrepancies to simulate real-world differences
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/HP_0001945",
                    "label": "Fever",
                    "source": "ols",
                    "ontology": "HP",
                    "description": "Body temperature elevated beyond normal",
                    "synonyms": ["Pyrexia", "Hyperthermia"],
                },
                {
                    "uri": "http://purl.bioontology.org/ontology/SNOMEDCT/386661006",
                    "label": "Fever",
                    "source": "bioportal",
                    "ontology": "SNOMEDCT",
                    "description": "Elevation of body temperature above normal",
                    "synonyms": ["Febrile state", "Pyrexia"],
                },
            ],
            {
                "discrepancies": ["Different synonym counts", "Source terminology differences"],
                "bioportal_count": 15,
                "ols_count": 8,
            },
        )

        cli = CLIInterface()

        test_args = cli.parser.parse_args(
            [
                "--single-word",
                "fever",
                "--ontologies",
                "HP,SNOMEDCT,MONDO",
                "--comparison-only",
                "--terminal-only",
            ]
        )

        # Simulate user reviewing both options
        with patch("builtins.input", return_value="1,2"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                with patch("cli.interface.logger") as mock_logger:
                    cli.run()

                    # Verify discrepancy warnings were shown
                    warning_calls = [call.args[0] for call in mock_logger.warning.call_args_list]
                    self.assertTrue(any("Service Comparison Alert" in msg for msg in warning_calls))
                    self.assertTrue(any("Different synonym counts" in msg for msg in warning_calls))

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_ontology_curator_scenario(self, mock_ols, mock_bioportal, mock_generator, mock_lookup):
        """
        Scenario: Ontology curator needs to quickly check what standard
        terms are available for specific concepts across multiple ontologies
        """
        # Setup mocks
        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance

        # Mock comprehensive results across multiple ontologies
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0005015",
                    "label": "Diabetes mellitus",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "A metabolic disorder",
                    "synonyms": ["Diabetes", "DM"],
                },
                {
                    "uri": "http://purl.obolibrary.org/obo/DOID_9351",
                    "label": "Diabetes mellitus",
                    "source": "ols",
                    "ontology": "DOID",
                    "description": "A glucose metabolism disorder",
                    "synonyms": ["Diabetes"],
                },
                {
                    "uri": "http://purl.bioontology.org/ontology/ICD10CM/E11",
                    "label": "Type 2 diabetes mellitus",
                    "source": "bioportal",
                    "ontology": "ICD10CM",
                    "description": "Non-insulin-dependent diabetes mellitus",
                    "synonyms": ["NIDDM", "Type 2 DM"],
                },
            ],
            {"discrepancies": [], "bioportal_count": 3, "ols_count": 2},
        )

        cli = CLIInterface()

        test_args = cli.parser.parse_args(
            [
                "--single-word",
                "diabetes",
                "--ontologies",
                "MONDO,DOID,ICD10CM,HP",
                "--max-results",
                "10",
                "--terminal-only",
            ]
        )

        # Simulate curator skipping after review
        with patch("builtins.input", return_value="0"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                cli.run()

        # Verify comprehensive search was performed
        mock_lookup.assert_called_once()
        lookup_call_args = mock_lookup.call_args
        # Check that ontologies were passed as the third argument (default_ontologies)
        self.assertEqual(lookup_call_args[0][2], "MONDO,DOID,ICD10CM,HP")

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.OntologyParser")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    @patch("os.path.exists")
    def test_interactive_ontology_improvement_scenario(
        self, mock_exists, mock_ols, mock_bioportal, mock_parser, mock_generator, mock_lookup
    ):
        """
        Scenario: User wants to interactively improve an existing ontology
        by selecting alignments for each concept
        """
        mock_exists.return_value = True

        # Setup mocks for interactive workflow
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_parser_instance.parse.return_value = True
        mock_parser_instance.get_priority_concepts.return_value = [
            {"key": "hypertension", "label": "Hypertension", "type": "class", "category": "class"}
        ]

        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance
        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/HP_0000822",
                    "label": "Hypertension",
                    "source": "ols",
                    "ontology": "HP",
                    "description": "High blood pressure",
                    "synonyms": ["High blood pressure", "HTN"],
                },
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0001134",
                    "label": "Essential hypertension",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "Primary hypertension",
                    "synonyms": ["Primary hypertension"],
                },
            ],
            {"discrepancies": [], "bioportal_count": 2, "ols_count": 2},
        )

        mock_generator_instance = MagicMock()
        mock_generator.return_value = mock_generator_instance

        cli = CLIInterface()

        output_file = self.temp_dir_path / "improved_ontology.ttl"
        test_args = cli.parser.parse_args(
            [str(self.medical_ttl_file), "--output", str(output_file), "--ontologies", "HP,MONDO"]
        )

        # Simulate user selecting multiple alignments and confirming
        with patch("builtins.input", side_effect=["1,2", "y"]):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                cli.run()

        # Verify interactive workflow
        mock_lookup_instance.lookup_concept.assert_called_once()
        mock_generator_instance.generate_improved_ontology.assert_called_once()

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_quick_term_lookup_scenario(
        self, mock_ols, mock_bioportal, mock_generator, mock_lookup
    ):
        """
        Scenario: Quick lookup of a single term without generating output files
        """
        # Setup mocks
        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance

        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/HP_0002315",
                    "label": "Headache",
                    "source": "ols",
                    "ontology": "HP",
                    "description": "Cephalgia, or pain in the head",
                    "synonyms": ["Cephalgia", "Head pain"],
                }
            ],
            {"discrepancies": [], "bioportal_count": 1, "ols_count": 1},
        )

        cli = CLIInterface()

        test_args = cli.parser.parse_args(["--single-word", "headache", "--terminal-only"])

        # Simulate quick skip after viewing results
        with patch("builtins.input", return_value="0"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                cli.run()

        # Verify quick lookup was performed
        mock_lookup_instance.lookup_concept.assert_called_once()
        concept_arg = mock_lookup_instance.lookup_concept.call_args[0][0]
        self.assertEqual(concept_arg["label"], "headache")

    @patch("cli.interface.ConceptLookup")
    @patch("cli.interface.OntologyGenerator")
    @patch("cli.interface.BioPortalLookup")
    @patch("cli.interface.OLSLookup")
    def test_limited_service_scenario(self, mock_ols, mock_bioportal, mock_generator, mock_lookup):
        """
        Scenario: User wants to use only one service (e.g., only OLS due to API limitations)
        """
        # Setup mocks
        mock_lookup_instance = MagicMock()
        mock_lookup.return_value = mock_lookup_instance

        mock_lookup_instance.lookup_concept.return_value = (
            [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004979",
                    "label": "Asthma",
                    "source": "ols",
                    "ontology": "MONDO",
                    "description": "A chronic respiratory condition",
                    "synonyms": ["Bronchial asthma"],
                }
            ],
            {"discrepancies": [], "bioportal_count": 0, "ols_count": 1},
        )

        cli = CLIInterface()

        test_args = cli.parser.parse_args(
            [
                "--single-word",
                "asthma",
                "--disable-bioportal",
                "--ontologies",
                "MONDO,HP",
                "--terminal-only",
            ]
        )

        # Simulate user selecting the only available option
        with patch("builtins.input", return_value="1"):
            with patch.object(cli.parser, "parse_args", return_value=test_args):
                cli.run()

        # Verify OLS-only search was performed
        mock_lookup.assert_called_once()
        mock_lookup_instance.lookup_concept.assert_called_once()

    def test_help_and_documentation_scenario(self):
        """
        Scenario: User needs to understand available options and ontologies
        """
        cli = CLIInterface()

        # Test listing available ontologies
        test_args = cli.parser.parse_args(["--list-ontologies"])

        with patch.object(cli.parser, "parse_args", return_value=test_args):
            with patch("cli.interface.logger") as mock_logger:
                cli.run()

                # Verify comprehensive ontology information was provided
                logged_messages = [call.args[0] for call in mock_logger.info.call_args_list]

                # Check for key information sections
                self.assertTrue(any("Available Ontologies" in msg for msg in logged_messages))
                self.assertTrue(any("Individual Ontologies:" in msg for msg in logged_messages))
                self.assertTrue(any("Recommended Combinations:" in msg for msg in logged_messages))
                self.assertTrue(any("Usage Examples:" in msg for msg in logged_messages))


if __name__ == "__main__":
    unittest.main()
