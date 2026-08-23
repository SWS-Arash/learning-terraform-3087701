#!/usr/bin/env python3
"""Collect ACO Jira Incidents and Bugs for Antuit CloudOps and Antuit DBA."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def jira_search(base_url: str, auth: tuple[str, str], jql: str, fields: list[str]) -> list[dict]:
    url = urljoin(base_url.rstrip("/") + "/", "rest/api/3/search/jql")
    issues: list[dict] = []
    next_page_token: str | None = None

    while True:
        payload: dict = {
            "jql": jql,
            "maxResults": 100,
            "fields": fields,
        }
        if next_page_token:
            payload["nextPageToken"] = next_page_token

        resp = requests.post(url, json=payload, auth=auth, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        issues.extend(data.get("issues", []))
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    return issues


def flatten_issue(issue: dict, scrum_field: str) -> dict:
    fields = issue.get("fields", {})
    scrum_team = fields.get(scrum_field)
    if isinstance(scrum_team, dict):
        scrum_team = scrum_team.get("value") or scrum_team.get("name")

    components = [c.get("name", "") for c in fields.get("components", []) or []]
    labels = fields.get("labels", []) or []

    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "issue_type": (fields.get("issuetype") or {}).get("name"),
        "status": (fields.get("status") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "scrum_team": scrum_team,
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "resolved": fields.get("resolutiondate"),
        "components": "|".join(components),
        "labels": "|".join(labels),
        "description": _extract_text(fields.get("description")),
    }


def _extract_text(description) -> str:
    if description is None:
        return ""
    if isinstance(description, str):
        return description[:2000]
    # ADF (Atlassian Document Format) — extract plain text recursively
    texts: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for child in node.get("content", []) or []:
                walk(child)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(description)
    return " ".join(texts)[:2000]


def build_jql(project: str, teams: list[str], start_date: str, scrum_field: str) -> str:
    team_list = ", ".join(f'"{t}"' for t in teams)
    return (
        f'project = {project} '
        f'AND issuetype in (Incident, Bug) '
        f'AND "{scrum_field}" in ({team_list}) '
        f'AND created >= "{start_date}" '
        f"ORDER BY created DESC"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect ACO Jira incidents and bugs")
    parser.add_argument("--output", type=Path, default=Path("docs/aco-ops/data/jira"))
    parser.add_argument("--jql", help="Override default JQL query")
    args = parser.parse_args()

    base_url = env("JIRA_BASE_URL")
    email = env("JIRA_USER_EMAIL")
    token = env("JIRA_API_TOKEN")
    project = os.environ.get("JIRA_PROJECT", "ACO")
    scrum_field = os.environ.get("JIRA_SCRUM_TEAM_FIELD", "Scrum Team")
    teams = [t.strip() for t in os.environ.get("JIRA_TEAMS", "Antuit CloudOps,Antuit DBA").split(",")]
    start_date = os.environ.get("JIRA_START_DATE", "2026-01-01")

    jql = args.jql or build_jql(project, teams, start_date, scrum_field)
    fields = [
        "summary", "issuetype", "status", "priority", "assignee", "reporter",
        "created", "updated", "resolutiondate", "components", "labels", "description",
        scrum_field,
    ]

    print(f"JQL: {jql}")
    issues = jira_search(base_url, (email, token), jql, fields)
    print(f"Fetched {len(issues)} issues")

    args.output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    json_path = args.output / f"jira_issues_{timestamp}.json"
    csv_path = args.output / f"jira_issues_{timestamp}.csv"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"jql": jql, "count": len(issues), "issues": issues}, f, indent=2)

    rows = [flatten_issue(i, scrum_field) for i in issues]
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
