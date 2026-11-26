"""Argument parsing for generate / score / selftest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from runner.generate import generate_run
from runner.runs import ROOT, ensure_run_dir, list_task_ids, new_run_id, refuse_existing
from runner.score import score_suite, score_task, write_scores


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="runner")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="call Ollama and write raw answers")
    gen.add_argument("--model", required=True)
    gen.add_argument("--host-class", required=True, choices=["downstairs-4080", "downstairs-3060", "halo-395"])
    gen.add_argument("--backend", default="vulkan")
    gen.add_argument("--quant", default="unknown")
    gen.add_argument("--run-id", default="")
    gen.add_argument("--tasks", default="all")
    gen.add_argument("--arm", default="S", choices=["S", "M", "L"])
    gen.add_argument("--config", default="A", choices=["A", "B", "C", "D"])
    gen.add_argument("--split", default="pilot", choices=["pilot", "dev", "holdout"])
    gen.add_argument("--num-ctx", type=int, default=8192)
    gen.add_argument("--samples", type=int, default=0, help="sampled runs per task (k); 0 = greedy only")
    gen.add_argument("--temperature", type=float, default=0.8, help="temperature for sampled runs")
    gen.add_argument("--seed", type=int, action="append", dest="seeds", help="sample seed (repeat for each seed)")
    gen.add_argument("--top-p", type=float, default=0.95)

    sc = sub.add_parser("score", help="score a run dir or fixtures")
    sc.add_argument("--run-dir", type=Path, default=None)
    sc.add_argument("--fixture-dir", type=Path, default=None)
    sc.add_argument("--tasks", default="all")
    sc.add_argument("--fixture", type=Path, default=None, help="single answer markdown")
    sc.add_argument("--task-id", default="", help="with --fixture, score one task")

    st = sub.add_parser("selftest", help="KB01 must fail; E01-good must pass")

    return parser.parse_args(argv)


def _task_list(arg: str) -> list[str]:
    if arg == "all":
        return [t for t in list_task_ids() if t != "KB01"]
    return [t.strip() for t in arg.split(",") if t.strip()]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.command == "generate":
        run_id = args.run_id or new_run_id(args.model)
        if args.run_id:
            run_dir = ROOT / "experiments" / "runs" / run_id
            refuse_existing(run_dir)
            run_dir.mkdir(parents=True)
            (run_dir / "raw").mkdir()
        else:
            run_dir = ensure_run_dir(run_id)
        seeds = args.seeds if args.seeds else list(range(1, args.samples + 1)) if args.samples else []
        generate_run(
            run_dir,
            model=args.model,
            host_class=args.host_class,
            backend=args.backend,
            quant=args.quant,
            task_ids=_task_list(args.tasks),
            arm=args.arm,
            config=args.config,
            split=args.split,
            num_ctx=args.num_ctx,
            samples=args.samples,
            sample_temperature=args.temperature,
            sample_seeds=seeds,
            top_p=args.top_p,
        )
        print(run_dir)
        return 0

    if args.command == "score":
        tasks = _task_list(args.tasks)
        if args.fixture and args.task_id:
            result = score_task(args.task_id, fixture_path=args.fixture)
            print(json.dumps(result.to_json(), indent=2))
            return 0 if result.pass_ else 1
        if args.run_dir is None and args.fixture_dir is None:
            fixture_dir = ROOT / "benchmark" / "fixtures" / "scoring-stubs"
            run_dir = ROOT / "experiments" / "runs" / "m2-fixture-suite"
            if not run_dir.exists():
                run_dir.mkdir(parents=True)
                (run_dir / "raw").mkdir(exist_ok=True)
            payload = score_suite(tasks, run_dir=run_dir if (run_dir / "raw").exists() else None, fixture_dir=fixture_dir)
        else:
            payload = score_suite(tasks, run_dir=args.run_dir, fixture_dir=args.fixture_dir)
        if args.run_dir:
            write_scores(args.run_dir, payload)
        print(json.dumps(payload["summary"], indent=2))
        return 0

    if args.command == "selftest":
        kb = score_task("KB01", use_project_only=True)
        if kb.pass_:
            print("selftest: KB01 should fail but passed", file=sys.stderr)
            return 1
        reach = kb.layers.get("reachability")
        if reach is None or reach.status != "fail":
            print("selftest: KB01 reachability must fail", file=sys.stderr)
            return 1
        if kb.first_failure not in {None, "reachability"}:
            print(f"selftest: KB01 unexpected first_failure={kb.first_failure}", file=sys.stderr)
            return 1
        print("selftest: KB01 FAIL (reachability)", file=sys.stderr)
        good = ROOT / "benchmark" / "fixtures" / "known-good" / "E01-good.md"
        e01 = score_task("E01", fixture_path=good)
        if not e01.pass_:
            print(json.dumps(e01.to_json(), indent=2), file=sys.stderr)
            print("selftest: E01-good should pass", file=sys.stderr)
            if any(v.status == "error" for v in e01.layers.values()):
                print("compile-level verification pending (mvn/javac missing?)", file=sys.stderr)
                return 2
            return 1
        print("selftest ok: KB01 fail, E01-good pass")
        return 0

    return 2