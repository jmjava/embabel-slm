"""Snippet oracle checks cover only snippets a real parser accepts."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from analysis.hashes import sha256_text
from analysis.project_oracle import path_under_source_root
from analysis.snippet_oracle import (
    check_python_snippets,
    cypher_parameters,
    cypher_text_in_document,
    evidence_record_from_check,
    recorded_cypher_parameters,
    write_work_manifest,
)


class SnippetOracleTests(unittest.TestCase):
    def test_python_parser_accepts_only_valid_syntax(self) -> None:
        valid = "def answer():\n    return 1\n"
        invalid = "def answer(\n"
        rows = [
            {"example_id": "a" * 64, "code_sha256": sha256_text(valid), "code": valid},
            {"example_id": "b" * 64, "code_sha256": sha256_text(invalid), "code": invalid},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            write_work_manifest(workdir, rows)
            results = check_python_snippets(workdir)
        self.assertEqual([row["ok"] for row in results], [True, False])

    def test_evidence_omits_failed_snippets(self) -> None:
        results = [
            {"example_id": "a" * 64, "code_sha256": "c" * 64, "ok": True},
            {"example_id": "b" * 64, "code_sha256": "d" * 64, "ok": False},
        ]
        record = evidence_record_from_check(
            evidence_id="parser-python-example",
            source_repo="embabel/example",
            source_pin="e" * 40,
            oracle_kind="parser",
            argv=["python3", "-m", "analysis.snippet_oracle", "check-python", "/tmp/work"],
            run_meta={
                "exit_code": 0,
                "command_sha256": "f" * 64,
                "output_sha256": "1" * 64,
                "artifact_sha256": "2" * 64,
            },
            results=results,
        )
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(len(record["covered_examples"]), 1)
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(json.loads(json.dumps(record["covered_examples"]))[0]["example_id"], "a" * 64)

    def test_cypher_parameters_bind_each_name_once(self) -> None:
        self.assertEqual(cypher_parameters("RETURN $p + $p + $row_2"), {"p": "x", "row_2": "x"})

    def test_recorded_cypher_parameters_follow_the_matching_step(self) -> None:
        document = {
            "cases": [
                {"steps": [{"cypher": "RETURN $n", "parameters": {"n": 2}}]},
                {"steps": [{"cypher": "RETURN $n", "parameters": {"n": "x"}}]},
            ]
        }
        self.assertEqual(
            recorded_cypher_parameters(document, "RETURN $n"),
            [{"n": 2}, {"n": "x"}],
        )
        self.assertEqual(recorded_cypher_parameters(document, "RETURN $missing"), [])
        self.assertEqual(recorded_cypher_parameters(document, "RETURN $n\n"), [{"n": 2}, {"n": "x"}])
        self.assertTrue(cypher_text_in_document(document, "RETURN $n\n"))
        self.assertFalse(cypher_text_in_document(document, "RETURN $missing"))

    def test_project_source_roots_skip_gradle_scripts(self) -> None:
        self.assertTrue(path_under_source_root("src/main/kotlin/App.kt", ["src/main/kotlin"]))
        self.assertTrue(
            path_under_source_root("drivine4j-cli/src/test/kotlin/Cmd.kt", ["drivine4j-cli/src/test/kotlin"])
        )
        self.assertFalse(path_under_source_root("compiler/build.gradle.kts", ["compiler/src/commonMain"]))
        self.assertFalse(path_under_source_root("src/main/kotlin/notes.md", ["src/main/kotlin"]))

    def test_nonzero_exit_produces_no_evidence(self) -> None:
        record = evidence_record_from_check(
            evidence_id="parser-python-example",
            source_repo="embabel/example",
            source_pin="e" * 40,
            oracle_kind="parser",
            argv=["python3"],
            run_meta={
                "exit_code": 1,
                "command_sha256": "f" * 64,
                "output_sha256": "1" * 64,
                "artifact_sha256": "2" * 64,
            },
            results=[{"example_id": "a" * 64, "code_sha256": "c" * 64, "ok": True}],
        )
        self.assertIsNone(record)


if __name__ == "__main__":
    unittest.main()
