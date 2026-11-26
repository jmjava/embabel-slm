"""Extract fenced code files from model markdown answers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator

FENCE_RE = re.compile(
    r"```([^\n`]*)\n(.*?)```",
    re.DOTALL,
)


@dataclass(frozen=True)
class ExtractedFile:
    path: str
    content: str


def _normalize_path(label: str) -> str:
    label = label.strip()
    for prefix in (
        "java ",
        "kotlin ",
        "xml ",
        "java:",
        "kotlin:",
        "xml:",
    ):
        if label.lower().startswith(prefix):
            label = label[len(prefix) :].strip()
    label = label.lstrip("./")
    if label.startswith("src/") or label.endswith((".java", ".kt", ".xml", ".properties")):
        return label
    if label:
        return label
    return "src/main/java/Generated.java"


def extract_fenced_files(text: str) -> list[ExtractedFile]:
    files: list[ExtractedFile] = []
    for match in FENCE_RE.finditer(text):
        label, body = match.group(1), match.group(2)
        if not body.strip():
            continue
        path = _normalize_path(label)
        files.append(ExtractedFile(path=path, content=body.rstrip() + "\n"))
    return files


def merge_with_project(base_files: dict[str, str], extracted: Iterable[ExtractedFile]) -> dict[str, str]:
    merged = dict(base_files)
    for item in extracted:
        merged[item.path] = item.content
    return merged