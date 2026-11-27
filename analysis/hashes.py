"""Canonical content hashes for pipeline artifacts (stdlib only)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping, Sequence


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_command_sha256(argv: Sequence[str]) -> str:
    payload = json.dumps(list(argv), separators=(",", ":"))
    return sha256_text(payload)


def canonical_jsonl_sha256(rows: Sequence[Mapping[str, object]], *, id_key: str = "example_id") -> str:
    """Hash JSONL by sorted record ids and canonical JSON lines."""
    def line_for(row: Mapping[str, object]) -> str:
        return json.dumps(row, sort_keys=True, separators=(",", ":"))

    ordered = sorted(rows, key=lambda row: str(row.get(id_key, "")))
    joined = "\n".join(line_for(row) for row in ordered) + ("\n" if ordered else "")
    return sha256_text(joined)


def prereg_sha256(prereg_path: Path) -> str:
    return sha256_file(prereg_path)