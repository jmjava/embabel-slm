"""Deterministic MinHash / LSH near-duplicate detection (stdlib only).

LSH is candidate generation only. A pair is reported as a near-duplicate only
when exact Jaccard similarity on token shingles is >= the threshold (default 0.8).

MinHash configuration (fixed, pre-registered):
  - 128 independent hash functions, seeded via SHA-256 (not ``hash()``).
  - LSH: 32 bands × 4 rows/band (= 128), tuned for high recall at 0.8.
  - Approximate candidate recall at Jaccard s: P = 1 - (1 - s**4)**32
    (≈0.99999995 at s=0.8; ≈0.99985 at s=0.7). LSH remains probabilistic;
    use ``exhaustive=True`` when complete candidate recall is required.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, FrozenSet, Iterable, Mapping, Sequence

from analysis.jsonl_io import iter_physical_jsonl_lines

SHINGLE_SIZE = 5
MINHASH_NUM_PERM = 128
LSH_BANDS = 32
LSH_ROWS_PER_BAND = 4
JACCARD_THRESHOLD_DEFAULT = 0.8
EXHAUSTIVE_PAIRWISE_MAX_RECORDS = 48

# Large prime for universal hashing (2**61 - 1).
_HASH_PRIME = (1 << 61) - 1
_EMPTY_SIGNATURE_FILL = (1 << 64) - 1

_TOKEN_PATTERN = re.compile(
    r"[\w]+|[-+*/=<>!&|^~%@#.;:,\[\]{}()'\"\\]+",
    re.UNICODE,
)

_PERMUTATION_SEED = b"embabel-slm-minhash-v1"


class CrossSplitNearDuplicateError(ValueError):
    """Raised when train/holdout near-duplicates exist at or above threshold."""

    def __init__(self, message: str, evidence: Sequence[Mapping[str, Any]]) -> None:
        super().__init__(message)
        self.evidence = list(evidence)


@dataclass(frozen=True)
class DedupRecord:
    record_id: str
    prompt: str
    code: str
    split: str


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _perm_coefficients() -> list[tuple[int, int]]:
    coeffs: list[tuple[int, int]] = []
    for index in range(MINHASH_NUM_PERM):
        digest = hashlib.sha256(_PERMUTATION_SEED + index.to_bytes(4, "big")).digest()
        a = int.from_bytes(digest[:16], "big") % _HASH_PRIME or 1
        b = int.from_bytes(digest[16:32], "big") % _HASH_PRIME
        coeffs.append((a, b))
    return coeffs


_PERM_COEFFICIENTS = _perm_coefficients()


def _extract_tokens(text: str) -> list[str]:
    collapsed = re.sub(r"\s+", " ", text.strip())
    if not collapsed:
        return []
    return _TOKEN_PATTERN.findall(collapsed)


def normalize_prompt_and_code(prompt: str, code: str) -> str:
    """NFKC, lowercase, whitespace/line-end norm; space-joined operator/word tokens."""
    if not isinstance(prompt, str) or not isinstance(code, str):
        raise TypeError("prompt and code must be strings")
    tokens: list[str] = []
    for part in (prompt, code):
        normalized = unicodedata.normalize("NFKC", part).lower()
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        tokens.extend(_extract_tokens(normalized))
    return " ".join(tokens)


def content_hash_normalized(text: str) -> str:
    return _sha256_hex(text)


def token_shingles(text: str, size: int = SHINGLE_SIZE) -> FrozenSet[str]:
    """Deterministic shingle set from whitespace tokens in *text*."""
    if size < 1:
        raise ValueError("shingle size must be >= 1")
    tokens = text.split() if text else []
    count = len(tokens)
    if count == 0:
        return frozenset()
    if count < size:
        return frozenset([" ".join(tokens)])
    shingles = {" ".join(tokens[index : index + size]) for index in range(count - size + 1)}
    return frozenset(shingles)


def exact_jaccard(a: FrozenSet[str], b: FrozenSet[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union


def _shingle_int(shingle: str) -> int:
    digest = hashlib.sha256(shingle.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def minhash_signature(shingles: FrozenSet[str]) -> tuple[int, ...]:
    if not shingles:
        return tuple(_EMPTY_SIGNATURE_FILL for _ in range(MINHASH_NUM_PERM))
    ints = [_shingle_int(s) for s in shingles]
    signature: list[int] = []
    for a_coef, b_coef in _PERM_COEFFICIENTS:
        minimum = min((a_coef * value + b_coef) % _HASH_PRIME for value in ints)
        signature.append(minimum)
    return tuple(signature)


def lsh_band_keys(signature: Sequence[int]) -> tuple[tuple[int, ...], ...]:
    if len(signature) != MINHASH_NUM_PERM:
        raise ValueError(f"signature must have length {MINHASH_NUM_PERM}")
    keys: list[tuple[int, ...]] = []
    for band in range(LSH_BANDS):
        start = band * LSH_ROWS_PER_BAND
        band_slice = signature[start : start + LSH_ROWS_PER_BAND]
        keys.append(tuple(band_slice))
    return tuple(keys)


def approximate_lsh_candidate_recall(jaccard: float) -> float:
    """Probability a pair with given Jaccard lands in at least one LSH bucket."""
    if jaccard <= 0.0:
        return 0.0
    if jaccard >= 1.0:
        return 1.0
    band_hit = jaccard**LSH_ROWS_PER_BAND
    return 1.0 - (1.0 - band_hit) ** LSH_BANDS


def lsh_candidate_pairs(
    signatures: Sequence[tuple[int, ...]],
    *,
    include_same_index: bool = False,
) -> set[tuple[int, int]]:
    """Return index pairs (i, j) with i < j that share an LSH band bucket."""
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = {}
    for index, signature in enumerate(signatures):
        for band_index, key in enumerate(lsh_band_keys(signature)):
            bucket = (band_index, key)
            buckets.setdefault(bucket, []).append(index)
    pairs: set[tuple[int, int]] = set()
    for members in buckets.values():
        if len(members) < 2:
            continue
        members_sorted = sorted(members)
        for left in range(len(members_sorted)):
            for right in range(left + 1, len(members_sorted)):
                i, j = members_sorted[left], members_sorted[right]
                if not include_same_index and i == j:
                    continue
                pairs.add((i, j))
    return pairs


def _pairwise_indices(n: int) -> Iterable[tuple[int, int]]:
    for i in range(n):
        for j in range(i + 1, n):
            yield i, j


def _validate_split(split: str, line: int) -> str:
    if split not in ("train", "holdout"):
        raise ValueError(f"line {line}: split must be 'train' or 'holdout'")
    return split


def parse_record(raw: object, line: int) -> DedupRecord:
    if not isinstance(raw, dict):
        raise ValueError(f"line {line}: record must be a JSON object")
    required = ("id", "prompt", "code", "split")
    for key in required:
        if key not in raw:
            raise ValueError(f"line {line}: missing field {key}")
    extra = set(raw) - set(required)
    if extra:
        raise ValueError(f"line {line}: unexpected fields {sorted(extra)}")
    record_id = raw["id"]
    prompt = raw["prompt"]
    code = raw["code"]
    split = raw["split"]
    if not isinstance(record_id, str) or not record_id.strip():
        raise ValueError(f"line {line}: invalid id")
    if not isinstance(prompt, str) or not isinstance(code, str):
        raise ValueError(f"line {line}: prompt and code must be strings")
    if not isinstance(split, str):
        raise ValueError(f"line {line}: split must be a string")
    return DedupRecord(
        record_id=record_id.strip(),
        prompt=prompt,
        code=code,
        split=_validate_split(split.strip(), line),
    )


def load_records_jsonl(path: Path) -> list[DedupRecord]:
    records: list[DedupRecord] = []
    seen_ids: set[str] = set()
    for line_number, stripped in iter_physical_jsonl_lines(path):
        raw = json.loads(stripped)
        record = parse_record(raw, line_number)
        if record.record_id in seen_ids:
            raise ValueError(f"line {line_number}: duplicate id {record.record_id}")
        seen_ids.add(record.record_id)
        records.append(record)
    if not records:
        raise ValueError("empty records file")
    return records


def records_from_mapping(rows: Sequence[Mapping[str, Any]]) -> list[DedupRecord]:
    """Parse in-memory rows (same schema as JSONL)."""
    out: list[DedupRecord] = []
    seen: set[str] = set()
    for index, raw in enumerate(rows, start=1):
        record = parse_record(raw, index)
        if record.record_id in seen:
            raise ValueError(f"line {index}: duplicate id {record.record_id}")
        seen.add(record.record_id)
        out.append(record)
    return out


def _build_entry(record: DedupRecord) -> dict[str, Any]:
    normalized = normalize_prompt_and_code(record.prompt, record.code)
    shingles = token_shingles(normalized, size=SHINGLE_SIZE)
    return {
        "record": record,
        "normalized": normalized,
        "content_hash": content_hash_normalized(normalized),
        "shingles": shingles,
        "signature": minhash_signature(shingles),
    }


def find_near_duplicate_pairs(
    records: Sequence[DedupRecord],
    threshold: float = JACCARD_THRESHOLD_DEFAULT,
    *,
    exhaustive: bool = False,
    exhaustive_max_records: int = EXHAUSTIVE_PAIRWISE_MAX_RECORDS,
) -> list[dict[str, Any]]:
    """Return sorted near-duplicate evidence (exact Jaccard >= threshold)."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    seen_ids: set[str] = set()
    for record in records:
        if record.record_id in seen_ids:
            raise ValueError(f"duplicate id {record.record_id}")
        seen_ids.add(record.record_id)
    entries = [_build_entry(record) for record in records]
    n = len(entries)
    use_exhaustive = exhaustive or n <= exhaustive_max_records
    if use_exhaustive:
        candidate_pairs = set(_pairwise_indices(n))
    else:
        signatures = [entry["signature"] for entry in entries]
        candidate_pairs = lsh_candidate_pairs(signatures)

    evidence: list[dict[str, Any]] = []
    for i, j in sorted(candidate_pairs):
        score = exact_jaccard(entries[i]["shingles"], entries[j]["shingles"])
        if score + 1e-15 < threshold:
            continue
        id_a = entries[i]["record"].record_id
        id_b = entries[j]["record"].record_id
        if id_b < id_a:
            i, j = j, i
            id_a, id_b = id_b, id_a
        evidence.append(
            {
                "id_a": id_a,
                "id_b": id_b,
                "split_a": entries[i]["record"].split,
                "split_b": entries[j]["record"].split,
                "exact_jaccard": score,
                "content_hash_a": entries[i]["content_hash"],
                "content_hash_b": entries[j]["content_hash"],
            }
        )
    evidence.sort(key=lambda row: (row["id_a"], row["id_b"]))
    return evidence


