# RB-KEDB-0002: TLS Certificate Expiry — Automated Renewal

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0002](../kedb/entries/KEDB-0002.json) |
| **Type** | Automated |
| **Owner** | CloudOps Platform |
| **Severity** | P1 (<7 days to expiry) / P2 (<14 days) |
| **Est. MTTR** | 5 min (cert-manager) / 30 min (manual) |

## Triggers

- Datadog monitor: `certmanager_certificate_expiration_timestamp` < 14 days
- Browser SSL errors on ingress endpoints
- cert-manager Certificate status `Ready=False`

## Prerequisites

- cert-manager installed in cluster
- ClusterIssuer configured (Let's Encrypt or internal CA)
- kubectl access

## Diagnosis

```bash
# List certificates and expiry
kubectl get certificates -A
kubectl describe certificate <name> -n <namespace>

# Check cert-manager logs
kubectl logs -n cert-manager deploy/cert-manager --since=30m

# Verify ingress TLS secret
kubectl get secret <tls-secret> -n <namespace> -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates
```

## Remediation

### Automated (cert-manager managed)

cert-manager renews automatically at 2/3 of certificate lifetime. If renewal failed:

```bash
# 1. Check Certificate resource events
kubectl describe certificate <name> -n <namespace>

# 2. Common fixes
# Fix ClusterIssuer / DNS-01 challenge failure
kubectl get challenges -A
kubectl describe challenge <name> -n <namespace>

# 3. Force renewal by deleting the secret (cert-manager recreates)
kubectl delete secret <tls-secret-name> -n <namespace>
# Wait for cert-manager to reconcile (~2 min)
kubectl get certificate <name> -n <namespace> -w
```

### Manual (non-cert-manager certs)

1. Generate/obtain renewed certificate from CA
2. Update Kubernetes secret:
   ```bash
   kubectl create secret tls <tls-secret> \
     --cert=fullchain.pem --key=privkey.pem \
     -n <namespace> --dry-run=client -o yaml | kubectl apply -f -
   ```
3. Restart ingress controller if needed:
   ```bash
   kubectl rollout restart deployment/<ingress-controller> -n <ingress-namespace>
   ```

## Verification

```bash
# Confirm new cert dates
echo | openssl s_client -connect <host>:443 2>/dev/null | openssl x509 -noout -dates

# Datadog synthetic test passes
# Certificate Ready=True
kubectl get certificate <name> -n <namespace>
```

## Escalation

- DNS-01 challenge failures → CloudOps Network team
- Internal CA approval delays → Security team

## Post-Incident

- Migrate manual cert to cert-manager Certificate resource
- Add pre-expiry monitors at 30/14/7/1 days
- Update KEDB-0002 status to `mitigated` once migrated

## Automation Script (planned)

Location: `scripts/remediation/cert-renewal-check.sh`

```bash
#!/usr/bin/env bash
# Checks all certificates; triggers cert-manager renewal or pages if <7 days
set -euo pipefail
kubectl get certificates -A -o json | jq -r '
  .items[] |
  select(.status.notAfter != null) |
  "\(.metadata.namespace)/\(.metadata.name) \(.status.notAfter)"
'
```
