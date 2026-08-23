# RB-KEDB-0005: RBAC Permission Denied — Emergency Grant & GitOps Fix

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0005](../kedb/entries/KEDB-0005.json) |
| **Type** | Manual |
| **Owner** | CloudOps Security |
| **Severity** | P2 |
| **Est. MTTR** | 30 min |

## Triggers

- Kubernetes 403 Forbidden errors
- CI/CD kubectl apply failures
- `kubectl auth can-i` returns no

## Prerequisites

- **Approval required** for emergency RBAC grants
- kubectl admin access
- GitOps repo write access for permanent fix

## Diagnosis

```bash
# Identify who/what is denied
kubectl auth can-i <verb> <resource> --as=system:serviceaccount:<ns>:<sa> -n <namespace>

# Check existing bindings
kubectl get rolebinding,clusterrolebinding -A | grep <sa-name>
kubectl describe rolebinding <name> -n <namespace>
```

## Remediation

### Emergency Grant (24h expiry — requires manager approval)

```yaml
# emergency-rolebinding.yaml — DO NOT commit to GitOps
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: emergency-<sa>-<date>
  namespace: <namespace>
  annotations:
    aco.antuit.io/expiry: "2026-08-24T00:00:00Z"
    aco.antuit.io/approved-by: "<manager>"
    aco.antuit.io/kedb: "KEDB-0005"
subjects:
  - kind: ServiceAccount
    name: <sa>
    namespace: <namespace>
roleRef:
  kind: Role
  name: <required-role>
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl apply -f emergency-rolebinding.yaml
kubectl auth can-i <verb> <resource> --as=system:serviceaccount:<ns>:<sa> -n <namespace>
```

### Permanent Fix (GitOps PR)

1. Add Role + RoleBinding to GitOps repo
2. PR review by CloudOps Security
3. ArgoCD sync
4. Delete emergency RoleBinding after PR merges

## Verification

- `kubectl auth can-i` returns yes for required operations
- Application/CI pipeline succeeds

## Escalation

- ClusterRole changes → Security architect approval
- Cross-namespace access → Document in access registry

## Post-Incident

- Log emergency grant in access audit log
- CronJob to delete expired emergency RoleBindings (planned automation)
