#!/usr/bin/env python3
"""
Identify repeating manual-work (toil) patterns in ACO Jira tickets.
READ-ONLY: consumes exported CSV/JSON only — never writes to Jira.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Toil category patterns — ordered by specificity
TOIL_PATTERNS: dict[str, list[str]] = {
    "ACCESS_GRANT": [
        r"\bgrant\b.*\baccess\b", r"\badd\b.*\buser\b", r"\brbac\b", r"\bvpn\b.*\baccess\b",
        r"\bservice account\b", r"\bpermission\b", r"\biam\b", r"\brole\b.*\bbinding\b",
        r"\bkubeconfig\b", r"\bsso\b", r"\bsaml\b",
    ],
    "SECRET_ROTATE": [
        r"\brotate\b.*\bsecret\b", r"\brenew\b.*\bcert", r"\bcertificate\b.*\bexpir",
        r"\bupdate\b.*\bpassword\b", r"\brefresh\b.*\btoken\b", r"\btls\b", r"\bvault\b",
        r"\bexternal.?secret\b", r"\bcredential\b.*\brotat",
    ],
    "CAPACITY_SCALE": [
        r"\bincrease\b.*\bmemory\b", r"\bscale\b.*\bup\b", r"\badd\b.*\bnode\b",
        r"\bincrease\b.*\bdisk\b", r"\bbump\b.*\blimit", r"\bresize\b", r"\bhpa\b",
        r"\bresource\b.*\bquota\b", r"\bexpand\b.*\bpvc\b",
    ],
    "MONITOR_TUNING": [
        r"\bsilence\b.*\balert\b", r"\badjust\b.*\bthreshold\b", r"\bfalse positive\b",
        r"\bnoisy\b.*\bmonitor\b", r"\bmonitor\b.*\btun", r"\bdatadog\b.*\balert\b",
        r"\bpagerduty\b.*\bnoise\b",
    ],
    "DEPLOY_RERUN": [
        r"\bre-?run\b.*\bpipeline\b", r"\brestart\b.*\bpod\b", r"\bforce sync\b",
        r"\brollback\b", r"\bargocd\b.*\bsync\b", r"\bhelm\b.*\bupgrade\b",
        r"\bcrashloop\b", r"\bredeploy\b",
    ],
    "DATA_FIX": [
        r"\brun\b.*\bscript\b.*\bmanual", r"\bexecute\b.*\bsql\b", r"\bone-?off\b.*\bfix\b",
        r"\bad-?hoc\b.*\bquer", r"\bmanual\b.*\bintervention\b", r"\bdata\b.*\bfix\b",
        r"\bpatch\b.*\bprod\b",
    ],
    "PROVISION": [
        r"\bcreate\b.*\bnamespace\b", r"\bnew\b.*\benvironment\b", r"\bprovision\b.*\bdb\b",
        r"\bcreate\b.*\bbucket\b", r"\bnew\b.*\bcluster\b", r"\bspin up\b",
        r"\brequest\b.*\binfrastructure\b",
    ],
    "TROUBLESHOOT_HANDOFF": [
        r"\bplease check\b", r"\bcan someone\b.*\blook\b", r"\binvestigate\b",
        r"\bneed help with\b", r"\bassistance needed\b",
    ],
}


def load_jira_rows(jira_dir: Path) -> list[dict]:
    files = sorted(jira_dir.glob("jira_issues_*.csv"), reverse=True)
    if not files:
        raise SystemExit(f"No jira_issues_*.csv found in {jira_dir}")
    with open(files[0], newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def classify_toil(text: str) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    hits = []
    for category, patterns in TOIL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lower):
                hits.append(category)
                break
    return hits


def normalize_summary(summary: str) -> str:
    """Cluster similar summaries by removing ticket-specific tokens."""
    s = summary.lower().strip()
    s = re.sub(r"\b(aco|inc|bug|prod|dev|uat|qa)-\d+\b", "<id>", s)
    s = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "<date>", s)
    s = re.sub(r"\b\d+\b", "<n>", s)
    s = re.sub(r"\s+", " ", s)
    return s[:80]


def analyze(rows: list[dict]) -> dict:
    by_category: Counter = Counter()
    by_team: Counter = Counter()
    by_normalized: defaultdict[str, list] = defaultdict(list)
    ticket_toil: list[dict] = []

    for row in rows:
        summary = row.get("summary", "") or ""
        description = row.get("description", "") or ""
        labels = row.get("labels", "") or ""
        text = f"{summary} {description} {labels}"
        categories = classify_toil(text)
        key = row.get("key", "")

        if categories:
            for cat in categories:
                by_category[cat] += 1
            ticket_toil.append({
                "key": key,
                "summary": summary,
                "team": row.get("scrum_team", ""),
                "categories": categories,
                "status": row.get("status", ""),
            })

        team = row.get("scrum_team") or "Unknown"
        by_team[team] += 1

        norm = normalize_summary(summary)
        if norm:
            by_normalized[norm].append({
                "key": key,
                "summary": summary,
                "team": team,
                "categories": categories,
            })

    recurring = sorted(
        [(k, v) for k, v in by_normalized.items() if len(v) >= 2],
        key=lambda x: len(x[1]),
        reverse=True,
    )

    return {
        "total_tickets": len(rows),
        "toil_tickets": len(ticket_toil),
        "toil_pct": round(100 * len(ticket_toil) / max(len(rows), 1), 1),
        "by_category": dict(by_category.most_common()),
        "by_team": dict(by_team.most_common()),
        "recurring_patterns": [
            {
                "pattern": k,
                "count": len(v),
                "examples": v[:5],
                "categories": list({c for t in v for c in t.get("categories", [])}),
            }
            for k, v in recurring[:30]
        ],
        "toil_tickets_sample": ticket_toil[:50],
    }


def generate_report(stats: dict) -> str:
    lines = [
        "# ACO Toil Analysis — Repeating Manual Requests",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "**Mode: Read-only analysis — no Jira/Datadog changes made.**",
        "",
        "## Summary",
        "",
        f"- **Total tickets analyzed:** {stats['total_tickets']}",
        f"- **Tickets classified as toil:** {stats['toil_tickets']} ({stats['toil_pct']}%)",
        "",
        "## Toil by Category",
        "",
        "| Category | Count | Automation lever |",
        "|----------|-------|------------------|",
    ]

    levers = {
        "ACCESS_GRANT": "IAM-as-code, self-service portal, OIDC group sync",
        "SECRET_ROTATE": "ESO, cert-manager, rotation automation",
        "CAPACITY_SCALE": "VPA/HPA, cluster autoscaler, quota templates",
        "MONITOR_TUNING": "Monitor-as-code, noise audit, composite alerts",
        "DEPLOY_RERUN": "ArgoCD auto-sync/rollback, Reloader",
        "DATA_FIX": "GitOps scripts, scheduled jobs",
        "PROVISION": "Terraform modules, self-service catalog",
        "TROUBLESHOOT_HANDOFF": "Runbooks, auto-healing, better observability",
    }

    for cat, count in stats.get("by_category", {}).items():
        lines.append(f"| {cat} | {count} | {levers.get(cat, 'TBD')} |")

    lines.extend(["", "## Top Recurring Request Patterns (≥2 occurrences)", ""])
    for item in stats.get("recurring_patterns", [])[:20]:
        cats = ", ".join(item.get("categories", [])) or "uncategorized"
        examples = ", ".join(t["key"] for t in item["examples"][:3])
        lines.append(f"### `{item['pattern']}` — **{item['count']}x**")
        lines.append(f"- Categories: {cats}")
        lines.append(f"- Examples: {examples}")
        lines.append("")

    lines.extend([
        "## Recommended Toil Reduction Actions",
        "",
        "1. **Top 3 recurring patterns** → create KEDB entry + automated runbook each",
        "2. **ACCESS_GRANT toil** → self-service IAM portal or Terraform module",
        "3. **SECRET_ROTATE toil** → eliminate manual rotation; ESO + cert-manager only",
        "4. **DEPLOY_RERUN toil** → ArgoCD auto-heal + health-check rollback",
        "5. Track toil ratio monthly; target <20% of incoming tickets",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze ACO Jira toil patterns (read-only)")
    parser.add_argument("--jira", type=Path, default=Path("docs/aco-ops/data/jira"))
    parser.add_argument("--output", type=Path, default=Path("docs/aco-ops/reports"))
    args = parser.parse_args()

    rows = load_jira_rows(args.jira)
    stats = analyze(rows)

    args.output.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stats_path = args.output / f"toil_stats_{ts}.json"
    report_path = args.output / "toil-summary.md"

    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(generate_report(stats))

    print(f"Analyzed {stats['total_tickets']} tickets, {stats['toil_tickets']} toil ({stats['toil_pct']}%)")
    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
