# Accessing Jira & Datadog Data

This Cloud Agent runs in a **remote VM**. It does **not** inherit MCP servers or credentials from your local Cursor Desktop. Jira MCP on your PC and Datadog API on your PC are not automatically available here.

Choose one of the paths below.

---

## Option A — Enable access in Cloud Agent environment (recommended)

### Jira via MCP

1. Open your Cloud Agent environment: [0fe1ad6d-9f34-11f1-a7d1-d6b4613131ce](https://cursor.com/dashboard/cloud-agents/environments/e/0fe1ad6d-9f34-11f1-a7d1-d6b4613131ce)
2. Go to **MCP Servers** and add the **Atlassian/Jira** MCP server (same one you use locally)
3. Complete OAuth / API authentication when prompted
4. Add egress allowlist for your Jira host (e.g. `your-org.atlassian.net`)
5. Start a **new** Cloud Agent run — MCP tools appear after the run boots with the updated environment

### Datadog via API secrets

Add these as **Environment Secrets** in the same dashboard:

| Secret | Description |
|--------|-------------|
| `DD_API_KEY` | Datadog API key |
| `DD_APP_KEY` | Datadog Application key |
| `DD_SITE` | Optional — `datadoghq.com`, `datadoghq.eu`, etc. |

Then re-run the agent or execute:

```bash
pip install -r docs/aco-ops/scripts/requirements.txt
python3 docs/aco-ops/scripts/collect_datadog.py
python3 docs/aco-ops/scripts/analyze_pain_points.py
```

---

## Option B — Export from your PC and attach to agent

Run these on your PC where Jira MCP / Datadog API already work.

### Datadog (from your PC)

```bash
export DD_API_KEY="your-api-key"
export DD_APP_KEY="your-app-key"
export DD_SITE="datadoghq.com"   # or datadoghq.eu

# Export 2026 YTD monitors + alert events
bash docs/aco-ops/scripts/local_datadog_export.sh docs/aco-ops/data/datadog/
```

Upload the generated files from `docs/aco-ops/data/datadog/` to this agent (attach in chat or commit to repo).

### Jira (from your PC — manual export)

In Jira, run this filter and export CSV:

```jql
project = ACO
AND issuetype in (Incident, Bug)
AND "Scrum Team" in ("Antuit CloudOps", "Antuit DBA")
AND created >= "2026-01-01"
ORDER BY created DESC
```

Save as `docs/aco-ops/data/jira/jira_issues_export.csv` and attach or commit.

### Jira (from your PC — if you have API token)

```bash
export JIRA_BASE_URL="https://your-org.atlassian.net"
export JIRA_USER_EMAIL="you@example.com"
export JIRA_API_TOKEN="your-token"

python3 docs/aco-ops/scripts/collect_jira.py --output docs/aco-ops/data/jira/
```

Upload the CSV/JSON output to this agent.

---

## Option C — Run analysis locally in Cursor Desktop

If Jira MCP is already working on your PC:

1. Open this repo locally in Cursor Desktop
2. Use Jira MCP to query incidents/bugs for both scrum teams
3. Run Datadog export script locally
4. Run `analyze_pain_points.py` locally
5. Commit updated reports and KEDB entries

---

## After data is available

Once files exist under `docs/aco-ops/data/` or MCP/secrets are configured:

```bash
python3 docs/aco-ops/scripts/analyze_pain_points.py \
  --jira docs/aco-ops/data/jira/ \
  --datadog docs/aco-ops/data/datadog/ \
  --output docs/aco-ops/reports/
```

The agent will then:
- Rank real pain points by frequency
- Link Jira keys and Datadog monitor IDs to KEDB entries
- Promote templates from `template` → `active`
- Update `REMEDIATION-ROADMAP.md` with data-driven priorities
