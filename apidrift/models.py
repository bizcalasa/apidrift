"""Data models for representing API endpoints extracted from OpenAPI specs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")


@dataclass(frozen=True)
class Parameter:
    name: str
    location: str  # query, path, header, cookie
    required: bool = False
    schema: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass(frozen=True)
class Response:
    status_code: str
    description: str = ""
    schema: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)


@dataclass
class Endpoint:
    path: str
    method: str
    operation_id: str | None = None
    summary: str = ""
    deprecated: bool = False
    parameters: list[Parameter] = field(default_factory=list)
    responses: dict[str, Response] = field(default_factory=dict)
    request_body: dict[str, Any] | None = None
    tags: list[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Unique identifier for this endpoint."""
        return f"{self.method.upper()} {self.path}"

    def __repr__(self) -> str:
        return f"<Endpoint {self.key}>"


def extract_endpoints(spec: dict[str, Any]) -> dict[str, Endpoint]:
    """Extract all endpoints from a parsed OpenAPI spec."""
    endpoints: dict[str, Endpoint] = {}
    paths = spec.get("paths", {})

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        shared_params = _parse_parameters(path_item.get("parameters", []))

        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue

            op_params = _parse_parameters(operation.get("parameters", []))
            all_params = {p.name: p for p in shared_params}
            all_params.update({p.name: p for p in op_params})

            responses = {
                str(code): Response(
                    status_code=str(code),
                    description=resp_obj.get("description", "") if isinstance(resp_obj, dict) else "",
                )
                for code, resp_obj in operation.get("responses", {}).items()
            }

            ep = Endpoint(
                path=path,
                method=method,
                operation_id=operation.get("operationId"),
                summary=operation.get("summary", ""),
                deprecated=operation.get("deprecated", False),
                parameters=list(all_params.values()),
                responses=responses,
                request_body=operation.get("requestBody"),
                tags=operation.get("tags", []),
            )
            endpoints[ep.key] = ep

    return endpoints


def _parse_parameters(raw: list[Any]) -> list[Parameter]:
    return [
        Parameter(
            name=p["name"],
            location=p.get("in", "query"),
            required=p.get("required", False),
            schema=p.get("schema", {}),
        )
        for p in raw
        if isinstance(p, dict) and "name" in p
    ]
