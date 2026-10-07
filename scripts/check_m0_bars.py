#!/usr/bin/env python3
"""Lock the M0 bars. A later edit fails unless it is an explicit amendment."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE_PATH = ROOT / "docs" / "m0-bars.md"
AMEND_PATH = ROOT / "docs" / "m0-bars-amendments.md"
RUNNER_STABLE_PATH = ROOT / "docs" / "runner-stable.md"

EXPECTED_SHA256 = "90260c785e8ae256d519a0d2f5f964e546f92704af4e318ec666fd31162db7ef"

LOCK_PATHS = (
    "docs/m0-bars.md",
    "docs/m0-bars-amendments.md",
    "scripts/check_m0_bars.py",
    ".github/workflows/m0-bars.yml",
)

POISON_PREFIXES = (
    "experiments/",
    "benchmark/",
    "training/",
    "datasets/",
    "evaluation/",
    "runs/",
    "results/",
)

START = "<!-- m0-bars:start -->"
END = "<!-- m0-bars:end -->"

EXPECTED_BARS = {
    "frozen_on": "2026-10-07",
    "general_coding_floor": {
        "tasks": ["tests", "repair", "multi_file_edit", "explanation"],
        "release_fail_drop_points": 5,
        "scope": "any_single_task",
        "averaging": "forbidden",
        "missing_score": "fail",
        "compare_to": "pinned_base_model_on_the_same_tasks",
    },
    "embabel_gain": {
        "metrics": [
            {"id": "compile_rate", "direction": "higher", "lift_points": 5},
            {"id": "full_task_success", "direction": "higher", "lift_points": 5},
            {"id": "hallucinated_api_rate", "direction": "lower", "lift_points": 5},
            {"id": "planner_success", "direction": "higher", "lift_points": 5},
            {"id": "repair_iterations", "direction": "lower", "max_percent_of_base": 80},
        ],
        "counts_when": "every_metric_meets_its_lift",
        "unlisted_metrics_count": False,
    },
    "host_budget": {
        "first_min_billion_parameters": 7,
        "first_max_billion_parameters": 14,
        "later_class_min_billion_parameters": 30,
        "later_class_max_billion_parameters": 34,
        "later_only_after": "docs/runner-stable.md",
        "runner_stable_requires": [
            "runner_command",
            "known_bad_fixture_failed",
            "scoring_run_id",
        ],
        "known_bad_fixture_failed_must_equal": True,
        "inference_hosts": ["downstairs-4080", "downstairs-3060"],
        "inference_hosts_after_downstairs_scores": ["halo-395"],
        "ide_workstation": "mcp_host",
        "quantization_uses_base_parameter_count": True,
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_bars(text: str) -> dict:
    start = text.index(START)
    end = text.index(END)
    block = text[start + len(START) : end]
    fence = "```json"
    opening = block.index(fence) + len(fence)
    closing = block.index("```", opening)
    return json.loads(block[opening:closing])


def general_floor_holds(base: dict, candidate: dict, bars: dict) -> bool:
    floor = bars["general_coding_floor"]
    if floor["averaging"] != "forbidden" or floor["scope"] != "any_single_task":
        return False
    if floor["missing_score"] != "fail":
        return False
    drop = floor["release_fail_drop_points"]
    for task in floor["tasks"]:
        if task not in base or task not in candidate:
            return False
        if candidate[task] < base[task] - drop:
            return False
    return True


def _metric_meets(spec: dict, base: float, candidate: float) -> bool:
    if spec["id"] == "repair_iterations":
        if base == 0:
            return candidate == 0
        return candidate * 100 <= base * spec["max_percent_of_base"] + 1e-6
    points = spec["lift_points"]
    if spec["direction"] == "higher":
        if base > 100 - points:
            return candidate >= 100
        return candidate >= base + points
    if spec["direction"] == "lower":
        if base < points:
            return candidate <= 0
        return candidate <= base - points
    return False


def embabel_lift_counts(base: dict, candidate: dict, bars: dict) -> bool:
    gain = bars["embabel_gain"]
    if gain["counts_when"] != "every_metric_meets_its_lift":
        return False
    if gain["unlisted_metrics_count"] is not False:
        return False
    for spec in gain["metrics"]:
        metric_id = spec["id"]
        if metric_id not in base or metric_id not in candidate:
            return False
        if not _metric_meets(spec, base[metric_id], candidate[metric_id]):
            return False
    return True


def size_allowed(billions: float, runner_stable: bool, bars: dict) -> bool:
    host = bars["host_budget"]
    if host["first_min_billion_parameters"] <= billions <= host["first_max_billion_parameters"]:
        return True
    later = (
        host["later_class_min_billion_parameters"]
        <= billions
        <= host["later_class_max_billion_parameters"]
    )
    return bool(runner_stable and later)


def host_allowed(host_class: str, downstairs_has_scored_run: bool, bars: dict) -> bool:
    host = bars["host_budget"]
    if host_class in host["inference_hosts"]:
        return True
    return bool(
        downstairs_has_scored_run and host_class in host["inference_hosts_after_downstairs_scores"]
    )


def runner_record_is_stable(data: dict, bars: dict) -> bool:
    host = bars["host_budget"]
    if data.get("known_bad_fixture_failed") is not host["known_bad_fixture_failed_must_equal"]:
        return False
    for key in host["runner_stable_requires"]:
        if key not in data:
            return False
    if not str(data.get("runner_command", "")).strip():
        return False
    if not str(data.get("scoring_run_id", "")).strip():
        return False
    return True


def page_problems(text: str) -> list[str]:
    problems: list[str] = []
    digest = sha256_bytes(text.encode("utf-8"))
    if digest != EXPECTED_SHA256:
        problems.append(f"docs/m0-bars.md sha256 is {digest}, freeze is {EXPECTED_SHA256}")
    try:
        parsed = extract_bars(text)
    except (ValueError, json.JSONDecodeError) as exc:
        problems.append(f"normative JSON block is unreadable: {exc}")
        return problems
    if parsed != EXPECTED_BARS:
        problems.append("normative JSON does not match the frozen bar values")
    return problems


def _poison(path: str) -> bool:
    if path.startswith(POISON_PREFIXES):
        return True
    name = path.rsplit("/", 1)[-1]
    return path.endswith(".csv") or name in {"results.json", "scores.json", "score.json"}


def _one_amendment(extra: str, old_sha: str, new_sha: str) -> list[str]:
    problems: list[str] = []
    if extra.count("\n## Amendment\n") != 1 and not extra.startswith("## Amendment\n"):
        # The appended text should contain the heading once.
        headings = [line for line in extra.splitlines() if line == "## Amendment"]
        if len(headings) != 1:
            problems.append("append exactly one ## Amendment section")
            return problems
    if f"old_sha256: {old_sha}" not in extra:
        problems.append("amendment must record the old sha256")
    if f"new_sha256: {new_sha}" not in extra:
        problems.append("amendment must record the new sha256")
    reason = ""
    for line in extra.splitlines():
        if line.startswith("- reason:"):
            reason = line[len("- reason:") :].strip()
    if len(reason) < 80:
        problems.append("amendment reason must be at least 80 characters")
    return problems


def assess_edit(
    base_page: bytes | None,
    head_page: bytes | None,
    base_amend: bytes | None,
    head_amend: bytes | None,
    changed_paths: list[str],
    pr_title: str,
) -> list[str]:
    """Return problems when a lock file moves without an amendment."""
    if not any(path in LOCK_PATHS for path in changed_paths):
        return []
    problems: list[str] = []
    if any(_poison(path) for path in changed_paths):
        problems.append("a bar change also touches experiment runs, scores, or results")
    if base_page is None:
        if head_page is None:
            problems.append("the freeze page is missing")
        amend_text = (head_amend or b"").decode("utf-8")
        if any(line == "## Amendment" for line in amend_text.splitlines()):
            problems.append("the initial freeze includes an amendment")
        return problems
    if not (pr_title or "").startswith("amend(m0-bars):"):
        problems.append("pull request title must start with amend(m0-bars):")
    if base_amend is None or head_amend is None or not head_amend.startswith(base_amend):
        problems.append("docs/m0-bars-amendments.md must keep the existing bytes and append")
        return problems
    extra = head_amend[len(base_amend) :].decode("utf-8")
    old_sha = sha256_bytes(base_page)
    new_sha = sha256_bytes(head_page or b"")
    problems.extend(_one_amendment(extra, old_sha, new_sha))
    return problems


def _git_bytes(ref: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{ref}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def _changed_paths(ref: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{ref}...HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in proc.stdout.splitlines() if line]


def against(ref: str, pr_title: str) -> list[str]:
    return assess_edit(
        _git_bytes(ref, "docs/m0-bars.md"),
        _git_bytes("HEAD", "docs/m0-bars.md"),
        _git_bytes(ref, "docs/m0-bars-amendments.md"),
        _git_bytes("HEAD", "docs/m0-bars-amendments.md"),
        _changed_paths(ref),
        pr_title,
    )


def _load_runner_stable(bars: dict) -> tuple[bool, list[str]]:
    if not RUNNER_STABLE_PATH.exists():
        return False, []
    try:
        data = json.loads(RUNNER_STABLE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return False, [f"docs/runner-stable.md is not the JSON record: {exc}"]
    if not isinstance(data, dict) or not runner_record_is_stable(data, bars):
        return False, ["docs/runner-stable.md does not meet the frozen runner record"]
    return True, []


def _scan_result_files(bars: dict, runner_stable: bool) -> list[str]:
    problems: list[str] = []
    rows: list[tuple[str, dict]] = []
    for folder in ("experiments", "models"):
        directory = ROOT / folder
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".json", ".yml", ".yaml", ".csv"}:
                continue
            text = path.read_text(encoding="utf-8")
            if "parameter_billions" not in text and "host_class" not in text:
                continue
            parsed = _rows_from_text(text)
            if not parsed:
                problems.append(f"unreadable results file {path.relative_to(ROOT)}")
                continue
            for row in parsed:
                rows.append((str(path.relative_to(ROOT)), row))
    downstairs = any(
        row.get("host_class") in bars["host_budget"]["inference_hosts"] for _, row in rows
    )
    for name, row in rows:
        if "parameter_billions" in row and not size_allowed(
            float(row["parameter_billions"]), runner_stable, bars
        ):
            problems.append(f"{name} parameter_billions is outside the host budget")
        if "host_class" in row and not host_allowed(str(row["host_class"]), downstairs, bars):
            problems.append(f"{name} host_class is outside the host budget")
    return problems


def _rows_from_text(text: str) -> list[dict]:
    stripped = text.strip()
    if not stripped:
        return []
    if stripped[0] in "[{":
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            return []
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            return data
        return []
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if lines and "," in lines[0] and "host_class" in lines[0] or (
        lines and "parameter_billions" in lines[0] and "," in lines[0]
    ):
        header = [cell.strip() for cell in lines[0].split(",")]
        rows = []
        for line in lines[1:]:
            cells = [cell.strip() for cell in line.split(",")]
            rows.append(dict(zip(header, cells)))
        return rows
    row: dict = {}
    for line in lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        row[key.strip()] = value.strip().strip('"').strip("'")
    return [row] if row else []


def check_workspace() -> list[str]:
    if not PAGE_PATH.is_file():
        return ["docs/m0-bars.md is missing"]
    text = PAGE_PATH.read_text(encoding="utf-8")
    problems = page_problems(text)
    if problems:
        return problems
    bars = extract_bars(text)
    runner_stable, stable_problems = _load_runner_stable(bars)
    problems.extend(stable_problems)
    problems.extend(_scan_result_files(bars, runner_stable))
    return problems


def _rates(score: float, **overrides: float) -> dict:
    rates = {task: score for task in EXPECTED_BARS["general_coding_floor"]["tasks"]}
    rates.update(overrides)
    return rates


def _specialist(**overrides: float) -> dict:
    base = {
        "compile_rate": 50.0,
        "full_task_success": 40.0,
        "hallucinated_api_rate": 20.0,
        "planner_success": 30.0,
        "repair_iterations": 5.0,
    }
    base.update(overrides)
    return base


def self_test() -> int:
    problems = check_workspace()
    bars = extract_bars(PAGE_PATH.read_text(encoding="utf-8"))
    floor = bars["general_coding_floor"]
    gain = bars["embabel_gain"]
    host = bars["host_budget"]
    if floor["tasks"] != ["tests", "repair", "multi_file_edit", "explanation"]:
        problems.append("general-coding task list moved")
    if floor["release_fail_drop_points"] != 5:
        problems.append("release drop is no longer 5 points")
    if floor["averaging"] != "forbidden":
        problems.append("averaging is allowed")
    metric_ids = [item["id"] for item in gain["metrics"]]
    if metric_ids != [
        "compile_rate",
        "full_task_success",
        "hallucinated_api_rate",
        "planner_success",
        "repair_iterations",
    ]:
        problems.append("specialist metric list moved")
    for item in gain["metrics"]:
        if "lift_points" in item and item["lift_points"] != 5:
            problems.append(f"{item['id']} lift is no longer 5 points")
    repair = gain["metrics"][-1]
    if repair["max_percent_of_base"] != 80:
        problems.append("repair-iteration lift is no longer 80 percent of base")
    if host["first_min_billion_parameters"] != 7 or host["first_max_billion_parameters"] != 14:
        problems.append("first size band is no longer 7B–14B")
    if (
        host["later_class_min_billion_parameters"] != 30
        or host["later_class_max_billion_parameters"] != 34
    ):
        problems.append("32B class bounds moved")
    if host["inference_hosts"] != ["downstairs-4080", "downstairs-3060"]:
        problems.append("downstairs host list moved")
    if host["inference_hosts_after_downstairs_scores"] != ["halo-395"]:
        problems.append("halo host gate moved")
    if host["ide_workstation"] != "mcp_host":
        problems.append("IDE workstation is no longer the MCP host")

    if not general_floor_holds(_rates(80), _rates(80, tests=75), bars):
        problems.append("a 5 point drop on one task must still hold")
    if general_floor_holds(_rates(80), _rates(80, tests=74), bars):
        problems.append("a 6 point drop on one task must fail the release")
    if general_floor_holds(_rates(80), _rates(100, explanation=70), bars):
        problems.append("a gain on three tasks must not hide a drop on the fourth")
    if general_floor_holds(_rates(80), {task: 80 for task in floor["tasks"] if task != "repair"}, bars):
        problems.append("a missing task score must fail the release")

    good = _specialist(
        compile_rate=55,
        full_task_success=45,
        hallucinated_api_rate=15,
        planner_success=35,
        repair_iterations=4.0,
    )
    if not embabel_lift_counts(_specialist(), good, bars):
        problems.append("the frozen lift must count when every metric meets it")
    short = dict(good)
    short["full_task_success"] = 44
    if embabel_lift_counts(_specialist(), short, bars):
        problems.append("a 4 point full-task gain must not count")
    repair_slip = dict(good)
    repair_slip["repair_iterations"] = 4.01
    if embabel_lift_counts(_specialist(), repair_slip, bars):
        problems.append("repair iterations above 80 percent of base must not count")
    high_base = _specialist(compile_rate=97)
    at_ceiling = dict(good)
    at_ceiling["compile_rate"] = 100
    if not embabel_lift_counts(high_base, at_ceiling, bars):
        problems.append("a rate already above 95 counts only when the candidate reaches 100")
    under_ceiling = dict(at_ceiling)
    under_ceiling["compile_rate"] = 99
    if embabel_lift_counts(high_base, under_ceiling, bars):
        problems.append("99 must not satisfy a metric that needed the ceiling")
    low_hallu = _specialist(hallucinated_api_rate=3)
    cleared = dict(good)
    cleared["hallucinated_api_rate"] = 0
    if not embabel_lift_counts(low_hallu, cleared, bars):
        problems.append("a hallucinated-API rate already under 5 counts only at 0")
    leftover = dict(cleared)
    leftover["hallucinated_api_rate"] = 1
    if embabel_lift_counts(low_hallu, leftover, bars):
        problems.append("a leftover hallucinated API must not count when the base is already under 5")
    zero_repairs = _specialist(repair_iterations=0)
    still_zero = dict(good)
    still_zero["repair_iterations"] = 0
    if not embabel_lift_counts(zero_repairs, still_zero, bars):
        problems.append("a base with zero repair iterations counts only when the candidate stays at zero")

    if not size_allowed(7, False, bars) or not size_allowed(14, False, bars):
        problems.append("7B and 14B must be allowed before the runner is stable")
    if size_allowed(6.9, False, bars) or size_allowed(14.1, False, bars):
        problems.append("sizes outside 7B–14B must wait")
    if size_allowed(32, False, bars) or size_allowed(22, True, bars) or size_allowed(70, True, bars):
        problems.append("32B before stability, 22B, or 70B must stay outside the budget")
    if not size_allowed(30, True, bars) or not size_allowed(32, True, bars) or not size_allowed(34, True, bars):
        problems.append("30B–34B must be allowed only after the runner is stable")
    if size_allowed(29.9, True, bars) or size_allowed(34.1, True, bars):
        problems.append("the 32B class must stay inside 30B–34B")

    if not host_allowed("downstairs-4080", False, bars) or not host_allowed("downstairs-3060", False, bars):
        problems.append("downstairs hosts must be allowed before halo")
    if host_allowed("halo-395", False, bars):
        problems.append("halo-395 must wait for a downstairs scored run")
    if not host_allowed("halo-395", True, bars):
        problems.append("halo-395 must be allowed after a downstairs scored run")
    if host_allowed("ide-workstation", True, bars) or host_allowed("mcp_host", True, bars):
        problems.append("the IDE workstation must stay an MCP host")

    mutated = PAGE_PATH.read_text(encoding="utf-8").replace(
        '"release_fail_drop_points": 5',
        '"release_fail_drop_points": 15',
        1,
    )
    if not page_problems(mutated):
        problems.append("a quiet edit of the release drop was accepted")
    else:
        print("quiet-edit-rejected")

    base_page = b"base-page"
    head_page = b"head-page"
    base_amend = b"header\n"
    quiet = assess_edit(
        base_page,
        head_page,
        base_amend,
        base_amend,
        ["docs/m0-bars.md"],
        "Adjust the floor",
    )
    if not quiet:
        problems.append("a quiet edit against the frozen page was accepted")
    reason = "The bar moved for a reason written down before any new score was used to pick the number."
    loud = assess_edit(
        base_page,
        head_page,
        base_amend,
        base_amend
        + (
            "\n## Amendment\n\n"
            f"- old_sha256: {sha256_bytes(base_page)}\n"
            f"- new_sha256: {sha256_bytes(head_page)}\n"
            f"- reason: {reason}\n"
        ).encode(),
        ["docs/m0-bars.md", "scripts/check_m0_bars.py"],
        "amend(m0-bars): record a real change",
    )
    if loud:
        problems.append("an explicit amendment was rejected: " + "; ".join(loud))
    poisoned = assess_edit(
        base_page,
        head_page,
        base_amend,
        base_amend + b"\n## Amendment\n",
        ["docs/m0-bars.md", "experiments/paper-v1/scores.csv"],
        "amend(m0-bars): hide a bad table",
    )
    if not poisoned:
        problems.append("an amendment packaged with scores was accepted")
    initial = assess_edit(
        None,
        b"new-page",
        None,
        b"header only\n",
        ["docs/m0-bars.md", "scripts/check_m0_bars.py"],
        "Freeze the M0 evaluation bars",
    )
    if initial:
        problems.append("the initial freeze was rejected: " + "; ".join(initial))

    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("m0 bars hold")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    problems = check_workspace()
    if "--against" in argv:
        ref = argv[argv.index("--against") + 1]
        title = ""
        if "--pr-title" in argv:
            title = argv[argv.index("--pr-title") + 1]
        problems.extend(against(ref, title))
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    print("m0 bars hold")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
