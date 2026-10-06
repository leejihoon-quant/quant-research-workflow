# Quantitative Research Workflow (Portfolio Overview)

A personal research engineering project exploring how quantitative alpha research can be organized into a repeatable, auditable workflow.

## What it demonstrates

- Python tooling for organizing research evidence by market region and delay setting.
- Structured records that preserve metrics, checks, provenance, and negative results instead of keeping only selected winners.
- Offline validation and command-line lookup for reviewing prior research records.
- A small synthetic-data pipeline demo and an adapted, callback-based collection helper.

## Demo

The demo validates a JSON record file, checks for duplicate IDs and malformed metric/check values, then filters records by region, delay, and idea family. It preserves `PENDING`, `UNKNOWN`, and failed checks in the output.

```bash
python pipeline_demo.py --region DEMO --delay 1
python pipeline_demo.py --family trend
```

`sample_records.json` is synthetic teaching data. Its metrics do not represent actual research or performance.

The `resilient_collection.py` module shows callback-based queue retries, cache validation, and reporting unresolved items. It is an adapted, standalone helper with no platform client, credentials, strategy logic, or private records.

## Workflow at a glance

1. Organize collected research records into a consistent regional structure.
2. Validate metadata and outcomes while retaining source references and missing or failed checks.
3. Build an offline index and query it by research scope or idea family.
4. Review evidence before deciding whether further research is warranted.

## Technology

Python standard library, JSON, and command-line tools.

## Scope and data

This repository contains a sanitized overview and small code examples. It intentionally contains no platform credentials, personal account data, proprietary expressions, simulation exports, real performance claims, or execution code. The project is for research organization and learning; it is not investment advice or a production trading system.
