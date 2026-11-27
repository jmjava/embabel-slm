"""Deterministic SFT records and prefix manifests (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from analysis.admission import verify_admission_receipt
from analysis.design import seeded_stratified_order
from analysis.jsonl_io import load_jsonl, write_jsonl
from analysis.practices import PREREG_PATH, areas, load_prereg, prefix_sizes
from analysis.publish import publish_directory


def base_source_file(source_file: str) -> str:
    """Path without method ``#`` suffix (slashes normalized)."""
    return source_file.replace("\\", "/").split("#", 1)[0]

FORMATTER_VERSION = "embabel-slm-code-sft-v1"

_HEX64 = re.compile(r"^[a-f0-9]{64}$")

_TOKEN_PATTERN = re.compile(
    r"[\w]+|[-+*/=<>!&|^~%@#.;:,\[\]{}()'\"\\]+",
    re.UNICODE,
)

_CLASS_FRAME = re.compile(
    r"(?m)^(?P<body>(?:[ \t]*@[A-Za-z_][\w.]*(?:\([^)\n]*\))?[ \t]*\n)*"
    r"[ \t]*(?:(?:public|private|protected|internal|open|abstract|data|sealed|inner)\s+)*"
    r"(?:class|interface|object|enum)\b[^\n{]*)"
)

_LANGUAGE_BY_SUFFIX: tuple[tuple[str, str], ...] = (
    (".kt", "kotlin"),
    (".kts", "kotlin"),
    (".java", "java"),
    (".scala", "scala"),
    (".groovy", "groovy"),
    (".py", "python"),
    (".js", "javascript"),
    (".ts", "typescript"),
    (".yaml", "yaml"),
    (".yml", "yaml"),
    (".json", "json"),
    (".sql", "sql"),
    (".cypher", "cypher"),
    (".g4", "antlr"),
    (".md", "markdown"),
)

_PROSE_FIELD_NAMES = frozenset(
    {
        "description",
        "doc",
        "documentation",
        "prose",
        "markdown",
        "rationale",
        "summary",
        "behavior",
        "nl_description",
        "model_output",
        "generated_text",
        "instruction",
        "instructions",
    }
)

_REQUIRED_ADMITTED = (
    "example_id",
    "oracle_evidence_validated",
    "domain",
    "area",
    "source_repo",
    "source_file",
    "source_pin",
    "grain",
    "code",
    "provenance_groups",
)


