"""
Command-line interface for SSN Redactor.

Usage:
    python -m ssn_redactor.cli <folder_path>
    python -m ssn_redactor.cli --help
"""

from __future__ import annotations

import argparse
import sys

from ssn_redactor import __version__
from ssn_redactor.engine import (
    BatchResult,
    Status,
    collect_files,
    process_folder,
    validate_folder,
    validate_output_dir_name,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ssn-redactor",
        description=(
            "Scan PDF and JPG files for U.S. Social Security Numbers "
            "and produce redacted copies. All processing runs locally."
        ),
    )
    parser.add_argument(
        "folder",
        help="Path to a folder containing PDF and/or JPG files.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="redacted_pdfs",
        help='Name of the output subdirectory (default: "redacted_pdfs").',
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _print_report(batch: BatchResult) -> None:
    print()
    print("=" * 56)
    print("  SSN Redaction Report")
    print("=" * 56)

    for r in batch.results:
        if r.status == Status.ERROR:
            label = f"ERROR: {r.error}"
        elif r.status == Status.NO_TEXT:
            label = "no text layer (skipped)"
        elif r.ssn_count == 0:
            label = "0 SSNs found"
        else:
            label = f"{r.ssn_count} SSN(s) redacted"
        print(f"  {r.filename:<40} {label}")

    print("=" * 56)
    print(f"  Total SSNs redacted: {batch.total_redacted}")
    if batch.total_errors:
        print(f"  Errors: {batch.total_errors}")
    print(f"  Output: {batch.output_folder}")
    print("=" * 56)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Validate inputs before any processing
    try:
        folder = validate_folder(args.folder)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    try:
        validate_output_dir_name(args.output_dir)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    files = collect_files(folder)
    if not files:
        print(f"No PDF or JPG files found in '{folder}'.")
        return 0

    print(f"Processing {len(files)} file(s) in {folder} ...")

    def on_progress(name: str, idx: int, total: int) -> None:
        print(f"  [{idx + 1}/{total}] {name}")

    batch = process_folder(
        str(folder),
        output_dir_name=args.output_dir,
        on_progress=on_progress,
    )

    _print_report(batch)
    return 1 if batch.total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
