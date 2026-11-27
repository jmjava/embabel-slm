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
import subprocess
from pathlib import Path
from typing import Mapping

from analysis.practices import areas, load_prereg

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
    """Count labeled code against the combined holdout and the six prefixes."""
    prefixes = [int(size) for size in prereg["statistics"]["example_doses"]["prefixes"]]
    holdout = int(prereg["splits"]["holdout_min_tasks"])
    needed = holdout + prefixes[-1]
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


def _git_pin(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _read_source(path: Path) -> str:
    if not path.is_file() or path.stat().st_size > 1_000_000:
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _load_jsonl(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _identity(row: Mapping[str, object]) -> dict[str, object]:
    kept = {
        key: row[key]
        for key in ("domain", "source_kind", "source_repo", "source_file", "source_pin", "text_sha256", "cypher", "case_name")
        if key in row
    }
    return kept


def label_manifest(manifest: Path, checkouts: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    labeled: list[dict[str, object]] = []
    review: list[dict[str, object]] = []
    seen: set[str] = set()
    for name in ("embabel-units.jsonl", "drivine-queries.jsonl", "drivine-units.jsonl"):
        for row in _load_jsonl(manifest / name):
            if row.get("source_kind") == "query" and isinstance(row.get("cypher"), str):
                pieces = [(str(row["source_file"]), str(row["cypher"]), "method", "")]
            else:
                text = _read_source(_checkout_file(checkouts, str(row["source_repo"]), str(row["source_file"])))
                pieces = [
                    (
                        f"{row['source_file']}#{name}" if grain == "method" else str(row["source_file"]),
                        section,
                        grain,
                        frame,
                    )
                    for name, section, grain, frame in code_sections(str(row["source_file"]), text)
                ]
            for source_file, piece, grain, frame in pieces:
                decision = label_text(str(row["domain"]), source_file, piece)
                item = {**_identity(row), **decision, "source_file": source_file, "grain": grain}
                if grain == "method" and frame:
                    item["class_frame"] = frame
                if source_file != row["source_file"]:
                    item["text_sha256"] = hashlib.sha256(piece.encode("utf-8")).hexdigest()
                    item["section"] = source_file.split("#", 1)[-1]
                digest = str(item.get("text_sha256") or "")
                if digest and digest in seen:
                    continue
                if digest:
                    seen.add(digest)
                if "area" in decision:
                    labeled.append(item)
                else:
                    review.append(item)
    return labeled, review


def mine_short_areas(
    checkouts: Path,
    labeled: list[dict[str, object]],
    review: list[dict[str, object]],
    prereg: dict,
) -> list[dict[str, object]]:
    """The combined ladder does not top an area up to its own 742-task exam."""
    del checkouts, labeled, review, prereg
    return []


def write_labels(manifest: Path, checkouts: Path, prereg: dict | None = None) -> dict[str, object]:
    prereg = prereg or load_prereg()
    labeled, review = label_manifest(manifest, checkouts)
    labeled.extend(mine_short_areas(checkouts, labeled, review, prereg))
    sheet = balance_sheet(labeled, review, prereg)
    _write_jsonl(manifest / "labeled.jsonl", labeled)
    _write_jsonl(manifest / "methods.jsonl", [row for row in labeled if row.get("grain") == "method"])
    _write_jsonl(manifest / "classes.jsonl", [row for row in labeled if row.get("grain") == "class"])
    _write_jsonl(manifest / "review.jsonl", review)
    (manifest / "balance.json").write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf-8")
    return sheet


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Label collected code into pre-registered areas.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--checkouts", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(write_labels(args.manifest, args.checkouts), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
