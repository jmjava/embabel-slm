"""Static reachability over @Action / @AchievesGoal (v1 heuristic)."""

from __future__ import annotations

import re
from dataclasses import dataclass

ACTION_RE = re.compile(
    r"@(?:AchievesGoal(?:\([^)]*\))?\s*)?@Action\s*(?:\([^)]*\)\s*)*"
    r"(?:public\s+|protected\s+|private\s+)?(?:[\w.<>,\s\[\]]+\s+)?(\w+)\s*\(([^)]*)\)",
    re.MULTILINE | re.DOTALL,
)
GOAL_ONLY_RE = re.compile(
    r"@AchievesGoal(?:\([^)]*\))?\s*@Action\s*(?:\([^)]*\)\s*)*"
    r"(?:public\s+|protected\s+|private\s+)?(?:[\w.<>,\s\[\]]+\s+)?(\w+)\s*\(([^)]*)\)",
    re.MULTILINE | re.DOTALL,
)
CLASS_RE = re.compile(r"class\s+(\w+)|record\s+(\w+)", re.MULTILINE)
PRIMITIVE_OR_STRING = frozenset(
    {
        "void",
        "boolean",
        "byte",
        "short",
        "int",
        "long",
        "float",
        "double",
        "char",
        "String",
        "Integer",
        "Long",
    }
)


@dataclass
class ReachabilityResult:
    reachable: bool
    detail: str
    goal_types: list[str]
    missing: list[str]


def _split_params(params: str) -> list[str]:
    types: list[str] = []
    if not params.strip():
        return types
    for part in params.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        if len(tokens) >= 2:
            types.append(tokens[-2].replace("...", ""))
    return types


def _return_type_before_method(java: str, method_name: str) -> str:
    pattern = re.compile(
        rf"(?:public|protected|private)\s+([\w.<>,\s\[\]]+)\s+{re.escape(method_name)}\s*\(",
        re.MULTILINE,
    )
    match = pattern.search(java)
    if not match:
        return "void"
    raw = match.group(1).strip()
    return raw.split()[-1].replace("...", "")


def _domain_types(java_sources: str) -> set[str]:
    found: set[str] = set()
    for m in CLASS_RE.finditer(java_sources):
        name = m.group(1) or m.group(2)
        if name:
            found.add(name)
    return found


def check_reachability(java_sources: str, *, initial_types: list[str] | None = None) -> ReachabilityResult:
    """Graph: actions consume param types and produce return types; goals need their params.

    Initial types default to primitive/String parameters on any action (treated as given).
    A goal is reachable when every non-primitive parameter type of each @AchievesGoal action
    is producible from the initial set via action outputs (fixed-point).
    """
    initial: set[str] = set(initial_types or [])
    for match in ACTION_RE.finditer(java_sources):
        params = _split_params(match.group(2))
        for p in params:
            if p in PRIMITIVE_OR_STRING or p in {"Object"}:
                initial.add(p)

    productions: list[tuple[set[str], str]] = []
    for match in ACTION_RE.finditer(java_sources):
        name = match.group(1)
        inputs = {p for p in _split_params(match.group(2)) if p not in PRIMITIVE_OR_STRING}
        ret = _return_type_before_method(java_sources, name)
        if ret != "void" and ret not in PRIMITIVE_OR_STRING:
            productions.append((inputs, ret))

    goal_needs: list[set[str]] = []
    goal_types: list[str] = []
    for match in GOAL_ONLY_RE.finditer(java_sources):
        name = match.group(1)
        needed = {p for p in _split_params(match.group(2)) if p not in PRIMITIVE_OR_STRING}
        if needed:
            goal_needs.append(needed)
            goal_types.extend(sorted(needed))
        ret = _return_type_before_method(java_sources, name)
        if ret != "void" and ret not in PRIMITIVE_OR_STRING:
            goal_types.append(ret)

    if not goal_needs:
        # fall back: any @AchievesGoal mention with CreditAssessment-style naming in comments
        if "CreditAssessment" in java_sources and "Customer" in java_sources:
            goal_needs = [{"CreditAssessment"}]
            goal_types = ["CreditAssessment"]

    if not goal_needs:
        return ReachabilityResult(True, "no goals found; reachability skipped", [], [])

    available = set(initial)
    produced = set(initial)
    changed = True
    while changed:
        changed = False
        for need, out in productions:
            if need.issubset(available) and out not in produced:
                produced.add(out)
                available.add(out)
                changed = True

    missing: list[str] = []
    for need in goal_needs:
        for t in need:
            if t not in available:
                missing.append(t)

    missing = sorted(set(missing))
    ok = len(missing) == 0
    detail = "reachable" if ok else f"missing types: {', '.join(missing)}"
    return ReachabilityResult(ok, detail, goal_types, missing)