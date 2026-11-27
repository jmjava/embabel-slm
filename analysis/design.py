"""Study design checks: holdout allocation, training order, provenance."""

from __future__ import annotations

import random
import re
from typing import Mapping, Sequence

from analysis.practices import areas, load_prereg, prefix_sizes

StratumKey = tuple[str, str]


def training_seed_plan(prereg: dict) -> dict[str, object]:
    """Validate registered training seeds and primary/replication roles."""
    stats = prereg["statistics"]
    identities = [int(seed) for seed in stats["training_seed_identities"]]
    expected = [20260227, 20260228, 20260229]
    if identities != expected:
        raise ValueError(f"training seeds must be {expected}")
    if int(stats["training_seeds_matched_count"]) != 3:
        raise ValueError("training_seeds_matched_count must be 3")
    primary = int(stats["primary_confirmatory_training_seed"])
    if primary != 20260227:
        raise ValueError("primary confirmatory training seed must be 20260227")
    replications = [int(seed) for seed in stats["mandatory_replication_training_seeds"]]
    if replications != [20260228, 20260229]:
        raise ValueError("replication seeds must be [20260228, 20260229]")
    if stats.get("pooled_task_by_training_seed_summaries_exploratory_only") is not True:
        raise ValueError("pooled task×seed summaries are exploratory only")
    return {
        "count": 3,
        "identities": expected,
        "primary": primary,
        "replications": replications,
        "pooled_exploratory_only": True,
    }


def holdout_domain_counts(prereg: dict) -> dict[str, int]:
    """Validate 371 Embabel + 371 Drivine holdout tasks."""
    raw = prereg["splits"]["holdout_domain_tasks"]
    counts = {str(domain): int(raw[domain]) for domain in ("embabel", "drivine")}
    if counts != {"embabel": 371, "drivine": 371}:
        raise ValueError("holdout domain tasks must be embabel=371 and drivine=371")
    total = sum(counts.values())
    if int(prereg["splits"]["holdout_min_tasks"]) != total or total != 742:
        raise ValueError("combined holdout must be 742 tasks")
    return counts


def hamilton_largest_remainder(
    weights: Mapping[str, int],
    total: int,
    *,
    minimum: Mapping[str, int] | None = None,
    capacity: Mapping[str, int] | None = None,
) -> dict[str, int]:
    """Apportion ``total`` seats by Hamilton with lexical tie-breaking.

    ``weights`` must be nonnegative integers summing to > 0. Optional per-key
    minimums and capacities are enforced; shortfall is redistributed among keys
    that still have capacity using the same rule.
    """
    if total < 0:
        raise ValueError("total must be nonnegative")
    keys = sorted(weights)
    min_map = {key: 0 for key in keys}
    if minimum is not None:
        for key, value in minimum.items():
            if key not in weights:
                raise ValueError(f"minimum for unknown stratum {key}")
            if value < 0:
                raise ValueError("minimums must be nonnegative")
            min_map[key] = int(value)
    cap_map: dict[str, int | None] = {key: None for key in keys}
    if capacity is not None:
        for key, value in capacity.items():
            if key not in weights:
                raise ValueError(f"capacity for unknown stratum {key}")
            if value < 0:
                raise ValueError("capacities must be nonnegative")
            cap_map[key] = int(value)
    for key in keys:
        weight = int(weights[key])
        if weight < 0:
            raise ValueError("weights must be nonnegative")
        cap = cap_map[key]
        if cap is not None and min_map[key] > cap:
            raise ValueError(f"minimum exceeds capacity for {key}")
    min_sum = sum(min_map.values())
    if min_sum > total:
        raise ValueError("total is insufficient for per-stratum minimums")
    if not keys:
        if total != 0:
            raise ValueError("cannot apportion to zero strata")
        return {}
    weight_sum = sum(int(weights[key]) for key in keys)
    if weight_sum <= 0:
        raise ValueError("weight sum must be positive")

    def _hamilton_round(
        alloc: dict[str, int],
        pool_keys: list[str],
        pool_weights: dict[str, int],
        seats: int,
    ) -> dict[str, int]:
        if seats <= 0 or not pool_keys:
            return dict(alloc)
        w_sum = sum(pool_weights[key] for key in pool_keys)
        if w_sum <= 0:
            raise ValueError("no positive weight among eligible strata")
        quotas = {key: pool_weights[key] * seats / w_sum for key in pool_keys}
        floors = {key: int(quotas[key]) for key in pool_keys}
        assigned = sum(floors.values())
        remainder = seats - assigned
        fractional = sorted(
            pool_keys,
            key=lambda key: (-(quotas[key] - floors[key]), key),
        )
        out = dict(alloc)
        for key in pool_keys:
            out[key] += floors[key]
        for index in range(remainder):
            out[fractional[index % len(fractional)]] += 1
        return out

    def _apply_caps(counts: dict[str, int]) -> tuple[dict[str, int], int]:
        trimmed = dict(counts)
        surplus = 0
        for key in keys:
            cap = cap_map[key]
            if cap is not None and trimmed[key] > cap:
                surplus += trimmed[key] - cap
                trimmed[key] = cap
        return trimmed, surplus

    counts = dict(min_map)
    remaining = total - min_sum
    counts = _hamilton_round(counts, keys, {key: int(weights[key]) for key in keys}, remaining)
    for _ in range(len(keys) + 5):
        counts, _overflow = _apply_caps(counts)
        need = total - sum(counts.values())
        if need == 0:
            break
        if need < 0:
            raise ValueError("allocation exceeds requested total under capacity")
        eligible = [
            key
            for key in keys
            if cap_map[key] is None or counts[key] < cap_map[key]
        ]
        if not eligible:
            raise ValueError("insufficient capacity to satisfy allocation total")
        spare = {
            key: (cap_map[key] - counts[key] if cap_map[key] is not None else need)
            for key in eligible
        }
        pool = {key: value for key, value in spare.items() if value > 0}
        if sum(pool.values()) < need:
            raise ValueError("insufficient capacity to satisfy allocation total")
        counts = _hamilton_round(counts, sorted(pool), pool, need)
    else:
        raise ValueError("capacity redistribution did not converge")
    if sum(counts.values()) != total:
        raise ValueError("allocation does not match requested total")
    for key in keys:
        cap = cap_map[key]
        if cap is not None and counts[key] > cap:
            raise ValueError(f"allocation exceeds capacity for {key}")
        if counts[key] < min_map[key]:
            raise ValueError(f"allocation below minimum for {key}")
    return counts


