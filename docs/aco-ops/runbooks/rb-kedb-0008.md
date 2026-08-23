# RB-KEDB-0008: Critical CVE Blocking Deployment

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0008](../kedb/entries/KEDB-0008.json) |
| **Type** | Manual |
| **Owner** | CloudOps Security |
| **Severity** | P2 (deploy blocked) / P1 (exploitable in prod) |
| **Est. MTTR** | 4h–7d depending on patch availability |

## Triggers

- CI/CD image scan failure (Trivy/Wiz/Prisma)
- Gatekeeper/OPA policy deny
- Datadog: critical CVE count > 0 in production images

## Prerequisites

- Access to vulnerability scanner dashboard
- CI/CD pipeline access
- Security exception approval workflow

## Diagnosis

1. Identify CVE ID, CVSS score, affected package/image
2. Assess exploitability in your context:
   - Is the vulnerable component exposed externally?
   - Is there a known exploit in the wild?
   - Are compensating controls in place (WAF, network isolation)?

```bash
# Trivy scan example
trivy image --severity CRITICAL <image:tag>

# Check if base image update available
trivy image --list-all-pkgs <image:tag> | grep <package>
```

## Remediation

### Path A — Patch Available

1. Update base image or dependency version
2. Rebuild and scan image
3. Deploy via normal GitOps pipeline
4. Verify CVE cleared in scanner

### Path B — No Patch Yet (Exception Required)

1. Document in CVE Exception Registry:
   - CVE ID, CVSS, affected service
   - Exploitability assessment
   - Compensating controls
   - Exception expiry date (max 30 days)
   - Owner responsible for monitoring
2. Obtain Security team approval
3. Add OPA/Gatekeeper exception annotation to deployment
4. Set calendar reminder to re-evaluate when patch available

### Path C — Exploitable in Production (P1)

1. Immediate containment: network isolate, disable feature, WAF rule
2. Emergency patch or rollback to last known-good image
3. Incident bridge with Security + App team

## Verification

- Image scan passes in CI
- No critical CVEs in production inventory
- Exception documented if applicable

## Escalation

- Zero-day with active exploitation → CISO notification
- Patch breaks application → App team + DBA for compatibility testing

## Post-Incident

- Update Renovate/Dependabot config if dependency was outdated
- Review base image rebuild cadence
