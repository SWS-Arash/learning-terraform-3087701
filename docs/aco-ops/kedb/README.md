# Known Error Database (KEDB)

Central registry of recurring operational issues for Antuit CloudOps and Antuit DBA. Each entry links to a runbook and tracks path to permanent resolution.

## Entry Lifecycle

```
template → active → mitigated → resolved
```

- **template:** Framework placeholder — validate against live Jira/Datadog data
- **active:** Confirmed recurring issue with documented workaround
- **mitigated:** Permanent fix partially deployed; workaround still available
- **resolved:** Root cause eliminated; entry archived after 90 days without recurrence

## Index

| ID | Title | Category | Team | Runbook Type | Status |
|----|-------|----------|------|--------------|--------|
| [KEDB-0001](entries/KEDB-0001.json) | Datadog CPU alert flapping on idle pods | MONITOR_NOISE | CloudOps | hybrid | template |
| [KEDB-0002](entries/KEDB-0002.json) | TLS certificate expiry causing ingress failures | SECRET_MGMT | CloudOps | automated | template |
| [KEDB-0003](entries/KEDB-0003.json) | Pod OOMKilled due to undersized memory limits | K8S_CAPACITY | CloudOps | hybrid | template |
| [KEDB-0004](entries/KEDB-0004.json) | ExternalSecret sync failure after rotation | SECRET_MGMT | CloudOps | automated | template |
| [KEDB-0005](entries/KEDB-0005.json) | RBAC permission denied for service account | ACCESS_IAM | CloudOps | manual | template |
| [KEDB-0006](entries/KEDB-0006.json) | Database connection pool exhaustion | DBA_PERF | DBA | hybrid | template |
| [KEDB-0007](entries/KEDB-0007.json) | Replication lag on read replica | DBA_PERF | DBA | hybrid | template |
| [KEDB-0008](entries/KEDB-0008.json) | Critical CVE blocking deployment | SECURITY_VULN | CloudOps | manual | template |
| [KEDB-0009](entries/KEDB-0009.json) | ArgoCD sync failure after Helm upgrade | DEPLOYMENT | CloudOps | automated | template |
| [KEDB-0010](entries/KEDB-0010.json) | Node disk pressure causing pod evictions | K8S_CAPACITY | CloudOps | hybrid | template |

## Adding a New Entry

1. Confirm recurrence criteria (see `ANALYSIS-METHODOLOGY.md`)
2. Copy `entries/_template.json` to `entries/KEDB-XXXX.json`
3. Create corresponding runbook in `runbooks/rb-kedb-XXXX.md`
4. Update this index table
5. Link related Jira tickets and Datadog monitors after live data pull

## Validation

After running collection scripts, validate each template entry:

```bash
python docs/aco-ops/scripts/analyze_pain_points.py
# Review reports/pain-points-summary.md
# Promote matching patterns from template → active
```
