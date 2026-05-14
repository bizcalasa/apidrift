"""Tests for parser, models, and differ modules."""

from __future__ import annotations

import pytest

from apidrift.parser import load_spec, SpecParseError, get_version
from apidrift.models import extract_endpoints
from apidrift.differ import diff_endpoints, ChangeType
from apidrift.reporter import generate_report


SIMPLE_SPEC_V1 = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "1.0"},
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "parameters": [
                    {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
                ],
                "responses": {"200": {"description": "OK"}},
            }
        },
        "/users/{id}": {
            "delete": {
                "operationId": "deleteUser",
                "parameters": [{"name": "id", "in": "path", "required": True}],
                "responses": {"204": {"description": "No Content"}},
            }
        },
    },
}

SIMPLE_SPEC_V2 = {
    "openapi": "3.0.0",
    "info": {"title": "Test API", "version": "2.0"},
    "paths": {
        "/users": {
            "get": {
                "operationId": "listUsers",
                "parameters": [
                    {"name": "limit", "in": "query", "required": False},
                    {"name": "filter", "in": "query", "required": True},  # new required param
                ],
                "responses": {
                    "200": {"description": "OK"},
                    "400": {"description": "Bad Request"},
                },
            }
        },
        # /users/{id} DELETE removed
        "/health": {
            "get": {
                "operationId": "healthCheck",
                "responses": {"200": {"description": "OK"}},
            }
        },
    },
}


class TestParser:
    def test_load_dict_spec(self):
        spec = load_spec(SIMPLE_SPEC_V1)
        assert spec["openapi"] == "3.0.0"

    def test_missing_paths_raises(self):
        with pytest.raises(SpecParseError, match="paths"):
            load_spec({"openapi": "3.0.0"})

    def test_unsupported_version_raises(self):
        with pytest.raises(SpecParseError, match="Unsupported"):
            load_spec({"openapi": "1.0", "paths": {}})

    def test_get_version(self):
        assert get_version(SIMPLE_SPEC_V1) == "3.0.0"

    def test_swagger_version(self):
        spec = {"swagger": "2.0", "paths": {}}
        loaded = load_spec(spec)
        assert get_version(loaded) == "2.0"


class TestModels:
    def test_extract_endpoints_count(self):
        endpoints = extract_endpoints(SIMPLE_SPEC_V1)
        assert len(endpoints) == 2
        assert "GET /users" in endpoints
        assert "DELETE /users/{id}" in endpoints

    def test_endpoint_parameters(self):
        endpoints = extract_endpoints(SIMPLE_SPEC_V1)
        get_users = endpoints["GET /users"]
        assert len(get_users.parameters) == 1
        assert get_users.parameters[0].name == "limit"
        assert get_users.parameters[0].required is False

    def test_endpoint_key(self):
        endpoints = extract_endpoints(SIMPLE_SPEC_V1)
        ep = endpoints["GET /users"]
        assert ep.key == "GET /users"


class TestDiffer:
    def setup_method(self):
        self.old = extract_endpoints(SIMPLE_SPEC_V1)
        self.new = extract_endpoints(SIMPLE_SPEC_V2)
        self.changes = diff_endpoints(self.old, self.new)

    def test_removed_endpoint_is_breaking(self):
        removed = [c for c in self.changes if c.change_type == ChangeType.ENDPOINT_REMOVED]
        assert len(removed) == 1
        assert removed[0].breaking is True
        assert removed[0].endpoint_key == "DELETE /users/{id}"

    def test_added_endpoint_non_breaking(self):
        added = [c for c in self.changes if c.change_type == ChangeType.ENDPOINT_ADDED]
        assert any(c.endpoint_key == "GET /health" for c in added)
        assert all(not c.breaking for c in added)

    def test_required_param_added_is_breaking(self):
        param_added = [c for c in self.changes if c.change_type == ChangeType.PARAMETER_ADDED]
        filter_change = next(c for c in param_added if "filter" in c.description)
        assert filter_change.breaking is True

    def test_response_added_non_breaking(self):
        resp_added = [c for c in self.changes if c.change_type == ChangeType.RESPONSE_ADDED]
        assert any("400" in c.description for c in resp_added)


class TestReporter:
    def test_text_report_contains_summary(self):
        old = extract_endpoints(SIMPLE_SPEC_V1)
        new = extract_endpoints(SIMPLE_SPEC_V2)
        changes = diff_endpoints(old, new)
        report = generate_report(changes, fmt="text", old_version="1.0", new_version="2.0")
        assert "Breaking" in report
        assert "1.0" in report

    def test_json_report_structure(self):
        import json
        old = extract_endpoints(SIMPLE_SPEC_V1)
        new = extract_endpoints(SIMPLE_SPEC_V2)
        changes = diff_endpoints(old, new)
        report = generate_report(changes, fmt="json", old_version="1.0", new_version="2.0")
        data = json.loads(report)
        assert "summary" in data
        assert data["summary"]["breaking"] > 0

    def test_empty_report(self):
        report = generate_report([], fmt="text")
        assert "No changes detected" in report
