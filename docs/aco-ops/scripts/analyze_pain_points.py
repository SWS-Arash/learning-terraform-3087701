#!/usr/bin/env python3
"""Analyze Jira + Datadog data to identify pain points and generate reports."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Classification rules — extend after reviewing live data
CATEGORY_PATTERNS: dict[str, list[str]] = {
    "MONITOR_NOISE": [
        r"false.?positive", r"noisy", r"flapping", r"threshold", r"alert.?storm",
        r"monitor.?tuning", r"datadog", r"pagerduty.*noise", r"alert.?fatigue",
    ],
    "SECRET_MGMT": [
        r"secret", r"certificate.*expir", r"cert.*expir", r"token.*expir",
        r"key.?rotation", r"vault", r"credential", r"password.*expir", r"tls",
        r"external.?secret", r"aws.?secret",
    ],
    "K8S_CAPACITY": [
        r"oom", r"out.?of.?memory", r"cpu.?throttl", r"evict", r"pending.?pod",
        r"resource.?quota", r"hpa", r"node.?pressure", r"disk.?full", r"pvc",
        r"capacity", r"autoscal", r"memory.?limit", r"cpu.?limit",
    ],
    "ACCESS_IAM": [
        r"access.?denied", r"permission", r"rbac", r"unauthorized", r"403",
        r"sso", r"saml", r"vpn", r"firewall.?rule", r"iam", r"role.?binding",
        r"service.?account", r"kubeconfig",
    ],
    "SECURITY_VULN": [
        r"cve", r"vulnerabilit", r"patch", r"misconfig", r"security.?scan",
        r"wiz", r"prisma", r"guardduty", r"exposed", r"compliance",
    ],
    "DBA_PERF": [
        r"deadlock", r"lock.?wait", r"slow.?query", r"replication.?lag",
        r"connection.?pool", r"database.?down", r"postgres", r"mysql", r"oracle",
        r"sql.?server", r"backup.?fail", r"restore", r"index",
    ],
    "NETWORK_DNS": [
        r"dns", r"ingress", r"load.?balancer", r"timeout", r"connection.?refused",
        r"network.?policy", r"route53", r"nat.?gateway",
    ],
    "DEPLOYMENT": [
        r"deploy.?fail", r"rollout", r"helm", r"argocd", r"gitops",
        r"image.?pull", r"crashloop", r"config.?drift", r"rollback",
    ],
}


def classify_text(text: str) -> list[str]:
    if not text:
        return ["UNCATEGORIZED"]
    text_lower = text.lower()
    matches = []
    for category, patterns in CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                matches.append(category)
                break
    return matches or ["UNCATEGORIZED"]


def load_latest_csv(directory: Path, prefix: str) -> list[dict]:
    files = sorted(directory.glob(f"{prefix}*.csv"), reverse=True)
    if not files:
        return []
    with open(files[0], newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_latest_json_events(directory: Path) -> list[dict]:
    files = sorted(directory.glob("alert_events_*.json"), reverse=True)
    if not files:
        return []
    with open(files[0], encoding="utf-8") as f:
        return json.load(f).get("events", [])


def analyze_jira(rows: list[dict]) -> dict:
    by_category: Counter = Counter()
    by_team: Counter = Counter()
    by_type: Counter = Counter()
    by_status: Counter = Counter()
    recurring: defaultdict[str, list] = defaultdict(list)

    for row in rows:
        text = " ".join(filter(None, [row.get("summary", ""), row.get("description", ""), row.get("labels", "")]))
        categories = classify_text(text)
        for cat in categories:
            by_category[cat] += 1
        by_team[row.get("scrum_team", "Unknown")] += 1
        by_type[row.get("issue_type", "Unknown")] += 1
        by_status[row.get("status", "Unknown")] += 1

        # Group similar summaries (first 60 chars normalized)
        norm = re.sub(r"\s+", " ", (row.get("summary") or "")[:60].lower().strip())
        if norm:
            recurring[norm].append(row.get("key"))

    top_recurring = sorted(
        [(k, v) for k, v in recurring.items() if len(v) >= 2],
        key=lambda x: len(x[1]),
        reverse=True,
    )[:20]

    return {
        "total": len(rows),
        "by_category": dict(by_category.most_common()),
        "by_team": dict(by_team.most_common()),
        "by_type": dict(by_type.most_common()),
        "by_status": dict(by_status.most_common()),
        "top_recurring": [{"pattern": k, "count": len(v), "tickets": v} for k, v in top_recurring],
    }


def analyze_datadog(events: list[dict], monitors: list[dict]) -> dict:
    by_monitor: Counter = Counter()
    by_tag: Counter = Counter()

    for event in events:
        title = event.get("title", "") or event.get("text", "")
        by_monitor[title[:100]] += 1
        for tag in event.get("tags", []) or []:
            if tag.startswith("team:") or tag.startswith("service:"):
                by_tag[tag] += 1

    noisy_monitors = []
    for m in monitors:
        name = m.get("name", "")
        tags = m.get("tags", "")
        noisy_monitors.append({"name": name, "tags": tags, "state": m.get("overall_state")})

    return {
        "total_events": len(events),
        "total_monitors": len(monitors),
        "top_alerting_monitors": dict(by_monitor.most_common(20)),
        "by_tag": dict(by_tag.most_common(20)),
    }


def generate_markdown(jira_stats: dict, dd_stats: dict) -> str:
    lines = [
        "# Pain Points Analysis Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Executive Summary",
        "",
        f"- **Jira tickets analyzed:** {jira_stats.get('total', 0)}",
        f"- **Datadog alert events:** {dd_stats.get('total_events', 0)}",
        f"- **Datadog monitors in scope:** {dd_stats.get('total_monitors', 0)}",
        "",
        "## Top Pain Point Categories (Jira)",
        "",
        "| Category | Count | Recommended Lever |",
        "|----------|-------|-------------------|",
    ]

    lever_map = {
        "MONITOR_NOISE": "Monitor tuning, composite alerts, alert grouping",
        "SECRET_MGMT": "Vault rotation, ESO, pre-expiry automation",
        "K8S_CAPACITY": "Right-sizing, VPA/HPA, capacity planning",
        "ACCESS_IAM": "IAM automation, access reviews, break-glass",
        "SECURITY_VULN": "Patch cadence, image gates, remediation SLAs",
        "DBA_PERF": "Query tuning, maintenance windows, pooling",
        "NETWORK_DNS": "IaC, health-check tuning, DNS automation",
        "DEPLOYMENT": "GitOps, canary, auto-rollback",
        "UNCATEGORIZED": "Manual triage — refine classification rules",
    }

    for cat, count in sorted(jira_stats.get("by_category", {}).items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {count} | {lever_map.get(cat, 'TBD')} |")

    lines.extend([
        "",
        "## Recurring Jira Patterns (≥2 occurrences)",
        "",
    ])
    for item in jira_stats.get("top_recurring", []):
        lines.append(f"- **{item['pattern']}** ({item['count']}x): {', '.join(item['tickets'][:5])}")

    lines.extend([
        "",
        "## Top Datadog Alerting Monitors",
        "",
    ])
    for name, count in list(dd_stats.get("top_alerting_monitors", {}).items())[:15]:
        lines.append(f"- {name}: **{count}** events")

    lines.extend([
        "",
        "## Recommended Actions",
        "",
        "1. Map top 5 recurring patterns to KEDB entries (see `kedb/entries/`)",
        "2. Tune or silence noisy Datadog monitors with documented justification",
        "3. Implement auto-healing for K8S_CAPACITY and SECRET_MGMT categories",
        "4. Schedule quarterly access reviews for ACCESS_IAM items",
        "5. Align security patch SLAs with SECURITY_VULN backlog",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze pain points from Jira and Datadog")
    parser.add_argument("--jira", type=Path, default=Path("docs/aco-ops/data/jira"))
    parser.add_argument("--datadog", type=Path, default=Path("docs/aco-ops/data/datadog"))
    parser.add_argument("--output", type=Path, default=Path("docs/aco-ops/reports"))
    args = parser.parse_args()

    jira_rows = load_latest_csv(args.jira, "jira_issues_")
    dd_events = load_latest_json_events(args.datadog)
    dd_monitors = load_latest_csv(args.datadog, "monitors_")

    jira_stats = analyze_jira(jira_rows)
    dd_stats = analyze_datadog(dd_events, dd_monitors)

    args.output.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    stats_path = args.output / f"pain_points_stats_{timestamp}.json"
    report_path = args.output / "pain-points-summary.md"

    combined = {"jira": jira_stats, "datadog": dd_stats, "generated_at": timestamp}
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)

    report = generate_markdown(jira_stats, dd_stats)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Wrote {stats_path}")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
