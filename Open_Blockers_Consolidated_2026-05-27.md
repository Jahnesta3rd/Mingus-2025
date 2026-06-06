# Open Blockers — Consolidated (2026-05-27)

## Today's session

| Date | Update |
|------|--------|
| 2026-05-29 | Update 2026-05-29: #151 RESOLVED — fresh cloud signups get a non-NULL UUID (confirmed via real browser signup, id 34); auth half reclassified to a low-priority 2-row legacy backfill (maya id 9, jasmine id 11, backfill still pending), not a blocker. #155 CLOSED (snapshot card rewire deployed, all cards render). #156 CLOSED — Add-Important-Date modal rewired off the onboarding commit-module to a direct PATCH /api/user/profile with email upsert; fixed, verified end-to-end, committed 9aa13bd7, pushed (retrospectively Tier 1 — no working event-add path had existed). No remaining Tier-0/Tier-1 launch blockers from today's items. |

## Blocker register

| ID | Tier | Status | Summary |
|----|------|--------|---------|
| #151 | 1 | RESOLVED | Dashboard snapshot endpoints / UUID-vs-integer suspect |
| #155 | 1 | CLOSED | Snapshot card rewire |
| #156 | 1 | CLOSED | Add Important Date modal does not persist events |

### #151 — updates

Update 2026-05-29: #151 RESOLVED — fresh cloud signups get a non-NULL UUID (confirmed via real browser signup, id 34); auth half reclassified to a low-priority 2-row legacy backfill (maya id 9, jasmine id 11, backfill still pending), not a blocker. #155 CLOSED (snapshot card rewire deployed, all cards render). #156 CLOSED — Add-Important-Date modal rewired off the onboarding commit-module to a direct PATCH /api/user/profile with email upsert; fixed, verified end-to-end, committed 9aa13bd7, pushed (retrospectively Tier 1 — no working event-add path had existed). No remaining Tier-0/Tier-1 launch blockers from today's items.
