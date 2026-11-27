#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from analysis.dedup import (
    CrossSplitNearDuplicateError,
    DedupRecord,
    analyze_dedup_records,
    content_hash_normalized,
    dedup_exit_code,
    exact_jaccard,
    find_near_duplicate_pairs,
    load_records_jsonl,
    lsh_candidate_pairs,
    minhash_signature,
    normalize_prompt_and_code,
    token_shingles,
    validate_no_cross_split_near_duplicates,
)


def _rec(record_id: str, prompt: str, code: str, split: str) -> DedupRecord:
    return DedupRecord(record_id=record_id, prompt=prompt, code=code, split=split)


def _long_body(prefix: str) -> str:
    """Enough tokens for stable 5-shingles."""
    return " ".join(f"{prefix}_token_{i}" for i in range(20))


class NormalizeTests(unittest.TestCase):
    def test_nfkc_lower_whitespace(self):
        text = normalize_prompt_and_code("  HELLO\r\n", "ﬁle\t\t")
        self.assertIn("hello", text)
        self.assertIn("file", text)
        self.assertNotIn("\r", text)

    def test_preserves_operators(self):
        text = normalize_prompt_and_code("add", "a + b == c")
        self.assertIn("+", text)
        self.assertIn("==", text)

    def test_content_hash_stable(self):
        norm = normalize_prompt_and_code("A", "B")
        self.assertEqual(content_hash_normalized(norm), content_hash_normalized(norm))


class ShingleAndJaccardTests(unittest.TestCase):
    def test_empty_shingles(self):
        self.assertEqual(token_shingles(""), frozenset())
        self.assertEqual(exact_jaccard(frozenset(), frozenset()), 1.0)

    def test_short_text_single_shingle(self):
        shingles = token_shingles("one two three")
        self.assertEqual(shingles, frozenset(["one two three"]))
        self.assertEqual(exact_jaccard(shingles, shingles), 1.0)

    def test_exact_copy_score(self):
        body = _long_body("x")
        s = token_shingles(body)
        self.assertEqual(exact_jaccard(s, s), 1.0)


class NearDuplicatePairTests(unittest.TestCase):
    def setUp(self):
        self.base_prompt = "implement feature"
        self.base_code = _long_body("code")

    def test_exact_copy_pair(self):
        a = _rec("a", self.base_prompt, self.base_code, "train")
        b = _rec("b", self.base_prompt, self.base_code, "holdout")
        pairs = find_near_duplicate_pairs([a, b], exhaustive=True)
        self.assertEqual(len(pairs), 1)
        self.assertGreaterEqual(pairs[0]["exact_jaccard"], 0.8)

    def test_high_similarity_variant(self):
        variant = self.base_code.replace("token_19", "token_19b")
        a = _rec("a", self.base_prompt, self.base_code, "train")
        b = _rec("b", self.base_prompt, variant, "train")
        pairs = find_near_duplicate_pairs([a, b], exhaustive=True)
        self.assertEqual(len(pairs), 1)
        self.assertGreaterEqual(pairs[0]["exact_jaccard"], 0.8)

    def test_below_threshold_not_reported(self):
        other = _long_body("other")
        a = _rec("a", self.base_prompt, self.base_code, "train")
        b = _rec("b", "other task", other, "train")
        pairs = find_near_duplicate_pairs([a, b], exhaustive=True)
        self.assertEqual(pairs, [])

    def test_short_same_content_pair(self):
        a = _rec("a", "hi", "x = 1", "train")
        b = _rec("b", "hi", "x = 1", "holdout")
        pairs = find_near_duplicate_pairs([a, b], exhaustive=True)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["exact_jaccard"], 1.0)

    def test_cross_split_validation_raises(self):
        a = _rec("a", self.base_prompt, self.base_code, "train")
        b = _rec("b", self.base_prompt, self.base_code, "holdout")
        with self.assertRaises(CrossSplitNearDuplicateError) as ctx:
            validate_no_cross_split_near_duplicates([a], [b], exhaustive=True)
        self.assertGreaterEqual(len(ctx.exception.evidence), 1)

    def test_same_split_only_ignored_for_cross_check(self):
        a = _rec("a", self.base_prompt, self.base_code, "train")
        b = _rec("b", self.base_prompt, self.base_code, "train")
        validate_no_cross_split_near_duplicates([a, b], [], exhaustive=True)

    def test_duplicate_ids_rejected(self):
        a = _rec("dup", "p", "c", "train")
        b = _rec("dup", "p", "c", "holdout")
        with self.assertRaises(ValueError):
            find_near_duplicate_pairs([a, b])

    def test_sorted_evidence(self):
        a = _rec("z", self.base_prompt, self.base_code, "train")
        b = _rec("a", self.base_prompt, self.base_code, "holdout")
        pairs = find_near_duplicate_pairs([a, b], exhaustive=True)
        self.assertEqual(pairs[0]["id_a"], "a")
        self.assertEqual(pairs[0]["id_b"], "z")


