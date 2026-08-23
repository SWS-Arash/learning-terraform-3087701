#!/usr/bin/env bash
# Run full ACO ops analysis on YOUR PC (read-only).
# Requires: Jira API env vars and/or pre-exported CSV, plus Datadog API keys.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
JIRA_DIR="${ROOT}/data/jira"
DD_DIR="${ROOT}/data/datadog"
REPORT_DIR="${ROOT}/reports"

mkdir -p "$JIRA_DIR" "$DD_DIR" "$REPORT_DIR"

echo "==> ACO Ops Analysis (read-only)"
echo "    Jira data:    $JIRA_DIR"
echo "    Datadog data: $DD_DIR"
echo "    Reports:      $REPORT_DIR"
echo ""

# --- Jira ---
if [[ -n "${JIRA_BASE_URL:-}" && -n "${JIRA_API_TOKEN:-}" && -n "${JIRA_USER_EMAIL:-}" ]]; then
  echo "==> Collecting Jira tickets via API..."
  export JIRA_TEAMS="${JIRA_TEAMS:-Antuit CloudOps,Antuit DBA}"
  export JIRA_START_DATE="${JIRA_START_DATE:-2026-01-01}"
  python3 "${ROOT}/scripts/collect_jira.py" --output "$JIRA_DIR"
elif compgen -G "$JIRA_DIR/jira_issues_*.csv" > /dev/null 2>&1; then
  echo "==> Using existing Jira CSV in $JIRA_DIR"
elif compgen -G "$JIRA_DIR/*.csv" > /dev/null 2>&1; then
  echo "==> Normalizing Jira CSV export..."
  IMPORT=$(ls -t "$JIRA_DIR"/*.csv | head -1)
  python3 "${ROOT}/scripts/import_jira_csv.py" "$IMPORT" --output "$JIRA_DIR"
else
  echo "ERROR: No Jira data. Either:"
  echo "  1. Set JIRA_BASE_URL, JIRA_USER_EMAIL, JIRA_API_TOKEN"
  echo "  2. Place Jira CSV export in $JIRA_DIR and re-run"
  echo "  3. Use Jira MCP in Cursor Desktop to export tickets to CSV"
  exit 1
fi

# --- Datadog ---
if [[ -n "${DD_API_KEY:-}" && -n "${DD_APP_KEY:-}" ]]; then
  echo "==> Collecting Datadog alert history via API..."
  export DD_TEAM_TAGS="${DD_TEAM_TAGS:-team:cloudops,team:dba}"
  export DD_START_DATE="${DD_START_DATE:-2026-01-01}"
  python3 "${ROOT}/scripts/collect_datadog.py" --output "$DD_DIR"
elif compgen -G "$DD_DIR/alert_events_*.json" > /dev/null 2>&1; then
  echo "==> Using existing Datadog export in $DD_DIR"
else
  echo "WARN: No Datadog data — pain-point report will be Jira-only."
fi

# --- Analysis ---
echo "==> Running pain-point analysis..."
python3 "${ROOT}/scripts/analyze_pain_points.py" \
  --jira "$JIRA_DIR" \
  --datadog "$DD_DIR" \
  --output "$REPORT_DIR"

echo "==> Running toil analysis..."
python3 "${ROOT}/scripts/analyze_toil.py" \
  --jira "$JIRA_DIR" \
  --output "$REPORT_DIR"

echo ""
echo "Done. Reports:"
echo "  ${REPORT_DIR}/pain-points-summary.md"
echo "  ${REPORT_DIR}/toil-summary.md"
echo ""
echo "Next: review reports, promote KEDB entries template -> active, link ticket/monitor IDs."
python3 "${ROOT}/scripts/promote_kedb.py" --reports "$REPORT_DIR"
