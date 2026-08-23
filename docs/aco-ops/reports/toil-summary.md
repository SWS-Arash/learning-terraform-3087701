# ACO Toil Analysis — Repeating Manual Requests

Generated: 2026-08-23T21:12:09.484554+00:00
**Mode: Read-only analysis — no Jira/Datadog changes made.**

## Summary

- **Total tickets analyzed:** 16
- **Tickets classified as toil:** 10 (62.5%)

## Toil by Category

| Category | Count | Automation lever |
|----------|-------|------------------|
| ACCESS_GRANT | 3 | IAM-as-code, self-service portal, OIDC group sync |
| SECRET_ROTATE | 3 | ESO, cert-manager, rotation automation |
| MONITOR_TUNING | 2 | Monitor-as-code, noise audit, composite alerts |
| DEPLOY_RERUN | 1 | ArgoCD auto-sync/rollback, Reloader |
| CAPACITY_SCALE | 1 | VPA/HPA, cluster autoscaler, quota templates |

## Top Recurring Request Patterns (≥2 occurrences)

## Recommended Toil Reduction Actions

1. **Top 3 recurring patterns** → create KEDB entry + automated runbook each
2. **ACCESS_GRANT toil** → self-service IAM portal or Terraform module
3. **SECRET_ROTATE toil** → eliminate manual rotation; ESO + cert-manager only
4. **DEPLOY_RERUN toil** → ArgoCD auto-heal + health-check rollback
5. Track toil ratio monthly; target <20% of incoming tickets
