"""Publish a staged directory by rename, without deleting the destination first."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def publish_directory(staging: Path, destination: Path, *, force: bool) -> None:
    """Replace ``destination`` with ``staging`` using directory renames.

    A nonempty destination is moved aside first. If the staged rename fails,
    that previous directory is moved back. The destination is never deleted
    before the replacement is in place.
    """
    if not staging.is_dir():
        raise ValueError(f"staging directory is missing: {staging}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and any(destination.iterdir()) and not force:
        raise ValueError(f"output directory {destination} is not empty (use --force to replace)")
    if not destination.exists():
        staging.replace(destination)
        return
    if not any(destination.iterdir()):
        destination.rmdir()
        staging.replace(destination)
        return
    backup = destination.with_name(f".{destination.name}.replacing-{os.getpid()}")
    if backup.exists():
        shutil.rmtree(backup)
    destination.replace(backup)
    try:
        staging.replace(destination)
    except Exception:
        backup.replace(destination)
        raise
    shutil.rmtree(backup)