def _stratum_label(domain: str, area: str) -> str:
    return f"{domain}|{area}"


def allocate_holdout_areas(
    clean_counts_by_domain_area: Mapping[tuple[str, str], int],
    prereg: dict,
) -> dict[tuple[str, str], int]:
    """Hamilton holdout counts per domain; training counts are weights only.

    Holdout tasks are authored independently of training source supply. Clean
    admitted training-pool counts set area weights, not capacities or subtractions.
    """
    holdout_domain_counts(prereg)
    minimum = int(
        prereg["splits"]["holdout_area_allocation"]["minimum_tasks_per_registered_area_per_domain"]
    )
    per_domain = int(prereg["splits"]["embabel"]["holdout_tasks"])
    labels = areas(prereg)
    allocation: dict[tuple[str, str], int] = {}
    for domain, domain_areas in sorted(labels.items()):
        weight_keys = [_stratum_label(domain, area) for area in domain_areas]
        weights: dict[str, int] = {}
        for area in domain_areas:
            key = (domain, area)
            if key not in clean_counts_by_domain_area:
                raise ValueError(f"missing clean count for {domain}/{area}")
            weight = int(clean_counts_by_domain_area[key])
            if weight < 0:
                raise ValueError(f"negative clean count for {domain}/{area}")
            label = _stratum_label(domain, area)
            weights[label] = weight
        weight_sum = sum(weights.values())
        if weight_sum <= 0:
            raise ValueError(f"nonpositive weight sum for {domain}")
        mins = {label: minimum for label in weight_keys}
        if per_domain < minimum * len(domain_areas):
            raise ValueError(f"domain total too small for minimums in {domain}")
        domain_alloc = hamilton_largest_remainder(
            weights,
            per_domain,
            minimum=mins,
        )
        for area in domain_areas:
            label = _stratum_label(domain, area)
            allocation[(domain, area)] = domain_alloc[label]
    if sum(allocation.values()) != 742:
        raise ValueError("holdout allocation must total 742 tasks")
    return allocation


_HEX64 = re.compile(r"^[a-f0-9]{64}$")


