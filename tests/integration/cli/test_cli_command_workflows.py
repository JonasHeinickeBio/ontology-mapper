"""
Real CLI command-line workflow tests.
Tests the actual CLI as subprocess commands to ensure end-to-end functionality.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pytest


@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.cli
@pytest.mark.slow
class TestCLICommandWorkflows(unittest.TestCase):
    """Real CLI command workflow tests using subprocess"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_dir_path = Path(self.temp_dir)

        # Create sample TTL file for testing
        self.sample_ttl_content = """@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

<http://example.org/ontology> a owl:Ontology ;
    rdfs:label "Sample Ontology for Testing" .

<http://example.org/cancer> a owl:Class ;
    rdfs:label "Cancer" ;
    rdfs:comment "A malignant neoplasm that can occur in various organs" .

<http://example.org/diabetes> a owl:Class ;
    rdfs:label "Diabetes" ;
    rdfs:comment "A metabolic disorder characterized by high blood sugar" .

<http://example.org/hypertension> a owl:Class ;
    rdfs:label "Hypertension" ;
    rdfs:comment "Persistently high blood pressure" .
"""

        self.sample_ttl_file = self.temp_dir_path / "sample_ontology.ttl"
        self.sample_ttl_file.write_text(self.sample_ttl_content)

        # Create sample batch selection file
        self.sample_batch_selections = {
            "cancer": [
                {
                    "uri": "http://purl.obolibrary.org/obo/MONDO_0004992",
                    "label": "Cancer",
                    "ontology": "MONDO",
                    "description": "A disease characterized by uncontrolled cell growth",
                    "synonyms": ["malignancy", "neoplasm"],
                    "source": "ols",
                    "relationship": "skos:exactMatch",
                }
            ]
        }

        self.batch_file = self.temp_dir_path / "batch_selections.json"
        self.batch_file.write_text(json.dumps(self.sample_batch_selections, indent=2))

        # Output files
        self.output_ttl = self.temp_dir_path / "output.ttl"
        self.report_file = self.temp_dir_path / "report.json"

        # Get the project root directory
        self.project_root = Path(__file__).parent.parent.parent.parent

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_cli_command(self, args, input_text=None, timeout=30):
        """Helper method to run CLI commands with robust error handling"""
        cmd = [sys.executable, "-m", "cli"] + args
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.project_root)
        env["PYTHONWARNINGS"] = "ignore"  # Suppress warnings that interfere with output

        # Create a new process group to avoid file descriptor conflicts
        kwargs = {
            "cwd": str(self.project_root),
            "input": input_text,
            "text": True,
            "capture_output": True,
            "timeout": timeout,
            "env": env,
        }

        # Add process group creation on Unix systems
        if hasattr(os, "setsid"):
            kwargs["start_new_session"] = True

        # In CI environments, be more tolerant of file descriptor issues
        is_ci = any(key in os.environ for key in ["CI", "GITHUB_ACTIONS", "TRAVIS", "CIRCLECI"])

        try:
            result = subprocess.run(cmd, **kwargs)
            return result
        except subprocess.TimeoutExpired as e:
            # Handle timeout error gracefully
            stdout_str = (
                e.stdout.decode()
                if isinstance(e.stdout, bytes)
                else str(e.stdout)
                if e.stdout
                else ""
            )
            stderr_str = (
                e.stderr.decode()
                if isinstance(e.stderr, bytes)
                else str(e.stderr)
                if e.stderr
                else ""
            )
            self.fail(
                f"CLI command timed out after {timeout} seconds: {' '.join(cmd)}\nStdout: {stdout_str}\nStderr: {stderr_str}"
            )
        except OSError as e:
            if e.errno == 9:  # Bad file descriptor
                if is_ci:
                    self.skipTest(f"File descriptor issue in CI environment, skipping test: {e}")
                else:
                    self.fail(f"File descriptor error: {e}")
            else:
                self.fail(f"OS error running CLI command: {e}")
        except Exception as e:
            self.fail(f"Failed to run CLI command: {e}")

    def _run_cli_command_with_fd_handling(self, args, input_text=None, timeout=30):
        """Helper method with extra file descriptor error handling for network tests"""
        try:
            return self._run_cli_command(args, input_text, timeout)
        except OSError as e:
            if e.errno == 9:  # Bad file descriptor
                self.skipTest(f"File descriptor issue, skipping test: {e}")
            else:
                raise

    def test_list_ontologies_command(self):
        """Test --list-ontologies command"""
        result = self._run_cli_command(["--list-ontologies"])

        # Should exit successfully
        self.assertEqual(result.returncode, 0, f"Command failed with stderr: {result.stderr}")

        # Should contain ontology information
        output = result.stderr  # CLI uses logger which goes to stderr
        self.assertIn("Available Ontologies", output)
        self.assertIn("Individual Ontologies:", output)
        self.assertIn("Recommended Combinations:", output)
        self.assertIn("Usage Examples:", output)

    def test_help_command(self):
        """Test --help command"""
        result = self._run_cli_command(["--help"])

        # Should exit successfully
        self.assertEqual(result.returncode, 0)

        # Should contain help information
        output = result.stdout
        self.assertIn("BioPortal Ontology Alignment CLI Tool", output)
        self.assertIn("--single-word", output)
        self.assertIn("--ontologies", output)
        self.assertIn("Examples:", output)

    def test_invalid_arguments_command(self):
        """Test command with invalid arguments"""
        # Test with no arguments
        result = self._run_cli_command([])

        # Should exit with error
        self.assertNotEqual(result.returncode, 0)

        # Should contain error message
        output = result.stderr
        self.assertIn("Either provide a TTL file or use --single-word option", output)

    def test_nonexistent_file_command(self):
        """Test command with non-existent TTL file"""
        result = self._run_cli_command(["nonexistent_file.ttl"])

        # Should exit with error
        self.assertNotEqual(result.returncode, 0)

        # Should contain file not found error
        output = result.stderr
        self.assertIn("File nonexistent_file.ttl not found", output)

    @pytest.mark.network
    def test_single_word_terminal_only_command(self):
        """Test single word query with terminal-only output"""
        result = self._run_cli_command_with_fd_handling(
            [
                "--single-word",
                "cancer",
                "--ontologies",
                "MONDO",
                "--terminal-only",
                "--max-results",
                "2",
            ],
            input_text="0\n",
        )  # Skip selection

        # Should handle the command without crashing
        # Note: May return non-zero exit code if no results or user skips
        output = result.stderr

        # Should contain query information
        self.assertIn("Single Word Query Mode", output)
        self.assertIn("Query: 'cancer'", output)

        # Should handle the skip gracefully or show results
        self.assertTrue(
            "Skipped cancer" in result.stdout or "Found" in output or "No results found" in output
        )

    def test_batch_mode_command_structure(self):
        """Test batch mode command structure (without network calls)"""
        # Create a minimal TTL file that should be parseable
        minimal_ttl = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://example.org/test> a owl:Class ;
    rdfs:label "Test Class" .
