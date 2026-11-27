"""Collect, cleanse, and validate raw Embabel and Drivine material.

Embabel units come only from the github.com/embabel organization.
Drivine units are the query language: Cypher spec steps, .cypher files,
the grammar, and query-language docs in the official liberation-data
clients. Category labels are not assigned here. A unit that already
carries an area is refused. The size report compares cleansed counts
with the pre-registered holdout floor and leaves labeling closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable, Mapping

from analysis.practices import areas, load_prereg

EMBABEL_OWNER = "embabel"

DRIVINE_QUERY_REPOS = frozenset(
    {
        "liberation-data/drivine-cypher-spec",
        "liberation-data/drivine",
        "liberation-data/drivine-python",
        "liberation-data/drivine4j",
        "liberation-data/drivine-inspiration",
    }
)

DRIVINE_DIR_TO_REPO = {
    "drivine-cypher-spec": "liberation-data/drivine-cypher-spec",
    "drivine": "liberation-data/drivine",
    "drivine-python": "liberation-data/drivine-python",
    "drivine4j": "liberation-data/drivine4j",
    "drivine-inspiration": "liberation-data/drivine-inspiration",
}

SKIP_DIRS = frozenset(
    {
        ".git",
        ".github",
        ".gradle",
        "node_modules",
        "dist",
        "build",
        "target",
        "out",
        "vendor",
        "generated",
    }
)

BINARY_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".jar",
        ".wasm",
        ".class",
        ".so",
        ".dll",
        ".zip",
        ".gz",
        ".pdf",
        ".mp4",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".bin",
        ".h",
        ".def",
        ".map",
    }
)

CODE_SUFFIXES = frozenset({".java", ".kt", ".kts"})
DRIVINE_CODE_SUFFIXES = frozenset({".java", ".kt", ".kts", ".py", ".ts", ".tsx", ".mts"})
DOC_SUFFIXES = frozenset({".md", ".adoc", ".rst"})
LITERATURE_REPOS = frozenset({"blogs", "publications"})
QUERY_DOC = re.compile(
    r"(cypher|statements|query-dsl|query_dsl|persistence-manager|persistence_manager)",
    re.IGNORECASE,
)
_CYPHER_LINE = re.compile(r"^(\s*)(?:-\s+)?cypher:\s*(.*?)\s*$")
_NAME_LINE = re.compile(r"^(\s*)(?:-\s+)?name:\s*(.*?)\s*$")
_ORACLE_LINE = re.compile(r"^\s+(?:rows|error)\s*:")
_CYPHER_START = re.compile(
    r"(MATCH|OPTIONAL\s+MATCH|RETURN|WITH|CREATE|MERGE|DELETE|DETACH|REMOVE|SET|UNWIND|CALL|SHOW|DROP|FOREACH)\b",
    re.IGNORECASE,
)
_SECRET_TEXT = re.compile(
    r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY|AKIA[0-9A-Z]{16}",
)
MAX_BYTES = 1_000_000
COLLECTED_KINDS = frozenset({"code", "query"})


def cleanse_text(text: str) -> str | None:
    """Return normalized text, or None when the text is empty or secret."""
    if "\0" in text:
        return None
    if _SECRET_TEXT.search(text):
        return None
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized:
        return None
    return normalized


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _unquote(value: str) -> tuple[str, str]:
    if value in {"|", ">", "|-", ">-", "|+", ">+"}:
        return "block", ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        inner = value[1:-1]
        if value[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return "plain", inner
    return "plain", value


def extract_cypher_steps(text: str) -> list[dict[str, object]]:
    """Pull Cypher steps out of a Drivine spec file.

    Each step keeps the statement, the case name, whether the spec gives
    rows or an error, and a fingerprint. The YAML reader is used when it
    can load the file. A line reader covers the same `cases` / `steps` shape
    when YAML is not installed.
    """
    parsed = _steps_from_yaml(text)
    if parsed is not None:
        return parsed
    return _steps_from_lines(text)


def _steps_from_yaml(text: str) -> list[dict[str, object]] | None:
    try:
        import yaml
    except ImportError:
        return None
    try:
        data = yaml.safe_load(text)
    except Exception:
        return None
    if not isinstance(data, dict):
        return []
    steps: list[dict[str, object]] = []
    _walk_cypher(data, "", steps)
    return steps


def _walk_cypher(node: object, case_name: str, steps: list[dict[str, object]]) -> None:
    """Record every Cypher string in a spec document, not only cases/steps."""
    if isinstance(node, list):
        for item in node:
            _walk_cypher(item, case_name, steps)
        return
    if not isinstance(node, dict):
        return
    name = node.get("name") if isinstance(node.get("name"), str) else case_name
    statement = node.get("cypher")
    if not isinstance(statement, str):
        statement = node.get("statement") if isinstance(node.get("statement"), str) else None
        if isinstance(statement, str) and not _CYPHER_START.match(statement.lstrip()):
            statement = None
    if isinstance(statement, str):
        cleansed = cleanse_text(statement)
        if cleansed is not None:
            oracle = "rows" in node or bool(node.get("error")) or "holds" in node or "neo4j" in node
            fingerprint = json.dumps(
                {
                    "anchor": node.get("anchor"),
                    "case": name,
                    "cypher": cleansed,
                    "error": bool(node.get("error")),
                    "holds": node.get("holds"),
                    "parameters": node.get("parameters"),
                    "rows": node.get("rows"),
                },
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )
            steps.append(
                {
                    "cypher": cleansed,
                    "case_name": name,
                    "oracle": oracle,
                    "step_sha256": _sha256(fingerprint),
                }
            )
    for value in node.values():
        _walk_cypher(value, name, steps)


def _steps_from_lines(text: str) -> list[dict[str, object]]:
    lines = text.splitlines()
    steps: list[dict[str, object]] = []
    case_name = ""
    index = 0
    while index < len(lines):
        name_match = _NAME_LINE.match(lines[index])
        cypher_match = _CYPHER_LINE.match(lines[index])
        if name_match and not cypher_match:
            case_name = _unquote(name_match.group(2))[1]
            index += 1
            continue
        if not cypher_match:
            index += 1
            continue
        base = len(cypher_match.group(1))
        mode, statement = _unquote(cypher_match.group(2))
        block: list[str] = []
        step_lines = [lines[index]]
        oracle = False
        index += 1
        if mode == "block":
            while index < len(lines):
                current = lines[index]
                indent = len(current) - len(current.lstrip(" "))
                if current.strip() and indent <= base + 2:
                    break
                step_lines.append(current)
                if current.strip():
                    block.append(current.strip())
                index += 1
            statement = "\n".join(block).strip()
        while index < len(lines):
            current = lines[index]
            if _CYPHER_LINE.match(current):
                break
            if current.strip() and (len(current) - len(current.lstrip(" "))) <= base and current.lstrip().startswith("- "):
                break
            step_lines.append(current)
            if _ORACLE_LINE.match(current):
                oracle = True
            index += 1
        cleansed = cleanse_text(statement)
        if cleansed is None:
            continue
        step_text = "\n".join(step_lines).strip()
        steps.append(
            {
                "cypher": cleansed,
                "case_name": case_name,
                "oracle": oracle,
                "step_sha256": _sha256(step_text),
            }
        )
    return steps


def secret_path(path: str) -> bool:
    name = Path(path).name
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    return name.endswith((".pem", ".key", ".p12", ".pfx"))


def _skipped_path(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return any(part in SKIP_DIRS for part in parts)


def classify_embabel_path(repo: str, path: str) -> str | None:
    """Return a source kind for an Embabel org file, or None to ignore it."""
    if _skipped_path(path) or secret_path(path):
        return None
    owner, _, name = repo.partition("/")
    if owner != EMBABEL_OWNER or not name:
        return None
    suffix = Path(path).suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return None
    if name in LITERATURE_REPOS and suffix in DOC_SUFFIXES:
        return "literature"
    if suffix in DOC_SUFFIXES:
        return "documentation"
    if suffix in CODE_SUFFIXES or suffix == ".cypher":
        return "code"
    return None


def classify_drivine_path(repo: str, path: str) -> str | None:
    """Return the query-language role of a path, or None when it is not one."""
    if repo not in DRIVINE_QUERY_REPOS or _skipped_path(path) or secret_path(path):
        return None
    parts = path.replace("\\", "/").split("/")
    filename = parts[-1]
    lower = filename.lower()
    if lower.endswith((".yaml", ".yml")) and len(parts) == 1 and repo.endswith("drivine-cypher-spec"):
        return "spec_yaml"
    if lower == "cypher.g4":
        return "grammar"
    if lower.endswith(".cypher"):
        return "cypher_file"
    if lower.endswith(".md") and QUERY_DOC.search(path):
        return "query_doc"
    return None


def classify_drivine_corpus(repo: str, path: str) -> str | None:
    """Return code or documentation for an official Drivine client file.

    Query-language paths stay with classify_drivine_path. Other repositories
    are ignored.
    """
    if repo not in DRIVINE_QUERY_REPOS or _skipped_path(path) or secret_path(path):
        return None
    if classify_drivine_path(repo, path) is not None:
        return None
    suffix = Path(path).suffix.lower()
    if suffix in DOC_SUFFIXES:
        return "documentation"
    if suffix in DRIVINE_CODE_SUFFIXES:
        return "code"
    return None


def kept_source_kind(kind: object) -> str | None:
    """Prose is not collected. Code and Cypher statements are."""
    if kind in COLLECTED_KINDS:
        return str(kind)
    return None


def validate_unit(record: Mapping[str, object]) -> list[str]:
    """Return the reasons a cleansed unit is refused. Empty means kept."""
    reasons: list[str] = []
    if "area" in record or "areas" in record:
        reasons.append("area_assigned_too_early")
    repo = record.get("source_repo")
    path = record.get("source_file")
    pin = record.get("source_pin")
    domain = record.get("domain")
    if not isinstance(repo, str) or "/" not in repo:
        reasons.append("wrong_owner")
    if not isinstance(path, str) or not path.strip():
        reasons.append("missing_source_file")
    if not isinstance(pin, str) or not pin.strip():
        reasons.append("missing_pin")
    if domain == "embabel":
        if not isinstance(repo, str) or not repo.startswith(f"{EMBABEL_OWNER}/"):
            reasons.append("not_embabel_org")
        kind = record.get("source_kind")
        if kind not in {"code", "documentation", "literature"}:
            reasons.append("unknown_source_kind")
    elif domain == "drivine":
        if not isinstance(repo, str) or repo not in DRIVINE_QUERY_REPOS:
            reasons.append("not_query_language")
        kind = record.get("source_kind")
        if kind not in {"query", "query_doc", "code", "documentation"}:
            reasons.append("not_query_language")
        if kind == "query" and record.get("executable_oracle") is not True:
            reasons.append("missing_query_oracle")
    else:
        reasons.append("unknown_domain")
    if record.get("secret") is True:
        reasons.append("secret")
    if record.get("empty") is True:
        reasons.append("empty")
    if record.get("duplicate") is True:
        reasons.append("duplicate")
    if record.get("binary_or_generated") is True:
        reasons.append("binary_or_generated")
    return reasons


def size_report(collected: Mapping[str, int], prereg: dict) -> dict[str, object]:
    """Compare code-unit counts with the largest independently trained prefix."""
    doses = prereg["statistics"]["example_doses"]
    prefixes = [int(size) for size in doses["prefixes"]]
    holdout = int(prereg["splits"]["holdout_min_tasks"])
    largest = prefixes[-1]
    needed = largest
    domains: dict[str, dict[str, object]] = {}
    total = 0
    for domain, names in areas(prereg).items():
        count = int(collected.get(domain, 0))
        total += count
        domains[domain] = {
            "areas": list(names),
            "area_count": len(names),
            "collected_units": count,
        }
    return {
        "categories_determined": False,
        "labeling_allowed": False,
        "code_only": True,
        "holdout_min_tasks": holdout,
        "holdout_scope": prereg["splits"]["holdout_min_tasks_scope"],
        "prefixes": prefixes,
        "training_examples_at_largest_prefix": largest,
        "labeled_units_needed_for_plan": needed,
        "collected_units": total,
        "shortfall": max(0, needed - total),
        "covers_plan": total >= needed,
        "unit_note": (
            "Only code is collected for training. The independently authored "
            "742-task confirmatory exam is kept disjoint from the training prefixes. "
            "A collected unit is not an authored holdout task and not an admitted example."
        ),
        "domains": domains,
    }


def _read_text(path: Path) -> str | None:
    if path.stat().st_size > MAX_BYTES:
        return None
    data = path.read_bytes()
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def _git_pin(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not _skipped_path(str(path.relative_to(root))):
            yield path


def scan_checkouts(checkouts: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Scan local clones. Returns accepted units and refused units."""
    accepted: list[dict[str, object]] = []
    refused: list[dict[str, object]] = []
    seen: set[str] = set()
    embabel_root = checkouts / "embabel"
    drivine_root = checkouts / "drivine"
    if embabel_root.is_dir():
        for repo_dir in sorted(p for p in embabel_root.iterdir() if p.is_dir()):
            repo = f"{EMBABEL_OWNER}/{repo_dir.name}"
            pin = _git_pin(repo_dir)
            for path in _iter_files(repo_dir):
                relative = str(path.relative_to(repo_dir))
                if secret_path(relative):
                    refused.append(_secret_record("embabel", repo, relative, pin))
                    continue
                kind = classify_embabel_path(repo, relative)
                if kept_source_kind(kind) is None:
                    continue
                text = _read_text(path)
                record = _file_record("embabel", repo, relative, pin, "code", text)
                _keep(record, seen, accepted, refused)
    if drivine_root.is_dir():
        for repo_dir in sorted(p for p in drivine_root.iterdir() if p.is_dir()):
            repo = DRIVINE_DIR_TO_REPO.get(repo_dir.name, "")
            pin = _git_pin(repo_dir)
            for path in _iter_files(repo_dir):
                relative = str(path.relative_to(repo_dir))
                if secret_path(relative):
                    refused.append(_secret_record("drivine", repo, relative, pin))
                    continue
                role = classify_drivine_path(repo, relative)
                if role == "spec_yaml":
                    text = _read_text(path)
                    if text is None:
                        refused.append(
                            {
                                "domain": "drivine",
                                "source_repo": repo,
                                "source_file": relative,
                                "source_pin": pin,
                                "reasons": ["empty"],
                            }
                        )
                        continue
                    for step in extract_cypher_steps(text):
                        record = {
                            "domain": "drivine",
                            "source_kind": "query",
                            "source_repo": repo,
                            "source_file": relative,
                            "source_pin": pin,
                            "case_name": step["case_name"],
                            "cypher": step["cypher"],
                            "executable_oracle": step["oracle"] is True,
                            "text_sha256": step["step_sha256"],
                        }
                        _keep(record, seen, accepted, refused)
                    continue
                if role in {"grammar", "cypher_file"}:
                    text = _read_text(path)
                    record = _file_record("drivine", repo, relative, pin, "code", text)
                    record["query_surface"] = role
                    if role == "cypher_file" and text is not None:
                        record["cypher"] = cleanse_text(text) or ""
                    _keep(record, seen, accepted, refused)
                    continue
                kind = classify_drivine_corpus(repo, relative)
                if kept_source_kind(kind) is None:
                    continue
                text = _read_text(path)
                record = _file_record("drivine", repo, relative, pin, "code", text)
                _keep(record, seen, accepted, refused)
    return accepted, refused


