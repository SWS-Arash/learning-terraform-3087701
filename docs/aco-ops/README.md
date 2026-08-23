# ACO Operations Intelligence: Pain Points, KEDB & Runbooks

Operational analysis framework for **Antuit CloudOps** and **Antuit DBA** scrum teams, correlating **ACO Jira** incidents/bugs with **Datadog** alert history to identify recurring pain points and drive permanent fixes.

## Status

| Phase | Status |
|-------|--------|
| Framework & taxonomy | Complete |
| Data collection scripts | Complete |
| KEDB structure + seed entries | Complete (templates — validate against live data) |
| Runbooks | Complete (templates — validate against live data) |
| Live Jira/Datadog analysis | **Use PC** — secrets/MCP skipped in Cloud Agent |

See **[SETUP-STATUS.md](SETUP-STATUS.md)** for environment setup completion details.

## Quick Start

```bash
# 1. Install dependencies
pip install -r docs/aco-ops/scripts/requirements.txt

# 2. Collect Jira tickets (2026 YTD, CloudOps + DBA)
python docs/aco-ops/scripts/collect_jira.py --output docs/aco-ops/data/jira/

# 3. Collect Datadog alert history (2026 YTD)
python docs/aco-ops/scripts/collect_datadog.py --output docs/aco-ops/data/datadog/

# 4. Analyze and generate pain-point report
python docs/aco-ops/scripts/analyze_pain_points.py \
  --jira docs/aco-ops/data/jira/ \
  --datadog docs/aco-ops/data/datadog/ \
  --output docs/aco-ops/reports/
```

## Directory Structure

```
docs/aco-ops/
├── README.md                          # This file
├── ANALYSIS-METHODOLOGY.md            # How we classify and correlate issues
├── PAIN-POINT-TAXONOMY.md             # Category definitions
├── REMEDIATION-ROADMAP.md             # Prioritized permanent fixes
├── data/                              # Generated (gitignored secrets; data optional)
├── reports/                           # Generated analysis output
├── scripts/                           # Collection & analysis automation
├── kedb/                              # Known Error Database
│   ├── README.md
│   ├── schema.json
│   └── entries/                       # One file per known error
└── runbooks/                          # Operational runbooks
    ├── README.md
    └── rb-*.md                        # Runbook per KEDB entry or category
```

## Jira Scope (default JQL)

```jql
project = ACO
AND issuetype in (Incident, Bug)
AND "Scrum Team" in ("Antuit CloudOps", "Antuit DBA")
AND created >= "2026-01-01"
ORDER BY created DESC
```

Customize field names via environment variables — see `scripts/config.example.env`.

## Datadog Scope (default filters)

- Time range: `2026-01-01` → now
- Team tags: `team:cloudops`, `team:dba` (configurable)
- Alert states: Alert, Warn, No Data, Recovery

## Pain Point Categories

| Category | Root-cause focus | Permanent fix lever |
|----------|------------------|---------------------|
| **MONITOR_NOISE** | Threshold/evaluation tuning | Monitor refinement, composite monitors, SLO-based alerts |
| **SECRET_MGMT** | Expired/missing/rotated secrets | Vault rotation, External Secrets Operator, pre-expiry alerts |
| **K8S_CAPACITY** | CPU/memory/disk/HPA limits | Right-sizing, VPA, cluster autoscaling, quota planning |
| **ACCESS_IAM** | RBAC, SSO, cert, VPN | IAM automation, break-glass process, access reviews |
| **SECURITY_VULN** | CVE, misconfig, policy drift | Patch cadence, image scanning gates, Wiz/Prisma remediation SLAs |
| **DBA_PERF** | Locks, replication, storage | Index tuning, connection pooling, maintenance windows |
| **NETWORK_DNS** | LB, ingress, DNS, firewall | Infrastructure-as-code, health-check tuning |
| **DEPLOYMENT** | Failed rollouts, config drift | GitOps, canary, automated rollback |

## Next Steps After Credentials

1. Run collection scripts and review `reports/pain-points-summary.md`
2. Validate KEDB seed entries against top recurring issues
3. Promote high-frequency items to automated runbooks
4. Track remediation in `REMEDIATION-ROADMAP.md` with owners and target dates
