"""Configuration dataclass and loader for apidrift."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

try:
    import tomllib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]


@dataclass
class DriftConfig:
    """Runtime configuration for an apidrift run."""

    output_format: Literal["text", "json"] = "text"
    breaking_only: bool = False
    ignore_paths: list[str] = field(default_factory=list)
    ignore_methods: list[str] = field(default_factory=list)

    def should_ignore(self, path: str, method: str) -> bool:
        """Return True if this path/method combo should be skipped."""
        if path in self.ignore_paths:
            return True
        if method.lower() in [m.lower() for m in self.ignore_methods]:
            return True
        return False


def load_config(config_path: str | Path | None = None) -> DriftConfig:
    """Load config from a TOML or JSON file, or return defaults."""
    if config_path is None:
        for candidate in ("apidrift.toml", ".apidrift.toml", "apidrift.json"):
            p = Path(candidate)
            if p.exists():
                config_path = p
                break
        else:
            return DriftConfig()

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw: dict = {}
    if config_path.suffix in (".toml",):
        if tomllib is None:
            raise ImportError("tomllib/tomli is required to read TOML config files")
        with open(config_path, "rb") as fh:
            raw = tomllib.load(fh)
    elif config_path.suffix == ".json":
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported config format: {config_path.suffix}")

    return DriftConfig(
        output_format=raw.get("output_format", "text"),
        breaking_only=raw.get("breaking_only", False),
        ignore_paths=raw.get("ignore_paths", []),
        ignore_methods=raw.get("ignore_methods", []),
    )
