# READ-ONLY policy for ACO ops analysis

All scripts and agent actions against Jira and Datadog MUST be read-only.

## Jira — allowed
- Search issues (JQL)
- Get issue details
- Export to local CSV/JSON

## Jira — prohibited
- Create / update / delete issues
- Transition workflow states
- Add comments, attachments, or links
- Modify fields, labels, or assignments

## Datadog — allowed
- GET monitors, events, metrics queries
- List alert history

## Datadog — prohibited
- Create / update / delete monitors
- Mute / resolve alerts
- Modify dashboards or SLOs

## Verification
Scripts use only:
- Jira: `POST /rest/api/3/search/jql` (read)
- Datadog: `GET /api/v1/*` endpoints

No POST/PUT/PATCH/DELETE to Datadog management APIs.
