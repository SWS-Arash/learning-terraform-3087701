# Pain Points Analysis Report

> **Status:** Awaiting live data — Jira and Datadog API credentials not yet configured.
>
> Run the collection pipeline to populate this report with real metrics.

Generated: 2026-08-23 (framework placeholder)

## Executive Summary

- **Jira tickets analyzed:** 0 (pending credentials)
- **Datadog alert events:** 0 (pending credentials)
- **Datadog monitors in scope:** 0 (pending credentials)

## Expected Top Categories (Industry Baseline for CloudOps/DBA)

Based on typical enterprise CloudOps and DBA operational patterns, validate these against ACO data:

| Rank | Category | Typical % of Tickets | Primary Lever |
|------|----------|---------------------|---------------|
| 1 | MONITOR_NOISE | 25–35% | Monitor tuning, alert grouping |
| 2 | K8S_CAPACITY | 15–25% | Right-sizing, autoscaling |
| 3 | SECRET_MGMT | 10–15% | ESO, cert-manager, rotation automation |
| 4 | DEPLOYMENT | 10–15% | GitOps, canary, auto-rollback |
| 5 | DBA_PERF | 10–15% | Connection pooling, query tuning |
| 6 | ACCESS_IAM | 5–10% | RBAC automation, access reviews |
| 7 | SECURITY_VULN | 5–10% | Patch cadence, CI gates |
| 8 | NETWORK_DNS | 3–8% | IaC, synthetic monitoring |

## Next Steps

1. Configure environment secrets: `JIRA_*`, `DD_*`
2. Run: `python docs/aco-ops/scripts/collect_jira.py`
3. Run: `python docs/aco-ops/scripts/collect_datadog.py`
4. Run: `python docs/aco-ops/scripts/analyze_pain_points.py`
5. This file will be overwritten with real analysis results

## KEDB & Runbook Readiness

10 KEDB template entries and corresponding runbooks are prepared in:

- `kedb/entries/KEDB-0001.json` through `KEDB-0010.json`
- `runbooks/rb-kedb-0001.md` through `rb-kedb-0010.md`

After data pull, promote matching patterns from `template` → `active` status and link real Jira ticket keys and Datadog monitor IDs.
