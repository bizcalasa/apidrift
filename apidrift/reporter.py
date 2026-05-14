"""Report generator — formats diff results as plain text or JSON."""

from __future__ import annotations

import json
from typing import Literal

from .differ import Change


ReportFormat = Literal["text", "json"]


def generate_report(
    changes: list[Change],
    fmt: ReportFormat = "text",
    old_version: str = "old",
    new_version: str = "new",
) -> str:
    """Render a list of Change objects as a human-readable or machine-readable report."""
    if fmt == "json":
        return _json_report(changes, old_version, new_version)
    return _text_report(changes, old_version, new_version)


def _text_report(changes: list[Change], old_version: str, new_version: str) -> str:
    lines: list[str] = [
        f"API Drift Report: {old_version} → {new_version}",
        "=" * 60,
    ]

    breaking = [c for c in changes if c.breaking]
    non_breaking = [c for c in changes if not c.breaking]

    if not changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    lines.append(f"Total changes : {len(changes)}")
    lines.append(f"Breaking      : {len(breaking)}")
    lines.append(f"Non-breaking  : {len(non_breaking)}")
    lines.append("")

    if breaking:
        lines.append("BREAKING CHANGES")
        lines.append("-" * 40)
        for c in breaking:
            lines.append(f"  [✗] {c.change_type.value}")
            lines.append(f"      {c.endpoint_key}")
            lines.append(f"      {c.description}")
        lines.append("")

    if non_breaking:
        lines.append("NON-BREAKING CHANGES")
        lines.append("-" * 40)
        for c in non_breaking:
            lines.append(f"  [+] {c.change_type.value}")
            lines.append(f"      {c.endpoint_key}")
            lines.append(f"      {c.description}")

    return "\n".join(lines)


def _json_report(changes: list[Change], old_version: str, new_version: str) -> str:
    payload = {
        "old_version": old_version,
        "new_version": new_version,
        "summary": {
            "total": len(changes),
            "breaking": sum(1 for c in changes if c.breaking),
            "non_breaking": sum(1 for c in changes if not c.breaking),
        },
        "changes": [
            {
                "type": c.change_type.value,
                "endpoint": c.endpoint_key,
                "description": c.description,
                "breaking": c.breaking,
                "detail": c.detail,
            }
            for c in changes
        ],
    }
    return json.dumps(payload, indent=2)
