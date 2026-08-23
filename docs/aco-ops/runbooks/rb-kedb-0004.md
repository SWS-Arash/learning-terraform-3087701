# RB-KEDB-0004: ExternalSecret Sync Failure — Force Refresh & Restart

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0004](../kedb/entries/KEDB-0004.json) |
| **Type** | Automated |
| **Owner** | CloudOps Platform |
| **Severity** | P2 |
| **Est. MTTR** | 10 min |

## Triggers

- ExternalSecret status `SecretSyncedError`
- Pod `CreateContainerConfigError`
- Datadog monitor on ESO sync failures

## Diagnosis

```bash
kubectl get externalsecret -A | grep -v SecretSynced
kubectl describe externalsecret <name> -n <namespace>
kubectl logs -n external-secrets-system deploy/external-secrets --since=15m
```

## Remediation

### Automated (Reloader + ESO)

```bash
# 1. Force ESO refresh
kubectl annotate externalsecret <name> -n <namespace> \
  force-sync=$(date +%s) --overwrite

# 2. Verify secret updated
kubectl get secret <target-secret> -n <namespace> -o yaml | head -20

# 3. Restart deployments (Reloader does this automatically if annotated)
kubectl rollout restart deployment/<name> -n <namespace>
```

### If IAM/AccessDenied

```bash
# Verify IRSA annotation on ESO service account
kubectl describe sa external-secrets -n external-secrets-system

# Check SecretStore/ClusterSecretStore status
kubectl describe secretstore <name> -n <namespace>
```

## Verification

- ExternalSecret status `SecretSynced`
- Pods Running/Ready
- Application auth succeeds

## Post-Incident

- Audit `refreshInterval` vs Secrets Manager rotation schedule
- Ensure Stakater Reloader annotation on affected deployments
