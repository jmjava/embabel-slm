"""Call local Ollama for benchmark prompts."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from runner.config import OLLAMA_URL, SYSTEM_PROMPT
from runner.runs import load_spec, write_meta


def _http_json(url: str, payload: dict | None = None, *, method: str = "GET") -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body.strip() else {}


def model_digest(model: str) -> str:
    try:
        tags = _http_json(f"{OLLAMA_URL}/api/tags")
        for item in tags.get("models", []):
            if item.get("name") == model or item.get("model") == model:
                return item.get("digest", "")
    except (urllib.error.URLError, TimeoutError):
        return ""
    try:
        show = _http_json(f"{OLLAMA_URL}/api/show", {"name": model}, method="POST")
        return show.get("details", {}).get("digest", "") or show.get("modelfile", "")[:64]
    except (urllib.error.URLError, TimeoutError):
        return ""
    return ""


def generate_run(
    run_dir: Path,
    *,
    model: str,
    host_class: str,
    backend: str,
    quant: str,
    task_ids: list[str],
) -> dict:
    latencies: dict[str, float] = {}
    for task_id in task_ids:
        spec = load_spec(task_id)
        prompt = spec["prompt"]
        payload = {
            "model": model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0, "seed": 42},
        }
        start = time.perf_counter()
        result = _http_json(f"{OLLAMA_URL}/api/chat", payload, method="POST")
        elapsed = time.perf_counter() - start
        latencies[task_id] = elapsed
        message = result.get("message", {}).get("content", "")
        (run_dir / "raw" / f"{task_id}.md").write_text(message + "\n", encoding="utf-8")

    meta = {
        "model": model,
        "model_digest": model_digest(model),
        "quant": quant,
        "prompt_id": "embabel-benchmark-v1-system",
        "embabel_pin": "embabel/embabel-agent@3b9b74f494cb",
        "host_class": host_class,
        "backend": backend,
        "date": time.strftime("%Y-%m-%d", time.gmtime()),
        "task_latencies_sec": latencies,
    }
    write_meta(run_dir, meta)
    return meta