def _secret_record(domain: str, repo: str, relative: str, pin: str) -> dict[str, object]:
    record = {
        "domain": domain,
        "source_repo": repo,
        "source_file": relative,
        "source_pin": pin,
        "secret": True,
        "source_kind": "query" if domain == "drivine" else "code",
    }
    record["reasons"] = validate_unit(record)
    return record


def _file_record(
    domain: str,
    repo: str,
    relative: str,
    pin: str,
    kind: str,
    text: str | None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "domain": domain,
        "source_kind": kind,
        "source_repo": repo,
        "source_file": relative,
        "source_pin": pin,
    }
    if text is None:
        record["empty"] = True
        return record
    cleansed = cleanse_text(text)
    if cleansed is None:
        if text and _SECRET_TEXT.search(text):
            record["secret"] = True
        else:
            record["empty"] = True
        return record
    record["bytes"] = len(cleansed.encode("utf-8"))
    record["text_sha256"] = _sha256(cleansed)
    return record


def _keep(
    record: dict[str, object],
    seen: set[str],
    accepted: list[dict[str, object]],
    refused: list[dict[str, object]],
) -> None:
    digest = record.get("text_sha256")
    fingerprint = f"{record.get('domain')}:{digest}" if isinstance(digest, str) else ""
    if fingerprint and fingerprint in seen:
        record["duplicate"] = True
    reasons = validate_unit(record)
    if reasons:
        refused.append({**record, "reasons": reasons})
        return
    if fingerprint:
        seen.add(fingerprint)
    accepted.append(record)


