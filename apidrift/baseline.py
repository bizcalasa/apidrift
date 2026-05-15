"""Baseline management: save and load pinned OpenAPI specs for comparison."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_BASELINE_DIR = ".apidrift"
_INDEX_FILE = "baselines.json"


class BaselineError(Exception):
    """Raised when a baseline operation fails."""


def _index_path(baseline_dir: str) -> Path:
    return Path(baseline_dir) / _INDEX_FILE


def _load_index(baseline_dir: str) -> Dict[str, str]:
    """Return mapping of name -> relative spec filename."""
    idx = _index_path(baseline_dir)
    if not idx.exists():
        return {}
    with idx.open() as fh:
        return json.load(fh)


def _save_index(baseline_dir: str, index: Dict[str, str]) -> None:
    idx = _index_path(baseline_dir)
    with idx.open("w") as fh:
        json.dump(index, fh, indent=2)


def save_baseline(
    name: str,
    spec: Dict[str, Any],
    baseline_dir: str = DEFAULT_BASELINE_DIR,
) -> Path:
    """Persist *spec* under *name*; return the path written."""
    Path(baseline_dir).mkdir(parents=True, exist_ok=True)
    filename = f"{name}.json"
    dest = Path(baseline_dir) / filename
    with dest.open("w") as fh:
        json.dump(spec, fh, indent=2)
    index = _load_index(baseline_dir)
    index[name] = filename
    _save_index(baseline_dir, index)
    return dest


def load_baseline(
    name: str,
    baseline_dir: str = DEFAULT_BASELINE_DIR,
) -> Dict[str, Any]:
    """Load a previously saved baseline by *name*."""
    index = _load_index(baseline_dir)
    if name not in index:
        raise BaselineError(
            f"Baseline '{name}' not found in '{baseline_dir}'. "
            f"Available: {sorted(index)}"
        )
    dest = Path(baseline_dir) / index[name]
    if not dest.exists():
        raise BaselineError(f"Baseline file missing: {dest}")
    with dest.open() as fh:
        return json.load(fh)


def list_baselines(baseline_dir: str = DEFAULT_BASELINE_DIR) -> list[str]:
    """Return sorted list of saved baseline names."""
    return sorted(_load_index(baseline_dir).keys())


def delete_baseline(
    name: str,
    baseline_dir: str = DEFAULT_BASELINE_DIR,
) -> None:
    """Remove a saved baseline by *name*."""
    index = _load_index(baseline_dir)
    if name not in index:
        raise BaselineError(f"Baseline '{name}' not found.")
    dest = Path(baseline_dir) / index.pop(name)
    if dest.exists():
        os.remove(dest)
    _save_index(baseline_dir, index)
