#!/usr/bin/env bash
# Run on YOUR PC where DD_API_KEY and DD_APP_KEY are available.
# Usage: bash local_datadog_export.sh [output_dir]
set -euo pipefail

OUTPUT_DIR="${1:-docs/aco-ops/data/datadog}"
SITE="${DD_SITE:-datadoghq.com}"
START_DATE="${DD_START_DATE:-2026-01-01}"
TEAM_TAGS="${DD_TEAM_TAGS:-team:cloudops,team:dba}"

: "${DD_API_KEY:?Set DD_API_KEY}"
: "${DD_APP_KEY:?Set DD_APP_KEY}"

mkdir -p "$OUTPUT_DIR"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BASE="https://api.${SITE}"
AUTH=(-H "DD-API-KEY: ${DD_API_KEY}" -H "DD-APPLICATION-KEY: ${DD_APP_KEY}")

FROM_TS=$(date -d "${START_DATE}" +%s 2>/dev/null || date -j -f "%Y-%m-%d" "${START_DATE}" +%s)
TO_TS=$(date +%s)

echo "Fetching monitors..."
MONITORS_FILE="${OUTPUT_DIR}/monitors_${TIMESTAMP}.json"
echo '{"monitors":[]}' > "$MONITORS_FILE"

IFS=',' read -ra TAGS <<< "$TEAM_TAGS"
for tag in "${TAGS[@]}"; do
  tag=$(echo "$tag" | xargs)
  page=0
  while true; do
    resp=$(curl -sS "${AUTH[@]}" "${BASE}/api/v1/monitor?page=${page}&page_size=100&monitor_tags=${tag}")
    count=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d) if isinstance(d,list) else 0)")
    [[ "$count" -eq 0 ]] && break
    echo "$resp" | python3 -c "
import sys, json
new = json.load(sys.stdin)
path = sys.argv[1]
with open(path) as f:
    data = json.load(f)
existing = {m['id'] for m in data.get('monitors', [])}
for m in new:
    if m['id'] not in existing:
        data['monitors'].append(m)
        existing.add(m['id'])
data['count'] = len(data['monitors'])
with open(path, 'w') as f:
    json.dump(data, f, indent=2)
" "$MONITORS_FILE"
    [[ "$count" -lt 100 ]] && break
    page=$((page + 1))
  done
done

echo "Fetching alert events..."
EVENTS_FILE="${OUTPUT_DIR}/alert_events_${TIMESTAMP}.json"
curl -sS "${AUTH[@]}" \
  "${BASE}/api/v1/events?start=${FROM_TS}&end=${TO_TS}&sources=monitor%20alert&count=1000&unaggregated=true" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
out = {'from_ts': ${FROM_TS}, 'to_ts': ${TO_TS}, 'count': len(data.get('events', [])), 'events': data.get('events', [])}
json.dump(out, sys.stdout, indent=2)
" > "$EVENTS_FILE"

echo "Done."
echo "  Monitors: $MONITORS_FILE"
echo "  Events:   $EVENTS_FILE"
echo "Upload these files to the Cloud Agent or commit to the repo."
