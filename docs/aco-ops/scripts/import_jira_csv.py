#!/usr/bin/env python3
"""Convert a Jira CSV export to the format expected by analyze_pain_points.py."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Jira CSV export for analysis")
    parser.add_argument("input_csv", type=Path, help="Jira CSV export path")
    parser.add_argument("--output", type=Path, default=Path("docs/aco-ops/data/jira"))
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = args.output / f"jira_issues_{timestamp}.csv"

    # Map common Jira CSV column names to our schema
    field_map = {
        "Issue key": "key",
        "Summary": "summary",
        "Issue Type": "issue_type",
        "Status": "status",
        "Priority": "priority",
        "Assignee": "assignee",
        "Reporter": "reporter",
        "Created": "created",
        "Updated": "updated",
        "Resolved": "resolved",
        "Components": "components",
        "Labels": "labels",
        "Description": "description",
        "Scrum Team": "scrum_team",
        "Custom field (Scrum Team)": "scrum_team",
    }

    with open(args.input_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            normalized = {}
            for src, dst in field_map.items():
                if src in row and row[src]:
                    normalized[dst] = row[src]
            # Fallback: copy any unmapped fields from summary-like columns
            normalized.setdefault("key", row.get("Issue key", ""))
            normalized.setdefault("summary", row.get("Summary", ""))
            normalized.setdefault("description", row.get("Description", ""))
            normalized.setdefault("labels", row.get("Labels", ""))
            normalized.setdefault("scrum_team", row.get("Scrum Team") or row.get("Custom field (Scrum Team)", ""))
            rows.append(normalized)

    if not rows:
        raise SystemExit(f"No rows found in {args.input_csv}")

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
