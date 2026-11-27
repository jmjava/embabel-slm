"""Practices named in the protocol, as checks.

The pre-registration page is the source of the area labels, primary contrast,
exploratory dose curve, admission rule names, and guide add-on. This module
refuses an item or a dose list that breaks those rules.
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


def prefix_sizes(prereg: dict) -> tuple[int, ...]:
    raw = prereg["statistics"]["example_doses"]["prefixes"]
    return tuple(int(size) for size in raw)


def exploratory_contrast_names(prereg: dict) -> tuple[str, ...]:
    """Return the ordered adjacent contrasts used for descriptive analysis."""
    names = tuple(prereg["statistics"]["exploratory_adjacent_contrasts"])
    prefixes = prefix_sizes(prereg)
    expected = tuple(
        f"prefix_{prefixes[index]}_minus_{prefixes[index - 1]}"
        for index in range(1, len(prefixes))
    )
    if names != expected:
        raise ValueError("exploratory contrasts must be the successive prefix doublings")
    return names


def confirmatory_contrast_name(prereg: dict) -> str:
    """Return the sole registered example-dose confirmatory contrast."""
    comparisons = prereg["statistics"]["confirmatory_comparisons"]
    if comparisons != {
        "prefix_16000_minus_500": "prefix_16000_minus_prefix_500"
    }:
        raise ValueError("the sole confirmatory dose contrast must be 16000 minus 500")
    return "prefix_16000_minus_500"


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
    if record.get("oracle_evidence_validated") is not True:
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


def lock_prefixes(prereg: dict) -> dict[str, object]:
    """The six nested sizes named in the combined-dose plan."""
    doses = prereg["statistics"]["example_doses"]
    prefixes = prefix_sizes(prereg)
    starts = tuple(int(size) for size in doses["starts"])
    multipliers = tuple(int(size) for size in doses["multipliers"])
    if prefixes != (500, 1000, 2000, 4000, 8000, 16000):
        raise ValueError("prefixes must be 500, 1000, 2000, 4000, 8000, 16000")
    if starts != (500, 1000, 2000) or multipliers != (1, 2, 4, 8):
        raise ValueError("starts must be 500, 1000, 2000 and multipliers 1, 2, 4, 8")
    if int(prereg["splits"]["holdout_min_tasks"]) != 742:
        raise ValueError("the combined holdout is 742 tasks")
    if prereg["splits"]["holdout_min_tasks_scope"] != "combined":
        raise ValueError("the holdout scope is the combined exam")
    return {
        "prefixes": list(prefixes),
        "starts": list(starts),
        "multipliers": list(multipliers),
        "holdout_min_tasks": 742,
    }


def assign_doses(ordered_ids: Sequence[str], prereg: dict) -> dict[str, list[str]]:
    """Every training size is a prefix of the one ordered list."""
    locked = lock_prefixes(prereg)
    full = int(locked["prefixes"][-1])
    if len(ordered_ids) < full:
        raise ValueError("the authored list is shorter than the largest prefix")
    if len(set(ordered_ids)) != len(ordered_ids):
        raise ValueError("an example id appears twice")
    chosen = list(ordered_ids[:full])
    return {str(size): chosen[:size] for size in locked["prefixes"]}


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


def descriptive_exploratory_steps(
    p_by_test: Mapping[str, float],
    prereg: dict,
) -> dict[str, object]:
    """Holm-adjust adjacent-dose p-values for descriptive reporting only."""
    names = exploratory_contrast_names(prereg)
    missing = [name for name in names if name not in p_by_test]
    extra = [name for name in p_by_test if name not in names]
    if missing or extra:
        raise ValueError(
            f"p-values must cover the five exploratory contrasts; "
            f"missing={missing} extra={extra}"
        )
    alpha = prereg["statistics"]["alpha_confirmatory"]
    adjusted = holm_bonferroni([float(p_by_test[name]) for name in names])
    return {
        "confirmatory": False,
        "adjustment": "holm_descriptive",
        "steps": {
            name: {
                "raw_p": float(p_by_test[name]),
                "adjusted_p": adjusted[index],
                "descriptive_rejects": adjusted[index] <= alpha,
            }
            for index, name in enumerate(names)
        },
    }


def decide_confirmatory_contrast(
    p_by_test: Mapping[str, float],
    prereg: dict,
) -> dict[str, object]:
    """Apply the registered one-sided alpha to the sole primary contrast."""
    name = confirmatory_contrast_name(prereg)
    if set(p_by_test) != {name}:
        raise ValueError(f"p-values must contain exactly the primary contrast {name}")
    p_value = float(p_by_test[name])
    alpha = float(prereg["statistics"]["alpha_confirmatory"])
    return {
        "confirmatory": True,
        "contrast": name,
        "p_value": p_value,
        "alpha": alpha,
        "rejects": p_value <= alpha,
    }


def guide_practice_holds(prereg: dict) -> bool:
    """The guide is an add-on on a model that already has the adapter."""
    guide = prereg["statistics"]["guide"]
    configs = prereg["configs"]
    return (
        guide["when"] == "after_the_adapter_is_trained"
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
    """Product retrieval attaches only after the adapter exists."""
    return adapter_trained is True