def split_withheld(refused: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Cypher with no expected result is kept, and it does not count toward the floor."""
    withheld: list[dict[str, object]] = []
    rejected: list[dict[str, object]] = []
    for row in refused:
        if row.get("reasons") == ["missing_query_oracle"]:
            withheld.append(row)
        else:
            rejected.append(row)
    return withheld, rejected


def write_pool(checkouts: Path, out_dir: Path, prereg: dict | None = None) -> dict[str, object]:
    """Write JSONL indexes and the size report. Source trees stay in the checkouts."""
    accepted, refused = scan_checkouts(checkouts)
    withheld, refused = split_withheld(refused)
    out_dir.mkdir(parents=True, exist_ok=True)
    groups = {
        "embabel-units.jsonl": [row for row in accepted if row["domain"] == "embabel"],
        "drivine-queries.jsonl": [
            row for row in accepted if row["domain"] == "drivine" and row["source_kind"] == "query"
        ],
        "drivine-cypher-without-oracle.jsonl": withheld,
        "drivine-units.jsonl": [
            row for row in accepted if row["domain"] == "drivine" and row["source_kind"] == "code"
        ],
        "refused.jsonl": refused,
    }
    stale = out_dir / "drivine-query-docs.jsonl"
    if stale.exists():
        stale.unlink()
    for name, rows in groups.items():
        _write_jsonl(out_dir / name, rows)
    prereg = prereg or load_prereg()
    report = size_report(
        {
            "embabel": len(groups["embabel-units.jsonl"]),
            "drivine": len(groups["drivine-queries.jsonl"]),
        },
        prereg,
    )
    report["files"] = {name: len(rows) for name, rows in groups.items()}
    report["allowed_sources"] = {
        "embabel": "github.com/embabel/*",
        "drivine": sorted(DRIVINE_QUERY_REPOS),
    }
    (out_dir / "size-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cleanse and validate the raw Embabel and Drivine pools.")
    parser.add_argument("--checkouts", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    report = write_pool(args.checkouts, args.out)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
