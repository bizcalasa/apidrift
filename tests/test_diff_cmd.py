"""Tests for apidrift.commands.diff_cmd."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from apidrift.commands.diff_cmd import add_diff_subparser, run_diff
from apidrift.differ import Change, ChangeType
from apidrift.parser import SpecParseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        old="old.yaml",
        baseline=None,
        new="new.yaml",
        fmt="text",
        config=None,
        breaking_only=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


_BREAKING_CHANGE = Change(
    path="/pets",
    method="GET",
    change_type=ChangeType.BREAKING,
    description="Response 200 removed",
)

_INFO_CHANGE = Change(
    path="/pets",
    method="GET",
    change_type=ChangeType.NON_BREAKING,
    description="Description updated",
)


# ---------------------------------------------------------------------------
# add_diff_subparser
# ---------------------------------------------------------------------------

def test_add_diff_subparser_registers_command():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    add_diff_subparser(subs)
    ns = root.parse_args(["diff", "--old", "a.yaml", "b.yaml"])
    assert ns.command == "diff"
    assert ns.old == "a.yaml"
    assert ns.new == "b.yaml"


def test_add_diff_subparser_baseline_flag():
    root = argparse.ArgumentParser()
    subs = root.add_subparsers(dest="command")
    add_diff_subparser(subs)
    ns = root.parse_args(["diff", "--baseline", "v1", "new.yaml"])
    assert ns.baseline == "v1"
    assert ns.old is None


# ---------------------------------------------------------------------------
# run_diff
# ---------------------------------------------------------------------------

@patch("apidrift.commands.diff_cmd.generate_report", return_value="No changes.")
@patch("apidrift.commands.diff_cmd.diff_endpoints", return_value=[])
@patch("apidrift.commands.diff_cmd.get_paths", return_value={})
@patch("apidrift.commands.diff_cmd.load_spec", return_value={})
@patch("apidrift.commands.diff_cmd.load_config", return_value=MagicMock())
def test_run_diff_no_changes_returns_zero(lc, ls, gp, de, gr, capsys):
    code = run_diff(_make_args())
    assert code == 0
    captured = capsys.readouterr()
    assert "No changes." in captured.out


@patch("apidrift.commands.diff_cmd.generate_report", return_value="Breaking!")
@patch("apidrift.commands.diff_cmd.diff_endpoints", return_value=[_BREAKING_CHANGE])
@patch("apidrift.commands.diff_cmd.get_paths", return_value={})
@patch("apidrift.commands.diff_cmd.load_spec", return_value={})
@patch("apidrift.commands.diff_cmd.load_config", return_value=MagicMock())
def test_run_diff_breaking_change_returns_two(lc, ls, gp, de, gr):
    code = run_diff(_make_args())
    assert code == 2


@patch("apidrift.commands.diff_cmd.load_spec", side_effect=SpecParseError("bad spec"))
@patch("apidrift.commands.diff_cmd.load_config", return_value=MagicMock())
def test_run_diff_new_spec_parse_error_returns_one(lc, ls, capsys):
    code = run_diff(_make_args())
    assert code == 1
    assert "error" in capsys.readouterr().err


@patch("apidrift.commands.diff_cmd.generate_report", return_value="ok")
@patch("apidrift.commands.diff_cmd.diff_endpoints", return_value=[_BREAKING_CHANGE, _INFO_CHANGE])
@patch("apidrift.commands.diff_cmd.get_paths", return_value={})
@patch("apidrift.commands.diff_cmd.load_spec", return_value={})
@patch("apidrift.commands.diff_cmd.load_config", return_value=MagicMock())
def test_run_diff_breaking_only_filters(lc, ls, gp, de, gr):
    args = _make_args(breaking_only=True)
    run_diff(args)
    # generate_report should be called with only the breaking change
    reported_changes = gr.call_args[0][0]
    assert all(c.change_type == ChangeType.BREAKING for c in reported_changes)
    assert len(reported_changes) == 1