def sha256_code(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def lexical_token_count(text: str) -> int:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if not collapsed:
        return 0
    return len(_TOKEN_PATTERN.findall(collapsed))


def normalize_terminal_newline(code: str) -> str:
    """Append a single terminal newline when the excerpt has no trailing newline."""
    if not code or code.endswith("\n"):
        return code
    return code + "\n"


def detect_language(row: Mapping[str, object]) -> str:
    if row.get("source_kind") == "query":
        return "cypher"
    path = base_source_file(str(row.get("source_file", "")))
    lowered = path.lower()
    for suffix, language in _LANGUAGE_BY_SUFFIX:
        if lowered.endswith(suffix):
            return language
    domain = row.get("domain")
    if domain == "drivine" and str(row.get("grain")) == "method" and row.get("cypher"):
        return "cypher"
    return "unknown"


def type_framing_from_code(code: str) -> str:
    match = _CLASS_FRAME.search(code)
    if not match:
        return ""
    header_end = match.end()
    window = code[header_end : min(len(code), header_end + 800)]
    brace = window.find("{")
    line_end = code.find("\n", match.end())
    end = match.end()
    if brace != -1 and (line_end == -1 or header_end + brace <= line_end + 600):
        end = header_end + brace
    elif line_end != -1 and code[match.end() : line_end].rstrip().endswith(":"):
        end = line_end
    frame = code[match.start() : end]
    return "\n".join(line.strip() for line in frame.splitlines() if line.strip())


def attach_unit_code_metadata(row: dict[str, object], code: str) -> dict[str, object]:
    """Persist exact unit code and model-independent diagnostics on a labeled row."""
    row["code"] = code
    row["language"] = detect_language(row)
    row["char_count"] = len(code)
    row["lexical_token_count"] = lexical_token_count(code)
    digest = sha256_code(code)
    row["code_sha256"] = digest
    # The raw-pool hash is file-level. Once a file is split, identity and
    # deduplication must use the exact method/class/query unit, not the parent
    # file hash shared by every sibling.
    row["text_sha256"] = digest
    return row


def _prompt_context(row: Mapping[str, object]) -> dict[str, object]:
    grain = str(row["grain"])
    language = detect_language(row)
    base: dict[str, object] = {
        "formatter_version": FORMATTER_VERSION,
        "domain": str(row["domain"]),
        "area": str(row["area"]),
        "language": language,
        "grain": grain,
    }
    if row.get("source_kind") == "query" or (row.get("cypher") and row.get("case_name")):
        case_name = row.get("case_name")
        base["grain"] = "query"
        base["fixture_path"] = base_source_file(str(row["source_file"]))
        if isinstance(case_name, str) and case_name.strip():
            base["case_name"] = case_name.strip()
        return base
    if grain == "method":
        section = row.get("section")
        if not isinstance(section, str) or not section.strip():
            raise ValueError("method grain requires section (method name)")
        frame = row.get("class_frame")
        base["method_name"] = section.strip()
        base["source_path"] = base_source_file(str(row["source_file"]))
        if isinstance(frame, str) and frame.strip():
            base["class_frame"] = frame.strip()
        return base
    if grain == "class":
        base["source_path"] = base_source_file(str(row["source_file"]))
        framing = row.get("class_frame")
        if isinstance(framing, str) and framing.strip():
            base["type_frame"] = framing.strip()
        else:
            code = str(row.get("code", ""))
            extracted = type_framing_from_code(code)
            if extracted:
                base["type_frame"] = extracted
            else:
                base["type_frame"] = Path(base["source_path"]).name
        return base
    raise ValueError(f"unknown grain {grain!r}")


def build_prompt(row: Mapping[str, object]) -> str:
    """Serialize code-derived context deterministically (no prose)."""
    context = _prompt_context(row)
    return json.dumps(context, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _validate_admitted_row(row: Mapping[str, object], *, line: int | None = None) -> None:
    prefix = f"line {line}" if line is not None else "record"
    if not isinstance(row, Mapping):
        raise ValueError(f"{prefix}: row must be an object")
    for key in _REQUIRED_ADMITTED:
        if key not in row:
            raise ValueError(f"{prefix}: missing {key}")
    example_id = row["example_id"]
    if not isinstance(example_id, str) or not _HEX64.fullmatch(example_id):
        raise ValueError(f"{prefix}: invalid example_id")
    if row.get("oracle_evidence_validated") is not True:
        raise ValueError(f"{prefix}: oracle_evidence_validated must be true")
    for key in ("domain", "area", "source_repo", "source_file", "source_pin"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{prefix}: invalid {key}")
    registered = areas(load_prereg())
    domain = str(row["domain"])
    area = str(row["area"])
    if area not in registered.get(domain, ()):
        raise ValueError(f"{prefix}: unregistered area {domain}/{area}")
    grain = row.get("grain")
    if grain not in ("method", "class"):
        raise ValueError(f"{prefix}: grain must be method or class")
    provenance = row.get("provenance_groups")
    if not isinstance(provenance, list) or not provenance:
        raise ValueError(f"{prefix}: provenance_groups required")
    if any(not isinstance(group, str) or not group.strip() for group in provenance):
        raise ValueError(f"{prefix}: empty provenance group")
    code = row.get("code")
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"{prefix}: empty code")
    for prose_key in _PROSE_FIELD_NAMES:
        if prose_key in row:
            raise ValueError(f"{prefix}: prose field {prose_key!r} is not allowed")
    stored = row.get("code_sha256")
    if isinstance(stored, str) and _HEX64.fullmatch(stored):
        if stored != sha256_code(str(code)):
            raise ValueError(f"{prefix}: code_sha256 mismatch")
    text_sha = row.get("text_sha256")
    if isinstance(text_sha, str) and _HEX64.fullmatch(text_sha) and text_sha != sha256_code(str(code)):
        raise ValueError(f"{prefix}: text_sha256 does not match code")
    language = detect_language(row)
    if language == "unknown":
        raise ValueError(f"{prefix}: unknown language")
    if grain == "method" and row.get("source_kind") == "query":
        cypher = row.get("cypher")
        if not isinstance(cypher, str) or cypher != code:
            raise ValueError(f"{prefix}: query code must be exact cypher")
    _prompt_context(row)


def format_sft_example(row: Mapping[str, object], *, line: int | None = None) -> dict[str, object]:
    """Build one deterministic SFT record from an admitted unit."""
    _validate_admitted_row(row, line=line)
    code = str(row["code"])
    prompt = build_prompt(row)
    response = normalize_terminal_newline(code)
    language = detect_language(row)
    return {
        "example_id": str(row["example_id"]),
        "prompt": prompt,
        "response": response,
        "formatter_version": FORMATTER_VERSION,
        "metadata": {
            "domain": str(row["domain"]),
            "area": str(row["area"]),
            "language": language,
            "grain": str(row["grain"]),
            "source_repo": str(row["source_repo"]),
            "source_file": str(row["source_file"]),
            "source_pin": str(row["source_pin"]),
            "provenance_groups": [str(group).strip() for group in row["provenance_groups"]],
        },
        "code_sha256": sha256_code(code),
        "char_count": len(code),
        "lexical_token_count": lexical_token_count(code),
    }


def dedup_projection(example: Mapping[str, object]) -> dict[str, object]:
    """Build a train-split dedup record compatible with analysis.dedup."""
    return {
        "id": str(example["example_id"]),
        "prompt": str(example["prompt"]),
        "code": str(example["response"]),
        "split": "train",
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prereg_page_sha256() -> str:
    return hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()


def _prefix_nesting(ordered_ids: Sequence[str], prefixes: Sequence[int]) -> dict[str, object]:
    proof: dict[str, object] = {}
    for size in prefixes:
        slice_ids = list(ordered_ids[:size])
        nested: dict[str, bool] = {}
        for smaller in prefixes:
            if smaller <= size:
                nested[str(smaller)] = slice_ids[:smaller] == list(ordered_ids[:smaller])
        proof[str(size)] = {
            "count": len(slice_ids),
            "nested_prefix_of_larger": nested,
            "first_id": slice_ids[0] if slice_ids else None,
            "last_id": slice_ids[-1] if slice_ids else None,
        }
    return proof


def _example_stats(examples: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not examples:
        return {
            "records": 0,
            "char_total": 0,
            "char_mean": 0.0,
            "char_min": 0,
            "char_max": 0,
            "lexical_token_total": 0,
            "lexical_token_mean": 0.0,
            "lexical_token_min": 0,
            "lexical_token_max": 0,
        }
    chars = [int(row["char_count"]) for row in examples]
    tokens = [int(row["lexical_token_count"]) for row in examples]
    count = len(examples)
    return {
        "records": count,
        "char_total": sum(chars),
        "char_mean": sum(chars) / count,
        "char_min": min(chars),
        "char_max": max(chars),
        "lexical_token_total": sum(tokens),
        "lexical_token_mean": sum(tokens) / count,
        "lexical_token_min": min(tokens),
        "lexical_token_max": max(tokens),
        "lexical_token_count_note": (
            "model_independent_whitespace_token_count_not_selected_tokenizer_budget"
        ),
    }


def _domain_area_counts(examples: Sequence[Mapping[str, object]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in examples:
        domain = str(row["metadata"]["domain"])
        area = str(row["metadata"]["area"])
        bucket = counts.setdefault(domain, {})
        bucket[area] = bucket.get(area, 0) + 1
    return {domain: dict(sorted(items.items())) for domain, items in sorted(counts.items())}


def build_prefix_manifests(
    admitted_path: Path,
    outdir: Path,
    *,
    force: bool = False,
    prereg: dict | None = None,
    admission_receipt: Mapping[str, object] | None = None,
    labeled_path: Path | None = None,
    evidence_path: Path | None = None,
    require_admission_receipt: bool = False,
) -> dict[str, object]:
    """Format admitted rows, order them, and write six nested prefix files."""
    prereg = prereg or load_prereg()
    prefixes = prefix_sizes(prereg)
    largest = prefixes[-1]
    if require_admission_receipt or admission_receipt is not None:
        if admission_receipt is None:
            raise ValueError("admission receipt is required")
        if labeled_path is None or evidence_path is None:
            raise ValueError("admission receipt verification requires labeled and evidence paths")
        verify_admission_receipt(
            admission_receipt,
            labeled_path=labeled_path,
            evidence_path=evidence_path,
            admitted_path=admitted_path,
        )
    admitted = load_jsonl(admitted_path)

    formatted_by_id: dict[str, dict[str, object]] = {}
    for index, row in enumerate(admitted, start=1):
        example = format_sft_example(row, line=index)
        example_id = str(example["example_id"])
        if example_id in formatted_by_id:
            raise ValueError(f"duplicate example_id {example_id}")
        formatted_by_id[example_id] = example

    if len(formatted_by_id) < largest:
        raise ValueError(f"need at least {largest} admitted records, have {len(formatted_by_id)}")

    order_records = [
        {
            "id": example_id,
            "domain": formatted_by_id[example_id]["metadata"]["domain"],
            "area": formatted_by_id[example_id]["metadata"]["area"],
            "provenance_groups": formatted_by_id[example_id]["metadata"]["provenance_groups"],
        }
        for example_id in sorted(formatted_by_id)
    ]
    ordered_ids, order_report = seeded_stratified_order(order_records, prereg)
    ordered_examples = [formatted_by_id[example_id] for example_id in ordered_ids]

    if outdir.exists() and any(outdir.iterdir()) and not force:
        raise ValueError(f"output directory {outdir} is not empty (use --force to replace)")

    staging = Path(tempfile.mkdtemp(prefix="prefix-build-", dir=outdir.parent))
    try:
        ordered_path = staging / "ordered.jsonl"
        write_jsonl(ordered_path, ordered_examples, sort_keys=True)

        prefix_paths: dict[str, str] = {}
        prefix_stats: dict[str, object] = {}
        for size in prefixes:
            slice_rows = ordered_examples[:size]
            path = staging / f"prefix-{size}.jsonl"
            write_jsonl(path, slice_rows, sort_keys=True)
            prefix_paths[str(size)] = f"prefix-{size}.jsonl"
            prefix_stats[str(size)] = _example_stats(slice_rows)

        prefix_report = {
            "formatter_version": FORMATTER_VERSION,
            "order_seed": order_report["order_seed"],
            "prefixes": list(prefixes),
            "ordered_length": len(ordered_examples),
            "stratified_order": order_report,
            "prefix_statistics": prefix_stats,
            "domain_area_counts_full_order": _domain_area_counts(ordered_examples),
        }
        prefix_report_path = staging / "prefix-report.json"
        prefix_report_path.write_text(
            json.dumps(prefix_report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        nesting = _prefix_nesting(ordered_ids, prefixes)
        for size in prefixes:
            nested = nesting[str(size)]["nested_prefix_of_larger"]
            for check in prefixes:
                if check <= size and nested[str(check)] is not True:
                    raise ValueError(f"prefix {size} does not nest prefix {check}")

        manifest_payload: dict[str, object] = {
            "formatter_version": FORMATTER_VERSION,
            "order_seed": order_report["order_seed"],
            "prereg_sha256": _prereg_page_sha256(),
            "admitted_source": str(admitted_path),
            "record_count_admitted_input": len(admitted),
            "record_count_ordered": len(ordered_examples),
            "prefixes": list(prefixes),
            "files": {
                "ordered.jsonl": {
                    "sha256": _sha256_file(ordered_path),
                    "records": len(ordered_examples),
                },
                "prefix-report.json": {
                    "sha256": _sha256_file(prefix_report_path),
                },
            },
            "prefix_files": {},
            "statistics": {
                "full_order": _example_stats(ordered_examples),
                "by_prefix": prefix_stats,
            },
            "domain_area_counts": _domain_area_counts(ordered_examples),
            "prefix_nesting_by_example_id": nesting,
            "lexical_token_count_note": (
                "char_count and lexical_token_count are model-independent diagnostics; "
                "selected tokenizer counts remain a pre-training blocker"
            ),
        }
        for size in prefixes:
            name = f"prefix-{size}.jsonl"
            manifest_payload["prefix_files"][str(size)] = {
                "path": name,
                "sha256": _sha256_file(staging / name),
                "records": size,
            }
            manifest_payload["files"][name] = manifest_payload["prefix_files"][str(size)]
        manifest_path = staging / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        publish_directory(staging, outdir, force=force)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)

    return manifest_payload


def build_prefixes_cli(argv: list[str]) -> int:
    if len(argv) < 2:
        raise SystemExit(
            "usage: python3 -m analysis build-prefixes ADMITTED.jsonl OUTDIR "
            "--admission-receipt RECEIPT.json --labeled LABELED.jsonl --evidence EVIDENCE.jsonl [--force]"
        )
    admitted_path = Path(argv[0])
    outdir = Path(argv[1])
    force = False
    receipt_path: Path | None = None
    labeled_path: Path | None = None
    evidence_path: Path | None = None
    index = 2
    while index < len(argv):
        token = argv[index]
        if token == "--force":
            force = True
        elif token == "--admission-receipt":
            index += 1
            receipt_path = Path(argv[index])
        elif token == "--labeled":
            index += 1
            labeled_path = Path(argv[index])
        elif token == "--evidence":
            index += 1
            evidence_path = Path(argv[index])
        else:
            raise SystemExit(f"unknown option {token}")
        index += 1
    if receipt_path is None or labeled_path is None or evidence_path is None:
        raise SystemExit(
            "build-prefixes requires --admission-receipt, --labeled, and --evidence"
        )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    try:
        manifest = build_prefix_manifests(
            admitted_path,
            outdir,
            force=force,
            admission_receipt=receipt,
            labeled_path=labeled_path,
            evidence_path=evidence_path,
            require_admission_receipt=True,
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps({"manifest_path": str(outdir / "manifest.json"), "record_count_ordered": manifest["record_count_ordered"]}))
    return 0