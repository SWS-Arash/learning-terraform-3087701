#!/usr/bin/env python3
"""
Promote KEDB entries from template -> active when patterns match analysis output.
READ-ONLY: only updates local KEDB JSON files, never touches Jira/Datadog.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Map toil/pain categories to KEDB IDs
CATEGORY_TO_KEDB = {
    "MONITOR_NOISE": ["KEDB-0001"],
    "SECRET_MGMT": ["KEDB-0002", "KEDB-0004"],
    "K8S_CAPACITY": ["KEDB-0003", "KEDB-0010"],
    "ACCESS_IAM": ["KEDB-0005"],
    "SECURITY_VULN": ["KEDB-0008"],
    "DBA_PERF": ["KEDB-0006", "KEDB-0007"],
    "DEPLOYMENT": ["KEDB-0009"],
    "ACCESS_GRANT": ["KEDB-0005"],
    "SECRET_ROTATE": ["KEDB-0002", "KEDB-0004"],
    "CAPACITY_SCALE": ["KEDB-0003", "KEDB-0010"],
    "MONITOR_TUNING": ["KEDB-0001"],
    "DEPLOY_RERUN": ["KEDB-0009"],
}


def load_stats(report_dir: Path) -> tuple[dict, dict]:
    pain_files = sorted(report_dir.glob("pain_points_stats_*.json"), reverse=True)
    toil_files = sorted(report_dir.glob("toil_stats_*.json"), reverse=True)
    pain = json.loads(pain_files[0].read_text()) if pain_files else {}
    toil = json.loads(toil_files[0].read_text()) if toil_files else {}
    return pain, toil


def promote_kedb(kedb_dir: Path, pain: dict, toil: dict, dry_run: bool) -> list[str]:
    promoted = []
    entries_dir = kedb_dir / "entries"

    # Collect categories with evidence
    active_categories: set[str] = set()
    for cat in pain.get("jira", {}).get("by_category", {}):
        if cat != "UNCATEGORIZED":
            active_categories.add(cat)
    for cat in toil.get("by_category", {}):
        active_categories.add(cat)

    # Collect ticket keys from recurring patterns
    ticket_keys: dict[str, list[str]] = {}
    for item in pain.get("jira", {}).get("top_recurring", []):
        for key in item.get("tickets", []):
            ticket_keys.setdefault(key, []).append(item.get("pattern", ""))
    for item in toil.get("recurring_patterns", []):
        for ex in item.get("examples", []):
            key = ex.get("key", "")
            if key:
                ticket_keys.setdefault(key, []).append(item.get("pattern", ""))

    for category in active_categories:
        for kedb_id in CATEGORY_TO_KEDB.get(category, []):
            entry_path = entries_dir / f"{kedb_id}.json"
            if not entry_path.exists():
                continue
            entry = json.loads(entry_path.read_text())
            if entry.get("status") == "resolved":
                continue

            entry["status"] = "active"
            # Link tickets whose summaries match KEDB title keywords
            title_words = set(re.findall(r"\w{4,}", entry.get("title", "").lower()))
            linked = set(entry.get("related_jira", []))
            for key, patterns in ticket_keys.items():
                for pat in patterns:
                    if title_words & set(re.findall(r"\w{4,}", pat.lower())):
                        linked.add(key)
            entry["related_jira"] = sorted(linked)

            if not dry_run:
                entry_path.write_text(json.dumps(entry, indent=2) + "\n")
            promoted.append(f"{kedb_id} -> active ({category}, {len(linked)} tickets linked)")

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
