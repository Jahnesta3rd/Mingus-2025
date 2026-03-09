# Database Split Recommendation: From Single `mingus_vehicles.db` to App vs Vehicles

## Current State

- **Single DB:** `backend/models/database.py` sets  
  `database_url = os.environ.get('DATABASE_URL', 'sqlite:///mingus_vehicles.db')`  
  and `db.create_all()` creates **all** tables in that one file.
- **Result:** A file named `mingus_vehicles.db` that holds the **entire** app: users, auth, vehicles, housing, wellness, notifications, subscriptions, etc.
- **Issues:** Misleading name, no separation of sensitive (auth) vs feature data, harder to scale/back up/migrate by concern.

---

## Recommended Path: Two Phases

### Phase 1 — Rename and document (low risk, do first)

**Goal:** Stop implying “only vehicles” and make it clear where app/auth data lives. No model or FK changes.

1. **Change the default DB name in code**
   - In `backend/models/database.py`, change the default from `mingus_vehicles.db` to something like `mingus_app.db` or `app.db`:
     ```python
     database_url = os.environ.get('DATABASE_URL', 'sqlite:///mingus_app.db')
     ```
   - Update `get_database_url()` the same way.

2. **Keep existing deployments working**
   - Document that **existing** installs (including test.mingusapp.com) should keep using their current file via env:
     ```bash
     DATABASE_URL=sqlite:///mingus_vehicles.db   # or full path, e.g. /var/lib/mingus/mingus_vehicles.db
     ```
   - So: new installs get `mingus_app.db`; old installs keep `mingus_vehicles.db` until you choose to migrate.

3. **Optional: one-time rename for existing instances**
   - On a server that currently uses `mingus_vehicles.db`, you can switch to the new name without losing data:
     - Stop the app.
     - Copy or rename: `cp instance/mingus_vehicles.db instance/mingus_app.db` (or set `DATABASE_URL` to the new path).
     - Set `DATABASE_URL=sqlite:///mingus_app.db` (or the path you used).
     - Start the app.
   - No code change required beyond the default in `database.py`.

4. **Document where data lives**
   - In `docs/` (e.g. a short “Database” or “Operations” doc), state:
     - Auth, users, payments, subscriptions, and all other app data live in the **single** DB pointed to by `DATABASE_URL`.
     - For current production/test, that file is still `instance/mingus_vehicles.db` unless `DATABASE_URL` is set otherwise.
     - When seeding test users or checking auth, use that file (not `assessments.db` or `backend/app.db`).

**Outcome:** Clear naming, backward compatible, no schema or relationship changes.

---

### Phase 2 — True split into two databases (optional, higher effort)

**Goal:**  
- **App DB** (`app.db` / `mingus_app.db`): users, auth, payments, subscriptions, notifications, and any non-vehicle feature that FKs to `users`.  
- **Vehicles DB** (`mingus_vehicles.db`): vehicle-specific tables only.

**Why it’s non-trivial:**  
Almost every model has `db.ForeignKey('users.id')`. Splitting DBs means:

- Vehicle-related tables (e.g. `vehicles`, `maintenance_predictions`, `commute_scenarios`, `msa_gas_prices`) move to a **second** SQLite file.
- You **cannot** keep a real FK from `vehicles.user_id` → `users.id` across two files in SQLite. So you:
  - Keep `user_id` as a plain integer (no `ForeignKey`), and
  - Either drop `User.vehicles` or implement it in app code (e.g. query the vehicles bind by `user_id`).

**Steps (high level):**

1. **Env and config**
   - Add a second URL, e.g. `VEHICLE_DATABASE_URL` (default `sqlite:///mingus_vehicles.db`).
   - In `database.py`, set Flask-SQLAlchemy **binds**:
     - Default bind → `DATABASE_URL` (app DB).
     - Named bind `'vehicles'` → `VEHICLE_DATABASE_URL`.

2. **Assign models to binds**
   - On **vehicle-only** models (e.g. `Vehicle`, `MaintenancePrediction`, `CommuteScenario`, `MSAGasPrice`), set `__bind_key__ = 'vehicles'`.
   - All other models stay on the default (app) bind.

3. **Adjust Vehicle (and any other “vehicle DB” models)**
   - Remove `db.ForeignKey('users.id')` from `Vehicle.user_id`; keep `user_id = db.Column(db.Integer, nullable=False, index=True)`.
   - Remove or replace `User.vehicles` relationship:
     - Option A: Remove it and in endpoints query `Vehicle.query.filter_by(user_id=current_user.id).all()` (Flask-SQLAlchemy will use the `vehicles` bind for `Vehicle`).
     - Option B: Use a `relationship(..., primaryjoin=..., foreign_keys=..., lazy='select')` that does not rely on a DB-level FK (more involved).

4. **Create tables in both DBs**
   - After setting binds, call `db.create_all()` (or create_all per bind). That creates app tables in the app DB and vehicle tables in the vehicles DB.

5. **Data migration**
   - Export vehicle-related tables from the current single DB (e.g. `sqlite3 mingus_vehicles.db .dump` filtered to those tables, or a small script).
   - Create the new `mingus_vehicles.db` (or path from `VEHICLE_DATABASE_URL`) and import only those tables.
   - Point `DATABASE_URL` at the existing DB (now app-only if you removed vehicle tables) or at a new `mingus_app.db` that you’ve populated with non-vehicle tables.

6. **Tests and docs**
   - Update tests that assume one DB (e.g. set both `DATABASE_URL` and `VEHICLE_DATABASE_URL` for integration tests, or use in-memory SQLite for both).
   - Document the two URLs and which tables live in which DB.

**Caveats:**

- No cross-database FK or JOIN in SQLite; integrity is by app logic.
- Backups/restores and migrations become two-step (app DB + vehicles DB).
- Any code that joins User with Vehicle (or other vehicle tables) must do two queries or application-side “joins.”

---

## Model categorization (for Phase 2)

| Database   | Models / tables |
|-----------|------------------|
| **App**   | `User`, auth-related, `RecurringExpense`, `UserIncome`, housing, wellness, notifications, gamification, daily_outlook, tax_adjacent (expense/report), subscription, content_optimization, etc. — anything with `ForeignKey('users.id')` that is not vehicle-specific. |
| **Vehicles** | `Vehicle`, `MaintenancePrediction`, `CommuteScenario`, `MSAGasPrice`. Optionally: `FleetVehicle`, `MileageLog`, `BusinessExpense`, `MaintenanceRecord`, `TaxReport`, `FleetAnalytics` if you want all “fleet/vehicle” data in the second DB. |

---

## Summary

- **Do Phase 1 now:** Change default DB name to `mingus_app.db` (or `app.db`), document `DATABASE_URL` for existing installs, and document where auth/app data lives (`instance/mingus_vehicles.db` until you switch). Optionally add a one-line note or script for renaming the file and switching env.
- **Do Phase 2 only if you need** separate backup, scaling, or isolation of vehicle data; it requires bind setup, removing cross-DB FKs, and a one-time data migration.

After Phase 1, when you seed test users or check auth data, you still look at the file pointed to by `DATABASE_URL` (currently `instance/mingus_vehicles.db` unless overridden), and the name no longer implies “vehicles only” for new installs.