class DeterminismTests(unittest.TestCase):
    def test_signatures_stable(self):
        shingles = token_shingles(_long_body("d"))
        sig_a = minhash_signature(shingles)
        sig_b = minhash_signature(shingles)
        self.assertEqual(sig_a, sig_b)
        self.assertEqual(len(sig_a), 128)

    def test_lsh_candidates_deterministic(self):
        entries = [minhash_signature(token_shingles(_long_body(f"n{i}"))) for i in range(5)]
        entry_copy = list(entries)
        pairs_a = lsh_candidate_pairs(entries)
        pairs_b = lsh_candidate_pairs(entry_copy)
        self.assertEqual(pairs_a, pairs_b)


class JsonlTests(unittest.TestCase):
    def test_load_and_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            path.write_text(
                json.dumps(
                    {
                        "id": "1",
                        "prompt": "p",
                        "code": _long_body("c"),
                        "split": "train",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            records = load_records_jsonl(path)
            self.assertEqual(len(records), 1)

    def test_missing_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(json.dumps({"id": "1", "prompt": "p"}) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_records_jsonl(path)


class AnalyzeTests(unittest.TestCase):
    def test_exit_code(self):
        clean = {"cross_split_clean": True}
        dirty = {"cross_split_clean": False}
        self.assertEqual(dedup_exit_code(clean), 0)
        self.assertEqual(dedup_exit_code(dirty), 1)

    def test_small_auto_exhaustive(self):
        body = _long_body("small")
        records = [
            _rec("a", "p", body, "train"),
            _rec("b", "p", body, "holdout"),
        ]
        out = analyze_dedup_records(records)
        self.assertTrue(out["exhaustive"])
        self.assertFalse(out["cross_split_clean"])


class CliTests(unittest.TestCase):
    def test_cli_smoke_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            body = _long_body("cli")
            path.write_text(
                json.dumps({"id": "a", "prompt": "p", "code": body, "split": "train"}) + "\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, "-m", "analysis", "dedup", str(path)],
                cwd=Path(__file__).resolve().parent.parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["cross_split_clean"])

    def test_cli_cross_split_exit_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "records.jsonl"
            body = _long_body("cli2")
            row = json.dumps({"id": "a", "prompt": "p", "code": body, "split": "train"})
            row2 = json.dumps({"id": "b", "prompt": "p", "code": body, "split": "holdout"})
            path.write_text(row + "\n" + row2 + "\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "analysis", "dedup", str(path), "--exhaustive"],
                cwd=Path(__file__).resolve().parent.parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 1)
            payload = json.loads(proc.stdout)
            self.assertFalse(payload["cross_split_clean"])
            self.assertEqual(len(payload["cross_split_near_duplicate_pairs"]), 1)


if __name__ == "__main__":
    unittest.main()