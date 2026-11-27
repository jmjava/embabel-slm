"""Run fixed oracle commands and emit canonical evidence (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from analysis.hashes import canonical_command_sha256, sha256_text

_DEFAULT_TIMEOUT = 120
_MAX_CAPTURE = 1_000_000


def verify_git_pin(repo_path: Path, expected_pin: str) -> None:
    if not repo_path.is_dir():
        raise ValueError(f"missing repo checkout {repo_path}")
    proc = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise ValueError(f"git rev-parse failed in {repo_path}: {proc.stderr.strip()}")
    head = proc.stdout.strip()
    if head != expected_pin:
        raise ValueError(f"pin mismatch: expected {expected_pin}, saw {head}")


def run_fixed_argv(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> dict[str, object]:
    """Execute argv with shell=False; return bounded stdout/stderr hashes."""
    if not argv:
        raise ValueError("argv must be nonempty")
    proc = subprocess.run(
        list(argv),
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    stdout = proc.stdout[:_MAX_CAPTURE]
    stderr = proc.stderr[:_MAX_CAPTURE]
    combined = stdout + stderr
    stdout_text = stdout.decode("utf-8", errors="replace")
    stderr_text = stderr.decode("utf-8", errors="replace")
    return {
        "command_argv": list(argv),
        "command_sha256": canonical_command_sha256(argv),
        "exit_code": int(proc.returncode),
        "output_sha256": sha256_text(combined.decode("utf-8", errors="replace")),
        "artifact_sha256": hashlib.sha256(stdout).hexdigest(),
        "stdout_text": stdout_text,
        "stderr_text": stderr_text,
    }


def build_evidence_record(
    *,
    evidence_id: str,
    source_repo: str,
    source_pin: str,
    oracle_kind: str,
    argv: Sequence[str],
    covered_examples: Sequence[dict[str, str]],
    cwd: Path | None = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> dict[str, object]:
    """Run argv and attach covered example bindings."""
    run_meta = run_fixed_argv(argv, cwd=cwd, timeout=timeout)
    if int(run_meta["exit_code"]) != 0:
        raise ValueError(f"oracle command failed with exit {run_meta['exit_code']}")
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
        "covered_examples": [
            {"example_id": str(entry["example_id"]), "code_sha256": str(entry["code_sha256"])}
            for entry in covered_examples
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a fixed oracle argv and emit JSON evidence.")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--pin", required=True)
    parser.add_argument("--evidence-id", required=True)
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--oracle-kind", default="test")
    parser.add_argument("--command", nargs="+", required=True, help="argv tokens, no shell")
    parser.add_argument("--covered", action="append", default=[], help="example_id:code_sha256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    verify_git_pin(args.repo, args.pin)
    covered: list[dict[str, str]] = []
    for token in args.covered:
        example_id, code_hash = token.split(":", 1)
        covered.append({"example_id": example_id, "code_sha256": code_hash})
    record = build_evidence_record(
        evidence_id=args.evidence_id,
        source_repo=args.source_repo,
        source_pin=args.pin,
        oracle_kind=args.oracle_kind,
        argv=args.command,
        covered_examples=covered,
        cwd=args.repo,
    )
    args.out.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())