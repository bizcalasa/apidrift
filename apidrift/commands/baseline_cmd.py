"""CLI sub-commands for baseline management (save / load / list / delete)."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from apidrift.baseline import (
    BaselineError,
    DEFAULT_BASELINE_DIR,
    delete_baseline,
    list_baselines,
    load_baseline,
    save_baseline,
)
from apidrift.parser import SpecParseError, load_spec
from apidrift.reporter import generate_report
from apidrift.differ import diff_endpoints
from apidrift.parser import get_paths


def add_baseline_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach 'baseline' sub-command to an existing subparsers group."""
    p = subparsers.add_parser("baseline", help="Manage saved API baselines")
    bp = p.add_subparsers(dest="baseline_action", required=True)

    # save
    ps = bp.add_parser("save", help="Pin a spec as a named baseline")
    ps.add_argument("name", help="Baseline name")
    ps.add_argument("spec", help="Path to OpenAPI spec file")
    ps.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")

    # list
    pl = bp.add_parser("list", help="List saved baselines")
    pl.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")

    # delete
    pd = bp.add_parser("delete", help="Remove a saved baseline")
    pd.add_argument("name", help="Baseline name to remove")
    pd.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")

    # diff
    pdi = bp.add_parser("diff", help="Diff a spec against a saved baseline")
    pdi.add_argument("name", help="Baseline name to compare against")
    pdi.add_argument("spec", help="Path to current OpenAPI spec")
    pdi.add_argument("--dir", default=DEFAULT_BASELINE_DIR, dest="baseline_dir")
    pdi.add_argument("--format", choices=["text", "json"], default="text", dest="fmt")


def run_baseline(args: argparse.Namespace) -> int:
    """Dispatch baseline sub-commands; return exit code."""
    action = args.baseline_action

    if action == "save":
        try:
            spec = load_spec(args.spec)
        except (SpecParseError, FileNotFoundError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        dest = save_baseline(args.name, spec, baseline_dir=args.baseline_dir)
        print(f"Baseline '{args.name}' saved to {dest}")
        return 0

    if action == "list":
        names = list_baselines(baseline_dir=args.baseline_dir)
        if not names:
            print("No baselines saved.")
        else:
            for n in names:
                print(n)
        return 0

    if action == "delete":
        try:
            delete_baseline(args.name, baseline_dir=args.baseline_dir)
            print(f"Baseline '{args.name}' deleted.")
        except BaselineError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if action == "diff":
        try:
            old_spec = load_baseline(args.name, baseline_dir=args.baseline_dir)
            new_spec = load_spec(args.spec)
        except (BaselineError, SpecParseError, FileNotFoundError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        changes = diff_endpoints(get_paths(old_spec), get_paths(new_spec))
        print(generate_report(changes, fmt=args.fmt))
        return 1 if changes else 0

    print(f"Unknown baseline action: {action}", file=sys.stderr)
    return 1
