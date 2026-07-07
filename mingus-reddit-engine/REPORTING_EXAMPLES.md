# Contact Attempt Reporting — Examples

PostgreSQL reporting layer for the Mingus leads dashboard. All objects live in
`storage/reporting_layer_queries.sql`.

## Setup

```bash
cd mingus-reddit-engine
psql "$DATABASE_URL" -f storage/reporting_layer_queries.sql
```

Verify views:

```sql
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'public' AND table_name LIKE 'vw_%'
ORDER BY table_name;
```

## Views

| View | Purpose |
|------|---------|
| `vw_lead_attempt_summary` | Totals and rates by `source` |
| `vw_lead_attempt_pipeline` | Funnel stage counts |
| `vw_leads_needing_action` | Queue with `next_action` |
| `vw_requeue_activity_7d` | Re-queue outcomes (7 days) |
| `vw_attempt_duration_analysis` | Days between attempts |

### Example — Instagram summary

```sql
SELECT * FROM vw_lead_attempt_summary WHERE source = 'instagram';
```

### Example — Funnel chart data

```sql
SELECT funnel_stage, lead_count
FROM vw_lead_attempt_pipeline
WHERE source = 'instagram'
ORDER BY stage_order;
```

Use in a bar or funnel chart: Not Contacted → Attempt 1 → Attempt 2 → Attempt 3 → Got Reply / No Reply.

## Live API endpoint

```bash
curl -u "$DASHBOARD_USER:$DASHBOARD_PASSWORD" \
  "https://dashboard.mingusapp.com/leads/attempt-report?source=instagram&days=30"
```

Returns `summary` (aggregate counts) and `details` (top 100 in-progress leads).

## Ad-hoc queries

Uncomment any `QUERY 1`–`QUERY 9` block in `storage/reporting_layer_queries.sql`, or run directly:

```sql
-- Leads needing attempt 2 today
SELECT l.id, l.ig_handle, l.attempt_1_at, a.notes
FROM leads l
LEFT JOIN lead_contact_attempts a ON a.lead_id = l.id AND a.attempt_number = 1
WHERE l.source = 'instagram'
  AND l.contact_attempt_count = 1
  AND l.response_got_dm = FALSE
  AND l.no_reply = FALSE
ORDER BY l.attempt_1_at ASC
LIMIT 50;
```

## Frontend chart ideas

1. **Summary cards** — `vw_lead_attempt_summary`: total, not_contacted, reply_rate_pct
2. **Funnel** — `vw_lead_attempt_pipeline`: stage_order on x-axis
3. **Action queue** — `vw_leads_needing_action` filtered by `next_action`
4. **Timing** — `vw_attempt_duration_analysis`: histogram of `days_attempt_1_to_2`

## weekly_report.py

Existing queries use `responded`, `response_got_dm`, and `no_reply`. The
`log-attempt` API sets `responded = TRUE` when `contact_attempt_count >= 1`, so
weekly engagement metrics remain valid without changes.

Optional enrichment — add to weekly report:

```sql
SELECT * FROM vw_lead_attempt_summary WHERE source = 'instagram';
```

## Optional Flask wrappers

Mirror QUERY 2 as an endpoint:

```python
@app.route("/api/leads/awaiting-attempt-2")
@requires_auth
def leads_awaiting_attempt_2():
    rows = _query("""
        SELECT l.id, l.author, l.ig_handle, l.attempt_1_at,
               (NOW()::date - l.attempt_1_at::date) AS days_since
        FROM leads l
        WHERE l.source = 'instagram' AND l.contact_attempt_count = 1
          AND l.response_got_dm = FALSE AND l.no_reply = FALSE
        ORDER BY l.attempt_1_at ASC LIMIT 50
    """)
    return jsonify(rows)
```
