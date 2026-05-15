"""Tests for the apidrift CLI."""

import json
import pytest
from unittest.mock import patch, MagicMock

from apidrift.cli import run, build_parser
from apidrift.differ import Change, ChangeType
from apidrift.parser import SpecParseError


MINIMAL_SPEC_OLD = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {"responses": {"200": {"description": "OK"}}}
        }
    },
}

MINIMAL_SPEC_NEW = {
    "openapi": "3.0.0",
    "info": {"title": "Test", "version": "2.0.0"},
    "paths": {},
}


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["old.yaml", "new.yaml"])
    assert args.old_spec == "old.yaml"
    assert args.new_spec == "new.yaml"
    assert args.output_format == "text"
    assert args.output is None
    assert args.breaking_only is False


def test_build_parser_all_flags():
    parser = build_parser()
    args = parser.parse_args(["a.yaml", "b.yaml", "--format", "json", "--breaking-only", "-o", "out.json"])
    assert args.output_format == "json"
    assert args.breaking_only is True
    assert args.output == "out.json"


@patch("apidrift.cli.load_spec")
@patch("apidrift.cli.diff_endpoints", return_value=[])
def test_run_no_changes_returns_zero(mock_diff, mock_load):
    mock_load.return_value = MINIMAL_SPEC_OLD
    code = run(["old.yaml", "new.yaml"])
    assert code == 0


@patch("apidrift.cli.load_spec", side_effect=SpecParseError("bad spec"))
def test_run_parse_error_returns_one(mock_load, capsys):
    code = run(["old.yaml", "new.yaml"])
    assert code == 1
    captured = capsys.readouterr()
    assert "Error loading spec" in captured.err


@patch("apidrift.cli.load_spec", side_effect=FileNotFoundError("no such file"))
def test_run_file_not_found_returns_one(mock_load, capsys):
    code = run(["missing.yaml", "new.yaml"])
    assert code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err


@patch("apidrift.cli.load_spec")
@patch("apidrift.cli.diff_endpoints")
def test_run_breaking_change_returns_one(mock_diff, mock_load):
    mock_load.return_value = MINIMAL_SPEC_OLD
    mock_diff.return_value = [
        Change(change_type=ChangeType.BREAKING, path="/users", method="get", description="Endpoint removed")
    ]
    code = run(["old.yaml", "new.yaml"])
    assert code == 1


@patch("apidrift.cli.load_spec")
@patch("apidrift.cli.diff_endpoints")
def test_run_breaking_only_filters(mock_diff, mock_load):
    mock_load.return_value = MINIMAL_SPEC_OLD
    mock_diff.return_value = [
        Change(change_type=ChangeType.NON_BREAKING, path="/users", method="get", description="Added field")
    ]
    code = run(["old.yaml", "new.yaml", "--breaking-only"])
    assert code == 0


@patch("apidrift.cli.load_spec")
@patch("apidrift.cli.diff_endpoints", return_value=[])
def test_run_json_format(mock_diff, mock_load):
    mock_load.return_value = MINIMAL_SPEC_OLD
    code = run(["old.yaml", "new.yaml", "--format", "json"])
    assert code == 0


@patch("apidrift.cli.load_spec")
@patch("apidrift.cli.diff_endpoints", return_value=[])
def test_run_output_file(mock_diff, mock_load, tmp_path):
    mock_load.return_value = MINIMAL_SPEC_OLD
    out_file = tmp_path / "report.txt"
    code = run(["old.yaml", "new.yaml", "-o", str(out_file)])
    assert code == 0
    assert out_file.exists()
