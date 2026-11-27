"""Physical-line JSONL readers (stdlib only).

JSON strings may contain U+2028 LINE SEPARATOR or U+2029 PARAGRAPH SEPARATOR.
Whole-file ``splitlines()`` treats those as record boundaries and corrupts JSONL.
Readers here iterate file handles so only physical newlines split records.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Mapping, Sequence


def iter_physical_jsonl_lines(path: Path) -> Iterator[tuple[int, str]]:
    """Yield ``(line_number, stripped_line)`` for each nonempty JSONL record."""
    if not path.is_file():
        raise ValueError(f"missing file {path}")
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            yield line_number, stripped


def load_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for line_number, line in iter_physical_jsonl_lines(path):
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise ValueError(f"line {line_number}: row must be a JSON object")
        rows.append(raw)
    return rows


def write_jsonl(path: Path, rows: Sequence[Mapping[str, object]], *, sort_keys: bool = False) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=sort_keys) + "\n")


def write_canonical_jsonl(
    path: Path,
    rows: Sequence[Mapping[str, object]],
    *,
    id_key: str = "example_id",
) -> None:
    """Write the exact byte layout hashed by ``canonical_jsonl_sha256``."""
    ordered = sorted(rows, key=lambda row: str(row.get(id_key, "")))
    with path.open("w", encoding="utf-8") as handle:
        for row in ordered:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")