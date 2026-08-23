# RB-KEDB-0007: Replication Lag on Read Replica

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0007](../kedb/entries/KEDB-0007.json) |
| **Type** | Hybrid |
| **Owner** | Antuit DBA |
| **Severity** | P2 |
| **Est. MTTR** | 30 min |

## Triggers

- `ReplicaLag` > SLA threshold (default 30s)
- Stale data reports from read-only endpoints
- CloudWatch/RDS `OldestReplicationSlotLag` elevated

## Diagnosis

```sql
-- PostgreSQL: replication lag
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
FROM pg_stat_replication;

-- Long running transactions on primary blocking WAL
SELECT pid, usename, state, query_start, query
FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - interval '5 minutes';
```

## Remediation

### Phase A — Immediate

1. Route critical reads to primary (update connection string / DNS weight)
2. Identify blocking transaction on primary:
   ```sql
   SELECT pg_cancel_backend(pid); -- or pg_terminate_backend if needed
   ```

### Phase B — Scale

- Increase replica instance class if CPU/IOPS saturated
- Increase replica storage IOPS if I/O bound

### Phase C — Permanent

- Optimize slow writes causing large WAL
- Right-size replica to match primary write throughput
- Set `max_standby_streaming_delay` appropriately

## Verification

- ReplicaLag < SLA for 15 min
- Read-only endpoints return current data

## Escalation

- Lag > 5 min AND growing → DBA lead + application team
- Replica unreachable → Failover runbook

## Post-Incident

- Document lag SLA per application tier
- Schedule write query optimization if root cause was slow writes
