#!/usr/bin/env python3
"""Collect Datadog monitor alert history for CloudOps and DBA teams."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def dd_headers() -> dict:
    return {
        "DD-API-KEY": env("DD_API_KEY"),
        "DD-APPLICATION-KEY": env("DD_APP_KEY"),
        "Content-Type": "application/json",
    }


def dd_base() -> str:
    site = os.environ.get("DD_SITE", "datadoghq.com")
    return f"https://api.{site}"


def list_monitors(base: str, headers: dict, tag_filter: str | None) -> list[dict]:
    monitors: list[dict] = []
    page = 0
    while True:
        params: dict = {"page": page, "page_size": 100}
        if tag_filter:
            params["monitor_tags"] = tag_filter
        resp = requests.get(f"{base}/api/v1/monitor", headers=headers, params=params, timeout=120)
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        monitors.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return monitors


def get_monitor_groups(base: str, headers: dict, monitor_id: int, from_ts: int, to_ts: int) -> list[dict]:
    """Fetch alert groups for a monitor in the time window."""
    resp = requests.get(
        f"{base}/api/v1/monitor/{monitor_id}/groups",
        headers=headers,
        params={"from": from_ts, "to": to_ts},
        timeout=120,
    )
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("groups", {})


def search_events(base: str, headers: dict, query: str, from_ts: int, to_ts: int) -> list[dict]:
    """Search Datadog events (alert notifications) in time range."""
    events: list[dict] = []
    start = from_ts
    while start < to_ts:
        resp = requests.get(
            f"{base}/api/v1/events",
            headers=headers,
            params={
                "start": start,
                "end": to_ts,
                "priority": "normal",
                "sources": "monitor alert",
                "unaggregated": "true",
                "count": 1000,
            },
            timeout=120,
        )
        resp.raise_for_status()
        batch = resp.json().get("events", [])
        if not batch:
            break
        events.extend(batch)
        last_ts = max(e.get("date_happened", start) for e in batch)
        if last_ts <= start:
            break
        start = last_ts + 1
    return events


def parse_date(date_str: str) -> int:
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def flatten_monitor(m: dict) -> dict:
    return {
        "id": m.get("id"),
        "name": m.get("name"),
        "type": m.get("type"),
        "query": m.get("query"),
        "message": (m.get("message") or "")[:500],
        "tags": "|".join(m.get("tags", []) or []),
        "priority": m.get("priority"),
        "overall_state": m.get("overall_state"),
        "created": m.get("created"),
        "modified": m.get("modified"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Datadog alert history")
    parser.add_argument("--output", type=Path, default=Path("docs/aco-ops/data/datadog"))
    parser.add_argument("--tag-filter", help="Monitor tag filter, e.g. team:cloudops")
    args = parser.parse_args()

    base = dd_base()
    headers = dd_headers()
    start_date = os.environ.get("DD_START_DATE", "2026-01-01")
    from_ts = parse_date(start_date)
    to_ts = int(datetime.now(timezone.utc).timestamp())

    team_tags = [t.strip() for t in os.environ.get("DD_TEAM_TAGS", "team:cloudops,team:dba").split(",") if t.strip()]

    all_monitors: list[dict] = []
    seen_ids: set[int] = set()
    for tag in team_tags:
        print(f"Fetching monitors with tag: {tag}")
        for m in list_monitors(base, headers, tag):
            mid = m.get("id")
            if mid not in seen_ids:
                seen_ids.add(mid)
                all_monitors.append(m)

    # Also fetch events for monitor alerts in range
    event_queries = [f'tags:"{tag}"' for tag in team_tags]
    combined_query = " OR ".join(event_queries) if event_queries else "source:monitor"
    print(f"Searching events: {combined_query}")
    events = search_events(base, headers, combined_query, from_ts, to_ts)
    print(f"Fetched {len(events)} alert events, {len(all_monitors)} monitors")

    args.output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    monitors_path = args.output / f"monitors_{timestamp}.json"
    events_path = args.output / f"alert_events_{timestamp}.json"
    csv_path = args.output / f"monitors_{timestamp}.csv"

    with open(monitors_path, "w", encoding="utf-8") as f:
        json.dump({"count": len(all_monitors), "monitors": all_monitors}, f, indent=2)

    with open(events_path, "w", encoding="utf-8") as f:
        json.dump({"count": len(events), "from_ts": from_ts, "to_ts": to_ts, "events": events}, f, indent=2)

    rows = [flatten_monitor(m) for m in all_monitors]
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Wrote {monitors_path}")
    print(f"Wrote {events_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
