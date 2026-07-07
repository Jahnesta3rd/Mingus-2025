-- Contact attempt tracking — PostgreSQL reporting layer
-- Run: psql $DATABASE_URL -f storage/reporting_layer_queries.sql
--
-- Safe to re-run: uses CREATE OR REPLACE VIEW
--
-- Verify:
--   SELECT table_name
--   FROM information_schema.views
--   WHERE table_schema = 'public' AND table_name LIKE 'vw_%'
--   ORDER BY table_name;

-- ===========================================================================
-- VIEW 1: vw_lead_attempt_summary — aggregate metrics by source
-- ===========================================================================

CREATE OR REPLACE VIEW vw_lead_attempt_summary AS
SELECT
    l.source,
    COUNT(*) AS total_leads,
    COUNT(*) FILTER (
        WHERE COALESCE(l.contact_attempt_count, 0) = 0
          AND COALESCE(l.no_reply, FALSE) = FALSE
    ) AS not_contacted,
    COUNT(*) FILTER (
        WHERE l.contact_attempt_count = 1
          AND COALESCE(l.response_got_dm, FALSE) = FALSE
          AND COALESCE(l.no_reply, FALSE) = FALSE
    ) AS awaiting_attempt_2,
    COUNT(*) FILTER (
        WHERE l.contact_attempt_count = 2
          AND COALESCE(l.response_got_dm, FALSE) = FALSE
          AND COALESCE(l.no_reply, FALSE) = FALSE
    ) AS awaiting_attempt_3,
    COUNT(*) FILTER (
        WHERE l.contact_attempt_count >= 3
          AND COALESCE(l.response_got_dm, FALSE) = FALSE
          AND COALESCE(l.no_reply, FALSE) = FALSE
    ) AS awaiting_response,
    COUNT(*) FILTER (WHERE COALESCE(l.response_got_dm, FALSE) = TRUE) AS got_reply,
    COUNT(*) FILTER (WHERE COALESCE(l.no_reply, FALSE) = TRUE) AS no_reply,
    COUNT(*) FILTER (WHERE l.requeued_at IS NOT NULL) AS ever_requeued,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE COALESCE(l.response_got_dm, FALSE) = TRUE)
        / NULLIF(COUNT(*), 0),
        1
    ) AS reply_rate_pct,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE COALESCE(l.no_reply, FALSE) = TRUE)
        / NULLIF(COUNT(*), 0),
        1
    ) AS no_reply_rate_pct
FROM leads l
GROUP BY l.source;

-- ===========================================================================
-- VIEW 2: vw_lead_attempt_pipeline — funnel stage counts by source
-- ===========================================================================

CREATE OR REPLACE VIEW vw_lead_attempt_pipeline AS
SELECT
    l.source,
    funnel_stage,
    stage_order,
    COUNT(*) AS lead_count
FROM leads l
CROSS JOIN LATERAL (
    VALUES
        ('not_contacted', 1,
            COALESCE(l.contact_attempt_count, 0) = 0
            AND COALESCE(l.no_reply, FALSE) = FALSE
            AND COALESCE(l.response_got_dm, FALSE) = FALSE),
        ('attempt_1', 2,
            l.contact_attempt_count = 1
            AND COALESCE(l.response_got_dm, FALSE) = FALSE
            AND COALESCE(l.no_reply, FALSE) = FALSE),
        ('attempt_2', 3,
            l.contact_attempt_count = 2
            AND COALESCE(l.response_got_dm, FALSE) = FALSE
            AND COALESCE(l.no_reply, FALSE) = FALSE),
        ('attempt_3', 4,
            l.contact_attempt_count >= 3
            AND COALESCE(l.response_got_dm, FALSE) = FALSE
            AND COALESCE(l.no_reply, FALSE) = FALSE),
        ('got_reply', 5, COALESCE(l.response_got_dm, FALSE) = TRUE),
        ('no_reply', 6, COALESCE(l.no_reply, FALSE) = TRUE)
) AS stages(funnel_stage, stage_order, is_active)
WHERE is_active
GROUP BY l.source, funnel_stage, stage_order
ORDER BY l.source, stage_order;

-- ===========================================================================
-- VIEW 3: vw_leads_needing_action — actionable queue with next step
-- ===========================================================================

CREATE OR REPLACE VIEW vw_leads_needing_action AS
SELECT
    l.id AS lead_id,
    l.source,
    l.author,
    l.ig_handle,
    l.contact_attempt_count,
    l.attempt_1_at,
    l.attempt_2_at,
    l.attempt_3_at,
    l.requeued_at,
    l.response_got_dm,
    l.no_reply,
    l.pipeline_stage,
    l.ingested_at,
    CASE
        WHEN COALESCE(l.response_got_dm, FALSE) = TRUE THEN 'terminal_got_reply'
        WHEN COALESCE(l.no_reply, FALSE) = TRUE THEN 'requeue_eligible'
        WHEN COALESCE(l.contact_attempt_count, 0) = 0 THEN 'log_attempt_1'
        WHEN l.contact_attempt_count = 1 THEN 'log_attempt_2'
        WHEN l.contact_attempt_count = 2 THEN 'log_attempt_3'
        WHEN l.contact_attempt_count >= 3 THEN 'awaiting_response_or_no_reply'
        ELSE 'unknown'
    END AS next_action,
    CASE
        WHEN l.attempt_1_at IS NULL THEN NULL
        ELSE (NOW()::date - l.attempt_1_at::date)
    END AS days_since_first_attempt,
    (
        SELECT MAX(t)
        FROM unnest(ARRAY[l.attempt_1_at, l.attempt_2_at, l.attempt_3_at]) AS t
    ) AS last_attempt_at
