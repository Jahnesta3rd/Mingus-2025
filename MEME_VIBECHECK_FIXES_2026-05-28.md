# Vibe-Check Meme Population + Fixes (2026-05-28)

## What was done
- Populated cloud Postgres `memes` table with 137 new memes (144 total) from
  memes_source/ via scripts/populate_memes_postgres.py.
- Files served from static/memes/<day_folder>/<file>.

## Root-cause bugs found and fixed (NOT in git - server/DB state)

### 1. backend/.env overrode DATABASE_URL to a local Postgres
- app.py loads .env then backend/.env with override=True.
- backend/.env pointed DATABASE_URL at localhost:5432/mingus_db (stale local DB
  with only 7 memes / ~30 users), so the app ignored the cloud DB.
- FIX: updated backend/.env DATABASE_URL to the cloud DigitalOcean URL.
- TODO: consolidate to a single .env to prevent recurrence.

### 2. Duplicate systemd services
- mingus.service (old, March) and mingus-test.service (active, April) both ran
  gunicorn on :5000. Disabled mingus.service. mingus-test.service is canonical.

### 3. Cloud DB schema drift (tables/migrations missing vs local DB)
- agreement_acceptances.id (uuid) had no default -> added gen_random_uuid();
  created_at had no default -> added CURRENT_TIMESTAMP. Enabled pgcrypto.
- meme_analytics table may be missing; auto-creates on first vote/view.
- TODO: audit cloud DB for other missing migrations.

### 4. static/memes file permissions
- Files copied with 600 perms / non-www-data owner -> nginx 403.
- FIX: chmod 755 dirs, 644 files under static/memes/.
- NOTE: re-apply after future uploads.

### 5. Test user marcus.thompson.test@gmail.com (id=10)
- Had no user_id UUID and no onboarding_progress row -> set both manually.
- Password reset via backend.utils.password.hash_password (bcrypt).

## Outstanding
- ~80 test users live in the orphaned local Postgres (mingus_db on droplet),
  not the cloud DB. Migrate if needed.
- Credentials rotated: doadmin (cloud), mingus_user (local, now throwaway).
