-- HRA-05: Seed distinct zips for test personas (Tracker #187)
-- Run: psql "$DATABASE_URL" -f backend/scripts/seed_test_zips.sql
--
-- Persona mapping (user_id → zip → CBSA):
--   9  Maya Johnson (Budget e2e)     → 77001 → 26420 Houston
--  31  probe test user               → 60601 → 16980 Chicago
--  40  career rec-seed               → 10001 → 35620 NYC
--  41  career designer seed          → 85001 → 38060 Phoenix
--  50  housing test user             → 30301 → 12060 Atlanta

BEGIN;

-- housing_profile (primary source for resolve_search_zip)
UPDATE housing_profile SET zip_or_city = '77001', updated_at = NOW() WHERE user_id = 9;
UPDATE housing_profile SET zip_or_city = '60601', updated_at = NOW() WHERE user_id = 31;
UPDATE housing_profile SET zip_or_city = '10001', updated_at = NOW() WHERE user_id = 40;
UPDATE housing_profile SET zip_or_city = '85001', updated_at = NOW() WHERE user_id = 41;
UPDATE housing_profile SET zip_or_city = '30301', updated_at = NOW() WHERE user_id = 50;

-- Mirror into user_profiles.zip_code (JRA-01 fallback chain)
UPDATE user_profiles SET zip_code = '77001', updated_at = NOW()
  WHERE email = 'maya.johnson.test@gmail.com';
UPDATE user_profiles SET zip_code = '60601', updated_at = NOW()
  WHERE email = 'probe.0528@mingustest.local';
UPDATE user_profiles SET zip_code = '10001', updated_at = NOW()
  WHERE email = 'rec-seed-d791ded7@example.com';
UPDATE user_profiles SET zip_code = '85001', updated_at = NOW()
  WHERE email = 'designer-ae4e6a50@example.com';
UPDATE user_profiles SET zip_code = '30301', updated_at = NOW()
  WHERE email = 'housing.test.a.06052026@gmail.com';

COMMIT;

-- Verify (optional):
-- SELECT hp.user_id, u.email, hp.zip_or_city, up.zip_code
-- FROM housing_profile hp
-- JOIN users u ON u.id = hp.user_id
-- LEFT JOIN user_profiles up ON up.email = u.email
-- WHERE hp.user_id IN (9, 31, 40, 41, 50)
-- ORDER BY hp.user_id;

-- =============================================================================
-- ROLLBACK (restore pre-HRA-05 values captured 2026-06-19)
-- =============================================================================
-- BEGIN;
-- UPDATE housing_profile SET zip_or_city = '30318', updated_at = NOW() WHERE user_id = 9;
-- UPDATE housing_profile SET zip_or_city = '30319', updated_at = NOW() WHERE user_id = 31;
-- UPDATE housing_profile SET zip_or_city = '10001', updated_at = NOW() WHERE user_id = 40;
-- UPDATE housing_profile SET zip_or_city = '85001', updated_at = NOW() WHERE user_id = 41;
-- UPDATE housing_profile SET zip_or_city = '30314', updated_at = NOW() WHERE user_id = 50;
-- UPDATE user_profiles SET zip_code = NULL, updated_at = NOW()
--   WHERE email IN (
--     'maya.johnson.test@gmail.com',
--     'probe.0528@mingustest.local',
--     'rec-seed-d791ded7@example.com',
--     'designer-ae4e6a50@example.com',
--     'housing.test.a.06052026@gmail.com'
--   );
-- COMMIT;
