#!/usr/bin/env python3
"""Minimal fenced stubs so score --tasks all runs unattended."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS = ROOT / "benchmark" / "specs"
OUT = ROOT / "benchmark" / "fixtures" / "scoring-stubs"

STUB_JAVA = """```java src/main/java/benchmark/stub/Stub.java
package benchmark.stub;

import com.embabel.agent.api.annotation.Action;
import com.embabel.agent.api.annotation.EmbabelComponent;

@EmbabelComponent
public class Stub {{
    @Action
    public String stub() {{
        return "stub";
    }}
}}
```"""

PROSE = {
    "E06": "CreditAssessment is unreachable because no action produces it; missing assess capability.",
    "E14": "PayInvoice is blocked until InvoiceId is available from LookupInvoice.",
    "E19": "Plan: OrderAction then ShipAction then @AchievesGoal FinishOrder.",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for spec_path in sorted(SPECS.glob("E*.json")):
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        tid = spec["task_id"]
        if spec.get("prose_checks"):
            (OUT / f"{tid}.md").write_text(PROSE.get(tid, tid + " explanation.\n"), encoding="utf-8")
        else:
            (OUT / f"{tid}.md").write_text(STUB_JAVA, encoding="utf-8")
    print("wrote stubs", len(list(OUT.glob("E*.md"))))


if __name__ == "__main__":
    main()