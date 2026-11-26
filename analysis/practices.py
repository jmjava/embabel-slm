"""Practices named in the protocol, as checks.

The pre-registration page is the source of the labels, the 22 test names,
the admission rule names, and the guide add-on. This module refuses an item
or a dose that breaks those rules, and it reports each area on its own.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Sequence

from analysis.holm import holm_bonferroni
from analysis.mcnemar import exact_mcnemar_p_value_one_sided

ROOT = Path(__file__).resolve().parent.parent
PREREG_PATH = ROOT / "docs" / "protocol" / "preregistration.md"
START = "<!-- prereg:start -->"
END = "<!-- prereg:end -->"


def load_prereg(path: Path | None = None) -> dict:
    """Read the locked JSON block from the pre-registration page."""
    text = (path or PREREG_PATH).read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END, start)
    block = text[start:end]
    return json.loads(block[block.index("{") : block.rindex("}") + 1])


def areas(prereg: dict) -> dict[str, tuple[str, ...]]:
    raw = prereg["statistics"]["areas"]
    return {domain: tuple(labels) for domain, labels in raw.items()}


def holm_test_names(prereg: dict) -> tuple[str, ...]:
    names = tuple(prereg["statistics"]["holm_tests"])
    expected = []
    for domain, labels in areas(prereg).items():
        for label in labels:
            expected.append(f"{domain}_{label}_H1")
            expected.append(f"{domain}_{label}_H2")
    if names != tuple(expected):
        raise ValueError("holm_tests must be H1 then H2 for every pre-registered area")
    return names


def _area_allowed(prereg: dict, domain: object, area: object) -> bool:
    labels = areas(prereg)
    return isinstance(domain, str) and isinstance(area, str) and area in labels.get(domain, ())


def admit_example(record: Mapping[str, object], prereg: dict) -> list[str]:
    """Return the protocol rule names this example breaks. Empty means admitted."""
    reasons: list[str] = []
    domain = record.get("domain")
    area = record.get("area")
    if not _area_allowed(prereg, domain, area):
        reasons.append("slice_label_from_pre_registered_set")
    listed = record.get("areas")
    if listed is not None and listed != [area]:
        reasons.append("authored_for_exactly_one_area")
    if record.get("executable_oracle") is not True:
        reasons.append("compiler_or_executable_oracle")
    source = record.get("source_file")
    pin = record.get("source_pin")
    if not isinstance(source, str) or not source.strip() or not isinstance(pin, str) or not pin.strip():
        reasons.append("source_file_and_pin_recorded")
    if record.get("near_duplicate_of_holdout") is True:
        reasons.append("not_near_duplicate_of_holdout")
    if record.get("random_pool") is True:
        reasons.append("random_pool_rejected")
    return reasons


def admit_holdout(
    record: Mapping[str, object],
    prereg: dict,
    *,
    manifest_hashed: bool,
) -> list[str]:
    """Return the protocol rule names this holdout task breaks."""
    reasons: list[str] = []
    if not _area_allowed(prereg, record.get("domain"), record.get("area")):
        reasons.append("slice_label_from_pre_registered_set")
    if record.get("label_chosen_after_model_output") is True:
        reasons.append("slice_label_before_any_model_output")
    if record.get("executable_oracle") is not True:
        reasons.append("executable_oracle_required")
    if not manifest_hashed:
        reasons.append("manifest_hash_before_first_score")
    if record.get("edited_after_first_model_output") is True:
        reasons.append("no_edit_after_first_model_output")
    return reasons


def lock_counts(middle: int, full: int) -> dict[str, int | bool]:
    """One middle count and one full count, shared by every area."""
    if isinstance(middle, bool) or isinstance(full, bool):
        raise TypeError("counts must be integers")
    if not isinstance(middle, int) or not isinstance(full, int):
        raise TypeError("counts must be integers")
    if middle < 1:
        raise ValueError("middle count must be at least 1")
    if full < 2 * middle:
        raise ValueError("full count must be at least twice the middle count")
    return {"middle": middle, "full": full, "same_pair_for_every_area": True}


def assign_doses(ordered_ids: Sequence[str], middle: int, full: int) -> dict[str, list[str]]:
    """The middle dose is the pre-fixed prefix of the full list."""
    lock_counts(middle, full)
    if len(ordered_ids) < full:
        raise ValueError("the authored list is shorter than the full count")
    if len(set(ordered_ids)) != len(ordered_ids):
        raise ValueError("an example id appears twice in one area")
    chosen = list(ordered_ids[:full])
    return {"middle": chosen[:middle], "full": chosen}


def discordant_counts(previous: Sequence[bool], later: Sequence[bool]) -> tuple[int, int]:
    """Return (b, c): b favors the previous dose, c favors the later dose."""
    if len(previous) != len(later):
        raise ValueError("the two doses must be scored on the same tasks")
    b = 0
    c = 0
    for earlier, current in zip(previous, later):
        if earlier and not current:
            b += 1
        elif current and not earlier:
            c += 1
    return b, c


def one_sided_step_p(previous: Sequence[bool], later: Sequence[bool]) -> float:
    b, c = discordant_counts(previous, later)
    return exact_mcnemar_p_value_one_sided(b, c)


def decide_areas(p_by_test: Mapping[str, float], prereg: dict) -> dict[str, object]:
    """An area is proved when both of its Holm-adjusted tests reject.

    The study does not require every area to be proved.
    """
    names = holm_test_names(prereg)
    missing = [name for name in names if name not in p_by_test]
    extra = [name for name in p_by_test if name not in names]
    if missing or extra:
        raise ValueError(f"p-values must cover the 22 named tests; missing={missing} extra={extra}")
    alpha = prereg["statistics"]["alpha_confirmatory"]
    adjusted = holm_bonferroni([float(p_by_test[name]) for name in names])
    rejected = {name: adjusted[i] < alpha for i, name in enumerate(names)}
    rows: dict[str, dict[str, bool]] = {}
    for domain, labels in areas(prereg).items():
        for label in labels:
            h1 = f"{domain}_{label}_H1"
            h2 = f"{domain}_{label}_H2"
            rows[f"{domain}/{label}"] = {
                "H1_rejects": rejected[h1],
                "H2_rejects": rejected[h2],
                "proved": rejected[h1] and rejected[h2],
            }
    return {
        "areas": rows,
        "proved_count": sum(1 for row in rows.values() if row["proved"]),
        "area_count": len(rows),
        "requires_every_area": False,
    }


def guide_practice_holds(prereg: dict) -> bool:
    """The guide is an add-on on a model that already has the adapter."""
    guide = prereg["statistics"]["guide"]
    configs = prereg["configs"]
    return (
        guide["when"] == "after_the_area_adapter_is_trained"
        and guide["what_it_does"] == "retrieves_pages_into_the_prompt"
        and guide["what_lora_does"] == "learns_the_admitted_examples"
        and guide["product_config"] == "D"
        and guide["reference_config_before_training"] == "B"
        and guide["fills_an_example_dose"] is False
        and configs["D"] == {"retrieval": True, "lora": True}
        and configs["B"] == {"retrieval": True, "lora": False}
        and configs["C"] == {"retrieval": False, "lora": True}
    )


def guide_may_attach(adapter_trained: bool) -> bool:
    """Product retrieval attaches only after the area adapter exists."""
    return adapter_trained is True
