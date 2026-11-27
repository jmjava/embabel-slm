"""Run pin-checked snippet checkers and emit evidence only for real exits of 0.

Python snippets are checked with the stdlib parser. Cypher snippets are compiled to
SQLite SQL by the ``drivine-cypher-compiler`` wheel declared by the pinned
``drivine-python`` package. A snippet that does not appear in its pinned source
file is not checked. This does not seal a study and does not treat a parse or
compile as a passing test suite.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Mapping, Sequence

from analysis.evidence_runner import run_fixed_argv, verify_git_pin
from analysis.hashes import sha256_file, sha256_text

_HEX64 = __import__("re").compile(r"^[a-f0-9]{64}$")


def resolve_checkout(checkouts: Path, repo: str) -> Path:
    org, name = repo.split("/", 1)
    folder = "embabel" if org == "embabel" else "drivine"
    candidate = checkouts / folder / name
    if not (candidate / ".git").is_dir():
        raise FileNotFoundError(f"no checkout for {repo} at {candidate}")
    return candidate


def source_file_path(checkout: Path, source_file: str) -> Path:
    relative = source_file.split("#", 1)[0]
    return checkout / relative


def snippet_in_source(checkout: Path, source_file: str, code: str) -> bool:
    path = source_file_path(checkout, source_file)
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    return code.replace("\r\n", "\n") in text


def write_work_manifest(workdir: Path, rows: Sequence[Mapping[str, str]]) -> None:
    snippet_dir = workdir / "snippets"
    snippet_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for row in rows:
        example_id = row["example_id"]
        code = row["code"]
        path = snippet_dir / f"{example_id}.txt"
        path.write_text(code, encoding="utf-8")
        digest = sha256_file(path)
        if digest != row["code_sha256"]:
            raise ValueError(f"snippet bytes do not match code_sha256 for {example_id}")
        manifest.append(
            {
                "example_id": example_id,
                "code_sha256": digest,
                "path": str(path),
            }
        )
    (workdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _load_manifest(workdir: Path) -> list[dict[str, str]]:
    payload = json.loads((workdir / "manifest.json").read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("manifest must be a list")
    return payload


def check_python_snippets(workdir: Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for item in _load_manifest(workdir):
        path = Path(item["path"])
        digest = sha256_file(path)
        if digest != item["code_sha256"]:
            raise ValueError(f"hash mismatch for {item['example_id']}")
        code = path.read_text(encoding="utf-8")
        try:
            ast.parse(code)
        except SyntaxError as exc:
            results.append(
                {
                    "example_id": item["example_id"],
                    "code_sha256": digest,
                    "ok": False,
                    "detail": f"SyntaxError: {exc.msg}",
                }
            )
        else:
            results.append(
                {
                    "example_id": item["example_id"],
                    "code_sha256": digest,
                    "ok": True,
                    "detail": "ast.parse",
                }
            )
    return results


def check_cypher_snippets(workdir: Path) -> list[dict[str, object]]:
    import drivine_cypher_compiler

    results: list[dict[str, object]] = []
    for item in _load_manifest(workdir):
        path = Path(item["path"])
        digest = sha256_file(path)
        if digest != item["code_sha256"]:
            raise ValueError(f"hash mismatch for {item['example_id']}")
        cypher = path.read_text(encoding="utf-8")
        request = json.dumps(
            {
                "store": "sqlite",
                "graph": {"name": "oracle_check"},
                "cypher": cypher,
                "parameters": {},
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        answer = json.loads(drivine_cypher_compiler.compile(request))
        if isinstance(answer, dict) and isinstance(answer.get("sql"), str) and "refusal" not in answer and "error" not in answer:
            results.append(
                {
                    "example_id": item["example_id"],
                    "code_sha256": digest,
                    "ok": True,
                    "detail": "compiled_to_sqlite_sql",
                }
            )
        else:
            detail = ""
            if isinstance(answer, dict):
                detail = str(answer.get("refusal") or answer.get("error") or "compile_refused")
            results.append(
                {
                    "example_id": item["example_id"],
                    "code_sha256": digest,
                    "ok": False,
                    "detail": detail[:500],
                }
            )
    return results


def write_check_result(workdir: Path, results: list[dict[str, object]]) -> None:
    result_path = workdir / "results.jsonl"
    lines = [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in results]
    text = ("\n".join(lines) + ("\n" if lines else ""))
    result_path.write_text(text, encoding="utf-8")
    summary = {
        "checked": len(results),
        "passed": sum(1 for row in results if row.get("ok") is True),
        "results_sha256": sha256_text(text),
    }
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))


def evidence_record_from_check(
    *,
    evidence_id: str,
    source_repo: str,
    source_pin: str,
    oracle_kind: str,
    argv: Sequence[str],
    run_meta: Mapping[str, object],
    results: Sequence[Mapping[str, object]],
) -> dict[str, object] | None:
    if int(run_meta["exit_code"]) != 0:
        return None
    covered = [
        {"example_id": str(row["example_id"]), "code_sha256": str(row["code_sha256"])}
        for row in results
        if row.get("ok") is True
        and isinstance(row.get("example_id"), str)
        and _HEX64.fullmatch(str(row["example_id"]))
        and isinstance(row.get("code_sha256"), str)
        and _HEX64.fullmatch(str(row["code_sha256"]))
    ]
    if not covered:
        return None
    return {
        "evidence_id": evidence_id,
        "source_repo": source_repo,
        "source_pin": source_pin,
        "oracle_kind": oracle_kind,
        "command_argv": list(argv),
        "command_sha256": str(run_meta["command_sha256"]),
        "output_sha256": str(run_meta["output_sha256"]),
        "artifact_sha256": str(run_meta["artifact_sha256"]),
        "exit_code": 0,
        "covered_examples": covered,
    }


def _code_of(row: Mapping[str, object]) -> str | None:
    code = row.get("code")
    if isinstance(code, str) and code.strip():
        return code
    cypher = row.get("cypher")
    if isinstance(cypher, str) and cypher.strip():
        return cypher
    return None


def emit_language(
    *,
    language: str,
    labeled_path: Path,
    checkouts: Path,
    work_root: Path,
    python_executable: str,
    limit: int | None = None,
) -> dict[str, object]:
    if language not in {"python", "cypher"}:
        raise ValueError("language must be python or cypher")
    oracle_kind = "parser" if language == "python" else "compiler"
    mode = "check-python" if language == "python" else "check-cypher"
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    skipped = {"not_in_source": 0, "missing_code": 0, "hash_mismatch": 0}
    considered = 0
    from analysis.jsonl_io import load_jsonl

    for row in load_jsonl(labeled_path):
        if row.get("language") != language:
            continue
        if limit is not None and considered >= limit:
            break
        considered += 1
        repo = row.get("source_repo")
        pin = row.get("source_pin")
        source_file = row.get("source_file")
        example_id = row.get("example_id")
        code_hash = row.get("code_sha256")
        code = _code_of(row)
        if not all(isinstance(value, str) and value for value in (repo, pin, source_file, example_id, code_hash, code)):
            skipped["missing_code"] += 1
            continue
        if sha256_text(str(code)) != code_hash:
            skipped["hash_mismatch"] += 1
            continue
        checkout = resolve_checkout(checkouts, str(repo))
        verify_git_pin(checkout, str(pin))
        if not snippet_in_source(checkout, str(source_file), str(code)):
            skipped["not_in_source"] += 1
            continue
        grouped.setdefault((str(repo), str(pin)), []).append(
            {"example_id": str(example_id), "code_sha256": str(code_hash), "code": str(code)}
        )

    evidence: list[dict[str, object]] = []
    groups: list[dict[str, object]] = []
    for (repo, pin), rows in sorted(grouped.items()):
        workdir = work_root / language / repo.replace("/", "__")
        if workdir.exists():
            for child in workdir.iterdir():
                if child.is_file():
                    child.unlink()
        write_work_manifest(workdir, rows)
        argv = [python_executable, "-m", "analysis.snippet_oracle", mode, str(workdir)]
        run_meta = run_fixed_argv(argv, cwd=Path(__file__).resolve().parents[1], timeout=900)
        result_path = workdir / "results.jsonl"
        passed = 0
        results_hash = ""
        verified = False
        if int(run_meta["exit_code"]) == 0 and result_path.is_file():
            result_text = result_path.read_text(encoding="utf-8")
            results_hash = sha256_text(result_text)
            try:
                reported = json.loads(str(run_meta["stdout_text"]).strip())
            except json.JSONDecodeError:
                reported = {}
            if reported.get("results_sha256") == results_hash:
                verified = True
                parsed_results = [json.loads(line) for line in result_text.splitlines() if line.strip()]
                record = evidence_record_from_check(
                    evidence_id=f"{oracle_kind}-{language}-{repo.replace('/', '__')}-{pin[:12]}",
                    source_repo=repo,
                    source_pin=pin,
                    oracle_kind=oracle_kind,
                    argv=argv,
                    run_meta=run_meta,
                    results=parsed_results,
                )
                if record is not None:
                    evidence.append(record)
                    passed = len(record["covered_examples"])
        groups.append(
            {
                "source_repo": repo,
                "source_pin": pin,
                "candidates": len(rows),
                "exit_code": run_meta["exit_code"],
                "results_verified": verified,
                "results_sha256": results_hash,
                "passed": passed,
            }
        )
    return {
        "language": language,
        "oracle_kind": oracle_kind,
        "considered": considered,
        "skipped": skipped,
        "groups": groups,
        "evidence_rows": len(evidence),
        "passed": sum(len(row["covered_examples"]) for row in evidence),
        "evidence": evidence,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run snippet oracles and emit evidence for successes.")
    sub = parser.add_subparsers(dest="command", required=True)
    check_python = sub.add_parser("check-python")
    check_python.add_argument("workdir", type=Path)
    check_cypher = sub.add_parser("check-cypher")
    check_cypher.add_argument("workdir", type=Path)
    emit = sub.add_parser("emit")
    emit.add_argument("--language", required=True, choices=("python", "cypher"))
    emit.add_argument("--labeled", type=Path, required=True)
    emit.add_argument("--checkouts", type=Path, required=True)
    emit.add_argument("--workdir", type=Path, required=True)
    emit.add_argument("--evidence-out", type=Path, required=True)
    emit.add_argument("--summary-out", type=Path, required=True)
    emit.add_argument("--python", default=sys.executable)
    emit.add_argument("--limit", type=int, default=None)
    args = parser.parse_args(argv)
    if args.command == "check-python":
        write_check_result(args.workdir, check_python_snippets(args.workdir))
        return 0
    if args.command == "check-cypher":
        write_check_result(args.workdir, check_cypher_snippets(args.workdir))
        return 0
    summary = emit_language(
        language=args.language,
        labeled_path=args.labeled,
        checkouts=args.checkouts,
        work_root=args.workdir,
        python_executable=args.python,
        limit=args.limit,
    )
    evidence = summary.pop("evidence")
    from analysis.jsonl_io import write_canonical_jsonl

    args.evidence_out.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_jsonl(args.evidence_out, evidence, id_key="evidence_id")
    args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: summary[key] for key in ("language", "oracle_kind", "considered", "passed", "skipped")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
