"""Seal labeled corpus, evidence, and holdout without mutating inputs."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Mapping, Sequence

from analysis.admission import MIN_CLEAN_TRAINING_EXAMPLES, run_admit, validate_oracle_evidence
from analysis.design import allocate_holdout_areas, validate_holdout_tasks, validate_provenance_disjoint
from analysis.dedup import (
    CrossSplitNearDuplicateError,
    find_near_duplicate_pairs,
    records_from_mapping,
    validate_no_cross_split_near_duplicates,
)
from analysis.hashes import prereg_sha256, sha256_file
from analysis.jsonl_io import load_jsonl, write_canonical_jsonl
from analysis.practices import PREREG_PATH, areas, load_prereg, prefix_sizes
from analysis.publish import publish_directory
from analysis.training_examples import FORMATTER_VERSION, build_prefix_manifests, dedup_projection, format_sft_example

SEALED_STUDY_SCHEMA_VERSION = 1


def _holdout_dedup_records(holdout_rows: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for row in holdout_rows:
        task_id = str(row["task_id"])
        prompt = str(row["prompt"])
        code = str(row["code"])
        out.append({"id": task_id, "prompt": prompt, "code": code, "split": "holdout"})
    return out


def _train_dedup_records(admitted: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for index, row in enumerate(admitted, start=1):
        example = format_sft_example(row, line=index)
        records.append(dedup_projection(example))
    return records


def _count_clean_training(
    admitted: Sequence[Mapping[str, object]],
    prereg: dict,
) -> dict[tuple[str, str], int]:
    labels = areas(prereg)
    counts: dict[tuple[str, str], int] = {
        (domain, area): 0 for domain, domain_areas in labels.items() for area in domain_areas
    }
    for row in admitted:
        key = (str(row["domain"]), str(row["area"]))
        if key not in counts:
            raise ValueError(f"unregistered admitted stratum {key[0]}/{key[1]}")
        counts[key] += 1
    return counts


def _cross_split_dedup_report(
    admitted: Sequence[Mapping[str, object]],
    holdout_rows: Sequence[Mapping[str, object]],
    *,
    exhaustive: bool,
) -> dict[str, object]:
    train_records = records_from_mapping(_train_dedup_records(admitted))
    holdout_records = records_from_mapping(_holdout_dedup_records(holdout_rows))
    combined = train_records + holdout_records
    pairs = find_near_duplicate_pairs(combined, exhaustive=exhaustive)
    cross = [
        pair for pair in pairs if pair["split_a"] != pair["split_b"]
    ]
    return {
        "exhaustive": exhaustive,
        "near_duplicate_pairs": len(pairs),
        "cross_split_near_duplicate_pairs": cross,
        "cross_split_clean": len(cross) == 0,
    }


def seal_study(
    labeled_path: Path,
    evidence_path: Path,
    holdout_path: Path,
    outdir: Path,
    *,
    force: bool = False,
    exhaustive: bool = False,
    prereg: dict | None = None,
    min_clean_training: int | None = None,
) -> dict[str, object]:
    prereg = prereg or load_prereg()
    if outdir.exists() and any(outdir.iterdir()) and not force:
        raise ValueError(f"output directory {outdir} is not empty (use --force)")

    labeled_rows = load_jsonl(labeled_path)
    evidence_rows = load_jsonl(evidence_path)
    holdout_rows = load_jsonl(holdout_path)
    evidence_errors = validate_oracle_evidence(evidence_rows)
    if evidence_errors:
        raise ValueError("oracle evidence invalid: " + "; ".join(evidence_errors))

    admit_summary = run_admit(
        labeled_path,
        evidence_path,
        holdout_path,
        prereg=prereg,
        include_rows=True,
    )
    if admit_summary.get("evidence_errors"):
        raise ValueError("admission aborted on evidence errors")
    admitted = list(admit_summary.get("admitted") or [])
    clean_floor = int(min_clean_training if min_clean_training is not None else MIN_CLEAN_TRAINING_EXAMPLES)
    if len(admitted) < clean_floor:
        raise ValueError(f"need >={clean_floor} clean admitted rows, have {len(admitted)}")

    clean_counts = _count_clean_training(admitted, prereg)
    allocation = allocate_holdout_areas(clean_counts, prereg)
    validate_holdout_tasks(holdout_rows, allocation=allocation, prereg=prereg)

    train_provenance = [
        {"id": str(row["example_id"]), "provenance_groups": row["provenance_groups"]}
        for row in admitted
    ]
    holdout_provenance = [
        {"id": str(row["task_id"]), "provenance_groups": row["provenance_groups"]}
        for row in holdout_rows
    ]
    provenance_report = validate_provenance_disjoint(train_provenance, holdout_provenance)

    dedup_report = _cross_split_dedup_report(admitted, holdout_rows, exhaustive=exhaustive)
    if not dedup_report["cross_split_clean"]:
        raise CrossSplitNearDuplicateError(
            "cross-split near-duplicate gate failed",
            dedup_report["cross_split_near_duplicate_pairs"],
        )
    if not exhaustive:
        dedup_report["method"] = "minhash_lsh_candidates_then_exact_jaccard"
    else:
        dedup_report["method"] = "exhaustive_exact_jaccard"

    staging = Path(tempfile.mkdtemp(prefix="seal-study-", dir=outdir.parent))
    try:
        admitted_path = staging / "admitted.jsonl"
        write_canonical_jsonl(admitted_path, admitted)
        receipt = dict(admit_summary["admission_receipt"])
        receipt["admitted_output_sha256"] = sha256_file(admitted_path)
        prefix_root = staging / "prefixes"
        prefix_root.mkdir()
        prefix_manifest = build_prefix_manifests(
            admitted_path,
            prefix_root,
            force=True,
            prereg=prereg,
        )

        allocation_report = {
            "schema_version": SEALED_STUDY_SCHEMA_VERSION,
            "clean_training_counts": {
                f"{dom}/{ar}": count for (dom, ar), count in sorted(clean_counts.items())
            },
            "holdout_allocation": {
                f"{dom}/{ar}": count for (dom, ar), count in sorted(allocation.items())
            },
        }
        (staging / "allocation-report.json").write_text(
            json.dumps(allocation_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (staging / "dedup-report.json").write_text(
            json.dumps(dedup_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        holdout_manifest = {
            "schema_version": SEALED_STUDY_SCHEMA_VERSION,
            "tasks": len(holdout_rows),
            "task_ids": sorted(str(row["task_id"]) for row in holdout_rows),
            "allocation": allocation_report["holdout_allocation"],
            "holdout_sha256": sha256_file(holdout_path),
        }
        (staging / "holdout-manifest.json").write_text(
            json.dumps(holdout_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (staging / "admission-receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        sealed_manifest = {
            "schema_version": SEALED_STUDY_SCHEMA_VERSION,
            "sealed": True,
            "prereg_sha256": prereg_sha256(PREREG_PATH),
            "formatter_version": FORMATTER_VERSION,
            "prefixes": list(prefix_sizes(prereg)),
            "min_clean_training_examples": clean_floor,
            "admitted_count": len(admitted),
            "inputs": {
                "labeled_sha256": sha256_file(labeled_path),
                "evidence_sha256": sha256_file(evidence_path),
                "holdout_sha256": sha256_file(holdout_path),
            },
            "artifacts": {
                "admission_receipt": "admission-receipt.json",
                "allocation_report": "allocation-report.json",
                "dedup_report": "dedup-report.json",
                "holdout_manifest": "holdout-manifest.json",
                "prefix_manifest": "prefixes/manifest.json",
            },
            "holdout": {
                "task_ids": holdout_manifest["task_ids"],
                "manifest_sha256": sha256_file(staging / "holdout-manifest.json"),
                "metadata_by_task": {
                    str(row["task_id"]): {
                        "domain": str(row["domain"]),
                        "area": str(row["area"]),
                    }
                    for row in sorted(holdout_rows, key=lambda item: str(item["task_id"]))
                },
            },
            "provenance_disjoint": provenance_report,
            "dedup_gate": {
                "cross_split_clean": dedup_report["cross_split_clean"],
                "exhaustive": dedup_report["exhaustive"],
                "method": dedup_report["method"],
            },
        }
        (staging / "sealed-study-manifest.json").write_text(
            json.dumps(sealed_manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        publish_directory(staging, outdir, force=force)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    return dict(sealed_manifest)


def load_sealed_manifest(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("sealed manifest must be a JSON object")
    if payload.get("sealed") is not True:
        raise ValueError("manifest is not marked sealed")
    if int(payload.get("schema_version", -1)) != SEALED_STUDY_SCHEMA_VERSION:
        raise ValueError("sealed manifest schema mismatch")
    return payload


def seal_cli(argv: list[str]) -> int:
    if len(argv) < 4:
        raise SystemExit(
            "usage: python3 -m analysis seal-study LABELED.jsonl EVIDENCE.jsonl HOLDOUT.jsonl OUTDIR [--force] [--exhaustive]"
        )
    labeled = Path(argv[0])
    evidence = Path(argv[1])
    holdout = Path(argv[2])
    outdir = Path(argv[3])
    force = False
    exhaustive = False
    for token in argv[4:]:
        if token == "--force":
            force = True
        elif token == "--exhaustive":
            exhaustive = True
        else:
            raise SystemExit(f"unknown seal-study option {token}")
    try:
        manifest = seal_study(
            labeled, evidence, holdout, outdir, force=force, exhaustive=exhaustive
        )
    except (ValueError, OSError, json.JSONDecodeError, CrossSplitNearDuplicateError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"sealed": True, "admitted_count": manifest["admitted_count"]}, sort_keys=True))
    return 0