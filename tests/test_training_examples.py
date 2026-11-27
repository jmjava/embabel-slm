#!/usr/bin/env python3

import hashlib
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analysis.design import seeded_stratified_order
from analysis.dedup import parse_record
from analysis.label_areas import attach_example_identity, code_sections
from analysis.practices import areas, load_prereg, prefix_sizes
from analysis.training_examples import (
    FORMATTER_VERSION,
    attach_unit_code_metadata,
    build_prefix_manifests,
    build_prompt,
    dedup_projection,
    format_sft_example,
    sha256_code,
)


ROOT = Path(__file__).resolve().parent.parent


def _admitted_row(**overrides) -> dict[str, object]:
    code = "@Action\nfun greet(name: String): String {\n    return name\n}"
    row = attach_example_identity(
        attach_unit_code_metadata(
            {
                "domain": "embabel",
                "area": "generation",
                "source_repo": "embabel/guide",
                "source_pin": "pin1234567890",
                "source_file": "src/Hello.kt#greet",
                "grain": "method",
                "section": "greet",
                "class_frame": "@EmbabelComponent\nclass Hello",
                "oracle_evidence_validated": True,
            },
            code,
        )
    )
    row.update(overrides)
    return row


class FormatSftTests(unittest.TestCase):
    def test_unit_hash_replaces_parent_file_hash(self):
        row = {"text_sha256": "0" * 64}
        attach_unit_code_metadata(row, "fun first() = 1")
        first_hash = row["text_sha256"]
        attach_unit_code_metadata(row, "fun second() = 2")
        self.assertNotEqual(first_hash, row["text_sha256"])
        self.assertEqual(row["text_sha256"], row["code_sha256"])

    def test_method_prompt_uses_frame_not_body(self):
        row = _admitted_row()
        example = format_sft_example(row)
        prompt = json.loads(example["prompt"])
        self.assertEqual(prompt["formatter_version"], FORMATTER_VERSION)
        self.assertEqual(prompt["method_name"], "greet")
        self.assertIn("class Hello", prompt["class_frame"])
        self.assertNotIn("fun greet", prompt["class_frame"])
        self.assertEqual(example["response"], row["code"] + "\n")

    def test_class_prompt_uses_path_framing(self):
        code = "@EmbabelComponent\nclass Solo {\n    fun x() {}\n}"
        row = _admitted_row(
            source_file="pkg/Solo.kt",
            grain="class",
            section=None,
            class_frame="",
            code=code,
            text_sha256=sha256_code(code),
            code_sha256=sha256_code(code),
        )
        row.pop("section", None)
        example = format_sft_example(row)
        prompt = json.loads(example["prompt"])
        self.assertEqual(prompt["grain"], "class")
        self.assertEqual(prompt["source_path"], "pkg/Solo.kt")
        self.assertIn("class Solo", prompt["type_frame"])

    def test_query_uses_exact_cypher(self):
        cypher = "MATCH (n) RETURN n"
        row = attach_example_identity(
            attach_unit_code_metadata(
                {
                    "domain": "drivine",
                    "area": "query",
                    "source_kind": "query",
                    "source_repo": "drivine/specs",
                    "source_pin": "deadbeef",
                    "source_file": "queries.yaml",
                    "case_name": "Co-actors",
                    "cypher": cypher,
                    "grain": "method",
                    "oracle_evidence_validated": True,
                },
                cypher,
            )
        )
        example = format_sft_example(row)
        self.assertEqual(example["response"], cypher + "\n")
        prompt = json.loads(example["prompt"])
        self.assertEqual(prompt["grain"], "query")
        self.assertEqual(prompt["case_name"], "Co-actors")

    def test_rejects_prose_field(self):
        row = _admitted_row(description="what it does")
        with self.assertRaises(ValueError):
            format_sft_example(row)

    def test_rejects_code_hash_mismatch(self):
        row = _admitted_row(code_sha256="0" * 64)
        with self.assertRaises(ValueError):
            format_sft_example(row)

    def test_deterministic_formatter(self):
        row = _admitted_row()
        first = format_sft_example(row)
        second = format_sft_example(row)
        self.assertEqual(first, second)
        self.assertEqual(build_prompt(row), first["prompt"])

    def test_dedup_projection(self):
        example = format_sft_example(_admitted_row())
        record = parse_record(dedup_projection(example), 1)
        self.assertEqual(record.split, "train")
        self.assertEqual(record.record_id, example["example_id"])


