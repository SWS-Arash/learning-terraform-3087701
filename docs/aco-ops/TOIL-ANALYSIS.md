# Toil Analysis — ACO Jira Repeating Manual Requests

**Scope:** Antuit CloudOps + Antuit DBA | **Mode:** Read-only (no Jira/Datadog mutations)

## What counts as toil

Operational **toil** is manual, repetitive, automatable work that scales linearly with request volume and does not permanently fix root cause.

| Toil signal in Jira | Example summary patterns |
|---------------------|--------------------------|
| **ACCESS_GRANT** | "Grant access", "Add user to", "RBAC", "VPN access", "Service account" |
| **SECRET_ROTATE** | "Rotate secret", "Update password", "Renew certificate", "Refresh token" |
| **CAPACITY_SCALE** | "Increase memory", "Scale up", "Add node", "Increase disk", "Bump limits" |
| **MONITOR_TUNING** | "Silence alert", "Adjust threshold", "False positive", "Noisy monitor" |
| **DEPLOY_RERUN** | "Re-run pipeline", "Restart pod", "Force sync", "Rollback deployment" |
| **DATA_FIX** | "Run script manually", "Execute SQL", "One-off fix", "Ad-hoc query" |
| **PROVISION** | "Create namespace", "New environment", "Provision DB", "Create bucket" |
| **TROUBLESHOOT_HANDOFF** | "Please check", "Investigate", "Can someone look at" (without permanent fix) |

## Read-only guarantee

All collection and analysis is **read-only**:

| System | Operations | Prohibited |
|--------|------------|------------|
| Jira | `search`, `get issue`, export | create, update, transition, comment |
| Datadog | `GET` monitors, events | create/update monitors, mute, resolve |

Scripts use only Jira Search API (`POST /rest/api/3/search/jql`) and Datadog `GET` endpoints.

## JQL for toil review (CloudOps + DBA)

```jql
project = ACO
AND issuetype in (Incident, Bug, Task, "Service Request")
AND "Scrum Team" in ("Antuit CloudOps", "Antuit DBA")
AND created >= "2026-01-01"
ORDER BY created DESC
```

Optional — likely toil-heavy request types:

```jql
project = ACO
AND "Scrum Team" in ("Antuit CloudOps", "Antuit DBA")
AND created >= "2026-01-01"
AND (
  summary ~ "access" OR summary ~ "grant" OR summary ~ "rotate"
  OR summary ~ "certificate" OR summary ~ "scale" OR summary ~ "restart"
  OR summary ~ "manual" OR summary ~ "provision" OR summary ~ "silence"
  OR labels in (toil, manual, access-request, runbook)
)
ORDER BY created DESC
```

## Running toil analysis

Once Jira data is available (MCP, API, or CSV export):

```bash
python3 docs/aco-ops/scripts/analyze_toil.py \
  --jira docs/aco-ops/data/jira/ \
  --output docs/aco-ops/reports/
```

Output:
- `reports/toil-summary.md` — ranked repeating manual requests
- `reports/toil-stats_*.json` — machine-readable clusters
- Automation recommendations per toil category

## Toil reduction levers

| Toil category | Automate with | KEDB link |
|---------------|---------------|-----------|
| ACCESS_GRANT | IAM-as-code, OIDC group sync, self-service portal | KEDB-0005 |
| SECRET_ROTATE | ESO + cert-manager + rotation Lambda | KEDB-0002, KEDB-0004 |
| CAPACITY_SCALE | VPA, HPA, cluster autoscaler, quota templates | KEDB-0003, KEDB-0010 |
| MONITOR_TUNING | Monitor-as-code PR review, noise audit cadence | KEDB-0001 |
| DEPLOY_RERUN | ArgoCD auto-sync, auto-rollback, Reloader | KEDB-0009 |
| DATA_FIX | Scheduled jobs, migration scripts in GitOps | New KEDB entries |
| PROVISION | Terraform modules, Backstage/self-service | New KEDB entries |

## Next step

Provide Jira data via one of:
1. **Jira MCP** enabled in [Cloud Agent environment](https://cursor.com/dashboard/cloud-agents/environments/e/0fe1ad6d-9f34-11f1-a7d1-d6b4613131ce) → new run
2. **CSV export** attached to this chat
3. **Jira API secrets** in environment (`JIRA_BASE_URL`, `JIRA_USER_EMAIL`, `JIRA_API_TOKEN`)

Then re-run this agent to produce the live toil report.
