"""Command-line interface for apidrift."""

import argparse
import sys
from pathlib import Path

from apidrift.parser import load_spec, SpecParseError
from apidrift.differ import diff_endpoints
from apidrift.reporter import generate_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apidrift",
        description="Detect breaking changes in REST APIs by diffing OpenAPI specs.",
    )
    parser.add_argument("old_spec", help="Path or URL to the old OpenAPI spec")
    parser.add_argument("new_spec", help="Path or URL to the new OpenAPI spec")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format for the report (default: text)",
    )
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Write report to FILE instead of stdout",
    )
    parser.add_argument(
        "--breaking-only",
        action="store_true",
        default=False,
        help="Only report breaking changes",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    """Entry point; returns exit code."""
    args = build_parser().parse_args(argv)

    try:
        old_spec = load_spec(args.old_spec)
        new_spec = load_spec(args.new_spec)
    except SpecParseError as exc:
        print(f"Error loading spec: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"File not found: {exc}", file=sys.stderr)
        return 1

    changes = diff_endpoints(old_spec, new_spec)

    if args.breaking_only:
        from apidrift.differ import ChangeType
        changes = [c for c in changes if c.change_type == ChangeType.BREAKING]

    report = generate_report(changes, fmt=args.output_format)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report)

    breaking = sum(1 for c in changes if hasattr(c, 'change_type') and
                   c.change_type.name == 'BREAKING')
    return 1 if breaking > 0 else 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
