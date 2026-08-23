# Analysis Methodology

## Objective

Correlate **ACO Jira** operational tickets with **Datadog** alert history to identify systemic pain points for Antuit CloudOps and Antuit DBA, then drive permanent remediation through KEDB entries and runbooks.

## Data Sources

| Source | Scope | Fields Used |
|--------|-------|-------------|
| Jira ACO | Incidents + Bugs, Scrum Team ∈ {CloudOps, DBA}, created ≥ 2026-01-01 | Summary, description, labels, components, status, resolution time |
| Datadog | Monitors tagged `team:cloudops` or `team:dba`, alert events 2026 YTD | Monitor name, query, tags, alert frequency, recovery time |

## Classification Process

1. **Automated keyword classification** — `analyze_pain_points.py` applies regex patterns in `PAIN-POINT-TAXONOMY.md`
2. **Manual validation** — SME reviews top 20 recurring patterns and recategorizes as needed
3. **Cross-correlation** — Match Jira ticket timestamps to Datadog alert events (±15 min window) to confirm alert-driven incidents
4. **Noise scoring** — Monitors with >10 alerts/month and zero downstream incidents = noise candidate

## Pain Point Scoring

Each identified pattern receives a **Priority Score (0–100)**:

```
Score = (Frequency × 30) + (MTTR_hours × 20) + (BusinessImpact × 30) + (AutomationGap × 20)
```

| Factor | Weight | Scale |
|--------|--------|-------|
| Frequency | 30 | Alerts/tickets per month (normalized 0–1) |
| MTTR | 20 | Mean time to resolve in hours (normalized) |
| Business Impact | 30 | P1=1.0, P2=0.7, P3=0.4, P4=0.1 |
| Automation Gap | 20 | 1.0 if fully manual, 0.0 if fully automated |

## Permanent Fix Categories

| Fix Type | When to Use | Example |
|----------|-------------|---------|
| **Monitor tuning** | High alert volume, low incident correlation | Raise CPU threshold, add `min(count_over_time())` |
| **Auto-healing** | Predictable recovery path | Restart pod on CrashLoopBackOff, rotate secret via ESO |
| **Capacity planning** | Resource exhaustion patterns | Increase node pool, adjust requests/limits |
| **Process improvement** | Human/process gaps | Secret rotation calendar, access review cadence |
| **Architecture change** | Recurring structural failures | Multi-AZ, read replicas, circuit breakers |

## KEDB Entry Criteria

A pattern becomes a KEDB entry when:

- Occurs **≥3 times** in 90 days, OR
- Causes **≥1 P1/P2 incident**, OR
- Consumes **≥4 engineer-hours/month** in manual remediation

## Runbook Type Selection

| Signal | Runbook Type |
|--------|--------------|
| Single deterministic fix | **Automated** (script/operator/webhook) |
| Requires judgment or approval | **Manual** |
| Automated triage + human approval for action | **Hybrid** |

## Review Cadence

- **Weekly:** Review new recurring patterns from automated analysis
- **Monthly:** Update KEDB entries, retire resolved known errors
- **Quarterly:** Re-score remediation roadmap priorities
