"""Call local Ollama for benchmark prompts."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from runner.config import OLLAMA_URL, SYSTEM_PROMPT
from runner.ollama_meta import ollama_version, peak_memory_gb_for_model
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


def _chat_once(
    *,
    model: str,
    prompt: str,
    temperature: float,
    seed: int,
    num_ctx: int,
    top_p: float,
) -> tuple[str, float]:
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "options": {
            "temperature": temperature,
            "seed": seed,
            "num_ctx": num_ctx,
            "top_p": top_p,
        },
    }
    start = time.perf_counter()
    result = _http_json(f"{OLLAMA_URL}/api/chat", payload, method="POST")
    elapsed = time.perf_counter() - start
    message = result.get("message", {}).get("content", "")
    return message, elapsed


def generate_run(
    run_dir: Path,
    *,
    model: str,
    host_class: str,
    backend: str,
    quant: str,
    task_ids: list[str],
    arm: str = "S",
    config: str = "A",
    split: str = "pilot",
    num_ctx: int = 8192,
    samples: int = 0,
    sample_temperature: float = 0.8,
    sample_seeds: list[int] | None = None,
    top_p: float = 0.95,
    inference_backend: str = "ollama",
) -> dict:
    if sample_seeds is None:
        sample_seeds = list(range(1, samples + 1)) if samples else []
    if samples and len(sample_seeds) != samples:
        raise ValueError("sample_seeds length must match samples")

    latencies: dict[str, float] = {}
    peak_mem: float | None = None
    for task_id in task_ids:
        spec = load_spec(task_id)
        prompt = spec["prompt"]
        greedy_text, greedy_lat = _chat_once(
            model=model,
            prompt=prompt,
            temperature=0,
            seed=42,
            num_ctx=num_ctx,
            top_p=top_p,
        )
        latencies[task_id] = greedy_lat
        (run_dir / "raw" / f"{task_id}.md").write_text(greedy_text + "\n", encoding="utf-8")
        (run_dir / "raw" / f"{task_id}.greedy.md").write_text(greedy_text + "\n", encoding="utf-8")

        for idx, seed in enumerate(sample_seeds, start=1):
            sample_text, _ = _chat_once(
                model=model,
                prompt=prompt,
                temperature=sample_temperature,
                seed=seed,
                num_ctx=num_ctx,
                top_p=top_p,
            )
            (run_dir / "raw" / f"{task_id}.sample{idx}.md").write_text(sample_text + "\n", encoding="utf-8")

    peak_mem = peak_memory_gb_for_model(model)

    meta = {
        "model": model,
        "model_digest": model_digest(model),
        "quant": quant,
        "prompt_id": "embabel-benchmark-v1-system",
        "embabel_pin": "embabel/embabel-agent@3b9b74f494cb",
        "host_class": host_class,
        "backend": backend,
        "inference_backend": inference_backend,
        "ollama_version": ollama_version(),
        "date": time.strftime("%Y-%m-%d", time.gmtime()),
        "arm": arm,
        "config": config,
        "split": split,
        "num_ctx": num_ctx,
        "decoding": {
            "greedy_temperature": 0,
            "greedy_seed": 42,
            "sample_temperature": sample_temperature,
            "sample_count": samples,
            "sample_seeds": sample_seeds,
            "top_p": top_p,
        },
        "peak_memory_gb": peak_mem,
        "peak_memory_note": "from Ollama /api/ps size_vram when available; else null",
        "task_latencies_sec": latencies,
    }
    write_meta(run_dir, meta)
    return meta