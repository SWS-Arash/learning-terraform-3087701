#!/usr/bin/env bash
# Validate analysis pipeline using bundled sample data (no Jira/Datadog API needed).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JIRA_DIR="${ROOT}/data/jira"
DD_DIR="${ROOT}/data/datadog"
REPORT_DIR="${ROOT}/reports"

mkdir -p "$JIRA_DIR" "$DD_DIR" "$REPORT_DIR"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
cp "${ROOT}/data/jira/sample/jira_issues_demo.csv" "${JIRA_DIR}/jira_issues_${TS}.csv"
cp "${ROOT}/data/datadog/sample/monitors_demo.json" "${DD_DIR}/monitors_${TS}.json"
cp "${ROOT}/data/datadog/sample/alert_events_demo.json" "${DD_DIR}/alert_events_${TS}.json"

echo "==> Running pipeline on SAMPLE data (not live Jira/Datadog)"
python3 "${ROOT}/scripts/analyze_pain_points.py" --jira "$JIRA_DIR" --datadog "$DD_DIR" --output "$REPORT_DIR"
python3 "${ROOT}/scripts/analyze_toil.py" --jira "$JIRA_DIR" --output "$REPORT_DIR"
python3 "${ROOT}/scripts/promote_kedb.py" --reports "$REPORT_DIR"

echo ""
echo "Sample pipeline complete. Reports in ${REPORT_DIR}/"
echo "NOTE: Sample data only. For live analysis run on PC with Jira MCP / Datadog API."
