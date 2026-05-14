"""Diff engine — compares two sets of endpoints and produces structured change records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import Endpoint


class ChangeType(str, Enum):
    ENDPOINT_ADDED = "endpoint_added"
    ENDPOINT_REMOVED = "endpoint_removed"
    PARAMETER_ADDED = "parameter_added"
    PARAMETER_REMOVED = "parameter_removed"
    PARAMETER_REQUIRED_CHANGED = "parameter_required_changed"
    RESPONSE_ADDED = "response_added"
    RESPONSE_REMOVED = "response_removed"
    DEPRECATED_CHANGED = "deprecated_changed"
    REQUEST_BODY_CHANGED = "request_body_changed"


BREAKING_CHANGES = {
    ChangeType.ENDPOINT_REMOVED,
    ChangeType.PARAMETER_REMOVED,
    ChangeType.PARAMETER_REQUIRED_CHANGED,
    ChangeType.RESPONSE_REMOVED,
}


@dataclass
class Change:
    change_type: ChangeType
    endpoint_key: str
    description: str
    breaking: bool
    detail: dict[str, Any] | None = None

    def __repr__(self) -> str:
        tag = "[BREAKING]" if self.breaking else "[non-breaking]"
        return f"{tag} {self.change_type.value}: {self.endpoint_key} — {self.description}"


def diff_endpoints(
    old: dict[str, Endpoint],
    new: dict[str, Endpoint],
) -> list[Change]:
    """Compare old vs new endpoint maps and return a list of Change objects."""
    changes: list[Change] = []

    old_keys = set(old)
    new_keys = set(new)

    for key in old_keys - new_keys:
        changes.append(Change(
            change_type=ChangeType.ENDPOINT_REMOVED,
            endpoint_key=key,
            description=f"Endpoint '{key}' was removed.",
            breaking=True,
        ))

    for key in new_keys - old_keys:
        changes.append(Change(
            change_type=ChangeType.ENDPOINT_ADDED,
            endpoint_key=key,
            description=f"Endpoint '{key}' was added.",
            breaking=False,
        ))

    for key in old_keys & new_keys:
        changes.extend(_diff_endpoint(old[key], new[key]))

    return changes


def _diff_endpoint(old: Endpoint, new: Endpoint) -> list[Change]:
    changes: list[Change] = []
    key = old.key

    if old.deprecated != new.deprecated:
        changes.append(Change(
            change_type=ChangeType.DEPRECATED_CHANGED,
            endpoint_key=key,
            description=f"'deprecated' changed from {old.deprecated} to {new.deprecated}.",
            breaking=False,
        ))

    old_params = {p.name: p for p in old.parameters}
    new_params = {p.name: p for p in new.parameters}

    for name in set(old_params) - set(new_params):
        changes.append(Change(
            change_type=ChangeType.PARAMETER_REMOVED,
            endpoint_key=key,
            description=f"Parameter '{name}' was removed.",
            breaking=True,
        ))

    for name in set(new_params) - set(old_params):
        p = new_params[name]
        breaking = p.required
        changes.append(Change(
            change_type=ChangeType.PARAMETER_ADDED,
            endpoint_key=key,
            description=f"Parameter '{name}' was added (required={p.required}).",
            breaking=breaking,
        ))

    for name in set(old_params) & set(new_params):
        op, np = old_params[name], new_params[name]
        if op.required != np.required:
            changes.append(Change(
                change_type=ChangeType.PARAMETER_REQUIRED_CHANGED,
                endpoint_key=key,
                description=(
                    f"Parameter '{name}' required changed "
                    f"{op.required} → {np.required}."
                ),
                breaking=np.required and not op.required,
            ))

    old_resp = set(old.responses)
    new_resp = set(new.responses)
    for code in old_resp - new_resp:
        changes.append(Change(
            change_type=ChangeType.RESPONSE_REMOVED,
            endpoint_key=key,
            description=f"Response status '{code}' was removed.",
            breaking=True,
        ))
    for code in new_resp - old_resp:
        changes.append(Change(
            change_type=ChangeType.RESPONSE_ADDED,
            endpoint_key=key,
            description=f"Response status '{code}' was added.",
            breaking=False,
        ))

    return changes