def validate_holdout_tasks(
    holdout_rows: Sequence[Mapping[str, object]],
    *,
    allocation: Mapping[tuple[str, str], int] | None = None,
    prereg: dict | None = None,
) -> dict[str, object]:
    """Validate independently authored holdout tasks and per-area allocation."""
    prereg = prereg or load_prereg()
    holdout_domain_counts(prereg)
    registered = areas(prereg)
    if len(holdout_rows) != 742:
        raise ValueError(f"holdout must have exactly 742 tasks, saw {len(holdout_rows)}")
    seen_ids: set[str] = set()
    domain_counts: dict[str, int] = {"embabel": 0, "drivine": 0}
    area_counts: dict[tuple[str, str], int] = {}
    for index, row in enumerate(holdout_rows):
        prefix = f"holdout[{index}]"
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not _HEX64.fullmatch(task_id.strip()):
            raise ValueError(f"{prefix}: task_id must be 64 hex chars")
        task_id = task_id.strip()
        if task_id in seen_ids:
            raise ValueError(f"{prefix}: duplicate task_id {task_id}")
        seen_ids.add(task_id)
        domain = row.get("domain")
        area = row.get("area")
        if not isinstance(domain, str) or not isinstance(area, str):
            raise ValueError(f"{prefix}: domain and area required")
        if area not in registered.get(domain, ()):
            raise ValueError(f"{prefix}: unregistered area {domain}/{area}")
        if row.get("executable_oracle") is not True:
            raise ValueError(f"{prefix}: executable_oracle must be true")
        prompt = row.get("prompt")
        code = row.get("code")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"{prefix}: missing prompt")
        if not isinstance(code, str) or not code.strip():
            raise ValueError(f"{prefix}: missing code")
        groups = row.get("provenance_groups")
        if not isinstance(groups, list) or not groups:
            raise ValueError(f"{prefix}: provenance_groups required")
        if any(not isinstance(group, str) or not group.strip() for group in groups):
            raise ValueError(f"{prefix}: empty provenance group")
        if any(group.strip().startswith("repository:") for group in groups):
            raise ValueError(f"{prefix}: repository-wide provenance group forbidden")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1
        key = (domain, area)
        area_counts[key] = area_counts.get(key, 0) + 1
    if domain_counts != {"embabel": 371, "drivine": 371}:
        raise ValueError(f"holdout domain counts must be 371 each, saw {domain_counts}")
    if allocation is not None:
        for key, expected in sorted(allocation.items()):
            realized = area_counts.get(key, 0)
            if realized != expected:
                raise ValueError(
                    f"holdout area {key[0]}/{key[1]} expected {expected} tasks, saw {realized}"
                )
    return {
        "tasks": len(seen_ids),
        "domain_counts": domain_counts,
        "area_counts": {f"{dom}/{ar}": area_counts[(dom, ar)] for dom, ar in sorted(area_counts)},
        "allocation_verified": allocation is not None,
    }


def _stratum_seed(order_seed: int, domain: str, area: str) -> int:
    token = f"{order_seed}:{domain}:{area}"
    return zlib_crc32(token) ^ order_seed


def zlib_crc32(text: str) -> int:
    import zlib

    return zlib.crc32(text.encode("utf-8")) & 0xFFFFFFFF


def _record_stratum(record: Mapping[str, object]) -> StratumKey:
    domain = record.get("domain")
    area = record.get("area")
    if not isinstance(domain, str) or not isinstance(area, str):
        raise ValueError("record domain and area must be strings")
    return domain, area


def seeded_stratified_order(
    records: Sequence[Mapping[str, object]],
    prereg: dict,
) -> tuple[list[str], dict[str, object]]:
    """Build the training ordered list with seeded per-stratum shuffles."""
    doses = prereg["statistics"]["example_doses"]
    order_seed = int(doses["order_seed"])
    prefixes = prefix_sizes(prereg)
    largest = prefixes[-1]
    registered = areas(prereg)
    seen_ids: set[str] = set()
    by_stratum: dict[StratumKey, list[Mapping[str, object]]] = {}
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id.strip():
            raise ValueError("each record needs a nonempty string id")
        if record_id in seen_ids:
            raise ValueError(f"duplicate record id {record_id}")
        seen_ids.add(record_id)
        domain, area = _record_stratum(record)
        if area not in registered.get(domain, ()):
            raise ValueError(f"unregistered stratum {domain}/{area}")
        by_stratum.setdefault((domain, area), []).append(record)
    total = sum(len(bucket) for bucket in by_stratum.values())
    if total < largest:
        raise ValueError(f"need at least {largest} records for the largest prefix")
    shuffled: dict[StratumKey, list[str]] = {}
    weights: dict[StratumKey, int] = {}
    for key in sorted(by_stratum):
        domain, area = key
        bucket = sorted(by_stratum[key], key=lambda row: str(row["id"]))
        ids = [str(row["id"]) for row in bucket]
        rng = random.Random(_stratum_seed(order_seed, domain, area))
        rng.shuffle(ids)
        shuffled[key] = ids
        weights[key] = len(ids)
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("empty training pool")

    queues = {key: list(ids) for key, ids in shuffled.items()}
    id_to_stratum = {
        record_id: key for key, ids in shuffled.items() for record_id in ids
    }
    picked: dict[StratumKey, int] = {key: 0 for key in queues}
    ordered: list[str] = []
    while sum(len(queue) for queue in queues.values()) > 0:
        active = [key for key in sorted(queues) if queues[key]]
        if not active:
            break
        remaining_supply = {key: len(queues[key]) for key in active}
        active_weight = sum(remaining_supply[key] for key in active)
        position = len(ordered) + 1
        best = min(
            active,
            key=lambda key: (
                -(remaining_supply[key] * position / active_weight - picked[key]),
                key[0],
                key[1],
            ),
        )
        ordered.append(queues[best].pop(0))
        picked[best] += 1

    prefix_report: dict[str, object] = {}
    for prefix in prefixes:
        slice_ids = ordered[:prefix]
        realized = {key: 0 for key in weights}
        for record_id in slice_ids:
            realized[id_to_stratum[record_id]] += 1
        expected_counts = hamilton_largest_remainder(
            {_stratum_label(*key): weights[key] for key in sorted(weights)},
            prefix,
        )
        strata_report = {}
        for key in sorted(weights):
            domain, area = key
            label = _stratum_label(domain, area)
            exp = expected_counts[label]
            real = realized[key]
            strata_report[label] = {
                "expected_count": exp,
                "realized_count": real,
                "expected_share": exp / prefix,
                "realized_share": real / prefix,
            }
        prefix_report[str(prefix)] = {"strata": strata_report}

    report = {
        "order_seed": order_seed,
        "prefixes": list(prefixes),
        "pool_total": weight_sum,
        "ordered_length": len(ordered),
        "prefix_reports": prefix_report,
    }
    return ordered, report


