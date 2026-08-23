# Runbooks — Antuit CloudOps & DBA

Operational runbooks linked to KEDB entries. Each runbook specifies type, triggers, steps, and automation hooks.

## Runbook Types

| Type | Description |
|------|-------------|
| **manual** | Human executes all steps; used when judgment/approval required |
| **automated** | Script/operator/webhook executes without human intervention |
| **hybrid** | Automated triage + human approval gate for remediation action |

## Index

| Runbook | KEDB | Type | Category |
|---------|------|------|----------|
| [rb-kedb-0001](rb-kedb-0001.md) | KEDB-0001 | hybrid | MONITOR_NOISE |
| [rb-kedb-0002](rb-kedb-0002.md) | KEDB-0002 | automated | SECRET_MGMT |
| [rb-kedb-0003](rb-kedb-0003.md) | KEDB-0003 | hybrid | K8S_CAPACITY |
| [rb-kedb-0004](rb-kedb-0004.md) | KEDB-0004 | automated | SECRET_MGMT |
| [rb-kedb-0005](rb-kedb-0005.md) | KEDB-0005 | manual | ACCESS_IAM |
| [rb-kedb-0006](rb-kedb-0006.md) | KEDB-0006 | hybrid | DBA_PERF |
| [rb-kedb-0007](rb-kedb-0007.md) | KEDB-0007 | hybrid | DBA_PERF |
| [rb-kedb-0008](rb-kedb-0008.md) | KEDB-0008 | manual | SECURITY_VULN |
| [rb-kedb-0009](rb-kedb-0009.md) | KEDB-0009 | automated | DEPLOYMENT |
| [rb-kedb-0010](rb-kedb-0010.md) | KEDB-0010 | hybrid | K8S_CAPACITY |

## Runbook Template Structure

Every runbook includes:

1. **Metadata** — ID, owner, severity, estimated MTTR
2. **Triggers** — Datadog monitor, Jira pattern, alert conditions
3. **Prerequisites** — Access, tools, approval requirements
4. **Diagnosis** — How to confirm this is the known error
5. **Remediation** — Step-by-step (manual) or script reference (automated)
6. **Verification** — How to confirm resolution
7. **Escalation** — When to escalate and to whom
8. **Post-incident** — KEDB update, permanent fix tracking

## Automation Integration

Runbooks can be triggered via:

- **Datadog Workflow Automation** — webhook on monitor alert
- **PagerDuty** — custom incident action linking to runbook URL
- **Argo Workflows / GitHub Actions** — scheduled or event-driven
- **Kubernetes Job** — triggered by Alertmanager webhook

Store automation scripts in `scripts/remediation/` (create as permanent fixes are implemented).
