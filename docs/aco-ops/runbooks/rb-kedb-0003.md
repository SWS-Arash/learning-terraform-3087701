# RB-KEDB-0003: Pod OOMKilled — Emergency Scale & Right-Size

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0003](../kedb/entries/KEDB-0003.json) |
| **Type** | Hybrid |
| **Owner** | CloudOps SRE |
| **Severity** | P2 |
| **Est. MTTR** | 20 min (emergency) / 1 week (right-size) |

## Triggers

- Pod status `OOMKilled` (exit code 137)
- Datadog: `kubernetes.memory.usage` at limit
- CrashLoopBackOff after memory kill

## Diagnosis

```bash
kubectl describe pod <pod> -n <namespace> | grep -A5 "Last State\|Limits\|Requests"
kubectl top pod <pod> -n <namespace>
kubectl get events -n <namespace> --field-selector reason=OOMKilling
```

## Remediation

### Phase A — Emergency (auto-approved for P2)

```bash
# Temporary memory limit increase (patch deployment)
kubectl patch deployment <name> -n <namespace> -p \
  '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"2Gi"}}}]}}}}'

# Or scale replicas to distribute load
kubectl scale deployment <name> -n <namespace> --replicas=<N+2>
```

### Phase B — Root Cause (requires app team)

1. Check APM for memory leak patterns ( steadily increasing heap )
2. Review VPA recommendations:
   ```bash
   kubectl get vpa -n <namespace>
   kubectl describe vpa <name> -n <namespace>
   ```
3. Update Helm values with right-sized limits (P99 + 20% headroom)

## Verification

- Pod Running/Ready for >30 min
- No OOMKilled events in last hour
- Memory utilization stable below 85% of limit

## Escalation

- Repeated OOM after limit increase → Application team (likely memory leak)

## Post-Incident

- Create Jira for permanent Helm chart update
- Enable VPA in recommendation mode if not deployed
