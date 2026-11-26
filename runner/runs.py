"""Run directory helpers."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "benchmark" / "specs"
RUNS_DIR = ROOT / "experiments" / "runs"


def slugify_model(model: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", model).strip("-") or "model"


def new_run_id(model: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{slugify_model(model)}"


def refuse_existing(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"run directory already exists: {path}")


def ensure_run_dir(run_id: str) -> Path:
    run_dir = RUNS_DIR / run_id
    refuse_existing(run_dir)
    run_dir.mkdir(parents=True)
    (run_dir / "raw").mkdir()
    return run_dir


def load_spec(task_id: str) -> dict:
    path = SPECS_DIR / f"{task_id}.json"
    if not path.is_file():
        raise FileNotFoundError(task_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_task_ids() -> list[str]:
    return sorted(p.stem for p in SPECS_DIR.glob("*.json"))


def read_meta(run_dir: Path) -> dict:
    meta_path = run_dir / "meta.json"
    if meta_path.is_file():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


def write_meta(run_dir: Path, meta: dict) -> None:
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")