"""Ollama version and memory probes."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from runner.config import OLLAMA_URL


def _http_json(url: str, payload: dict | None = None, *, method: str = "GET") -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body.strip() else {}


def ollama_version() -> str:
    try:
        data = _http_json(f"{OLLAMA_URL}/api/version")
        return str(data.get("version", ""))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return "unknown"


def peak_memory_gb_for_model(model: str) -> float | None:
    """Read Ollama /api/ps size_vram (bytes) for `model` after a generate. None if unavailable."""
    try:
        data = _http_json(f"{OLLAMA_URL}/api/ps")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    best: float | None = None
    for row in data.get("models", []):
        name = row.get("name") or row.get("model") or ""
        if model not in name and name not in model:
            continue
        vram = row.get("size_vram") or row.get("size")
        if vram is None:
            continue
        gb = float(vram) / (1024**3)
        best = gb if best is None else max(best, gb)
    return best