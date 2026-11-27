"""CLI entrypoints for analysis (stdlib only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from analysis.admission import admit_cli
from analysis.dedup import dedup_exit_code, run_dedup
from analysis.power import power_table
from analysis.seal import seal_cli
from analysis.study_results import dumps_deterministic_json, study_results_cli
from analysis.training_examples import build_prefixes_cli


def main(argv: list[str]) -> int:
    if not argv:
        print(
            "usage:\n  python3 -m analysis power\n"
            "  python3 -m analysis study-results SCORES.jsonl --sealed-manifest PATH "
            "[--samples SAMPLES.jsonl]\n"
            "  python3 -m analysis dedup RECORDS.jsonl [--exhaustive]\n"
            "  python3 -m analysis admit LABELED.jsonl EVIDENCE.jsonl [--holdout HOLDOUT.jsonl]\n"
            "  python3 -m analysis build-prefixes ADMITTED.jsonl OUTDIR --admission-receipt R "
            "--labeled L --evidence E [--force]\n"
            "  python3 -m analysis seal-study LABELED EVIDENCE HOLDOUT OUTDIR [--force] [--exhaustive]",
            file=sys.stderr,
        )
        return 2
    if argv[0] == "power":
        if len(argv) != 1:
            print("usage: python3 -m analysis power", file=sys.stderr)
            return 2
        print(json.dumps(power_table(), indent=2))
        return 0
    if argv[0] == "study-results":
        return study_results_cli(argv[1:])
    if argv[0] == "dedup":
        if len(argv) not in (2, 3):
            print(
                "usage: python3 -m analysis dedup RECORDS.jsonl [--exhaustive]",
                file=sys.stderr,
            )
            return 2
        exhaustive = False
        if len(argv) == 3:
            if argv[2] != "--exhaustive":
                print(
                    "usage: python3 -m analysis dedup RECORDS.jsonl [--exhaustive]",
                    file=sys.stderr,
                )
                return 2
            exhaustive = True
        path_argv = argv[1]
        try:
            result = run_dedup(Path(path_argv), exhaustive=exhaustive)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(dumps_deterministic_json(result), end="")
        return dedup_exit_code(result)
    if argv[0] == "admit":
        return admit_cli(argv[1:])
    if argv[0] == "build-prefixes":
        return build_prefixes_cli(argv[1:])
    if argv[0] == "seal-study":
        return seal_cli(argv[1:])
    print(
        "usage:\n  python3 -m analysis power\n"
        "  python3 -m analysis study-results SCORES.jsonl --sealed-manifest PATH "
        "[--samples SAMPLES.jsonl]\n"
        "  python3 -m analysis dedup RECORDS.jsonl [--exhaustive]\n"
        "  python3 -m analysis admit LABELED.jsonl EVIDENCE.jsonl [--holdout HOLDOUT.jsonl]\n"
        "  python3 -m analysis build-prefixes ADMITTED.jsonl OUTDIR --admission-receipt R "
        "--labeled L --evidence E [--force]\n"
        "  python3 -m analysis seal-study LABELED EVIDENCE HOLDOUT OUTDIR [--force] [--exhaustive]",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))