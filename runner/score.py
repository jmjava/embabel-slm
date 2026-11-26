"""Score tasks: layers, metrics, summaries."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from runner.config import EMBABEL_COMMIT, EMBABEL_REPO
from runner.extract import extract_fenced_files, merge_with_project
from runner.maven import compile_tree
from runner.reachability import check_reachability
from runner.runs import ROOT, load_spec

CACHE_DIR = ROOT / ".cache" / "runner-m2"


@dataclass
class LayerOutcome:
    status: str  # pass | fail | skip | error
    detail: str = ""


@dataclass
class TaskScore:
    task_id: str
    layers: dict[str, LayerOutcome]
    pass_: bool
    first_failure: str | None
    hallucinated_api: bool = False

    def to_json(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "layers": {k: {"status": v.status, "detail": v.detail} for k, v in self.layers.items()},
            "pass": self.pass_,
            "first_failure": self.first_failure,
            "hallucinated_api": self.hallucinated_api,
        }


def _layer_pass(name: str, status: str) -> bool:
    return status == "pass"


def structure_checks(java_text: str, checks: list[dict]) -> LayerOutcome:
    for check in checks:
        kind = check.get("kind")
        if kind == "regex":
            if not re.search(check["pattern"], java_text, re.MULTILINE | re.DOTALL):
                return LayerOutcome("fail", check.get("message", "structure regex miss"))
        elif kind == "contains":
            if check.get("text") not in java_text:
                return LayerOutcome("fail", check.get("message", "missing text"))
        elif kind == "forbid_regex":
            if re.search(check["pattern"], java_text, re.MULTILINE | re.DOTALL):
                return LayerOutcome("fail", check.get("message", "forbidden pattern"))
    if not checks:
        return LayerOutcome("skip", "no structure checks")
    return LayerOutcome("pass", "structure ok")


def prose_checks(text: str, checks: list[dict]) -> LayerOutcome:
    for check in checks:
        if check.get("kind") == "contains":
            if check.get("text") not in text:
                return LayerOutcome("fail", check.get("message", "prose missing"))
    if not checks:
        return LayerOutcome("skip", "no prose checks")
    return LayerOutcome("pass", "prose ok")


def load_answer_text(task_id: str, run_dir: Path | None, fixture_path: Path | None, use_project_only: bool) -> str:
    if use_project_only:
        return ""
    if fixture_path and fixture_path.is_file():
        return fixture_path.read_text(encoding="utf-8")
    if run_dir:
        raw = run_dir / "raw" / f"{task_id}.md"
        if raw.is_file():
            return raw.read_text(encoding="utf-8")
    raise FileNotFoundError(f"no answer for {task_id}")


def score_task(
    task_id: str,
    *,
    run_dir: Path | None = None,
    fixture_path: Path | None = None,
    use_project_only: bool = False,
) -> TaskScore:
    spec = load_spec(task_id)
    answer = ""
    if not use_project_only:
        answer = load_answer_text(task_id, run_dir, fixture_path, use_project_only)

    base_files = {k: v for k, v in spec.get("input_project", {}).items()}
    extracted = extract_fenced_files(answer) if answer else []
    files = merge_with_project(base_files, extracted)

    layers: dict[str, LayerOutcome] = {}
    order = ["extract", "compile", "test", "structure", "reachability", "prose"]

    if use_project_only or spec.get("mode") == "project_only":
        layers["extract"] = LayerOutcome("skip", "fixture project only")
    elif not extracted and not spec.get("input_project"):
        layers["extract"] = LayerOutcome("fail", "no fenced files")
    elif spec.get("requires_extraction", True) and not extracted and answer:
        layers["extract"] = LayerOutcome("fail", "no fenced files in answer")
    else:
        layers["extract"] = LayerOutcome("pass", f"{len(extracted)} files" if extracted else "input project")

    java_blob = "\n".join(v for k, v in files.items() if k.endswith(".java"))

    want_compile = spec.get("checks", {}).get("compile", False)
    want_test = spec.get("checks", {}).get("test", False)
    hallucinated = False

    if want_compile:
        result = compile_tree(files, with_tests=want_test, cache_dir=CACHE_DIR)
        if result.output == "" and "mvn not found" in result.first_error:
            layers["compile"] = LayerOutcome("error", result.first_error)
            layers["test"] = LayerOutcome("error", "blocked by missing mvn") if want_test else LayerOutcome("skip", "")
        else:
            layers["compile"] = LayerOutcome("pass" if result.ok else "fail", result.first_error or "compiled")
            hallucinated = result.hallucinated
            if want_test:
                if result.ok:
                    layers["test"] = LayerOutcome("pass", "tests ok")
                else:
                    layers["test"] = LayerOutcome("fail", result.first_error or "tests failed")
            else:
                layers["test"] = LayerOutcome("skip", "no tests requested")
    else:
        layers["compile"] = LayerOutcome("skip", "compile not required")
        layers["test"] = LayerOutcome("skip", "tests not required")

    struct_rules = spec.get("structure_checks", [])
    if struct_rules:
        layers["structure"] = structure_checks(java_blob, struct_rules)
    else:
        layers["structure"] = LayerOutcome("skip", "no structure rules")

    if spec.get("checks", {}).get("reachability", False):
        init = spec.get("reachability", {}).get("initial_types")
        rr = check_reachability(java_blob, initial_types=init)
        layers["reachability"] = LayerOutcome("pass" if rr.reachable else "fail", rr.detail)
    else:
        layers["reachability"] = LayerOutcome("skip", "reachability not required")

    prose_rules = spec.get("prose_checks", [])
    if prose_rules:
        layers["prose"] = prose_checks(answer, prose_rules)
    else:
        layers["prose"] = LayerOutcome("skip", "no prose checks")

    required = {
        "extract": spec.get("requires_extraction", True) and not use_project_only,
        "compile": want_compile,
        "test": want_test,
        "structure": bool(struct_rules),
        "reachability": spec.get("checks", {}).get("reachability", False),
        "prose": bool(prose_rules),
    }
    first_failure: str | None = None
    overall = True
    for name in order:
        layer = layers.get(name)
        if layer is None:
            continue
        if not required.get(name, False) and layer.status == "skip":
            continue
        if layer.status == "error" and name == "compile" and "mvn not found" in layer.detail:
            overall = False
            continue
        if layer.status in {"fail", "error"}:
            overall = False
            first_failure = first_failure or name
        elif required.get(name, False) and layer.status != "pass":
            overall = False
            first_failure = first_failure or name

    return TaskScore(
        task_id=task_id,
        layers=layers,
        pass_=overall,
        first_failure=first_failure,
        hallucinated_api=hallucinated,
    )


def score_suite(
    task_ids: list[str],
    *,
    run_dir: Path | None = None,
    fixture_dir: Path | None = None,
) -> dict[str, Any]:
    tasks: list[dict] = []
    for tid in task_ids:
        fix = None
        if fixture_dir:
            candidate = fixture_dir / f"{tid}.md"
            if candidate.is_file():
                fix = candidate
        if tid == "KB01":
            score = score_task(tid, use_project_only=True)
        else:
            score = score_task(tid, run_dir=run_dir, fixture_path=fix)
        tasks.append(score.to_json())

    n = len(tasks)
    compiled = sum(1 for t in tasks if t["layers"].get("compile", {}).get("status") == "pass")
    compile_attempted = sum(
        1 for t in tasks if t["layers"].get("compile", {}).get("status") in {"pass", "fail", "error"}
    )
    full_success = sum(1 for t in tasks if t["pass"])
    hallu = sum(1 for t in tasks if t.get("hallucinated_api"))
    planner = sum(
        1
        for t in tasks
        if t["layers"].get("reachability", {}).get("status") == "pass"
        and t["layers"].get("reachability", {}).get("detail") != "no goals found; reachability skipped"
    )
    planner_req = sum(
        1 for tid in task_ids if load_spec(tid).get("checks", {}).get("reachability", False)
    )

    metrics = {
        "compile_rate": (compiled / compile_attempted) if compile_attempted else None,
        "full_task_success": (full_success / n) if n else None,
        "hallucinated_api_rate": (hallu / compile_attempted) if compile_attempted else None,
        "planner_success": (planner / planner_req) if planner_req else None,
        "repair_iterations": 0,
        "repair_iterations_note": "single-shot generate only; repair loop not scored in M2",
        "hallucinated_api_heuristic": "mvn compile/test stderr matches cannot-find-symbol or missing com.embabel package",
    }
    return {
        "embabel_pin": f"{EMBABEL_REPO}@{EMBABEL_COMMIT}",
        "tasks": tasks,
        "summary": metrics,
    }


def write_scores(run_dir: Path, payload: dict[str, Any]) -> Path:
    path = run_dir / "scores.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path