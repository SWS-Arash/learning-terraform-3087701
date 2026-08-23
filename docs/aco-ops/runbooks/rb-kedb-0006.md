# RB-KEDB-0006: Database Connection Pool Exhaustion

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0006](../kedb/entries/KEDB-0006.json) |
| **Type** | Hybrid |
| **Owner** | Antuit DBA |
| **Severity** | P1 |
| **Est. MTTR** | 15 min (emergency) |

## Triggers

- Application: "too many connections", "connection timed out"
- RDS `DatabaseConnections` > 80% of max
- PgBouncer `cl_waiting` > 0

## Diagnosis

```sql
-- PostgreSQL: active connections by state
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Long idle connections
SELECT pid, usename, application_name, state, query_start, query
FROM pg_stat_activity
WHERE state = 'idle' AND query_start < now() - interval '10 minutes'
ORDER BY query_start;

-- Current connection count vs max
SHOW max_connections;
SELECT count(*) FROM pg_stat_activity;
```

## Remediation

### Phase A — Emergency (auto via webhook for P1)

```sql
-- Terminate idle connections older than 10 minutes (CAUTION: review first)
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND query_start < now() - interval '10 minutes'
  AND pid <> pg_backend_pid();
```

### Phase B — Stabilize

1. Identify connection leak source (application_name, usename)
2. Notify application team to restart pods (releases leaked connections)
3. Temporarily increase `max_connections` via RDS parameter group (requires reboot window)

### Phase C — Permanent

- Deploy/verify RDS Proxy or PgBouncer
- Set app pool: `max_connections_per_instance ≤ (DB_max / num_replicas) * 0.8`
- Add connection timeout defaults in app config

## Verification

- Connection count < 70% of max
- Application errors cleared
- No `cl_waiting` in PgBouncer stats

## Escalation

- Primary DB unreachable → invoke DR runbook
- Suspected connection leak → Application team + DBA joint bridge

## Post-Incident

- Review per-app pool settings
- Schedule RDS Proxy deployment if not present
