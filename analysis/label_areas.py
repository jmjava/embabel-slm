"""Label collected code into one pre-registered area, or send it to review.

Rules are fixed text and path checks. A model score does not choose a
label. Two matches, or none, go to review. Generation and query are used
only when no earlier rule matches. A labeled row is not an admitted example.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping

from analysis.jsonl_io import iter_physical_jsonl_lines, load_jsonl, write_jsonl
from analysis.practices import areas, load_prereg
from analysis.training_examples import attach_unit_code_metadata

_EXAMPLE_ID_SCHEMA_VERSION = 1
_HEX64 = re.compile(r"^[a-f0-9]{64}$")

_EMBABEL_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("repair", re.compile(r"repair|unreachable|missing[-_ ]dependenc|diagnos|known-bad", re.I)),
    ("planning", re.compile(r"@Goal\b|\bGoal\b|eligibility|@Condition\b|planner", re.I)),
    ("transformation", re.compile(r"transform|spring-to-action|toEmbabel|imperative", re.I)),
    ("refactor", re.compile(r"refactor|split[-_ ]?(?:large|action)", re.I)),
    (
        "integration",
        re.compile(
            r"@RestController|@SpringBootApplication|Persistence|spring-boot|/rest/|webhook",
            re.I,
        ),
    ),
)
_EMBABEL_GENERATION = re.compile(r"@Action\b|@EmbabelComponent\b", re.I)
_DRIVINE_GRAPH = re.compile(
    r"loadNearest|loadMatching|VectorIndex|fulltext|full-text|embedding|db\.index\.(?:vector|fulltext)",
    re.I,
)
_DRIVINE_INTEGRATION = re.compile(
    r"\bCREATE\s+(?:INDEX|CONSTRAINT)\b|NodeStamp|@NodeStamp|multi-language|DATABASE_TYPE",
    re.I,
)
_DRIVINE_WRITE = re.compile(r"\b(?:MERGE|DELETE|DETACH|SET|REMOVE)\b|\bCREATE\b(?!\s+(?:INDEX|CONSTRAINT))", re.I)
_DRIVINE_READ = re.compile(r"\b(?:MATCH|OPTIONAL\s+MATCH|RETURN|WITH|UNWIND|CALL|SHOW)\b", re.I)
_CYPHER_TRIPLE = re.compile(
    r"(?P<q>\"\"\"|''')(?P<body>\s*(?:MATCH|OPTIONAL\s+MATCH|CREATE|MERGE|RETURN|WITH|UNWIND|CALL|SHOW)\b.{8,800}?)(?P=q)",
    re.I | re.S,
)
_CYPHER_QUOTED = re.compile(
    r"""(?P<q>["'])(?P<body>\s*(?:MATCH|OPTIONAL\s+MATCH|CREATE|MERGE|RETURN|WITH|UNWIND|CALL|SHOW)\b[^"'\\\n]{8,400})(?P=q)""",
    re.I,
)


def cypher_literals(text: str) -> list[str]:
    """Return Cypher statements embedded in client source."""
    found: list[str] = []
    for pattern in (_CYPHER_TRIPLE, _CYPHER_QUOTED):
        for match in pattern.finditer(text):
            statement = " ".join(match.group("body").split())
            if statement and statement not in found:
                found.append(statement)
    return found


_SECTION_DECL = re.compile(
    r"(?m)^(?P<ann>(?:[ \t]*@[A-Za-z_][\w.]*(?:\([^)\n]*\))?[ \t]*\n)*)"
    r"[ \t]*(?:(?:public|private|protected|internal|open|override|suspend|final|static|abstract|inline|operator|infix|export|async|synchronized)\s+)*"
    r"(?:fun|def|function)\s+(?P<name>`[^`]+`|\w+)"
)
_JAVA_DECL = re.compile(
    r"(?m)^(?P<ann>(?:[ \t]*@[A-Za-z_][\w.]*(?:\([^)\n]*\))?[ \t]*\n)*)"
    r"[ \t]*(?:(?:public|private|protected|static|final|synchronized)\s+)+"
    r"(?:[\w.<>,\[\]?]+\s+)+(?P<name>\w+)\s*\([^;]*\)\s*(?:throws [\w.,\s]+)?\{"
)


_CLASS_FRAME = re.compile(
    r"(?m)^(?P<body>(?:[ \t]*@[A-Za-z_][\w.]*(?:\([^)\n]*\))?[ \t]*\n)*"
    r"[ \t]*(?:(?:public|private|protected|internal|open|abstract|data|sealed|inner)\s+)*"
    r"(?:class|interface|object|enum)\b[^\n{]*)"
)


def _class_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for match in _CLASS_FRAME.finditer(text):
        start = match.start()
        end = _section_end(text, match.end())
        if end <= start:
            end = match.end()
        frame = _type_header(text, match)
        spans.append((start, end, frame))
    return spans


def _type_header(text: str, match: re.Match[str]) -> str:
    """Annotations and the type signature, stopping before the body."""
    limit = min(len(text), match.end() + 800)
    window = text[match.end() : limit]
    brace = window.find("{")
    line_end = text.find("\n", match.end())
    end = match.end()
    if brace != -1 and (line_end == -1 or match.end() + brace <= line_end + 600):
        end = match.end() + brace
    elif line_end != -1 and text[match.end() : line_end].rstrip().endswith(":"):
        end = line_end
    return "\n".join(line.strip() for line in text[match.start() : end].splitlines() if line.strip())


def enclosing_class_frame(text: str, at: int) -> str:
    """The type that contains this offset, signature only."""
    spans = _class_spans(text)
    enclosing = [span for span in spans if span[0] <= at < span[1]]
    if enclosing:
        return max(enclosing, key=lambda span: span[0])[2]
    prior = [span for span in spans if span[0] <= at]
    return prior[-1][2] if prior else ""


def code_sections(path: str, text: str) -> list[tuple[str, str, str, str]]:
    """Split a source file into methods. A file with one declaration stays a class."""
    spans: list[tuple[int, int, str]] = []
    for pattern in (_SECTION_DECL, _JAVA_DECL):
        for match in pattern.finditer(text):
            start = match.start()
            end = _section_end(text, match.end())
            if end <= start:
                continue
            section = text[start:end].strip()
            if len(section) < 40:
                continue
            name = match.group("name").strip("`")
            spans.append((start, end, name))
    spans.sort()
    chosen: list[tuple[str, str, str, str]] = []
    frames = _class_spans(text)
    cursor = -1
    seen_names: dict[str, int] = {}
    for start, end, name in spans:
        if start < cursor:
            continue
        cursor = end
        seen_names[name] = seen_names.get(name, 0) + 1
        label = name if seen_names[name] == 1 else f"{name}-{seen_names[name]}"
        chosen.append((label, text[start:end].strip(), "method", _frame_at(frames, start)))
    if len(chosen) < 2:
        return [(Path(path).name, text, "class", "")]
    return chosen


def _frame_at(spans: list[tuple[int, int, str]], at: int) -> str:
    enclosing = [span for span in spans if span[0] <= at < span[1]]
    if enclosing:
        return max(enclosing, key=lambda span: span[0])[2]
    prior = [span for span in spans if span[0] <= at]
    return prior[-1][2] if prior else ""


def _section_end(text: str, decl_end: int) -> int:
    line_end = text.find("\n", decl_end)
    if line_end == -1:
        line_end = len(text)
    window = text[decl_end : min(len(text), line_end + 400)]
    brace = window.find("{")
    if brace != -1 and brace <= (line_end - decl_end) + 200:
        end = _brace_end(text, decl_end + brace)
        if end:
            return end
    if text[decl_end:line_end].strip().endswith(":"):
        return _indent_end(text, line_end + 1)
    return line_end


def _brace_end(text: str, open_at: int) -> int | None:
    depth = 0
    for index in range(open_at, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _indent_end(text: str, body_at: int) -> int:
    lines = text[body_at:].splitlines(keepends=True)
    if not lines:
        return body_at
    taken = 0
    for line in lines:
        if line.strip() and not line.startswith((" ", "\t")):
            break
        taken += len(line)
    return body_at + taken


def embabel_hits(path: str, text: str) -> list[str]:
    blob = f"{path}\n{text}"
    return [name for name, pattern in _EMBABEL_RULES if pattern.search(blob)]


def drivine_hits(path: str, text: str) -> list[str]:
    if path.replace("\\", "/").endswith("refusals.yaml"):
        return ["repair"]
    blob = f"{path}\n{text}"
    hits: list[str] = []
    if _DRIVINE_GRAPH.search(blob):
        hits.append("graph_rag")
    if _DRIVINE_INTEGRATION.search(blob):
        hits.append("integration")
    if _DRIVINE_WRITE.search(blob):
        hits.append("generation")
    return hits


def label_text(domain: str, path: str, text: str) -> dict[str, object]:
    """Return an area, or a review reason. Does not admit an example."""
    if domain == "embabel":
        hits = embabel_hits(path, text)
        fallback = "generation" if _EMBABEL_GENERATION.search(f"{path}\n{text}") else None
    elif domain == "drivine":
        hits = drivine_hits(path, text)
        fallback = "query" if not hits and _DRIVINE_READ.search(text) else None
    else:
        raise ValueError(f"unknown domain {domain}")
    if len(hits) >= 2:
        return {"reason": "two_matches", "matches": hits}
    if len(hits) == 1:
        return {"area": hits[0], "admitted_example": False}
    if fallback:
        return {"area": fallback, "admitted_example": False}
    return {"reason": "zero_matches", "matches": []}


def balance_sheet(labeled: list[Mapping[str, object]], review: list[Mapping[str, object]], prereg: dict) -> dict[str, object]:
    """Count labeled code against the independently sourced training prefixes."""
    prefixes = [int(size) for size in prereg["statistics"]["example_doses"]["prefixes"]]
    holdout = int(prereg["splits"]["holdout_min_tasks"])
    needed = prefixes[-1]
    rows: dict[str, dict[str, object]] = {}
    total = 0
    for domain, names in areas(prereg).items():
        for name in names:
            members = [row for row in labeled if row.get("domain") == domain and row.get("area") == name]
            count = len(members)
            total += count
            rows[f"{domain}/{name}"] = {
                "domain": domain,
                "area": name,
                "labeled": count,
                "methods": sum(1 for row in members if row.get("grain") == "method"),
                "classes": sum(1 for row in members if row.get("grain") == "class"),
            }
    for row in rows.values():
        count = int(row["labeled"])
        row["share_of_labeled"] = (count / total) if total else 0.0
    return {
        "categories_determined": False,
        "admitted_examples": False,
        "prefixes_locked": True,
        "holdout_min_tasks": holdout,
        "holdout_scope": "combined",
        "prefixes": prefixes,
        "labeled": total,
        "needed_for_plan": needed,
        "short_of_plan": total < needed,
        "review": {
            "total": len(review),
            "zero_matches": sum(1 for row in review if row.get("reason") == "zero_matches"),
            "two_matches": sum(1 for row in review if row.get("reason") == "two_matches"),
        },
        "areas": rows,
    }


def _checkout_file(checkouts: Path, repo: str, source_file: str) -> Path:
    _owner, name = repo.split("/", 1)
    domain = "embabel" if repo.startswith("embabel/") else "drivine"
    return checkouts / domain / name / source_file


def _read_source(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > 1_000_000:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    return load_jsonl(path)


def base_source_file(source_file: str) -> str:
    """Path without method ``#`` suffix (slashes normalized)."""
    return source_file.replace("\\", "/").split("#", 1)[0]


def _unit_identity(row: Mapping[str, object]) -> dict[str, object]:
    """Stable grain, section, or query identity for canonical hashing."""
    base = base_source_file(str(row.get("source_file", "")))
    if row.get("source_kind") == "query":
        unit: dict[str, object] = {"kind": "query", "source_file": base}
        case_name = row.get("case_name")
        if isinstance(case_name, str) and case_name.strip():
            unit["case_name"] = case_name.strip()
        cypher = row.get("cypher")
        if isinstance(cypher, str) and cypher.strip():
            unit["cypher_sha256"] = hashlib.sha256(cypher.encode("utf-8")).hexdigest()
        return unit
    section = row.get("section")
    grain = row.get("grain")
    if isinstance(section, str) and section.strip():
        return {"kind": str(grain or "method"), "source_file": base, "section": section.strip()}
    source_file = str(row.get("source_file", ""))
    if "#" in source_file:
        _, section_name = source_file.split("#", 1)
        return {"kind": str(grain or "method"), "source_file": base, "section": section_name}
    return {"kind": str(grain or "class"), "source_file": base}


def example_id_canonical_payload(row: Mapping[str, object]) -> dict[str, object]:
    """Versioned fields hashed into ``example_id`` (input-order independent)."""
    text_sha = row.get("text_sha256")
    if not isinstance(text_sha, str) or not _HEX64.fullmatch(text_sha):
        raise ValueError("labeled unit missing text_sha256")
    for key in ("domain", "source_repo", "source_pin"):
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"labeled unit missing {key}")
    return {
        "schema_version": _EXAMPLE_ID_SCHEMA_VERSION,
        "domain": str(row["domain"]).strip(),
        "source_repo": str(row["source_repo"]).strip(),
        "source_pin": str(row["source_pin"]).strip(),
        "unit": _unit_identity(row),
        "text_sha256": text_sha,
    }


def compute_example_id(row: Mapping[str, object]) -> str:
    payload = example_id_canonical_payload(row)
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def provenance_groups_for(row: Mapping[str, object]) -> list[str]:
    """Namespaced provenance groups for train/holdout separation (no repository-wide)."""
    pin = str(row["source_pin"]).strip()
    base = base_source_file(str(row.get("source_file", "")))
    groups: list[str] = [f"file:{base}@{pin}"]
    if row.get("source_kind") == "query":
        groups.append(f"fixture:{base}@{pin}")
    frame = row.get("class_frame")
    if isinstance(frame, str) and frame.strip():
        frame_digest = hashlib.sha256(frame.strip().encode("utf-8")).hexdigest()
        groups.append(f"class:{frame_digest}@{pin}")
    seen: set[str] = set()
    unique: list[str] = []
    for group in groups:
        if group not in seen:
            seen.add(group)
            unique.append(group)
    return unique


def _identity_sort_key(row: Mapping[str, object]) -> tuple[str, ...]:
    return (
        str(row.get("domain", "")),
        str(row.get("area", "")),
        str(row.get("source_repo", "")),
        str(row.get("source_file", "")),
        str(row.get("grain", "")),
        str(row.get("section", "")),
        str(row.get("example_id", "")),
    )


def _dedup_exact_code_candidates(
    candidates: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    """Dedup by exact code hash; conflicts on domain/area go to review."""
    raw_count = len(candidates)
    by_code: dict[str, list[dict[str, object]]] = {}
    for item in candidates:
        digest = str(item.get("text_sha256") or item.get("code_sha256") or "")
        if not digest:
            continue
        by_code.setdefault(digest, []).append(item)
    exact_groups = sum(1 for members in by_code.values() if len(members) > 1)
    removed = sum(len(members) - 1 for members in by_code.values() if len(members) > 1)
    labeled: list[dict[str, object]] = []
    review: list[dict[str, object]] = []
    conflicting = 0
    for members in by_code.values():
        sorted_members = sorted(members, key=_identity_sort_key)
        labels = {
            (str(row.get("domain", "")), str(row.get("area", "")))
            for row in members
            if "area" in row
        }
        if len(labels) > 1:
            conflicting += 1
            for row in sorted_members:
                conflict = dict(row)
                conflict["reason"] = "conflicting_label_exact_duplicate"
                conflict["matches"] = sorted(
                    {f"{dom}/{ar}" for dom, ar in labels if dom and ar}
                )
                review.append(conflict)
            continue
        chosen = sorted_members[0]
        decision = {key: chosen[key] for key in ("area", "admitted_example") if key in chosen}
        if "area" in decision:
            labeled.append(chosen)
        else:
            review.append(chosen)
    labeled.sort(key=_identity_sort_key)
    review.sort(key=lambda row: (str(row.get("reason", "")), *_identity_sort_key(row)))
    audit = {
        "raw_candidates": raw_count,
        "exact_code_duplicate_groups": exact_groups,
        "exact_duplicates_removed": removed,
        "conflicting_label_exact_duplicates": conflicting,
        "labeled": len(labeled),
        "review": len(review),
    }
    return labeled, review, audit


def attach_example_identity(item: dict[str, object]) -> dict[str, object]:
    """Add deterministic ``example_id`` and ``provenance_groups``."""
    item["example_id"] = compute_example_id(item)
    item["provenance_groups"] = provenance_groups_for(item)
    return item


def _identity(row: Mapping[str, object]) -> dict[str, object]:
    kept = {
        key: row[key]
        for key in ("domain", "source_kind", "source_repo", "source_file", "source_pin", "text_sha256", "cypher", "case_name")
        if key in row
    }
    return kept


def label_manifest(
    manifest: Path,
    checkouts: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    candidates: list[dict[str, object]] = []
    id_payloads: dict[str, str] = {}
    for name in ("embabel-units.jsonl", "drivine-queries.jsonl", "drivine-units.jsonl"):
        for row in _load_jsonl(manifest / name):
            if row.get("source_kind") == "query" and isinstance(row.get("cypher"), str):
                pieces = [(str(row["source_file"]), str(row["cypher"]), "method", "")]
            else:
                text = _read_source(_checkout_file(checkouts, str(row["source_repo"]), str(row["source_file"])))
                pieces = [
                    (
                        f"{row['source_file']}#{section_name}" if grain == "method" else str(row["source_file"]),
                        section,
                        grain,
                        frame,
                    )
                    for section_name, section, grain, frame in code_sections(str(row["source_file"]), text)
                ]
            for source_file, piece, grain, frame in pieces:
                decision = label_text(str(row["domain"]), source_file, piece)
                item = {**_identity(row), **decision, "source_file": source_file, "grain": grain}
                attach_unit_code_metadata(item, piece)
                if grain == "method" and frame:
                    item["class_frame"] = frame
                if source_file != row["source_file"]:
                    item["section"] = source_file.split("#", 1)[-1]
                attach_example_identity(item)
                payload = json.dumps(
                    example_id_canonical_payload(item),
                    sort_keys=True,
                    separators=(",", ":"),
                )
                example_id = str(item["example_id"])
                prior_payload = id_payloads.get(example_id)
                if prior_payload is not None and prior_payload != payload:
                    raise ValueError(f"example_id collision for {example_id}")
                id_payloads[example_id] = payload
                candidates.append(item)
    labeled, review, audit = _dedup_exact_code_candidates(candidates)
    by_domain_area: dict[str, int] = {}
    for row in labeled:
        key = f"{row['domain']}/{row['area']}"
        by_domain_area[key] = by_domain_area.get(key, 0) + 1
    for row in review:
        if "domain" in row and "area" in row:
            key = f"{row['domain']}/{row['area']}"
            by_domain_area[key] = by_domain_area.get(key, 0) + 1
    audit["by_domain_area"] = dict(sorted(by_domain_area.items()))
    unique_code_hashes = {str(row.get("text_sha256")) for row in labeled if row.get("text_sha256")}
    audit["unique_target_code_hashes"] = len(unique_code_hashes)
    return labeled, review, audit


def write_labels(manifest: Path, checkouts: Path, prereg: dict | None = None) -> dict[str, object]:
    prereg = prereg or load_prereg()
    labeled, review, audit = label_manifest(manifest, checkouts)
    sheet = balance_sheet(labeled, review, prereg)
    sheet["label_audit"] = audit
    write_jsonl(manifest / "labeled.jsonl", labeled)
    write_jsonl(manifest / "methods.jsonl", [row for row in labeled if row.get("grain") == "method"])
    write_jsonl(manifest / "classes.jsonl", [row for row in labeled if row.get("grain") == "class"])
    write_jsonl(manifest / "review.jsonl", review)
    (manifest / "balance.json").write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf-8")
    (manifest / "label-audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sheet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Label collected code into pre-registered areas.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--checkouts", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(write_labels(args.manifest, args.checkouts), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