class LabelCodeFieldTests(unittest.TestCase):
    def test_method_code_is_not_whole_file(self):
        text = """
class Other {
    fun noise(): String {
        return "noise-value"
    }
}

@EmbabelComponent
class Hello {
    @Action
    fun greet(name: String): String {
        return name
    }

    @Goal
    fun finish(): Boolean {
        return true
    }
}
"""
        sections = code_sections("Hello.kt", text)
        greet = next(section for name, section, _, _ in sections if name == "greet")
        self.assertLess(len(greet), len(text))
        row = attach_unit_code_metadata({"domain": "embabel", "source_file": "Hello.kt#greet"}, greet)
        self.assertEqual(row["code"], greet)
        self.assertEqual(row["code_sha256"], sha256_code(greet))


class PrefixBuildTests(unittest.TestCase):
    def setUp(self):
        self.prereg = load_prereg()
        self.largest = prefix_sizes(self.prereg)[-1]

    def _synthetic_admitted(self, n: int, *, salt: int = 0) -> list[dict[str, object]]:
        labels = areas(self.prereg)
        rows: list[dict[str, object]] = []
        domains = ("embabel", "drivine")
        for index in range(n):
            domain = domains[index % 2]
            area = labels[domain][index % len(labels[domain])]
            code = f"// unit {salt}-{index}\nfun f{index}() = {index}"
            row = attach_example_identity(
                attach_unit_code_metadata(
                    {
                        "domain": domain,
                        "area": area,
                        "source_repo": f"{domain}/repo",
                        "source_pin": f"pin{salt:04d}",
                        "source_file": f"src/File{index}.kt#f{index}",
                        "grain": "method",
                        "section": f"f{index}",
                        "class_frame": f"class File{index}",
                        "oracle_evidence_validated": True,
                    },
                    code,
                )
            )
            rows.append(row)
        return rows

    def _write_admitted(self, rows: list[dict[str, object]], path: Path) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, sort_keys=True) + "\n")

    def test_prefix_nesting_hashes_and_counts(self):
        rows = self._synthetic_admitted(self.largest)
        with tempfile.TemporaryDirectory() as tmp:
            admitted = Path(tmp) / "admitted.jsonl"
            outdir = Path(tmp) / "out"
            self._write_admitted(rows, admitted)
            manifest = build_prefix_manifests(admitted, outdir, prereg=self.prereg)
            self.assertEqual(manifest["record_count_ordered"], self.largest)
            for size in prefix_sizes(self.prereg):
                path = outdir / f"prefix-{size}.jsonl"
                self.assertTrue(path.is_file())
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertEqual(len(lines), size)
                digest = manifest["prefix_files"][str(size)]["sha256"]
                self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
            ordered = [
                json.loads(line)["example_id"] for line in (outdir / "ordered.jsonl").read_text().splitlines()
            ]
            for size in prefix_sizes(self.prereg)[1:]:
                smaller = size // 2 if size in (1000, 2000, 4000, 8000, 14000) else None
                for check in prefix_sizes(self.prereg):
                    if check < size:
                        self.assertEqual(ordered[:check], ordered[:size][:check])

    def test_input_order_invariant(self):
        rows_a = self._synthetic_admitted(self.largest, salt=1)
        rows_b = list(reversed(self._synthetic_admitted(self.largest, salt=1)))
        random.shuffle(rows_a)
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / "a.jsonl"
            path_b = Path(tmp) / "b.jsonl"
            out_a = Path(tmp) / "out-a"
            out_b = Path(tmp) / "out-b"
            self._write_admitted(rows_a, path_a)
            self._write_admitted(rows_b, path_b)
            build_prefix_manifests(path_a, out_a, prereg=self.prereg)
            build_prefix_manifests(path_b, out_b, prereg=self.prereg)
            text_a = (out_a / "ordered.jsonl").read_text(encoding="utf-8")
            text_b = (out_b / "ordered.jsonl").read_text(encoding="utf-8")
            self.assertEqual(text_a, text_b)

    def test_duplicate_ids_rejected(self):
        rows = self._synthetic_admitted(10)
        rows.append(dict(rows[0]))
        with tempfile.TemporaryDirectory() as tmp:
            admitted = Path(tmp) / "admitted.jsonl"
            outdir = Path(tmp) / "out"
            self._write_admitted(rows, admitted)
            with self.assertRaises(ValueError):
                build_prefix_manifests(admitted, outdir, prereg=self.prereg)

    def test_short_pool_rejected(self):
        rows = self._synthetic_admitted(100)
        with tempfile.TemporaryDirectory() as tmp:
            admitted = Path(tmp) / "admitted.jsonl"
            outdir = Path(tmp) / "out"
            self._write_admitted(rows, admitted)
            with self.assertRaises(ValueError):
                build_prefix_manifests(admitted, outdir, prereg=self.prereg)

    def test_nonempty_outdir_without_force(self):
        rows = self._synthetic_admitted(self.largest)
        with tempfile.TemporaryDirectory() as tmp:
            admitted = Path(tmp) / "admitted.jsonl"
            outdir = Path(tmp) / "out"
            self._write_admitted(rows, admitted)
            outdir.mkdir()
            (outdir / "stray.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(ValueError):
                build_prefix_manifests(admitted, outdir, prereg=self.prereg)

    def test_stratified_report_matches_seeded_order(self):
        rows = self._synthetic_admitted(self.largest)
        order_inputs = [
            {
                "id": row["example_id"],
                "domain": row["domain"],
                "area": row["area"],
                "provenance_groups": row["provenance_groups"],
            }
            for row in sorted(rows, key=lambda item: str(item["example_id"]))
        ]
        _, report = seeded_stratified_order(order_inputs, self.prereg)
        with tempfile.TemporaryDirectory() as tmp:
            admitted = Path(tmp) / "admitted.jsonl"
            outdir = Path(tmp) / "out"
            self._write_admitted(rows, admitted)
            build_prefix_manifests(admitted, outdir, prereg=self.prereg)
            written = json.loads((outdir / "prefix-report.json").read_text(encoding="utf-8"))
            self.assertEqual(
                written["stratified_order"]["prefix_reports"],
                report["prefix_reports"],
            )


class CliSmokeTests(unittest.TestCase):
    def test_build_prefixes_cli_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "analysis"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertIn("build-prefixes", result.stderr)

    def test_forged_admission_receipt_rejected(self):
        from tests.test_admission import _evidence_for, _labeled_row
        from analysis.admission import run_admit

        row = _labeled_row()
        evidence = _evidence_for([row])
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            labeled = base / "labeled.jsonl"
            ev_path = base / "evidence.jsonl"
            admitted = base / "admitted.jsonl"
            labeled.write_text(__import__("json").dumps(row) + "\n", encoding="utf-8")
            ev_path.write_text(__import__("json").dumps(evidence) + "\n", encoding="utf-8")
            summary = run_admit(labeled, ev_path, admitted_out=admitted)
            forged = dict(summary["admission_receipt"])
            forged["admitted_output_sha256"] = "0" * 64
            receipt = base / "receipt.json"
            receipt.write_text(__import__("json").dumps(forged, indent=2), encoding="utf-8")
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "analysis",
                    "build-prefixes",
                    str(admitted),
                    str(base / "out"),
                    "--admission-receipt",
                    str(receipt),
                    "--labeled",
                    str(labeled),
                    "--evidence",
                    str(ev_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("admitted_output_sha256", proc.stderr)


if __name__ == "__main__":
    unittest.main()