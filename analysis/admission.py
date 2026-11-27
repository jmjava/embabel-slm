"""Evidence-backed corpus admission (stdlib only)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from analysis.hashes import canonical_command_sha256, canonical_jsonl_sha256, prereg_sha256, sha256_file
from analysis.jsonl_io import load_jsonl, write_canonical_jsonl, write_jsonl
from analysis.practices import PREREG_PATH, admit_example, load_prereg, prefix_sizes
ADMISSION_RECEIPT_SCHEMA_VERSION = 1
MIN_CLEAN_TRAINING_EXAMPLES = 14000
_HEX64 = re.compile(r"^[a-f0-9]{64}$")
_ALLOWED_ORACLE_KINDS = frozenset({"compiler", "test", "executable_query", "parser"})


def validate_oracle_evidence(rows: Sequence[Mapping[str, object]]) -> list[str]:
    """Return structural evidence errors. Nonempty means admission must abort."""
    errors: list[str] = []
    required = (
        "evidence_id",
        "source_repo",
        "source_pin",
        "oracle_kind",
        "command_argv",
        "command_sha256",
        "output_sha256",
        "artifact_sha256",
        "exit_code",
        "covered_examples",
    )
    seen_evidence: set[str] = set()
    coverage_index: dict[str, str] = {}

    for index, row in enumerate(rows):
        prefix = f"evidence[{index}]"
        if not isinstance(row, Mapping):
            errors.append(f"{prefix}: not an object")
            continue
        for key in required:
            if key not in row:
                errors.append(f"{prefix}: missing {key}")
        evidence_id = row.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(f"{prefix}: invalid evidence_id")
        elif evidence_id in seen_evidence:
            errors.append(f"{prefix}: duplicate evidence_id {evidence_id}")
        else:
            seen_evidence.add(evidence_id)
        repo = row.get("source_repo")
        pin = row.get("source_pin")
        if not isinstance(repo, str) or not repo.strip():
            errors.append(f"{prefix}: invalid source_repo")
        if not isinstance(pin, str) or not pin.strip():
            errors.append(f"{prefix}: invalid source_pin")
        kind = row.get("oracle_kind")
        if kind not in _ALLOWED_ORACLE_KINDS:
            errors.append(f"{prefix}: oracle_kind must be one of {sorted(_ALLOWED_ORACLE_KINDS)}")
        argv = row.get("command_argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(part, str) for part in argv):
            errors.append(f"{prefix}: command_argv must be a nonempty string list")
        elif isinstance(argv, list) and argv:
            expected = canonical_command_sha256(argv)
            command_hash = row.get("command_sha256")
            if not isinstance(command_hash, str) or command_hash != expected:
                errors.append(f"{prefix}: command_sha256 does not match canonical argv hash")
        for hash_key in ("command_sha256", "output_sha256", "artifact_sha256"):
            value = row.get(hash_key)
            if not isinstance(value, str) or not _HEX64.fullmatch(value):
                errors.append(f"{prefix}: {hash_key} must be 64 hex chars")
        exit_code = row.get("exit_code")
        if exit_code != 0:
            errors.append(f"{prefix}: exit_code must be exactly 0")
        covered = row.get("covered_examples")
        if not isinstance(covered, list) or not covered:
            errors.append(f"{prefix}: covered_examples must be a nonempty list")
            continue
        for entry_index, entry in enumerate(covered):
            entry_prefix = f"{prefix}.covered_examples[{entry_index}]"
            if not isinstance(entry, Mapping):
                errors.append(f"{entry_prefix}: must be an object")
                continue
            example_id = entry.get("example_id")
            code_hash = entry.get("code_sha256")
            if not isinstance(example_id, str) or not _HEX64.fullmatch(example_id):
                errors.append(f"{entry_prefix}: invalid example_id")
                continue
            if not isinstance(code_hash, str) or not _HEX64.fullmatch(code_hash):
                errors.append(f"{entry_prefix}: invalid code_sha256")
                continue
            prior = coverage_index.get(example_id)
            if prior is not None and prior != str(evidence_id):
                errors.append(
                    f"{entry_prefix}: example {example_id} already covered by evidence {prior}"
                )
            else:
                coverage_index[example_id] = str(evidence_id)
    return errors


def _code_sha256_for_labeled(row: Mapping[str, object]) -> str | None:
    for key in ("code_sha256", "text_sha256"):
        value = row.get(key)
        if isinstance(value, str) and _HEX64.fullmatch(value):
            return value
    return None


def _holdout_provenance_groups(holdout_rows: Sequence[Mapping[str, object]]) -> set[str]:
    groups: set[str] = set()
    for row in holdout_rows:
        provenance = row.get("provenance_groups")
        if not isinstance(provenance, list):
            continue
        for group in provenance:
            if isinstance(group, str) and group.strip():
                groups.add(group.strip())
    return groups


def _matching_evidence(
    example_id: str,
    code_sha256: str,
    repo: str,
    pin: str,
    evidence_rows: Sequence[Mapping[str, object]],
) -> list[Mapping[str, object]]:
    matches: list[Mapping[str, object]] = []
    for row in evidence_rows:
        if row.get("source_repo") != repo or row.get("source_pin") != pin:
            continue
        covered = row.get("covered_examples")
        if not isinstance(covered, list):
            continue
        for entry in covered:
            if not isinstance(entry, Mapping):
                continue
            if entry.get("example_id") == example_id and entry.get("code_sha256") == code_sha256:
                matches.append(row)
                break
    return matches


def _count_by_domain_area(rows: Sequence[Mapping[str, object]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in rows:
        domain = row.get("domain")
        area = row.get("area")
        if not isinstance(domain, str) or not isinstance(area, str):
            continue
        bucket = counts.setdefault(domain, {})
        bucket[area] = bucket.get(area, 0) + 1
    return {domain: dict(sorted(areas.items())) for domain, areas in sorted(counts.items())}


def build_admission_receipt(
    *,
    labeled_hash: str,
    evidence_hash: str,
    admitted_hash: str,
    admitted_count: int,
    prereg_hash: str,
) -> dict[str, object]:
    return {
        "schema_version": ADMISSION_RECEIPT_SCHEMA_VERSION,
        "labeled_input_sha256": labeled_hash,
        "evidence_input_sha256": evidence_hash,
        "admitted_output_sha256": admitted_hash,
        "admitted_count": admitted_count,
        "prereg_sha256": prereg_hash,
    }


def verify_admission_receipt(
    receipt: Mapping[str, object],
    *,
    labeled_path: Path,
    evidence_path: Path,
    admitted_path: Path,
    prereg_path: Path | None = None,
) -> None:
    if int(receipt.get("schema_version", -1)) != ADMISSION_RECEIPT_SCHEMA_VERSION:
        raise ValueError("admission receipt schema version mismatch")
    prereg_path = prereg_path or PREREG_PATH
    expected = {
        "labeled_input_sha256": sha256_file(labeled_path),
        "evidence_input_sha256": sha256_file(evidence_path),
        "admitted_output_sha256": sha256_file(admitted_path),
        "prereg_sha256": prereg_sha256(prereg_path),
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise ValueError(f"admission receipt {key} mismatch")
    admitted = load_jsonl(admitted_path)
    if int(receipt.get("admitted_count", -1)) != len(admitted):
        raise ValueError("admission receipt admitted_count mismatch")


def admit_labeled_examples(
    labeled_rows: Sequence[Mapping[str, object]],
    evidence_rows: Sequence[Mapping[str, object]],
    holdout_rows: Sequence[Mapping[str, object]] | None = None,
    prereg: dict | None = None,
) -> dict[str, object]:
    """Admit labeled units with validated oracle evidence and protocol checks."""
    structural = validate_oracle_evidence(evidence_rows)
    if structural:
        raise ValueError("oracle evidence invalid: " + "; ".join(structural))

    prereg = prereg or load_prereg()
    largest_prefix = prefix_sizes(prereg)[-1]
    holdout_groups = _holdout_provenance_groups(holdout_rows or ())

    seen_ids: dict[str, int] = {}
    admitted: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []

    for index, row in enumerate(labeled_rows):
        reasons: list[str] = []
        example_id = row.get("example_id")
        if not isinstance(example_id, str) or not _HEX64.fullmatch(example_id):
            reasons.append("missing_or_invalid_example_id")
        else:
            seen_ids[example_id] = seen_ids.get(example_id, 0) + 1

        if row.get("oracle_evidence_validated") is True:
            reasons.append("self_asserted_oracle_evidence_validated")

        provenance = row.get("provenance_groups")
        if not isinstance(provenance, list) or not provenance:
            reasons.append("missing_provenance_groups")
        elif any(not isinstance(group, str) or not group.strip() for group in provenance):
            reasons.append("empty_provenance_group")
        elif any(str(group).strip().startswith("repository:") for group in provenance):
            reasons.append("repository_wide_provenance_group_forbidden")

        repo = row.get("source_repo")
        pin = row.get("source_pin")
        if not isinstance(repo, str) or not repo.strip() or not isinstance(pin, str) or not pin.strip():
            reasons.append("source_file_and_pin_recorded")

        area = row.get("area")
        if not isinstance(area, str):
            reasons.append("slice_label_from_pre_registered_set")

        code_hash = _code_sha256_for_labeled(row)
        if code_hash is None:
            reasons.append("missing_code_sha256")

        matches: list[Mapping[str, object]] = []
        if isinstance(example_id, str) and _HEX64.fullmatch(example_id) and code_hash is not None:
            matches = _matching_evidence(example_id, code_hash, str(repo), str(pin), evidence_rows)
        if not matches:
            reasons.append("oracle_evidence_not_covering_example")
        elif len(matches) > 1:
            reasons.append("conflicting_oracle_evidence")

        if isinstance(provenance, list):
            for group in provenance:
                if isinstance(group, str) and group.strip() in holdout_groups:
                    reasons.append("provenance_overlaps_holdout")
                    break

        out_row = dict(row)
        out_row.pop("oracle_evidence_validated", None)
        if not reasons:
            protocol = admit_example({**out_row, "oracle_evidence_validated": True}, prereg)
            reasons.extend(protocol)

        if reasons:
            rejected.append({**dict(row), "rejection_reasons": sorted(set(reasons))})
        else:
            out_row["oracle_evidence_validated"] = True
            out_row["executable_oracle"] = True
            admitted.append(out_row)

    duplicate_ids = sorted(example_id for example_id, count in seen_ids.items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"duplicate example_id in labeled pool: {duplicate_ids[:5]}")

    return {
        "largest_registered_prefix": largest_prefix,
        "admitted_count": len(admitted),
        "rejected_count": len(rejected),
        "short_of_largest_prefix": len(admitted) < largest_prefix,
        "short_of_clean_training_floor": len(admitted) < MIN_CLEAN_TRAINING_EXAMPLES,
        "admitted_by_domain_area": _count_by_domain_area(admitted),
        "rejected_by_domain_area": _count_by_domain_area(rejected),
        "admitted": admitted,
        "rejected": rejected,
    }


def admit_exit_code(summary: Mapping[str, Any]) -> int:
    if summary.get("evidence_errors"):
        return 1
    if summary.get("short_of_largest_prefix"):
        return 1
    if summary.get("short_of_clean_training_floor"):
        return 1
    return 0


def run_admit(
    labeled_path: Path,
    evidence_path: Path,
    holdout_path: Path | None = None,
    *,
    prereg: dict | None = None,
    admitted_out: Path | None = None,
    rejected_out: Path | None = None,
    receipt_out: Path | None = None,
    include_rows: bool = True,
) -> dict[str, object]:
    labeled = load_jsonl(labeled_path)
    evidence = load_jsonl(evidence_path)
    holdout = load_jsonl(holdout_path) if holdout_path is not None else None

    try:
        result = admit_labeled_examples(labeled, evidence, holdout, prereg)
        evidence_errors: list[str] = []
    except ValueError as exc:
        message = str(exc)
        if message.startswith("oracle evidence invalid:"):
            evidence_errors = [
                part.strip() for part in message.removeprefix("oracle evidence invalid:").split(";")
            ]
            result = {
                "largest_registered_prefix": prefix_sizes(prereg or load_prereg())[-1],
                "admitted_count": 0,
                "rejected_count": len(labeled),
                "short_of_largest_prefix": True,
                "short_of_clean_training_floor": True,
                "admitted_by_domain_area": {},
                "rejected_by_domain_area": _count_by_domain_area(labeled),
                "admitted": [],
                "rejected": [{**row, "rejection_reasons": ["oracle_evidence_invalid"]} for row in labeled],
            }
        else:
            raise

    summary: dict[str, object] = {
        "labeled_path": str(labeled_path),
        "evidence_path": str(evidence_path),
        "holdout_path": str(holdout_path) if holdout_path else None,
        "largest_registered_prefix": result["largest_registered_prefix"],
        "admitted_count": result["admitted_count"],
        "rejected_count": result["rejected_count"],
        "short_of_largest_prefix": result["short_of_largest_prefix"],
        "short_of_clean_training_floor": result["short_of_clean_training_floor"],
        "admitted_by_domain_area": result["admitted_by_domain_area"],
        "rejected_by_domain_area": result["rejected_by_domain_area"],
        "evidence_errors": evidence_errors,
    }
    if include_rows:
        summary["admitted"] = result["admitted"]
        summary["rejected"] = result["rejected"]

    if admitted_out is not None:
        write_canonical_jsonl(admitted_out, result["admitted"])
        summary["admitted_out"] = str(admitted_out)
        admitted_hash = sha256_file(admitted_out)
    else:
        admitted_hash = canonical_jsonl_sha256(result["admitted"])
    receipt = build_admission_receipt(
        labeled_hash=sha256_file(labeled_path),
        evidence_hash=sha256_file(evidence_path),
        admitted_hash=admitted_hash,
        admitted_count=int(result["admitted_count"]),
        prereg_hash=prereg_sha256(PREREG_PATH),
    )
    summary["admission_receipt"] = receipt
    if rejected_out is not None:
        write_jsonl(rejected_out, result["rejected"], sort_keys=True)
        summary["rejected_out"] = str(rejected_out)
    if receipt_out is not None:
        receipt_out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary["receipt_out"] = str(receipt_out)

    return summary


def admit_cli(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit(
            "usage: python3 -m analysis admit LABELED.jsonl EVIDENCE.jsonl "
            "[--holdout HOLDOUT.jsonl] [--admitted-out PATH] [--rejected-out PATH] [--receipt-out PATH]"
        )
    labeled_path = Path(argv[0])
    evidence_path = Path(argv[1])
    holdout_path: Path | None = None
    admitted_out: Path | None = None
    rejected_out: Path | None = None
    receipt_out: Path | None = None
    index = 2
    while index < len(argv):
        token = argv[index]
        if token == "--holdout":
            index += 1
            if index >= len(argv):
                raise SystemExit("missing path after --holdout")
            holdout_path = Path(argv[index])
        elif token == "--admitted-out":
            index += 1
            if index >= len(argv):
                raise SystemExit("missing path after --admitted-out")
            admitted_out = Path(argv[index])
        elif token == "--rejected-out":
            index += 1
            if index >= len(argv):
                raise SystemExit("missing path after --rejected-out")
            rejected_out = Path(argv[index])
        elif token == "--receipt-out":
            index += 1
            if index >= len(argv):
                raise SystemExit("missing path after --receipt-out")
            receipt_out = Path(argv[index])
        else:
            raise SystemExit(f"unknown admit option {token}")
        index += 1

    try:
        summary = run_admit(
            labeled_path,
            evidence_path,
            holdout_path,
            admitted_out=admitted_out,
            rejected_out=rejected_out,
            receipt_out=receipt_out,
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=2, sort_keys=True), end="")
    return admit_exit_code(summary)