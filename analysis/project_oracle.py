"""Admit snippets only when the pinned project's own compile command exits 0.

A snippet counts only when its source path is under a compiled source root and
its text is in that file. A failed build covers nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping, Sequence

from analysis.evidence_runner import run_fixed_argv, verify_git_pin
from analysis.hashes import sha256_text
from analysis.snippet_oracle import _code_of, evidence_record_from_check, resolve_checkout, snippet_in_source

_COMPILED_SUFFIXES = frozenset({".kt", ".java", ".ts", ".tsx"})


def path_under_source_root(source_file: str, roots: Sequence[str]) -> bool:
    relative = source_file.split("#", 1)[0].replace("\\", "/")
    suffix = Path(relative).suffix
    if suffix not in _COMPILED_SUFFIXES:
        return False
    for root in roots:
        normalized = root.strip("/").replace("\\", "/")
        if relative == normalized or relative.startswith(normalized + "/"):
            return True
    return False


def covered_by_successful_build(
    rows: Sequence[Mapping[str, object]],
    checkout: Path,
    roots: Sequence[str],
) -> list[dict[str, str]]:
    covered: list[dict[str, str]] = []
    for row in rows:
        source_file = row.get("source_file")
        example_id = row.get("example_id")
        code_hash = row.get("code_sha256")
        code = _code_of(row)
        if not all(isinstance(value, str) and value for value in (source_file, example_id, code_hash, code)):
            continue
        if sha256_text(str(code)) != code_hash:
            continue
        if not path_under_source_root(str(source_file), roots):
            continue
        if not snippet_in_source(checkout, str(source_file), str(code)):
            continue
        covered.append({"example_id": str(example_id), "code_sha256": str(code_hash)})
    return covered


def run_project_compile(
    *,
    repo: str,
    checkout: Path,
    pin: str,
    labeled_rows: Sequence[Mapping[str, object]],
    roots: Sequence[str],
    argv: Sequence[str],
    timeout: int,
    command_cwd: Path | None = None,
) -> dict[str, object]:
    verify_git_pin(checkout, pin)
    checkout_resolved = checkout.resolve()
    workdir = (command_cwd or checkout).resolve()
    workdir.relative_to(checkout_resolved)
    run_meta = run_fixed_argv(argv, cwd=workdir, timeout=timeout)
    repo_rows = [row for row in labeled_rows if row.get("source_repo") == repo and row.get("source_pin") == pin]
    covered: list[dict[str, str]] = []
    record = None
    if int(run_meta["exit_code"]) == 0:
        covered = covered_by_successful_build(repo_rows, checkout, roots)
        if covered:
            record = evidence_record_from_check(
                evidence_id=f"compiler-project-{repo.replace('/', '__')}-{pin[:12]}",
                source_repo=repo,
                source_pin=pin,
                oracle_kind="compiler",
                argv=argv,
                run_meta=run_meta,
                results=[{"example_id": item["example_id"], "code_sha256": item["code_sha256"], "ok": True} for item in covered],
            )
    return {
        "source_repo": repo,
        "source_pin": pin,
        "exit_code": run_meta["exit_code"],
        "candidates": len(repo_rows),
        "passed": 0 if record is None else len(record["covered_examples"]),
        "evidence": record,
        "stdout_tail": str(run_meta.get("stdout_text", ""))[-1500:],
        "stderr_tail": str(run_meta.get("stderr_text", ""))[-2500:],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile a pinned checkout and emit evidence for its snippets.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--checkouts", type=Path, required=True)
    parser.add_argument("--labeled", type=Path, required=True)
    parser.add_argument("--evidence-out", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    parser.add_argument("--source-root", action="append", required=True)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--command-cwd", default=".", help="directory under the checkout where the compile command runs")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("usage: project_oracle ... --source-root REL -- ./gradlew compileKotlin", file=sys.stderr)
        return 2
    from analysis.jsonl_io import load_jsonl, write_canonical_jsonl

    labeled = load_jsonl(args.labeled)
    pin = ""
    for row in labeled:
        if row.get("source_repo") == args.repo and isinstance(row.get("source_pin"), str):
            pin = str(row["source_pin"])
            break
    if not pin:
        print(f"no labeled pin for {args.repo}", file=sys.stderr)
        return 1
    checkout = resolve_checkout(args.checkouts, args.repo)
    summary = run_project_compile(
        repo=args.repo,
        checkout=checkout,
        pin=pin,
        labeled_rows=labeled,
        roots=args.source_root,
        argv=command,
        timeout=args.timeout,
        command_cwd=(checkout / args.command_cwd).resolve(),
    )
    evidence = summary.pop("evidence")
    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_jsonl(args.evidence_out, [evidence] if evidence else [], id_key="evidence_id")
    args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("source_repo", "exit_code", "candidates", "passed")}))
    return 0 if summary["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
