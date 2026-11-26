#!/usr/bin/env python3
"""One-shot generator for benchmark/specs/*.json (run from repo root)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "benchmark" / "specs"

PROMPTS = {
    "E01": (
        "embabel-e01-simple-action-v1",
        "Write one Embabel @Action on an @EmbabelComponent class. "
        "It must take a String name and return a greeting domain type (not void). "
        "Include the domain type and the action class as separate Java files.",
    ),
    "E02": (
        "embabel-e02-two-inputs-v1",
        "Create an @EmbabelComponent with an @Action that requires CustomerId and Amount parameters "
        "and returns PaymentRequest. Define small domain records for CustomerId, Amount, and PaymentRequest.",
    ),
    "E03": (
        "embabel-e03-domain-v1",
        "Define an immutable domain type Product and an @Action that builds it from a String sku and int quantity.",
    ),
    "E04": (
        "embabel-e04-goal-v1",
        "In a fixture that already defines CreditAssessment, add a goal declaration "
        "(AchievesGoal) that is satisfied when CreditAssessment is produced.",
    ),
    "E05": (
        "embabel-e05-two-step-v1",
        "Provide two @Action methods: the first maps String id to Customer, the second maps Customer to CreditAssessment. "
        "Add a goal that needs CreditAssessment.",
    ),
    "E06": (
        "embabel-e06-diagnose-v1",
        "Explain in prose why the goal CreditAssessment is unreachable given only CollectCustomer producing Customer. "
        "Optionally include no code or minimal code; name the missing capability.",
    ),
    "E07": (
        "embabel-e07-repair-v1",
        "Patch the broken project by adding an @Action that produces CreditAssessment from Customer.",
    ),
    "E08": (
        "embabel-e08-annotations-v1",
        "Fix misplaced Embabel annotations on ValidAgent so @Action methods are recognized.",
    ),
    "E09": (
        "embabel-e09-unit-test-v1",
        "Add a JUnit 5 test for DoubleAction that asserts the action output.",
    ),
    "E10": (
        "embabel-e10-spring-v1",
        "Add a minimal Spring @Configuration that exposes an Embabel agent bean for BootTests.",
    ),
    "E11": (
        "embabel-e11-transform-v1",
        "Replace the body of LegacyService.process with an @Action on the same class.",
    ),
    "E12": (
        "embabel-e12-split-v1",
        "Split MonolithAction into three @Action methods that still reach the same goal.",
    ),
    "E13": (
        "embabel-e13-condition-v1",
        "Add an Embabel condition gate so ChargeAction runs only when KycStatus is COMPLETE.",
    ),
    "E14": (
        "embabel-e14-blocked-v1",
        "Explain which input blocks PayInvoice in the provided fixture.",
    ),
    "E15": (
        "embabel-e15-manual-v1",
        "Refactor ManualFlow to planner-driven @Action methods without manual chaining.",
    ),
    "E16": (
        "embabel-e16-persist-v1",
        "Add persistence for SavedOrder produced by SaveOrderAction using the provided repository stub.",
    ),
    "E17": (
        "embabel-e17-rest-v1",
        "Add a Spring @RestController endpoint that triggers the agent for AgentRequest.",
    ),
    "E18": (
        "embabel-e18-repair-boot-v1",
        "Fix the missing @Bean in BrokenConfig so ApplicationContext loads.",
    ),
    "E19": (
        "embabel-e19-plan-v1",
        "List the plan steps (A then B then goal) for the given three actions and goal.",
    ),
    "E20": (
        "embabel-e20-app-v1",
        "From the requirement text, add domain, 2-3 actions, goal, and a minimal Boot entry class.",
    ),
}

INPUTS = {
    "E04": {
        "src/main/java/benchmark/e04/CreditAssessment.java": (
            "package benchmark.e04;\n\npublic record CreditAssessment(String id, int score) {}\n"
        ),
        "src/main/java/benchmark/e04/CreditFlow.java": (
            "package benchmark.e04;\n\nimport com.embabel.agent.api.annotation.EmbabelComponent;\n\n"
            "@EmbabelComponent\npublic class CreditFlow {\n    // model adds goal\n}\n"
        ),
    },
    "E07": {
        "src/main/java/benchmark/e07/Domain.java": (
            "package benchmark.e07;\n\n"
            "public record Customer(String id) {}\n"
            "public record CreditAssessment(String id, int score) {}\n"
        ),
        "src/main/java/benchmark/e07/BrokenFlow.java": (
            "package benchmark.e07;\n\n"
            "import com.embabel.agent.api.annotation.*;\n"
            "import com.embabel.agent.api.common.PlannerType;\n\n"
            "@Agent(description=\"broken\", planner=PlannerType.GOAP)\n"
            "public class BrokenFlow {\n"
            "  @Action public Customer load(String id){return new Customer(id);}\n"
            "  @AchievesGoal @Action public CreditAssessment assess(Customer c){return new CreditAssessment(c.id(),1);}\n"
            "}\n"
        ),
    },
    "E08": {
        "src/main/java/benchmark/e08/ValidAgent.java": (
            "package benchmark.e08;\n\n"
            "import com.embabel.agent.api.annotation.Action;\n"
            "import com.embabel.agent.api.annotation.EmbabelComponent;\n\n"
            "@EmbabelComponent\npublic class ValidAgent {\n"
            "  @com.embabel.agent.api.annotation.Export\n"
            "  public String brokenAnnotation() { return \"x\"; }\n"
            "}\n"
        ),
    },
    "E09": {
        "src/main/java/benchmark/e09/DoubleAction.java": (
            "package benchmark.e09;\n\n"
            "import com.embabel.agent.api.annotation.Action;\n"
            "import com.embabel.agent.api.annotation.EmbabelComponent;\n\n"
            "public record Twice(int value) {}\n\n"
            "@EmbabelComponent\n"
            "public class DoubleAction {\n"
            "  @Action public Twice twice(int n){ return new Twice(n*2);}\n"
            "}\n"
        ),
    },
}

# fix E06 input from KB01
kb01_java = (ROOT / "benchmark/fixtures/known-bad/KB01/src/main/java/benchmark/kb01").glob("*.java")
E06_files = {}
for p in kb01_java:
    E06_files[f"src/main/java/benchmark/kb01/{p.name}"] = p.read_text(encoding="utf-8")
INPUTS["E06"] = E06_files

CHECKS_DEFAULT = {"compile": True, "test": False, "reachability": False}

SPECS_META = {
    "E01": {
        "checks": {"compile": True, "reachability": False, "test": False},
        "structure": [
            {"kind": "regex", "pattern": r"@Action", "message": "missing @Action"},
            {"kind": "regex", "pattern": r"@EmbabelComponent", "message": "missing component"},
        ],
    },
    "E05": {"checks": {"compile": True, "reachability": True}},
    "E06": {
        "checks": {"compile": False, "reachability": False},
        "prose": [
            {"kind": "contains", "text": "CreditAssessment", "message": "must name goal type"},
            {"kind": "contains", "text": "missing", "message": "must mention missing action/capability"},
        ],
        "requires_extraction": False,
    },
    "E07": {"checks": {"compile": True, "reachability": True}, "input": INPUTS["E07"]},
    "E14": {
        "checks": {"compile": False},
        "prose": [{"kind": "contains", "text": "InvoiceId", "message": "name blocker"}],
        "requires_extraction": False,
    },
    "E19": {
        "checks": {"compile": False},
        "prose": [{"kind": "contains", "text": "OrderAction", "message": "mention steps"}],
        "requires_extraction": False,
    },
    "KB01": {
        "mode": "project_only",
        "checks": {"compile": True, "reachability": True},
        "input_from_fixture": True,
    },
}


def kb01_files() -> dict[str, str]:
    root = ROOT / "benchmark/fixtures/known-bad/KB01"
    files: dict[str, str] = {}
    for path in root.rglob("*.java"):
        rel = path.relative_to(root).as_posix()
        files[rel] = path.read_text(encoding="utf-8")
    return files


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for task_id, (prompt_id, prompt) in PROMPTS.items():
        meta = SPECS_META.get(task_id, {})
        spec = {
            "task_id": task_id,
            "prompt_id": prompt_id,
            "prompt": prompt,
            "checks": {**CHECKS_DEFAULT, **meta.get("checks", {})},
            "input_project": meta.get("input", INPUTS.get(task_id, {})),
            "structure_checks": meta.get("structure", []),
            "prose_checks": meta.get("prose", []),
            "requires_extraction": meta.get("requires_extraction", True),
        }
        if meta.get("checks", {}).get("reachability"):
            spec["reachability"] = {"initial_types": ["String"]}
        (OUT / f"{task_id}.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    kb = {
        "task_id": "KB01",
        "prompt_id": "embabel-kb01-known-bad-v1",
        "prompt": "n/a",
        "mode": "project_only",
        "checks": {"compile": True, "reachability": True, "test": False},
        "input_project": kb01_files(),
        "structure_checks": [],
        "prose_checks": [],
        "requires_extraction": False,
        "reachability": {"initial_types": ["String"]},
    }
    (OUT / "KB01.json").write_text(json.dumps(kb, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(PROMPTS)+1} specs to {OUT}")


if __name__ == "__main__":
    main()