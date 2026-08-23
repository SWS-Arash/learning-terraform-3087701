# RB-KEDB-0009: ArgoCD Sync Failure — Auto Rollback & Manual Recovery

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0009](../kedb/entries/KEDB-0009.json) |
| **Type** | Automated |
| **Owner** | CloudOps Platform |
| **Severity** | P2 |
| **Est. MTTR** | 15 min |

## Triggers

- ArgoCD Application status `Degraded`, `Unknown`, `OutOfSync` (unhealthy)
- Sync error in ArgoCD UI
- Post-deploy health check failure

## Diagnosis

```bash
argocd app get <app-name> --show-operation
argocd app diff <app-name>
kubectl get events -n <namespace> --sort-by='.lastTimestamp' | tail -20
```

## Remediation

### Automated Rollback (Argo Rollouts / sync hook)

If health check fails post-sync, ArgoCD automated sync with rollback:

```bash
# Rollback to previous revision
argocd app rollback <app-name> <revision>

# Or Helm rollback if managed outside ArgoCD
helm rollback <release> -n <namespace>
```

### Common Manual Fixes

| Error | Fix |
|-------|-----|
| CRD not found | Apply CRD first (sync wave -1), then re-sync |
| Immutable field changed | Delete and recreate resource (PVC, Service clusterIP) |
| Resource conflict | `kubectl delete <resource>` then re-sync |
| Validation webhook deny | Fix manifest or update webhook policy |

```bash
# Force sync after fix
argocd app sync <app-name> --force --prune
```

## Verification

- ArgoCD Application `Healthy` + `Synced`
- All pods Running/Ready
- Smoke test / synthetic check passes

## Escalation

- Platform chart failure → CloudOps Platform team
- Application chart failure → Application team

## Post-Incident

- Pin Helm chart version if upgrade caused failure
- Add sync wave annotation for CRD ordering
- Test upgrade path in staging before prod

## Automation (planned)

ArgoCD Notification webhook → auto-rollback on `on-deployed` health degradation.
