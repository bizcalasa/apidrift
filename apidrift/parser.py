"""OpenAPI spec parser — loads and normalizes OpenAPI 2.x/3.x specs from files or dicts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


SUPPORTED_VERSIONS = ("2.0", "3.0", "3.1")


class SpecParseError(Exception):
    """Raised when an OpenAPI spec cannot be parsed or is unsupported."""


def load_spec(source: str | Path | dict) -> dict[str, Any]:
    """Load an OpenAPI spec from a file path, raw string, or already-parsed dict."""
    if isinstance(source, dict):
        spec = source
    elif isinstance(source, (str, Path)):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"Spec file not found: {path}")
        raw = path.read_text(encoding="utf-8")
        if path.suffix in (".yaml", ".yml"):
            spec = yaml.safe_load(raw)
        elif path.suffix == ".json":
            spec = json.loads(raw)
        else:
            # Try YAML first, fall back to JSON
            try:
                spec = yaml.safe_load(raw)
            except yaml.YAMLError:
                spec = json.loads(raw)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    _validate_spec(spec)
    return spec


def _validate_spec(spec: dict[str, Any]) -> None:
    """Basic structural validation of the loaded spec."""
    if not isinstance(spec, dict):
        raise SpecParseError("Spec must be a mapping/object at the top level.")

    version = spec.get("openapi") or spec.get("swagger")
    if version is None:
        raise SpecParseError("Missing 'openapi' or 'swagger' version field.")

    version_str = str(version)
    if not any(version_str.startswith(v) for v in SUPPORTED_VERSIONS):
        raise SpecParseError(
            f"Unsupported OpenAPI version '{version}'. "
            f"Supported: {SUPPORTED_VERSIONS}"
        )

    if "paths" not in spec:
        raise SpecParseError("Spec is missing required 'paths' field.")


def get_version(spec: dict[str, Any]) -> str:
    """Return the OpenAPI/Swagger version string from a parsed spec."""
    return str(spec.get("openapi") or spec.get("swagger", "unknown"))


def get_paths(spec: dict[str, Any]) -> dict[str, Any]:
    """Return the paths mapping from a parsed spec.

    Each key is a path template (e.g. '/users/{id}') and each value is a
    path-item object containing the HTTP method definitions.

    Returns an empty dict if the 'paths' field is absent or None.
    """
    return spec.get("paths") or {}
