#!/usr/bin/env python3

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from analysis.admission import admit_labeled_examples, verify_admission_receipt
from analysis.design import allocate_holdout_areas
from analysis.hashes import canonical_command_sha256
from analysis.jsonl_io import write_jsonl
from analysis.label_areas import attach_example_identity
from analysis.practices import areas, load_prereg, prefix_sizes
import copy
from analysis.seal import seal_study
from analysis.training_examples import attach_unit_code_metadata
def _task_id(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _evidence_batch(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    by_repo: dict[tuple[str, str], list[dict[str, object]]] = {}
    for row in rows:
        key = (str(row["source_repo"]), str(row["source_pin"]))
        by_repo.setdefault(key, []).append(row)
    evidence: list[dict[str, object]] = []
    argv = ["python3", "-c", "print('ok')"]
    command_hash = canonical_command_sha256(argv)
    zero = "0" * 64
    for index, ((repo, pin), covered_rows) in enumerate(sorted(by_repo.items())):
        evidence.append(
            {
                "evidence_id": f"evidence-{index}",
                "source_repo": repo,
                "source_pin": pin,
                "oracle_kind": "test",
                "command_argv": argv,
                "command_sha256": command_hash,
                "output_sha256": zero,
                "artifact_sha256": zero,
                "exit_code": 0,
                "covered_examples": [
                    {"example_id": str(row["example_id"]), "code_sha256": str(row["code_sha256"])}
                    for row in covered_rows
                ],
            }
        )
    return evidence


def _synthetic_labeled(n: int, prereg: dict) -> list[dict[str, object]]:
    labels = areas(prereg)
    rows: list[dict[str, object]] = []
    domains = ("embabel", "drivine")
    for index in range(n):
        domain = domains[index % 2]
        area = labels[domain][index % len(labels[domain])]
        code = f"// unit {index}\nfun f{index}() = {index}"
        row = attach_example_identity(
            attach_unit_code_metadata(
                {
                    "domain": domain,
                    "area": area,
                    "source_repo": f"{domain}/repo",
                    "source_pin": f"pin{index % 50:04d}",
                    "source_file": f"src/holdout-disjoint/File{index}.kt#f{index}",
                    "grain": "method",
                    "section": f"f{index}",
                    "class_frame": f"class File{index}",
                },
                code,
            )
        )
        rows.append(row)
    return rows


def _holdout_for_labeled(
    labeled: list[dict[str, object]],
    evidence: list[dict[str, object]],
    prereg: dict,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    admitted = admit_labeled_examples(labeled, evidence, prereg=prereg)["admitted"]
    labels = areas(prereg)
    counts: dict[tuple[str, str], int] = {
        (domain, area): 0 for domain, domain_areas in labels.items() for area in domain_areas
    }
    for row in admitted:
        key = (str(row["domain"]), str(row["area"]))
        counts[key] += 1
    holdout = _synthetic_holdout(prereg, counts)
    return holdout, admitted


def _padded_clean_counts(
    labeled: list[dict[str, object]],
    prereg: dict,
) -> dict[tuple[str, str], int]:
    labels = areas(prereg)
    counts: dict[tuple[str, str], int] = {
        (domain, area): 1 for domain, domain_areas in labels.items() for area in domain_areas
    }
    for row in labeled:
        key = (str(row["domain"]), str(row["area"]))
        counts[key] = counts.get(key, 0) + 1
    return counts


def _synthetic_holdout(prereg: dict, clean_counts: dict[tuple[str, str], int]) -> list[dict[str, object]]:
    allocation = allocate_holdout_areas(clean_counts, prereg)
    rows: list[dict[str, object]] = []
    for (domain, area), count in sorted(allocation.items()):
        for slot in range(count):
            token = f"holdout:{domain}:{area}:{slot}"
            rows.append(
                {
                    "task_id": _task_id(token),
                    "domain": domain,
                    "area": area,
                    "executable_oracle": True,
                    "prompt": json.dumps({"fixture": token}, sort_keys=True),
                    "code": f"// holdout task\nval id = {slot}\n",
                    "provenance_groups": [f"holdout-task:{token}@sealed"],
                }
            )
    return rows


def _small_prereg() -> dict:
    prereg = copy.deepcopy(load_prereg())
    prereg["statistics"]["example_doses"]["prefixes"] = [500, 1000]
    return prereg


class SealStudyTests(unittest.TestCase):
    def setUp(self):
        self.prereg = _small_prereg()
        self.min_train = prefix_sizes(self.prereg)[-1]

    def test_happy_path_exhaustive(self):
        labeled = _synthetic_labeled(self.min_train, self.prereg)
        evidence = _evidence_batch(labeled)
        holdout, _admitted = _holdout_for_labeled(labeled, evidence, self.prereg)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            labeled_path = base / "labeled.jsonl"
            evidence_path = base / "evidence.jsonl"
            holdout_path = base / "holdout.jsonl"
            outdir = base / "sealed"
            write_jsonl(labeled_path, labeled, sort_keys=True)
            write_jsonl(evidence_path, evidence, sort_keys=True)
            write_jsonl(holdout_path, holdout, sort_keys=True)
            manifest = seal_study(
                labeled_path,
                evidence_path,
                holdout_path,
                outdir,
                exhaustive=True,
                prereg=self.prereg,
                min_clean_training=self.min_train,
            )
            self.assertTrue(manifest["sealed"])
            self.assertEqual(manifest["dedup_gate"]["method"], "exhaustive_exact_jaccard")
            receipt = json.loads((outdir / "admission-receipt.json").read_text(encoding="utf-8"))
            verify_admission_receipt(
                receipt,
                labeled_path=labeled_path,
                evidence_path=evidence_path,
                admitted_path=outdir / "admitted.jsonl",
            )
            self.assertTrue((outdir / "sealed-study-manifest.json").is_file())
            self.assertTrue((outdir / "prefixes" / "manifest.json").is_file())

    def test_rejects_provenance_leak(self):
        labeled = _synthetic_labeled(self.min_train, self.prereg)
        clean_counts = _padded_clean_counts(labeled, self.prereg)
        holdout = _synthetic_holdout(self.prereg, clean_counts)
        holdout[0]["provenance_groups"] = list(labeled[0]["provenance_groups"])
        evidence = _evidence_batch(labeled)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_jsonl(base / "labeled.jsonl", labeled, sort_keys=True)
            write_jsonl(base / "evidence.jsonl", evidence, sort_keys=True)
            write_jsonl(base / "holdout.jsonl", holdout, sort_keys=True)
            with self.assertRaises(ValueError):
                seal_study(
                    base / "labeled.jsonl",
                    base / "evidence.jsonl",
                    base / "holdout.jsonl",
                    base / "out",
                    prereg=self.prereg,
                    min_clean_training=self.min_train,
                )

    def test_rejects_training_shortage(self):
        labeled = _synthetic_labeled(100, self.prereg)
        evidence = _evidence_batch(labeled)
        holdout, _admitted = _holdout_for_labeled(labeled, evidence, self.prereg)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_jsonl(base / "labeled.jsonl", labeled, sort_keys=True)
            write_jsonl(base / "evidence.jsonl", evidence, sort_keys=True)
            write_jsonl(base / "holdout.jsonl", holdout, sort_keys=True)
            with self.assertRaises(ValueError):
                seal_study(
                    base / "labeled.jsonl",
                    base / "evidence.jsonl",
                    base / "holdout.jsonl",
                    base / "out",
                    prereg=self.prereg,
                    min_clean_training=self.min_train,
                )

    def test_scores_reject_alternate_ids_against_seal(self):
        from analysis.seal import load_sealed_manifest
        from analysis.study_results import validate_scores_against_seal

        labeled = _synthetic_labeled(self.min_train, self.prereg)
        evidence = _evidence_batch(labeled)
        holdout, _admitted = _holdout_for_labeled(labeled, evidence, self.prereg)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_jsonl(base / "labeled.jsonl", labeled, sort_keys=True)
            write_jsonl(base / "evidence.jsonl", evidence, sort_keys=True)
            write_jsonl(base / "holdout.jsonl", holdout, sort_keys=True)
            outdir = base / "sealed"
            seal_study(
                base / "labeled.jsonl",
                base / "evidence.jsonl",
                base / "holdout.jsonl",
                outdir,
                prereg=self.prereg,
                min_clean_training=self.min_train,
            )
            sealed = load_sealed_manifest(outdir / "sealed-study-manifest.json")
            canonical = sealed["holdout"]["task_ids"][0]
            meta = sealed["holdout"]["metadata_by_task"][canonical]
            rows = [
                {
                    "task_id": "f" * 64,
                    "domain": meta["domain"],
                    "area": meta["area"],
                    "prefix_size": 500,
                    "training_seed": 20260227,
                    "passed": True,
                }
            ]
            with self.assertRaises(ValueError):
                validate_scores_against_seal(rows, sealed)
            rows[0]["task_id"] = canonical
            rows.append(
                {
                    "task_id": sealed["holdout"]["task_ids"][1],
                    "domain": meta["domain"],
                    "area": meta["area"],
                    "prefix_size": 500,
                    "training_seed": 20260227,
                    "passed": False,
                }
            )
            with self.assertRaises(ValueError):
                validate_scores_against_seal(rows, sealed)


if __name__ == "__main__":
    unittest.main()