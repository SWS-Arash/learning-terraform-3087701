#!/usr/bin/env python3
"""
Promote KEDB entries from template -> active when patterns match analysis output.
READ-ONLY: only updates local KEDB JSON files, never touches Jira/Datadog.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CATEGORY_TO_KEDB: dict[str, list[str]] = {
    "MONITOR_NOISE": ["KEDB-0001"],
    "MONITOR_TUNING": ["KEDB-0001"],
    "SECRET_MGMT": ["KEDB-0002", "KEDB-0004"],
    "SECRET_ROTATE": ["KEDB-0002", "KEDB-0004"],
    "K8S_CAPACITY": ["KEDB-0003", "KEDB-0010"],
    "CAPACITY_SCALE": ["KEDB-0003", "KEDB-0010"],
    "ACCESS_IAM": ["KEDB-0005"],
    "ACCESS_GRANT": ["KEDB-0005"],
    "SECURITY_VULN": ["KEDB-0008"],
    "DBA_PERF": ["KEDB-0006", "KEDB-0007"],
    "DEPLOYMENT": ["KEDB-0009"],
    "DEPLOY_RERUN": ["KEDB-0009"],
}


def load_stats(report_dir: Path) -> tuple[dict, dict]:
    pain_files = sorted(report_dir.glob("pain_points_stats_*.json"), reverse=True)
    toil_files = sorted(report_dir.glob("toil_stats_*.json"), reverse=True)
    pain = json.loads(pain_files[0].read_text()) if pain_files else {}
    toil = json.loads(toil_files[0].read_text()) if toil_files else {}
    return pain, toil


def tickets_for_category(toil: dict, category: str) -> list[str]:
    keys = []
    for ticket in toil.get("toil_tickets_sample", []):
        if category in ticket.get("categories", []):
            keys.append(ticket["key"])
    return keys


def promote_kedb(kedb_dir: Path, pain: dict, toil: dict, dry_run: bool) -> list[str]:
    promoted: list[str] = []
    seen: set[str] = set()
    entries_dir = kedb_dir / "entries"

    active_categories: set[str] = set()
    for cat in pain.get("jira", {}).get("by_category", {}):
        if cat != "UNCATEGORIZED":
            active_categories.add(cat)
    for cat in toil.get("by_category", {}):
        active_categories.add(cat)

    for category in sorted(active_categories):
        for kedb_id in CATEGORY_TO_KEDB.get(category, []):
            if kedb_id in seen:
                continue
            entry_path = entries_dir / f"{kedb_id}.json"
            if not entry_path.exists():
                continue

            entry = json.loads(entry_path.read_text())
            if entry.get("status") == "resolved":
                continue

            linked = set(entry.get("related_jira", []))
            linked.update(tickets_for_category(toil, category))

            entry["status"] = "active"
            entry["related_jira"] = sorted(linked)
            entry["frequency"] = f"{toil.get('by_category', {}).get(category, pain.get('jira', {}).get('by_category', {}).get(category, 0))} in sample window"

            if not dry_run:
                entry_path.write_text(json.dumps(entry, indent=2) + "\n")

            seen.add(kedb_id)
            promoted.append(f"{kedb_id} -> active ({category}, {len(linked)} tickets)")

    return promoted


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote KEDB entries based on analysis")
    parser.add_argument("--reports", type=Path, default=Path("docs/aco-ops/reports"))
    parser.add_argument("--kedb", type=Path, default=Path("docs/aco-ops/kedb"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pain, toil = load_stats(args.reports)
    if not pain and not toil:
        raise SystemExit(f"No analysis stats found in {args.reports}. Run run_full_analysis.sh first.")

    promoted = promote_kedb(args.kedb, pain, toil, args.dry_run)
    for line in promoted:
        print(line)
    print(f"\nPromoted {len(promoted)} KEDB entries.")


if __name__ == "__main__":
    main()
