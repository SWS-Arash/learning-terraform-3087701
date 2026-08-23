# Environment Setup Status

**Last updated:** 2026-08-23

## Completed in this environment

| Item | Status |
|------|--------|
| Python 3.12 + dependencies (`requirements.txt`) | Installed |
| `.cursor/environment.json` with `install` hook | Committed |
| Analysis scripts (collect, analyze, toil, promote) | Verified |
| Sample data + `validate_pipeline.sh` | Pipeline passes |
| KEDB (10 entries) + runbooks | Ready |
| Read-only policy documented | Yes |

## Skipped by user (live data blocked)

| Item | Status | Impact |
|------|--------|--------|
| Jira MCP in Cloud Agent | Skipped | Cannot query ACO Jira from cloud VM |
| Jira/Datadog API secrets | Skipped | Cannot call APIs from cloud VM |
| Datadog egress allowlist | Rejected | N/A — egress is unrestricted anyway |

## Sample pipeline validation results

Ran on 16 demo tickets + 6 demo alert events:

- **Toil rate:** 62.5% (10/16 tickets classified as manual/repetitive work)
- **Top toil:** ACCESS_GRANT (3), SECRET_ROTATE (3), MONITOR_TUNING (2)
- **Top pain points:** ACCESS_IAM, K8S_CAPACITY, SECRET_MGMT, DBA_PERF (3 each)
- **Noisiest monitor (sample):** CPU utilization > 80% (4 alert events)

See `reports/pain-points-summary.md` and `reports/toil-summary.md` (marked SAMPLE).

## Continue on PC (live data)

```bash
git checkout cursor/aco-ops-pain-points-kedb-8078
pip install -r docs/aco-ops/scripts/requirements.txt

# With Jira MCP: export CSV to docs/aco-ops/data/jira/
# With Datadog API keys:
export DD_API_KEY=... DD_APP_KEY=...

bash docs/aco-ops/scripts/run_full_analysis.sh
```

All operations remain **read-only** per `READ-ONLY-POLICY.md`.
