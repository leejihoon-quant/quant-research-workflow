#!/usr/bin/env python3
"""Small, offline demo of a quantitative research evidence pipeline.

The bundled records are fictional examples, not results from any platform.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = {"record_id", "region", "delay", "family", "metrics", "checks", "source"}
VALID_CHECK_STATES = {"PASS", "FAIL", "PENDING", "UNKNOWN"}


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load records and reject malformed or duplicate entries without discarding evidence."""
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("The input must be a JSON list of records.")

    seen: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not REQUIRED_FIELDS.issubset(record):
            raise ValueError(f"Record {index} is missing required fields.")
        record_id = record["record_id"]
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise ValueError(f"Record {index} has an empty or duplicate record_id.")
        seen.add(record_id)
        if record["source"] != "synthetic-example":
            raise ValueError(f"Record {record_id} is not marked as synthetic.")
        for name, value in record["metrics"].items():
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"Record {record_id} has an invalid metric: {name}.")
        for name, state in record["checks"].items():
            if state not in VALID_CHECK_STATES:
                raise ValueError(f"Record {record_id} has an invalid check state: {name}.")
    return records


def query_records(
    records: list[dict[str, Any]], region: str | None, delay: int | None, family: str | None
) -> list[dict[str, Any]]:
    """Filter records by scope and family; keep all recorded check states intact."""
    return [
        record
        for record in records
        if (region is None or record["region"] == region)
        and (delay is None or record["delay"] == delay)
        and (family is None or record["family"] == family)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(__file__).with_name("sample_records.json"))
    parser.add_argument("--region")
    parser.add_argument("--delay", type=int)
    parser.add_argument("--family")
    args = parser.parse_args()

    results = query_records(load_records(args.input), args.region, args.delay, args.family)
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
