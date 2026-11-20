#!/usr/bin/env python3
"""Fail when an LCOV report is below the agreed line-coverage gate.

Usage:
    python scripts/check_lcov.py mobile/coverage/lcov.info --min 50
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def read_lcov(path: Path) -> tuple[int, int]:
    found = 0
    hit = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("LF:"):
            found += int(line[3:])
        elif line.startswith("LH:"):
            hit += int(line[3:])
    return found, hit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lcov", type=Path)
    parser.add_argument("--min", type=float, default=50.0, help="minimum line coverage percent")
    args = parser.parse_args()

    if not args.lcov.exists():
        print(f"error: coverage file not found: {args.lcov}", file=sys.stderr)
        return 2

    found, hit = read_lcov(args.lcov)
    if found == 0:
        print("error: no LF/LH records in coverage file", file=sys.stderr)
        return 2

    percentage = hit / found * 100
    print(f"line coverage: {hit}/{found} = {percentage:.2f}% (gate {args.min:.0f}%)")
    if percentage + 1e-9 < args.min:
        print("coverage gate FAILED", file=sys.stderr)
        return 1
    print("coverage gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