FROM leads l
WHERE COALESCE(l.response_got_dm, FALSE) = FALSE
   OR COALESCE(l.no_reply, FALSE) = TRUE;

-- ===========================================================================
-- VIEW 4: vw_requeue_activity_7d — re-queue outcomes (past 7 days)
-- ===========================================================================

CREATE OR REPLACE VIEW vw_requeue_activity_7d AS
SELECT
    l.id AS lead_id,
    l.source,
    l.author,
    l.ig_handle,
    l.requeued_at,
    l.contact_attempt_count AS attempts_after_requeue,
    l.response_got_dm,
    l.no_reply,
    CASE
        WHEN COALESCE(l.response_got_dm, FALSE) = TRUE THEN 'requeued_then_got_reply'
        WHEN COALESCE(l.no_reply, FALSE) = TRUE THEN 'requeued_then_no_reply'
        WHEN COALESCE(l.contact_attempt_count, 0) > 0 THEN 'requeued_in_progress'
        ELSE 'requeued_not_started'
    END AS outcome,
    (
        SELECT COUNT(*)
        FROM lead_contact_attempts a
        WHERE a.lead_id = l.id
    ) AS total_logged_attempts
FROM leads l
WHERE l.requeued_at >= NOW() - INTERVAL '7 days'
ORDER BY l.requeued_at DESC;

-- ===========================================================================
-- VIEW 5: vw_attempt_duration_analysis — elapsed time between attempts
-- ===========================================================================

CREATE OR REPLACE VIEW vw_attempt_duration_analysis AS
SELECT
    l.id AS lead_id,
    l.source,
    l.author,
    l.ig_handle,
    l.contact_attempt_count,
    l.attempt_1_at,
    l.attempt_2_at,
    l.attempt_3_at,
    CASE
        WHEN l.attempt_1_at IS NOT NULL AND l.attempt_2_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (l.attempt_2_at - l.attempt_1_at)) / 86400.0
        ELSE NULL
    END AS days_attempt_1_to_2,
    CASE
        WHEN l.attempt_2_at IS NOT NULL AND l.attempt_3_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (l.attempt_3_at - l.attempt_2_at)) / 86400.0
        ELSE NULL
    END AS days_attempt_2_to_3,
    CASE
        WHEN l.attempt_1_at IS NOT NULL AND l.attempt_3_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (l.attempt_3_at - l.attempt_1_at)) / 86400.0
        ELSE NULL
    END AS days_attempt_1_to_3,
    CASE
        WHEN l.attempt_1_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (NOW() - l.attempt_1_at)) / 86400.0
        ELSE NULL
    END AS days_since_first_attempt
FROM leads l
WHERE COALESCE(l.contact_attempt_count, 0) > 0;

-- ===========================================================================
-- REPORTING QUERIES (ad-hoc or wrap in Flask endpoints)
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- QUERY 1 — Dashboard summary card (total, in progress, success rates)
-- ---------------------------------------------------------------------------
-- SELECT * FROM vw_lead_attempt_summary WHERE source = 'instagram';

-- ---------------------------------------------------------------------------
-- QUERY 2 — Leads awaiting attempt 2 (with notes from attempt 1)
-- ---------------------------------------------------------------------------
-- SELECT
--     l.id,
--     l.author,
--     l.ig_handle,
--     l.attempt_1_at,
--     (NOW()::date - l.attempt_1_at::date) AS days_since_attempt_1,
--     a.notes AS attempt_1_notes,
--     a.channel AS attempt_1_channel
-- FROM leads l
-- LEFT JOIN lead_contact_attempts a
--     ON a.lead_id = l.id AND a.attempt_number = 1
-- WHERE l.source = 'instagram'
--   AND l.contact_attempt_count = 1
--   AND COALESCE(l.response_got_dm, FALSE) = FALSE
--   AND COALESCE(l.no_reply, FALSE) = FALSE
-- ORDER BY l.attempt_1_at ASC
-- LIMIT 50;

