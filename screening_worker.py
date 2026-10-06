#!/usr/bin/env python3
"""Sanitized multi-stage screening worker using synthetic or user-supplied JSON.

The worker reports candidate IDs and gate outcomes only. It never prints or
transforms expression text. The built-in demo records are fictional.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

DEMO_RECORDS = [
    {
        "candidate_id": "demo-001",
        "candidate_type": "NUMERIC",
        "coverage": 0.72,
        "history_coverage": 0.91,
        "checks": {"metadata": "PASS", "quality": "PASS"},
    },
    {
        "candidate_id": "demo-002",
        "candidate_type": "VECTOR",
        "coverage": 0.44,
        "history_coverage": 0.68,
        "checks": {"metadata": "PASS", "quality": "PENDING"},
    },
    {
        "candidate_id": "demo-003",
        "candidate_type": "NUMERIC",
        "coverage": 0.12,
        "history_coverage": 0.88,
        "checks": {"metadata": "PASS", "quality": "PASS"},
    },
    {
        "candidate_id": "demo-004",
        "candidate_type": "TEXT",
        "coverage": 0.83,
        "history_coverage": 0.79,
        "checks": {"metadata": "FAIL", "quality": "PASS"},
    },
]


def _valid_fraction(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1


def screen_record(
    record: Any, *, min_coverage: float, min_history_coverage: float
) -> tuple[str, str]:
    """Return a disposition and reason; pending checks remain pending."""
    if not isinstance(record, dict):
        return "REJECTED", "invalid_record"
    candidate_id = record.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        return "REJECTED", "missing_candidate_id"
    if record.get("candidate_type") not in {"NUMERIC", "VECTOR"}:
        return "REJECTED", "unsupported_type"
    if not _valid_fraction(record.get("coverage")):
        return "REJECTED", "invalid_coverage"
    if record["coverage"] < min_coverage:
        return "REJECTED", "coverage_below_threshold"
    if not _valid_fraction(record.get("history_coverage")):
        return "REJECTED", "invalid_history_coverage"
    if record["history_coverage"] < min_history_coverage:
        return "REJECTED", "history_coverage_below_threshold"

    checks = record.get("checks")
    if not isinstance(checks, dict) or not checks:
        return "HELD", "checks_missing"
    states = set(checks.values())
    if "FAIL" in states:
        return "REJECTED", "check_failed"
    if states - {"PASS"}:
        return "HELD", "check_incomplete"
    return "SELECTED", "all_stages_passed"


def screen_records(
    records: list[Any], *, min_coverage: float, min_history_coverage: float, limit: int
) -> dict[str, Any]:
    selected: list[str] = []
    held: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    seen: set[str] = set()

    for record in records:
        disposition, reason = screen_record(
            record,
            min_coverage=min_coverage,
            min_history_coverage=min_history_coverage,
        )
        candidate_id = record.get("candidate_id") if isinstance(record, dict) else None
        if disposition == "SELECTED":
            if candidate_id in seen:
                rejected.append({"candidate_id": candidate_id, "reason": "duplicate_id"})
            elif len(selected) >= limit:
                rejected.append({"candidate_id": candidate_id, "reason": "result_limit"})
            else:
                seen.add(candidate_id)
                selected.append(candidate_id)
        elif disposition == "HELD":
            held.append({"candidate_id": str(candidate_id or ""), "reason": reason})
        else:
            rejected.append({"candidate_id": str(candidate_id or ""), "reason": reason})

    return {
        "selected_ids": selected,
        "held": held,
        "rejected": rejected,
        "counts": {
            "input": len(records),
            "selected": len(selected),
            "held": len(held),
            "rejected": len(rejected),
        },
        "note": "Only IDs and screening reasons are returned; expression text is not read or emitted.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, help="JSON file containing a list of candidate records")
    parser.add_argument("--demo", action="store_true", help="Use the built-in fictional examples")
    parser.add_argument("--min-coverage", type=float, default=0.50)
    parser.add_argument("--min-history-coverage", type=float, default=0.75)
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    if (args.input is None) == (not args.demo):
        parser.error("provide exactly one of --input or --demo")
    if not 0 <= args.min_coverage <= 1 or not 0 <= args.min_history_coverage <= 1:
        parser.error("coverage thresholds must be between 0 and 1")
    if args.limit < 0:
        parser.error("--limit must be non-negative")

    records = DEMO_RECORDS if args.demo else json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        parser.error("input JSON must contain a list")
    print(
        json.dumps(
            screen_records(
                records,
                min_coverage=args.min_coverage,
                min_history_coverage=args.min_history_coverage,
                limit=args.limit,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()


