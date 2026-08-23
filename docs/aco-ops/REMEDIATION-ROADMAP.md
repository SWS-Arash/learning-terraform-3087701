# Remediation Roadmap — Antuit CloudOps & DBA

Prioritized permanent fixes derived from pain point analysis. **Update after live Jira/Datadog data pull.**

## Priority Matrix

| Priority | Criteria |
|----------|----------|
| **P0** | Active P1 recurrence, customer impact, no workaround |
| **P1** | ≥5 incidents/quarter OR high alert noise affecting on-call |
| **P2** | ≥3 incidents/quarter, workaround exists |
| **P3** | ≤2 incidents/quarter, low impact |

---

## Phase 1 — Quick Wins (0–4 weeks)

### 1.1 Monitor Noise Reduction (P1)

| Item | Owner | KEDB | Action | Success Metric |
|------|-------|------|--------|----------------|
| Audit top 20 noisiest Datadog monitors | CloudOps SRE | KEDB-0001 | Run `analyze_pain_points.py`; tune thresholds on monitors with >10 alerts/month and 0 incidents | 50% reduction in false-positive pages |
| PagerDuty alert grouping | CloudOps SRE | KEDB-0001 | Configure 15-min grouping per monitor+host | Repeat pages reduced |
| Document silenced monitors | CloudOps SRE | — | All silences require expiry date + KEDB reference | 100% silences documented |

### 1.2 Secret & Certificate Hygiene (P1)

| Item | Owner | KEDB | Action | Success Metric |
|------|-------|------|--------|----------------|
| Certificate inventory | CloudOps Platform | KEDB-0002 | List all TLS certs; identify non-cert-manager | 100% inventory complete |
| Migrate manual certs to cert-manager | CloudOps Platform | KEDB-0002 | Create Certificate resources for each | 0 manual cert renewals |
| Pre-expiry monitors | CloudOps Platform | KEDB-0002 | Datadog monitors at 30/14/7/1 days | 0 expiry incidents |
| ESO refreshInterval audit | CloudOps Platform | KEDB-0004 | Ensure refreshInterval ≤ rotation/2 | 0 sync failures post-rotation |

### 1.3 K8s Capacity Baseline (P1)

| Item | Owner | KEDB | Action | Success Metric |
|------|-------|------|--------|----------------|
| VPA deployment (recommendation mode) | CloudOps SRE | KEDB-0003 | Deploy VPA on top 10 memory-OOM namespaces | Recommendations available |
| Node disk sizing review | CloudOps SRE | KEDB-0010 | Increase default disk to 100GB; enable log rotation | 0 disk pressure evictions |
| Resource quota audit | CloudOps SRE | KEDB-0003 | Review namespace quotas vs actual usage | Quotas aligned |

---

## Phase 2 — Process & Automation (4–12 weeks)

### 2.1 Auto-Healing Implementation (P1–P2)

| Item | Owner | KEDB | Mechanism | Status |
|------|-------|------|-----------|--------|
| ESO + Reloader | CloudOps Platform | KEDB-0004 | Auto pod restart on secret change | planned |
| cert-manager renewal | CloudOps Platform | KEDB-0002 | Automated TLS renewal | planned |
| ArgoCD auto-rollback | CloudOps Platform | KEDB-0009 | Rollback on failed health check | planned |
| Node cleanup DaemonSet | CloudOps SRE | KEDB-0010 | Image prune + log rotation | planned |
| Idle DB connection killer | Antuit DBA | KEDB-0006 | Lambda/webhook on connection threshold | planned |

### 2.2 Access & Security (P2)

| Item | Owner | KEDB | Action | Success Metric |
|------|-------|------|--------|----------------|
| RBAC GitOps migration | CloudOps Security | KEDB-0005 | All RBAC in Git with PR review | 0 emergency grants/month |
| Quarterly access review | CloudOps Security | KEDB-0005 | Automated report of SA/RBAC bindings | Review completed Q1/Q2/Q3/Q4 |
| CVE SLA enforcement | CloudOps Security | KEDB-0008 | CI gate: block Critical CVE deploy | 100% compliance |
| Renovate/Dependabot rollout | CloudOps Security | KEDB-0008 | Auto-PR for patchable deps | Mean time to patch < 7d |

### 2.3 DBA Performance (P2)

| Item | Owner | KEDB | Action | Success Metric |
|------|-------|------|--------|----------------|
| RDS Proxy deployment | Antuit DBA | KEDB-0006 | Deploy for top 5 connection-heavy apps | 0 pool exhaustion incidents |
| Replication lag SLAs | Antuit DBA | KEDB-0007 | Define per-tier lag thresholds | SLAs documented |
| Slow query baseline | Antuit DBA | KEDB-0007 | Enable pg_stat_statements / Performance Insights | Top 10 queries identified |

---

## Phase 3 — Strategic (12+ weeks)

### 3.1 Capacity Planning Program

- Quarterly cluster capacity review with growth projections
- Automated right-sizing reports from VPA recommendations
- FinOps integration: cost vs utilization dashboards

### 3.2 Observability Maturity

- SLO-based alerting replacing static thresholds
- Error budget burn rate alerts
- Alert-to-incident ratio target: <5:1

### 3.3 Known Error Database Operations

- Weekly KEDB review in CloudOps/DBA standup
- Auto-link new Jira incidents to KEDB entries via labels
- Retire resolved entries after 90 days without recurrence

---

## Tracking

| Metric | Baseline (TBD) | Target (6 mo) |
|--------|--------------|---------------|
| P1/P2 incidents/month (CloudOps) | — | -40% |
| P1/P2 incidents/month (DBA) | — | -40% |
| Datadog false-positive pages/month | — | -60% |
| Mean time to resolve (MTTR) | — | -30% |
| KEDB entries with automated runbooks | 0/10 | 7/10 |
| Manual secret/cert renewals/quarter | — | 0 |

---

## How to Update This Roadmap

1. Run data collection: `collect_jira.py` + `collect_datadog.py`
2. Run analysis: `analyze_pain_points.py`
3. Review `reports/pain-points-summary.md`
4. Promote top recurring patterns to P0/P1 in this document
5. Assign owners and target dates in Jira epic ACO-OPS-REMEDIATION (create if needed)