-- ---------------------------------------------------------------------------
-- QUERY 3 — Leads awaiting attempt 3 (with notes from attempt 2)
-- ---------------------------------------------------------------------------
-- SELECT
--     l.id,
--     l.author,
--     l.ig_handle,
--     l.attempt_2_at,
--     (NOW()::date - l.attempt_2_at::date) AS days_since_attempt_2,
--     a.notes AS attempt_2_notes,
--     a.channel AS attempt_2_channel
-- FROM leads l
-- LEFT JOIN lead_contact_attempts a
--     ON a.lead_id = l.id AND a.attempt_number = 2
-- WHERE l.source = 'instagram'
--   AND l.contact_attempt_count = 2
--   AND COALESCE(l.response_got_dm, FALSE) = FALSE
--   AND COALESCE(l.no_reply, FALSE) = FALSE
-- ORDER BY l.attempt_2_at ASC
-- LIMIT 50;

-- ---------------------------------------------------------------------------
-- QUERY 4 — Leads at attempt 3 with no reply (eligible for re-queue)
-- ---------------------------------------------------------------------------
-- SELECT
--     l.id,
--     l.author,
--     l.ig_handle,
--     l.attempt_3_at,
--     (NOW()::date - l.attempt_3_at::date) AS days_since_attempt_3
-- FROM leads l
-- WHERE l.source = 'instagram'
--   AND l.contact_attempt_count >= 3
--   AND COALESCE(l.response_got_dm, FALSE) = FALSE
--   AND COALESCE(l.no_reply, FALSE) = FALSE
-- ORDER BY l.attempt_3_at ASC;

-- ---------------------------------------------------------------------------
-- QUERY 5 — Re-queued in past 7 days (success tracking)
-- ---------------------------------------------------------------------------
-- SELECT * FROM vw_requeue_activity_7d WHERE source = 'instagram';

-- ---------------------------------------------------------------------------
-- QUERY 6 — Attempt history for single lead
-- ---------------------------------------------------------------------------
-- SELECT
--     a.attempt_number,
--     a.channel,
--     a.attempted_at,
--     a.notes,
--     a.logged_by,
--     a.created_at
-- FROM lead_contact_attempts a
-- WHERE a.lead_id = 'YOUR_LEAD_UUID_HERE'
-- ORDER BY a.attempt_number ASC;

-- ---------------------------------------------------------------------------
-- QUERY 7 — Bulk metrics for weekly_report.py
-- ---------------------------------------------------------------------------
-- SELECT
--     COUNT(*) AS total_leads_7d,
--     COUNT(*) FILTER (WHERE COALESCE(contact_attempt_count, 0) > 0) AS contacted_7d,
--     COUNT(*) FILTER (WHERE COALESCE(response_got_dm, FALSE) = TRUE) AS got_reply_7d,
--     COUNT(*) FILTER (WHERE COALESCE(no_reply, FALSE) = TRUE) AS no_reply_7d,
--     COUNT(*) FILTER (WHERE responded = TRUE) AS responded_flag_7d,
--     ROUND(AVG(contact_attempt_count) FILTER (
--         WHERE COALESCE(contact_attempt_count, 0) > 0
--     ), 2) AS avg_attempts_when_contacted
-- FROM leads
-- WHERE ingested_at >= NOW() - INTERVAL '7 days';

-- ---------------------------------------------------------------------------
-- QUERY 8 — Cohort analysis (reply rate by import week)
-- ---------------------------------------------------------------------------
-- SELECT
--     DATE_TRUNC('week', l.ingested_at)::date AS import_week,
--     l.source,
--     COUNT(*) AS leads_imported,
--     COUNT(*) FILTER (WHERE COALESCE(l.response_got_dm, FALSE) = TRUE) AS got_reply,
--     COUNT(*) FILTER (WHERE COALESCE(l.no_reply, FALSE) = TRUE) AS no_reply,
--     ROUND(
--         100.0 * COUNT(*) FILTER (WHERE COALESCE(l.response_got_dm, FALSE) = TRUE)
--         / NULLIF(COUNT(*), 0),
--         1
--     ) AS reply_rate_pct
-- FROM leads l
-- WHERE l.source = 'instagram'
-- GROUP BY DATE_TRUNC('week', l.ingested_at)::date, l.source
-- ORDER BY import_week DESC;

-- ---------------------------------------------------------------------------
-- QUERY 9 — Channel effectiveness (multiple channels)
-- ---------------------------------------------------------------------------
-- SELECT
--     a.channel,
--     COUNT(*) AS attempts_logged,
--     COUNT(DISTINCT a.lead_id) AS unique_leads,
--     COUNT(DISTINCT a.lead_id) FILTER (
--         WHERE COALESCE(l.response_got_dm, FALSE) = TRUE
--     ) AS leads_with_reply,
--     ROUND(
--         100.0 * COUNT(DISTINCT a.lead_id) FILTER (
--             WHERE COALESCE(l.response_got_dm, FALSE) = TRUE
--         ) / NULLIF(COUNT(DISTINCT a.lead_id), 0),
--         1
--     ) AS reply_rate_pct
-- FROM lead_contact_attempts a
-- JOIN leads l ON l.id = a.lead_id
-- GROUP BY a.channel
-- ORDER BY attempts_logged DESC;
