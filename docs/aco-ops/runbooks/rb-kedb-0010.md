# RB-KEDB-0010: Node Disk Pressure — Eviction Recovery & Cleanup

| Field | Value |
|-------|-------|
| **KEDB** | [KEDB-0010](../kedb/entries/KEDB-0010.json) |
| **Type** | Hybrid |
| **Owner** | CloudOps SRE |
| **Severity** | P2 |
| **Est. MTTR** | 30 min |

## Triggers

- Node condition `DiskPressure=True`
- Pods evicted: `The node was low on resource: ephemeral-storage`
- Datadog: node disk usage > 85%

## Diagnosis

```bash
kubectl describe node <node> | grep -A10 Conditions
kubectl get pods -A --field-selector spec.nodeName=<node>
kubectl get events -A --field-selector reason=Evicted | tail -20

# SSH to node (if permitted) or use debug pod
crictl images | sort -k6 -h  # largest images
du -sh /var/log/pods/*  | sort -h | tail -10
```

## Remediation

### Phase A — Immediate (automated cleanup DaemonSet)

```bash
# Cordon node to prevent new scheduling
kubectl cordon <node>

# Run image prune (via DaemonSet or SSM)
crictl rmi --prune

# Delete evicted pods
kubectl get pods -A --field-selector status.phase=Failed -o json | \
  jq -r '.items[] | select(.reason=="Evicted") | "\(.metadata.namespace) \(.metadata.name)"' | \
  while read ns name; do kubectl delete pod $name -n $ns; done
```

### Phase B — Drain & Replace

```bash
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
# Cluster autoscaler provisions replacement node
kubectl uncordon <node>  # only after disk issue resolved
```

### Phase C — Permanent

- Increase node disk in launch template / node pool config
- Configure kubelet log rotation:
  ```yaml
  containerLogMaxSize: 10Mi
  containerLogMaxFiles: 3
  imageGCHighThresholdPercent: 85
  imageGCLowThresholdPercent: 80
  ```
- Set `ephemeral-storage` requests on pods with large emptyDir

## Verification

- Node `DiskPressure=False`
- Evicted pods rescheduled and Running
- Disk usage < 70%

## Escalation

- Multiple nodes affected → Cluster capacity review
- Data loss from emptyDir eviction → Application team

## Post-Incident

- Review emptyDir usage in Helm charts
- Deploy node cleanup CronJob if not present
