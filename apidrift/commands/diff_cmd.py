"""CLI subcommand: diff two OpenAPI specs and report changes."""

from __future__ import annotations

import argparse
import sys

from apidrift.baseline import load_baseline, BaselineError
from apidrift.config import load_config
from apidrift.differ import diff_endpoints
from apidrift.parser import load_spec, get_paths, SpecParseError
from apidrift.reporter import generate_report


def add_diff_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register the *diff* subcommand on *subparsers*."""
    parser = subparsers.add_parser(
        "diff",
        help="Compare two OpenAPI specs and report breaking changes.",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--old",
        metavar="FILE",
        help="Path to the older OpenAPI spec file.",
    )
    source_group.add_argument(
        "--baseline",
        metavar="NAME",
        help="Name of a saved baseline to use as the old spec.",
    )
    parser.add_argument(
        "new",
        metavar="NEW_FILE",
        help="Path to the newer OpenAPI spec file.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to a apidrift config file (JSON/YAML).",
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        default=False,
        help="Only report breaking changes.",
    )


def run_diff(args: argparse.Namespace) -> int:
    """Execute the diff subcommand.  Returns an exit code."""
    config = load_config(args.config)

    # Load the *new* spec.
    try:
        new_spec = load_spec(args.new)
    except (SpecParseError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    # Load the *old* spec — either from a file or a saved baseline.
    try:
        if args.baseline:
            old_spec = load_baseline(args.baseline)
        else:
            old_spec = load_spec(args.old)
    except (SpecParseError, FileNotFoundError, BaselineError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    old_paths = get_paths(old_spec)
    new_paths = get_paths(new_spec)

    changes = diff_endpoints(old_paths, new_paths, config=config)

    if args.breaking_only:
        from apidrift.differ import ChangeType
        changes = [c for c in changes if c.change_type == ChangeType.BREAKING]

    report = generate_report(changes, fmt=args.fmt)
    print(report)

    # Non-zero exit when breaking changes are present.
    from apidrift.differ import ChangeType
    has_breaking = any(c.change_type == ChangeType.BREAKING for c in changes)
    return 2 if has_breaking else 0
