#!/usr/bin/env python3

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analysis.admission import (
    admit_exit_code,
    admit_labeled_examples,
    run_admit,
    validate_oracle_evidence,
)
from analysis.hashes import canonical_command_sha256
from analysis.label_areas import (
    attach_example_identity,
    compute_example_id,
    provenance_groups_for,
)
from analysis.training_examples import attach_unit_code_metadata
from analysis.practices import load_prereg

ROOT = Path(__file__).resolve().parent.parent


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _labeled_row(**overrides) -> dict[str, object]:
    text = "text-body-for-tests"
    row = attach_unit_code_metadata(
        {
            "domain": "embabel",
            "area": "generation",
            "source_repo": "embabel/guide",
            "source_pin": "pin1234567890",
            "source_file": "src/Hello.kt#greet",
            "grain": "method",
            "section": "greet",
            "class_frame": "@EmbabelComponent\nclass Hello",
        },
        text,
    )
    row.update(overrides)
    return attach_example_identity(row)


def _evidence_for(rows: list[dict[str, object]], **overrides) -> dict[str, object]:
    zero = "0" * 64
    argv = ["python3", "-c", "print('ok')"]
    record = {
        "evidence_id": "build-embabel-guide",
        "source_repo": "embabel/guide",
        "source_pin": "pin1234567890",
        "oracle_kind": "compiler",
        "command_argv": argv,
        "command_sha256": canonical_command_sha256(argv),
        "output_sha256": zero,
        "artifact_sha256": zero,
        "exit_code": 0,
        "covered_examples": [
            {"example_id": str(row["example_id"]), "code_sha256": str(row["code_sha256"])}
            for row in rows
        ],
    }
    record.update(overrides)
    return record


class ExampleIdentityTests(unittest.TestCase):
    def test_example_id_is_order_invariant(self):
        row_a = _labeled_row()
        row_b = _labeled_row()
        self.assertEqual(compute_example_id(row_a), compute_example_id(row_b))
        shuffled = [dict(row_a), dict(row_b)]
        ids = sorted(compute_example_id(row) for row in shuffled)
        self.assertEqual(ids[0], ids[1])

    def test_sibling_methods_share_file_provenance(self):
        first = _labeled_row(section="greet", source_file="src/Hello.kt#greet")
        second = _labeled_row(
            section="finish",
            source_file="src/Hello.kt#finish",
            text_sha256=_text_hash("other-body"),
        )
        file_groups = {
            g for g in provenance_groups_for(first) if g.startswith("file:")
        } & {g for g in provenance_groups_for(second) if g.startswith("file:")}
        self.assertEqual(len(file_groups), 1)

    def test_query_fixture_provenance(self):
        row = attach_example_identity(
            {
                "domain": "drivine",
                "area": "query",
                "source_kind": "query",
                "source_repo": "drivine/specs",
                "source_pin": "deadbeef",
                "source_file": "queries.yaml",
                "case_name": "Co-actors",
                "cypher": "MATCH (n) RETURN n",
                "text_sha256": _text_hash("MATCH (n) RETURN n"),
                "grain": "method",
            }
        )
        groups = provenance_groups_for(row)
        self.assertTrue(any(group.startswith("fixture:") for group in groups))


class OracleEvidenceValidationTests(unittest.TestCase):
    def test_rejects_failed_exit_code(self):
        zero = "0" * 64
        row = _evidence_for(
            [],
            exit_code=1,
            covered_examples=[{"example_id": zero, "code_sha256": zero}],
        )
        errors = validate_oracle_evidence([row])
        self.assertTrue(any("exit_code" in error for error in errors))

    def test_rejects_duplicate_coverage(self):
        rows = [_labeled_row(), _labeled_row(text_sha256=_text_hash("x"), section="other")]
        first = _evidence_for([rows[0]], evidence_id="e1")
        second = _evidence_for([rows[1]], evidence_id="e2")
        dup = {"example_id": rows[0]["example_id"], "code_sha256": rows[0]["code_sha256"]}
        first["covered_examples"] = [dup]
        second["covered_examples"] = [dup]
        errors = validate_oracle_evidence([first, second])
        self.assertTrue(any("already covered" in error for error in errors))

    def test_rejects_self_asserted_admission_marker(self):
        row = _labeled_row(oracle_evidence_validated=True)
        evidence = [_evidence_for([row])]
        summary = admit_labeled_examples([row], evidence, prereg=load_prereg())
        self.assertEqual(summary["admitted_count"], 0)
        self.assertIn("self_asserted_oracle_evidence_validated", summary["rejected"][0]["rejection_reasons"])


class AdmitLabeledExamplesTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()

    def test_admits_with_matching_evidence(self):
        row = _labeled_row()
        evidence = [_evidence_for([row])]
        summary = admit_labeled_examples([row], evidence, prereg=self.prereg)
        self.assertEqual(summary["admitted_count"], 1)
        self.assertEqual(summary["rejected_count"], 0)
        self.assertTrue(summary["admitted"][0].get("oracle_evidence_validated"))

    def test_rejects_repo_pin_mismatch(self):
        row = _labeled_row()
        evidence = [_evidence_for([row], source_repo="embabel/other", source_pin="otherpin")]
        summary = admit_labeled_examples([row], evidence, prereg=self.prereg)
        self.assertEqual(summary["admitted_count"], 0)
        self.assertIn("oracle_evidence_not_covering_example", summary["rejected"][0]["rejection_reasons"])

    def test_rejects_uncovered_example(self):
        row = _labeled_row()
        zero = "f" * 64
        evidence = [_evidence_for([row], covered_examples=[{"example_id": zero, "code_sha256": zero}])]
        summary = admit_labeled_examples([row], evidence, prereg=self.prereg)
        self.assertEqual(summary["admitted_count"], 0)

    def test_holdout_provenance_leak(self):
        row = _labeled_row()
        evidence = [_evidence_for([row])]
        holdout = [{"provenance_groups": row["provenance_groups"]}]
        summary = admit_labeled_examples([row], evidence, holdout, self.prereg)
        self.assertIn("provenance_overlaps_holdout", summary["rejected"][0]["rejection_reasons"])

    def test_duplicate_example_id_raises(self):
        row = _labeled_row()
        duplicate = dict(row)
        with self.assertRaises(ValueError):
            admit_labeled_examples([row, duplicate], [_evidence_for([row])], prereg=self.prereg)

    def test_short_of_largest_prefix_flag(self):
        row = _labeled_row()
        summary = admit_labeled_examples([row], [_evidence_for([row])], prereg=self.prereg)
        self.assertTrue(summary["short_of_largest_prefix"])
        self.assertEqual(admit_exit_code(summary), 1)


class AdmitCliTests(unittest.TestCase):
    def test_cli_exits_nonzero_when_short(self):
        row = _labeled_row()
        evidence = _evidence_for([row])
        with tempfile.TemporaryDirectory() as tmp:
            labeled = Path(tmp) / "labeled.jsonl"
            ev_path = Path(tmp) / "evidence.jsonl"
            labeled.write_text(json.dumps(row) + "\n", encoding="utf-8")
            ev_path.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "analysis", "admit", str(labeled), str(ev_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["short_of_largest_prefix"])

    def test_run_admit_never_mutates_inputs(self):
        row = _labeled_row()
        evidence = _evidence_for([row])
        with tempfile.TemporaryDirectory() as tmp:
            labeled = Path(tmp) / "labeled.jsonl"
            ev_path = Path(tmp) / "evidence.jsonl"
            labeled.write_text(json.dumps(row) + "\n", encoding="utf-8")
            ev_path.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
            labeled_before = labeled.read_text(encoding="utf-8")
            ev_before = ev_path.read_text(encoding="utf-8")
            run_admit(labeled, ev_path, include_rows=False)
            self.assertEqual(labeled.read_text(encoding="utf-8"), labeled_before)
            self.assertEqual(ev_path.read_text(encoding="utf-8"), ev_before)


if __name__ == "__main__":
    unittest.main()