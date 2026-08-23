# Pain Point Taxonomy

Standard categories for classifying ACO Jira tickets and Datadog alerts affecting Antuit CloudOps and Antuit DBA.

---

## MONITOR_NOISE

**Description:** Alerts that fire frequently without indicating real service degradation. Creates alert fatigue and delays response to genuine incidents.

**Indicators:**
- Alert-to-incident ratio < 10%
- Flapping monitors (Alert → OK → Alert within minutes)
- Thresholds set below normal operating variance

**Permanent fixes:**
- Add evaluation delay (`last(5m)` instead of `last(1m)`)
- Use anomaly detection or forecast monitors
- Composite monitors (Alert only when 2+ signals agree)
- Alert grouping and deduplication in PagerDuty/Opsgenie
- Document silenced monitors with expiry dates

**Auto-healing potential:** Low (preventive tuning, not reactive)

---

## SECRET_MGMT

**Description:** Failures caused by expired, missing, misconfigured, or improperly rotated secrets, certificates, and credentials.

**Indicators:**
- TLS/certificate expiry errors
- `SecretNotFound`, `AccessDenied` on secret fetch
- Pod restarts after credential rotation
- Manual secret updates in production

**Permanent fixes:**
- External Secrets Operator (ESO) with AWS Secrets Manager / Vault
- Automated cert-manager with Let's Encrypt or internal CA
- Pre-expiry alerts at 30/14/7/1 days
- Secret rotation runbooks with zero-downtime patterns
- Eliminate secrets in ConfigMaps/env vars

**Auto-healing potential:** High (ESO sync, cert-manager renewal)

---

## K8S_CAPACITY

**Description:** Resource exhaustion in Kubernetes clusters — CPU, memory, disk, pod count, or node capacity.

**Indicators:**
- OOMKilled pods
- Pending pods (Insufficient cpu/memory)
- Node disk pressure / eviction
- HPA unable to scale (max replicas hit)
- PVC full or unable to provision

**Permanent fixes:**
- Right-size requests/limits based on actual usage (VPA recommendations)
- Cluster autoscaling with appropriate min/max nodes
- Resource quota reviews per namespace
- PVC expansion policies and cleanup jobs
- Quarterly capacity planning with growth projections

**Auto-healing potential:** High (HPA, cluster autoscaler, PVC expand)

---

## ACCESS_IAM

**Description:** Authorization failures, missing RBAC bindings, SSO issues, VPN/firewall blocks, and stale credentials.

**Indicators:**
- HTTP 403 / AccessDenied in logs
- `User cannot get/list/create` Kubernetes errors
- SSO login failures
- Service account token issues
- Cross-account/cross-VPC access blocks

**Permanent fixes:**
- IAM-as-code (Terraform) with PR review
- Automated RBAC provisioning via OIDC groups
- Quarterly access reviews with automated revocation
- Break-glass process with audit logging
- Service account token auto-rotation

**Auto-healing potential:** Medium (automated RBAC sync; manual for approvals)

---

## SECURITY_VULN

**Description:** CVEs, misconfigurations, policy violations, and compliance gaps detected by scanning tools.

**Indicators:**
- Wiz/Prisma/GuardDuty findings
- Failed image scan in CI/CD
- Open critical CVEs past SLA
- Public S3 buckets, open security groups

**Permanent fixes:**
- Image scanning gates in CI/CD (block deploy on critical CVE)
- Patch cadence SLAs (Critical: 7d, High: 30d)
- Infrastructure drift detection
- Automated remediation for known misconfigs
- Exception process with expiry and owner

**Auto-healing potential:** Medium (auto-patch for non-breaking; manual for major version bumps)

---

## DBA_PERF

**Description:** Database performance, availability, replication, backup, and storage issues.

**Indicators:**
- Deadlocks, lock waits, slow queries
- Replication lag alerts
- Connection pool exhaustion
- Backup/restore failures
- Storage growth exceeding projections

**Permanent fixes:**
- Query performance baselines and index optimization
- Connection pooling (PgBouncer, RDS Proxy)
- Automated maintenance windows
- Read replica scaling for read-heavy workloads
- Backup verification automation

**Auto-healing potential:** Medium (auto-failover, connection pool scaling; manual for query tuning)

---

## NETWORK_DNS

**Description:** Connectivity failures involving load balancers, ingress controllers, DNS, NAT, and network policies.

**Indicators:**
- DNS resolution failures
- Ingress 502/503/504 errors
- Connection timeouts between services
- Network policy drops

**Permanent fixes:**
- DNS-as-code with health checks
- Ingress controller redundancy
- Network policy templates in GitOps
- Synthetic monitoring for critical paths

**Auto-healing potential:** Medium (DNS failover, LB health check replacement)

---

## DEPLOYMENT

**Description:** Failed deployments, rollouts, Helm/ArgoCD sync failures, image pull errors, and config drift.

**Indicators:**
- CrashLoopBackOff after deploy
- Helm upgrade failures
- ArgoCD OutOfSync / Degraded
- ImagePullBackOff
- ConfigMap/Secret mount failures post-deploy

**Permanent fixes:**
- GitOps with automated sync and rollback
- Canary/blue-green deployments
- Pre-deploy validation (helm template, kubeconform)
- Immutable image tags, no `:latest`
- Automated rollback on failed health checks

**Auto-healing potential:** High (ArgoCD auto-sync, rollout undo)

---

## UNCATEGORIZED

Tickets/alerts that do not match automated patterns. Requires manual triage and potential new category creation.
