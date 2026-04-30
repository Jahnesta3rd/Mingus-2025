-- user_state_audit.sql
-- One-row-per-user snapshot for regression checks after signup / Phases 2–4 fixes.
--
-- Run:
--   sudo -u postgres psql mingus_db -v ON_ERROR_STOP=1 -f scripts/diagnostics/user_state_audit.sql
--
-- Schema notes (from backend/models):
--   users.tier           — canonical subscription tier (default budget; Stripe webhook in app.py updates this)
--   user_profiles        — joined on normalized email (no FK to users.id in app code)
--   onboarding_progress — PK / FK user_id -> users.id
--   income_streams       — user_id -> users.id
--   recurring_expenses   — user_id -> users.id

\pset null '(NULL)'

SELECT
    u.id AS users_id,
    u.email AS users_email,

    -- Distinct from false: unknown vs absent
    (up.user_profile_id IS NOT NULL) AS user_profiles_row_exists,
    up.user_profile_id AS user_profiles_id,

    (op.user_id IS NOT NULL) AS onboarding_progress_row_exists,

    -- Counts are never NULL (LATERAL always returns one aggregate row)
    isc.income_streams_count,
    rec.recurring_expenses_count,

    -- Tier lives on users, not user_profiles (see User model + Stripe payment_intent.succeeded handler)
    COALESCE(NULLIF(BTRIM(u.tier), ''), '(NULL or blank)') AS subscription_tier_users_table,

    u.created_at AS users_created_at

FROM users u

-- At most one profile row per user email (deterministic: lowest id)
LEFT JOIN LATERAL (
    SELECT p.id AS user_profile_id
    FROM user_profiles p
    WHERE lower(btrim(p.email)) = lower(btrim(u.email))
    ORDER BY p.id
    LIMIT 1
) up ON TRUE

LEFT JOIN onboarding_progress op
    ON op.user_id = u.id

-- LATERAL COUNT(*) so "no rows" is 0, not a missing LEFT JOIN row from a pre-aggregated subquery.
LEFT JOIN LATERAL (
    SELECT count(*)::bigint AS income_streams_count
    FROM income_streams i
    WHERE i.user_id = u.id
) isc ON TRUE

LEFT JOIN LATERAL (
    SELECT count(*)::bigint AS recurring_expenses_count
    FROM recurring_expenses r
    WHERE r.user_id = u.id
) rec ON TRUE

ORDER BY u.id DESC;

\pset null ''
