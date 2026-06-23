-- HRA-05: Seed distinct zips for test personas (Tracker #187)
-- Run: psql "$DATABASE_URL" -f backend/scripts/seed_test_zips.sql
--
-- Persona mapping (user_id → zip → CBSA):
--   9  Maya (Phoenix)     → 85001 → 38060
--  10  Chicago persona    → 60601 → 16980
--  11  Jasmine (Houston)  → 77001 → 26420
--  40  Marcus (NYC)       → 10001 → 35620
--  41  Atlanta persona    → 30301 → 12060

BEGIN;

UPDATE housing_profile SET zip_or_city = '10001', updated_at = NOW()
  WHERE user_id = 40;   -- NYC (Marcus)
UPDATE housing_profile SET zip_or_city = '85001', updated_at = NOW()
  WHERE user_id = 9;    -- Phoenix (Maya)
UPDATE housing_profile SET zip_or_city = '77001', updated_at = NOW()
  WHERE user_id = 11;   -- Houston (Jasmine)
UPDATE housing_profile SET zip_or_city = '60601', updated_at = NOW()
  WHERE user_id = 10;   -- Chicago
UPDATE housing_profile SET zip_or_city = '30301', updated_at = NOW()
  WHERE user_id = 41;   -- Atlanta

-- Users 10 and 11 may lack housing_profile rows (e2e personas)
INSERT INTO housing_profile (
  user_id, housing_type, monthly_cost, zip_or_city, has_buy_goal,
  down_payment_saved, created_at, updated_at
)
VALUES
  (10, 'rent', 1400, '60601', false, 0, NOW(), NOW()),
  (11, 'rent', 1400, '77001', false, 0, NOW(), NOW())
ON CONFLICT (user_id) DO UPDATE
  SET zip_or_city = EXCLUDED.zip_or_city, updated_at = NOW();

-- Mirror into user_profiles.zip_code (JRA-01 fallback chain)
UPDATE user_profiles up
SET zip_code = mapping.zip, updated_at = NOW()
FROM (
  VALUES
    (9, '85001'),
    (10, '60601'),
    (11, '77001'),
    (40, '10001'),
    (41, '30301')
) AS mapping(user_id, zip)
JOIN users u ON u.id = mapping.user_id
WHERE up.email = u.email;

COMMIT;

-- Verify (optional):
-- SELECT user_id, zip_or_city FROM housing_profile
-- WHERE user_id IN (9, 10, 11, 40, 41)
-- ORDER BY user_id;

-- =============================================================================
-- ROLLBACK (restore pre-HRA-05 values captured 2026-06-19)
-- =============================================================================
-- BEGIN;
-- UPDATE housing_profile SET zip_or_city = '30318', updated_at = NOW() WHERE user_id = 9;
-- UPDATE housing_profile SET zip_or_city = '30319', updated_at = NOW() WHERE user_id = 10;
-- UPDATE housing_profile SET zip_or_city = '30314', updated_at = NOW() WHERE user_id = 11;
-- UPDATE housing_profile SET zip_or_city = '10001', updated_at = NOW() WHERE user_id = 40;
-- UPDATE housing_profile SET zip_or_city = '85001', updated_at = NOW() WHERE user_id = 41;
-- UPDATE user_profiles up SET zip_code = NULL, updated_at = NOW()
-- FROM users u
-- WHERE up.email = u.email AND u.id IN (9, 10, 11, 40, 41);
-- COMMIT;