def cross_split_pairs(
    pairs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(pair)
        for pair in pairs
        if pair["split_a"] != pair["split_b"]
    ]


def validate_no_cross_split_near_duplicates(
    train_records: Sequence[DedupRecord],
    holdout_records: Sequence[DedupRecord],
    threshold: float = JACCARD_THRESHOLD_DEFAULT,
    *,
    exhaustive: bool = False,
) -> None:
    combined = list(train_records) + list(holdout_records)
    pairs = find_near_duplicate_pairs(combined, threshold, exhaustive=exhaustive)
    bad = cross_split_pairs(pairs)
    if bad:
        raise CrossSplitNearDuplicateError(
            f"found {len(bad)} train/holdout near-duplicate pair(s) at Jaccard >= {threshold}",
            bad,
        )


def lsh_documentation() -> dict[str, Any]:
    return {
        "minhash_num_perm": MINHASH_NUM_PERM,
        "lsh_bands": LSH_BANDS,
        "lsh_rows_per_band": LSH_ROWS_PER_BAND,
        "jaccard_threshold": JACCARD_THRESHOLD_DEFAULT,
        "shingle_size": SHINGLE_SIZE,
        "approximate_candidate_recall_at_threshold": approximate_lsh_candidate_recall(
            JACCARD_THRESHOLD_DEFAULT
        ),
        "note": (
            "LSH proposes candidates; exact Jaccard on token shingles is the "
            "sole duplicate criterion."
        ),
    }


def analyze_dedup_records(
    records: Sequence[DedupRecord],
    *,
    threshold: float = JACCARD_THRESHOLD_DEFAULT,
    exhaustive: bool = False,
) -> dict[str, Any]:
    pairs = find_near_duplicate_pairs(records, threshold, exhaustive=exhaustive)
    cross = cross_split_pairs(pairs)
    return {
        "lsh": lsh_documentation(),
        "threshold": threshold,
        "exhaustive": exhaustive or len(records) <= EXHAUSTIVE_PAIRWISE_MAX_RECORDS,
        "record_count": len(records),
        "near_duplicate_pairs": pairs,
        "cross_split_near_duplicate_pairs": cross,
        "cross_split_clean": len(cross) == 0,
    }


def run_dedup(path: Path, *, exhaustive: bool = False) -> dict[str, Any]:
    records = load_records_jsonl(path)
    return analyze_dedup_records(records, exhaustive=exhaustive)


def dedup_exit_code(result: Mapping[str, Any]) -> int:
    """Exit 1 when cross-split near-duplicates exist; 0 when clean."""
    return 0 if result.get("cross_split_clean") else 1