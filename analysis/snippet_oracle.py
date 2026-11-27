"""Run pin-checked snippet checkers and emit evidence only for real exits of 0.

Python snippets are checked with the stdlib parser. Cypher snippets are compiled to SQL by the ``drivine-cypher-compiler`` wheel
declared by the pinned ``drivine-python`` package. A pinned YAML step's own
parameter values are tried before a text binding of each ``$name``. A snippet that does not appear in its pinned source
file is not checked. This does not seal a study and does not treat a parse or
compile as a passing test suite.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Mapping, Sequence

from analysis.evidence_runner import run_fixed_argv, verify_git_pin
from analysis.hashes import sha256_file, sha256_text

_HEX64 = re.compile(r"^[a-f0-9]{64}$")
_CYPHER_PARAM = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_CYPHER_STORES = ("sqlite", "postgres", "oracle")


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
        entry = {
            "example_id": example_id,
            "code_sha256": digest,
            "path": str(path),
        }
        source_path = row.get("source_path")
        if isinstance(source_path, str) and source_path:
            entry["source_path"] = source_path
        manifest.append(entry)
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


def cypher_parameters(cypher: str) -> dict[str, str]:
    """Bind each `$name` in the statement to text so the compiler can type it."""
    return {name: "x" for name in _CYPHER_PARAM.findall(cypher)}


def json_parameters(raw: Mapping[str, object]) -> dict[str, object] | None:
    """Keep a parameter map only when it is plain JSON."""
    try:
        encoded = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
    except TypeError:
        return None
    parsed = json.loads(encoded)
    if not isinstance(parsed, dict) or not all(isinstance(key, str) for key in parsed):
        return None
    return parsed


def cypher_text_in_document(document: object, cypher: str) -> bool:
    """True when a pinned YAML step's Cypher value is this statement.

    Block scalars are not raw substrings of the file. The parsed step value is
    the statement the corpus recorded.
    """
    wanted = cypher.replace("\r\n", "\n").strip()

    def walk(node: object) -> bool:
        if isinstance(node, dict):
            text = node.get("cypher")
            if isinstance(text, str) and text.replace("\r\n", "\n").strip() == wanted:
                return True
            return any(walk(value) for value in node.values())
        if isinstance(node, list):
            return any(walk(value) for value in node)
        return False

    return walk(document)


def recorded_cypher_parameters(document: object, cypher: str) -> list[dict[str, object]]:
    """Return parameter maps on pinned YAML steps whose Cypher text matches."""
    wanted = cypher.replace("\r\n", "\n").strip()
    found: list[dict[str, object]] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            text = node.get("cypher")
            if isinstance(text, str) and text.replace("\r\n", "\n").strip() == wanted:
                params = node.get("parameters")
                if params is None:
                    found.append({})
                elif isinstance(params, dict):
                    clean = json_parameters(params)
                    if clean is not None:
                        found.append(clean)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(document)
    return found


def cypher_compiles(
    cypher: str,
    compile_request,
    parameter_sets: Sequence[Mapping[str, object]] = (),
) -> str | None:
    """Return the store name when one Drivine SQL backend accepts the statement."""
    candidates: list[Mapping[str, object]] = []
    for parameters in (*parameter_sets, cypher_parameters(cypher)):
        if parameters not in candidates:
            candidates.append(parameters)
    for parameters in candidates:
        for store in _CYPHER_STORES:
            request = json.dumps(
                {
                    "store": store,
                    "graph": {"name": "oracle_check"},
                    "cypher": cypher,
                    "parameters": parameters,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
            answer = json.loads(compile_request(request))
            if (
                isinstance(answer, dict)
                and isinstance(answer.get("sql"), str)
                and "refusal" not in answer
                and "error" not in answer
            ):
                return store
    return None


def check_python_files(workdir: Path) -> list[dict[str, object]]:
    """Parse the pinned source file and keep snippets that are text in that file."""
    results: list[dict[str, object]] = []
    parsed: dict[str, bool] = {}
    for item in _load_manifest(workdir):
        path = Path(item["path"])
        digest = sha256_file(path)
        if digest != item["code_sha256"]:
            raise ValueError(f"hash mismatch for {item['example_id']}")
        source_path = Path(item["source_path"])
        snippet = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        source = source_path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
        key = str(source_path)
        if key not in parsed:
            try:
                ast.parse(source)
            except SyntaxError:
                parsed[key] = False
            else:
                parsed[key] = True
        ok = parsed[key] and snippet in source
        results.append(
            {
                "example_id": item["example_id"],
                "code_sha256": digest,
                "ok": ok,
                "detail": "source_file_ast.parse" if ok else "source_file_rejected",
            }
        )
    return results


_YAML_DOCUMENTS: dict[str, object] = {}


def _cypher_yaml_contains(checkout: Path, source_file: str, code: str) -> bool:
    path = source_file_path(checkout, source_file)
    if path.suffix not in {".yaml", ".yml"} or not path.is_file():
        return False
    key = str(path)
    if key not in _YAML_DOCUMENTS:
        import yaml

        _YAML_DOCUMENTS[key] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return cypher_text_in_document(_YAML_DOCUMENTS[key], code)


def _yaml_parameter_sets(source_path: str, cypher: str, cache: dict[str, object]) -> list[dict[str, object]]:
    if not source_path.endswith((".yaml", ".yml")):
        return []
    if source_path not in cache:
        import yaml

        cache[source_path] = yaml.safe_load(Path(source_path).read_text(encoding="utf-8"))
    return recorded_cypher_parameters(cache[source_path], cypher)


def check_cypher_snippets(workdir: Path) -> list[dict[str, object]]:
    import drivine_cypher_compiler

    documents: dict[str, object] = {}
    results: list[dict[str, object]] = []
    for item in _load_manifest(workdir):
        path = Path(item["path"])
        digest = sha256_file(path)
        if digest != item["code_sha256"]:
            raise ValueError(f"hash mismatch for {item['example_id']}")
        cypher = path.read_text(encoding="utf-8")
        source_path = item.get("source_path")
        parameter_sets = (
            _yaml_parameter_sets(source_path, cypher, documents)
            if isinstance(source_path, str)
            else []
        )
        store = cypher_compiles(cypher, drivine_cypher_compiler.compile, parameter_sets)
        if store is not None:
            results.append(
                {
                    "example_id": item["example_id"],
                    "code_sha256": digest,
                    "ok": True,
                    "detail": f"compiled_to_{store}_sql",
                }
            )
        else:
            results.append(
                {
                    "example_id": item["example_id"],
                    "code_sha256": digest,
                    "ok": False,
                    "detail": "compile_refused",
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


def checker_argv(
    language: str,
    workdir: Path,
    *,
    python_executable: str,
    node_executable: str = "node",
    typescript_package: str = "",
) -> list[str]:
    if language in {"python", "python-file"}:
        mode = "check-python" if language == "python" else "check-python-file"
        return [python_executable, "-m", "analysis.snippet_oracle", mode, str(workdir)]
    if language == "cypher":
        return [python_executable, "-m", "analysis.snippet_oracle", "check-cypher", str(workdir)]
    if language == "typescript":
        script = Path(__file__).with_name("ts_syntax_check.mjs")
        if not typescript_package:
            raise ValueError("typescript checks require the typescript package path")
        return [node_executable, str(script), typescript_package, str(workdir)]
    raise ValueError("language must be python, cypher, or typescript")


def emit_language(
    *,
    language: str,
    labeled_path: Path,
    checkouts: Path,
    work_root: Path,
    python_executable: str,
    limit: int | None = None,
    node_executable: str = "node",
    typescript_package: str = "",
    exclude_ids: set[str] | None = None,
) -> dict[str, object]:
    if language not in {"python", "python-file", "cypher", "typescript"}:
        raise ValueError("language must be python, python-file, cypher, or typescript")
    oracle_kind = "compiler" if language == "cypher" else "parser"
    labeled_language = "python" if language == "python-file" else language
    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    skipped = {"not_in_source": 0, "missing_code": 0, "hash_mismatch": 0}
    considered = 0
    from analysis.jsonl_io import load_jsonl

    for row in load_jsonl(labeled_path):
        if row.get("language") != labeled_language:
            continue
        if exclude_ids and str(row.get("example_id")) in exclude_ids:
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
        in_source = snippet_in_source(checkout, str(source_file), str(code))
        if not in_source and language == "cypher":
            in_source = _cypher_yaml_contains(checkout, str(source_file), str(code))
        if not in_source:
            skipped["not_in_source"] += 1
            continue
        item = {"example_id": str(example_id), "code_sha256": str(code_hash), "code": str(code)}
        if language in {"python-file", "cypher"}:
            item["source_path"] = str(source_file_path(checkout, str(source_file)))
        grouped.setdefault((str(repo), str(pin)), []).append(item)

    evidence: list[dict[str, object]] = []
    groups: list[dict[str, object]] = []
    for (repo, pin), rows in sorted(grouped.items()):
        workdir = work_root / language / repo.replace("/", "__")
        if workdir.exists():
            for child in workdir.iterdir():
                if child.is_file():
                    child.unlink()
        write_work_manifest(workdir, rows)
        argv = checker_argv(
            language,
            workdir,
            python_executable=python_executable,
            node_executable=node_executable,
            typescript_package=typescript_package,
        )
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
    check_python_file = sub.add_parser("check-python-file")
    check_python_file.add_argument("workdir", type=Path)
    check_cypher = sub.add_parser("check-cypher")
    check_cypher.add_argument("workdir", type=Path)
    emit = sub.add_parser("emit")
    emit.add_argument("--language", required=True, choices=("python", "python-file", "cypher", "typescript"))
    emit.add_argument("--labeled", type=Path, required=True)
    emit.add_argument("--checkouts", type=Path, required=True)
    emit.add_argument("--workdir", type=Path, required=True)
    emit.add_argument("--evidence-out", type=Path, required=True)
    emit.add_argument("--summary-out", type=Path, required=True)
    emit.add_argument("--python", default=sys.executable)
    emit.add_argument("--node", default="node")
    emit.add_argument("--typescript", default="")
    emit.add_argument("--limit", type=int, default=None)
    emit.add_argument("--exclude-evidence", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.command == "check-python":
        write_check_result(args.workdir, check_python_snippets(args.workdir))
        return 0
    if args.command == "check-python-file":
        write_check_result(args.workdir, check_python_files(args.workdir))
        return 0
    if args.command == "check-cypher":
        write_check_result(args.workdir, check_cypher_snippets(args.workdir))
        return 0
    exclude_ids: set[str] = set()
    if args.exclude_evidence is not None:
        from analysis.jsonl_io import load_jsonl

        for row in load_jsonl(args.exclude_evidence):
            covered = row.get("covered_examples")
            if not isinstance(covered, list):
                continue
            for entry in covered:
                if isinstance(entry, dict) and isinstance(entry.get("example_id"), str):
                    exclude_ids.add(entry["example_id"])
    summary = emit_language(
        language=args.language,
        labeled_path=args.labeled,
        checkouts=args.checkouts,
        work_root=args.workdir,
        python_executable=args.python,
        limit=args.limit,
        node_executable=args.node,
        typescript_package=args.typescript,
        exclude_ids=exclude_ids,
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
