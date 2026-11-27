#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from analysis.jsonl_io import iter_physical_jsonl_lines, load_jsonl
from analysis.admission import run_admit
from analysis.dedup import load_records_jsonl
from tests.test_admission import _evidence_for, _labeled_row


LS = "\u2028"
PS = "\u2029"


class JsonlIoTests(unittest.TestCase):
    def test_unicode_separators_in_one_physical_line(self):
        row = {"id": "x", "prompt": f"before{LS}after", "code": f"a{PS}b", "split": "train"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            self.assertEqual(len(list(iter_physical_jsonl_lines(path))), 1)
            records = load_records_jsonl(path)
            self.assertEqual(len(records), 1)
            self.assertIn(LS, records[0].prompt)

    def test_dedup_loader_physical_line(self):
        row = {"id": "x", "prompt": f"x{LS}", "code": f"y{PS}", "split": "train"}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(json.dumps(row) + "\n", encoding="utf-8")
            loaded = load_records_jsonl(path)
            self.assertEqual(len(loaded), 1)

    def test_admit_and_prefix_loaders(self):
        row = _labeled_row()
        row["code"] = f"fun x(){LS} = 1"
        evidence = _evidence_for([row])
        with tempfile.TemporaryDirectory() as tmp:
            labeled = Path(tmp) / "labeled.jsonl"
            evidence_path = Path(tmp) / "evidence.jsonl"
            labeled.write_text(json.dumps(row) + "\n", encoding="utf-8")
            evidence_path.write_text(json.dumps(evidence) + "\n", encoding="utf-8")
            summary = run_admit(labeled, evidence_path, admitted_out=Path(tmp) / "admitted.jsonl")
            self.assertEqual(summary["admitted_count"], 1)
            admitted = load_jsonl(Path(tmp) / "admitted.jsonl")
            self.assertEqual(len(admitted), 1)


if __name__ == "__main__":
    unittest.main()