def validate_provenance_disjoint(
    train_records: Sequence[Mapping[str, object]],
    holdout_records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Ensure provenance groups do not cross training and holdout."""
    def _collect(records: Sequence[Mapping[str, object]], split: str) -> tuple[set[str], dict[str, set[str]]]:
        ids: set[str] = set()
        provenance_index: dict[str, set[str]] = {}
        for record in records:
            record_id = record.get("id")
            if not isinstance(record_id, str) or not record_id.strip():
                raise ValueError(f"{split} record missing id")
            if record_id in ids:
                raise ValueError(f"duplicate {split} id {record_id}")
            ids.add(record_id)
            groups = record.get("provenance_groups")
            if not isinstance(groups, list) or not groups:
                raise ValueError(f"{split} record {record_id} missing provenance_groups")
            normalized = []
            for group in groups:
                if not isinstance(group, str) or not group.strip():
                    raise ValueError(f"{split} record {record_id} has empty provenance group")
                normalized.append(group.strip())
            for group in normalized:
                provenance_index.setdefault(group, set()).add(record_id)
        return ids, provenance_index

    train_ids, train_groups = _collect(train_records, "train")
    holdout_ids, holdout_groups = _collect(holdout_records, "holdout")
    overlap_ids = train_ids & holdout_ids
    if overlap_ids:
        raise ValueError("task id appears in both training and holdout")
    crossed = sorted(set(train_groups) & set(holdout_groups))
    if crossed:
        raise ValueError(f"provenance groups span train and holdout: {crossed}")
    return {
        "train_records": len(train_ids),
        "holdout_records": len(holdout_ids),
        "provenance_groups_train": len(train_groups),
        "provenance_groups_holdout": len(holdout_groups),
    }


def align_binary_scores(
    left_rows: Sequence[Mapping[str, object]],
    right_rows: Sequence[Mapping[str, object]],
) -> tuple[list[str], list[bool], list[bool]]:
    """Align paired boolean outcomes on sorted task_id."""
    def _index(rows: Sequence[Mapping[str, object]], label: str) -> dict[str, bool]:
        indexed: dict[str, bool] = {}
        for row in rows:
            task_id = row.get("task_id")
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError(f"{label} row missing task_id")
            if task_id in indexed:
                raise ValueError(f"duplicate {label} task_id {task_id}")
            passed = row.get("passed")
            if not isinstance(passed, bool):
                raise ValueError(f"{label} row {task_id} passed must be bool")
            indexed[task_id] = passed
        return indexed

    left = _index(left_rows, "left")
    right = _index(right_rows, "right")
    left_ids = set(left)
    right_ids = set(right)
    if left_ids != right_ids:
        missing = sorted(left_ids - right_ids)
        extra = sorted(right_ids - left_ids)
        raise ValueError(f"task_id mismatch missing={missing[:5]} extra={extra[:5]}")
    ids = sorted(left_ids)
    return ids, [left[task_id] for task_id in ids], [right[task_id] for task_id in ids]