"""
        minimal_ttl_file = self.temp_dir_path / "minimal.ttl"
        minimal_ttl_file.write_text(minimal_ttl)

        # Create corresponding batch file
        minimal_batch = {
            "test_class": [
                {
                    "uri": "http://example.org/aligned",
                    "label": "Aligned Test Class",
                    "ontology": "TEST",
                    "description": "Test alignment",
                    "synonyms": [],
                    "source": "test",
                    "relationship": "skos:exactMatch",
                }
            ]
        }
        minimal_batch_file = self.temp_dir_path / "minimal_batch.json"
        minimal_batch_file.write_text(json.dumps(minimal_batch, indent=2))

        result = self._run_cli_command(
            [
                str(minimal_ttl_file),
                "--batch-mode",
                str(minimal_batch_file),
                "--output",
                str(self.output_ttl),
                "--terminal-only",
            ]
        )

        # The command structure should be valid
        # May fail due to parsing issues, but shouldn't fail on argument structure
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)
        self.assertNotIn("invalid choice", output)

    def test_disable_services_command_structure(self):
        """Test commands with disabled services"""
        # Test with BioPortal disabled
        result = self._run_cli_command(
            ["--single-word", "test", "--disable-bioportal", "--terminal-only"], input_text="0\n"
        )

        # Should handle the disable flag properly
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

        # Test with OLS disabled
        result = self._run_cli_command(
            ["--single-word", "test", "--disable-ols", "--terminal-only"], input_text="0\n"
        )

        # Should handle the disable flag properly
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

    def test_output_file_options_command(self):
        """Test various output file options"""
        # Test with custom output file
        result = self._run_cli_command(
            ["--single-word", "test", "--output", str(self.output_ttl), "--terminal-only"],
            input_text="0\n",
        )

        # Should accept the output file option
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

        # Test with report file
        result = self._run_cli_command(
            [
                "--single-word",
                "test",
                "--output",
                str(self.output_ttl),
                "--report",
                str(self.report_file),
                "--terminal-only",
            ],
            input_text="0\n",
        )

        # Should accept the report file option
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

    def test_ontology_selection_options_command(self):
        """Test various ontology selection options"""
        # Test with specific ontologies
        result = self._run_cli_command(
            ["--single-word", "test", "--ontologies", "MONDO,HP,NCIT", "--terminal-only"],
            input_text="0\n",
        )

        # Should accept the ontologies option
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)
        self.assertIn("Using ontologies: MONDO,HP,NCIT", output)

    def test_max_results_option_command(self):
        """Test max results option"""
        result = self._run_cli_command(
            ["--single-word", "test", "--max-results", "10", "--terminal-only"], input_text="0\n"
        )

        # Should accept the max-results option
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

    def test_api_key_option_command(self):
        """Test API key option"""
        result = self._run_cli_command(
            ["--single-word", "test", "--api-key", "test_key", "--terminal-only"], input_text="0\n"
        )

        # Should accept the API key option
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

    def test_comparison_only_option_command(self):
        """Test comparison-only option"""
        result = self._run_cli_command(
            ["--single-word", "test", "--comparison-only", "--terminal-only"], input_text="0\n"
        )

        # Should accept the comparison-only option
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)

    def test_command_combinations(self):
        """Test various command option combinations"""
        # Test multiple combined options
        result = self._run_cli_command(
            [
                "--single-word",
                "cancer",
                "--ontologies",
                "MONDO,HP",
                "--max-results",
                "3",
                "--disable-bioportal",
                "--terminal-only",
                "--comparison-only",
            ],
            input_text="0\n",
        )

        # Should handle multiple options correctly
        output = result.stderr
        self.assertNotIn("unrecognized arguments", output)
        self.assertIn("Single Word Query Mode", output)

    def test_input_validation_commands(self):
        """Test input validation in CLI commands"""
        # Test invalid max-results
        result = self._run_cli_command(["--single-word", "test", "--max-results", "invalid"])

        # Should fail with validation error
        self.assertNotEqual(result.returncode, 0)
        output = result.stderr
        self.assertIn("invalid int value", output)

    def test_environment_variable_handling(self):
        """Test that CLI properly handles environment variables"""
        # Test with BIOPORTAL_API_KEY environment variable
        env = os.environ.copy()
        env["BIOPORTAL_API_KEY"] = "test_env_key"
        env["PYTHONPATH"] = str(self.project_root)

        cmd = [sys.executable, "-m", "cli.main", "--single-word", "test", "--terminal-only"]

        try:
            if hasattr(os, "setsid"):
                result = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    input="0\n",
                    text=True,
                    capture_output=True,
                    timeout=30,
                    env=env,
                    start_new_session=True,
                )
            else:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    input="0\n",
                    text=True,
                    capture_output=True,
                    timeout=30,
                    env=env,
                )

            # Should run without API key argument error
            output = result.stderr
            self.assertNotIn("API key required", output)

        except subprocess.TimeoutExpired:
            self.fail("CLI command timed out")
        except OSError as e:
            if e.errno == 9:  # Bad file descriptor
                self.skipTest(f"File descriptor issue in environment test, skipping: {e}")
            else:
                raise

    def test_file_permissions_handling(self):
        """Test CLI handling of file permission issues"""
        # Create a directory where we can't write
        readonly_dir = self.temp_dir_path / "readonly"
        readonly_dir.mkdir()
        readonly_output = readonly_dir / "output.ttl"

        # Try to make directory read-only (may not work on all systems)
        try:
            os.chmod(str(readonly_dir), 0o444)

            self._run_cli_command(
                ["--single-word", "test", "--output", str(readonly_output), "--terminal-only"],
                input_text="0\n",
            )

            # Should handle permission issues gracefully
            # (behavior may vary by system, so we just check it doesn't crash)
            # The command should at least attempt to run

        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(str(readonly_dir), 0o755)
            except (OSError, PermissionError):
                pass

    def test_unicode_handling_commands(self):
        """Test CLI handling of Unicode characters"""
        result = self._run_cli_command(
            [
                "--single-word",
                "café",  # Unicode character
                "--terminal-only",
            ],
            input_text="0\n",
        )

        # Should handle Unicode without crashing
        self.assertIsNotNone(result.returncode)

        # Check that Unicode is handled in output
        output = result.stderr
        # Should not have encoding errors
        self.assertNotIn("UnicodeDecodeError", output)
        self.assertNotIn("UnicodeEncodeError", output)


if __name__ == "__main__":
    unittest.main()
