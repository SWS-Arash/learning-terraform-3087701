# RB-KEDB-0001: Datadog CPU Alert Flapping — Triage & Monitor Tuning

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0001](../kedb/entries/KEDB-0001.json) |
| **Type** | Hybrid |
| **Owner** | CloudOps SRE |
| **Severity** | P3 (noise) / P2 if correlated with service degradation |
| **Est. MTTR** | 15 min (triage) / 2h (tuning) |

## Triggers

- Datadog monitor: CPU utilization > threshold
- PagerDuty alert with no customer-facing impact
- Pattern: Alert → OK within 5 minutes, repeats ≥3x/day

## Prerequisites

- Datadog read access
- kubectl access to affected cluster/namespace
- Datadog monitor edit permission (for tuning phase)

## Diagnosis

```bash
# 1. Identify affected pod(s)
kubectl get pods -n <namespace> -o wide
kubectl top pod -n <namespace>

# 2. Check if CPU spike is transient (GC, startup, health check)
kubectl logs -n <namespace> <pod> --since=10m | tail -50

# 3. Verify no customer impact
# Check APM error rate, synthetic tests, ingress 5xx rate in Datadog
```

**Confirm KEDB-0001 if:** CPU spikes are brief (<2 min), pod is Running/Ready, no elevated error rate.

## Remediation

### Phase A — Automated Triage (no approval needed)

1. PagerDuty alert grouping: suppress repeat pages within 15 min for same monitor+host
2. Auto-post to Slack `#cloudops-alerts` with pod metrics snapshot

### Phase B — Human Triage

1. Acknowledge alert in PagerDuty
2. Run diagnosis commands above
3. If no impact: resolve as false positive, tag Jira with `monitor-noise`

### Phase C — Permanent Tuning (requires approval)

1. Open Datadog monitor → Edit query:

   ```
   # Before (noisy)
   avg(last_1m):avg:kubernetes.cpu.usage.total{...} > 800000000

   # After (stable)
   avg(last_5m):avg:kubernetes.cpu.usage.total{...} > 800000000
   ```

2. Add recovery threshold (hysteresis): alert at 80%, recover at 70%
3. Add notification message: `@slack-cloudops` only (remove PagerDuty for P3)
4. Document change in monitor message with KEDB-0001 reference

## Verification

- Monitor does not fire for 7 days under normal load
- Alert-to-incident ratio improves (track in monthly review)

## Escalation

- If CPU sustained >80% for >10 min AND error rate elevated → escalate to application team (not monitor noise)

## Post-Incident

- Update KEDB-0001 `related_monitors` with monitor ID
- Log tuning change in `REMEDIATION-ROADMAP.md`
