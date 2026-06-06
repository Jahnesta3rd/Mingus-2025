# Income storage and conversation-history extraction (P3.2)

**Status:** Decision (April 30, 2026)  
**Scope:** Canonical persistence for modular onboarding income data; extraction pattern for Path 1 pre-beta.

---

## Decision summary

Canonical income storage for the modular onboarding chat flow is the **`user_income`** table via the **`UserIncome`** SQLAlchemy model. Other destinations (`income_streams` / `IncomeStream`, `user_profiles.financial_info`) are either vestigial or out of scope for structured income amounts and **must not** be treated as write targets for this flow.

---

## Why `user_income` is canonical

1. **Commit path writes here exclusively for income.** In `_modular_onboarding_gc2_commit.py`, income-related field commits (`monthly_takehome`, `pay_frequency`, `secondary_amount`, `has_secondary`) create and update **`UserIncome`** rows keyed by `user_id` and `source_name` (primary vs secondary). No parallel write path in that module persists the same facts to `IncomeStream` or `financial_info` for these branches.

2. **Verified user data.** Post-incident verification (e.g. user 4) shows a successful pre-bug session persisted as an active **`user_income`** row (e.g. employer label, amount, biweekly frequency)—consistent with production behavior when extraction and commit both succeed.

3. **Schema aligns with onboarding answers.** `UserIncome.frequency` is constrained to `monthly`, `biweekly`, `weekly`, `semimonthly`, and `annual` (`ck_user_income_frequency` in `financial_setup.py`). `_extract_income` maps user language to the same vocabulary (`biweekly`, `semimonthly`, `weekly`, `monthly`), so validated commits fit the table without ad hoc transforms.

4. **Relational integrity.** `user_id` is a foreign key to `users.id` with `ON DELETE CASCADE`, giving one clear relational home for per-user income sources.

**Model location:** `UserIncome` is defined in `backend/models/financial_setup.py` (table `user_income`), not in `user_models.py`.

**Non-canonical destinations (for this flow):**

| Destination | Role |
|-------------|------|
| `IncomeStream` / `income_streams` | Not used by modular onboarding GC2 commit for income; vestigial for this path. |
| `user_profiles.financial_info` | Legacy JSON; income module commit branches do not populate it for structured amounts (per P1.2). |

---

## Evidence: silent loss diagnosis (April 30, 2026)

End-to-end diagnosis used P3.0 diagnostic logging on the chat onboarding handler:

- **`chat_response_tail`** — assistant reply tail (confirms `[MODULE_COMPLETE:income]` and token gate behavior).
- **`chat_extraction`** — keys returned by `extract_module_data` for the active module.

Findings:

- The **`[MODULE_COMPLETE:income]`** gate and delegation from **`extract_module_data`** → **`_extract_income`** behave as designed.
- **`_extract_income`** only receives **`response_text`** (the latest assistant message). Dollar amounts and pay-frequency phrases supplied in **earlier user turns** are absent from that string when the token appears on the final reply, so **`monthly_takehome`** and **`pay_frequency`** are often missing while peripheral fields inferred from the closing reply (e.g. **`secondary_amount`**, **`bonus_cadence`**) may still parse.

---

## What this means for P3.2

- The fix is **extraction**, not **storage migration**. **`user_income` / `UserIncome`** remain the sole canonical destination for committed income from modular onboarding.
- **`_extract_income`** must receive enough **conversation context** (at minimum **user turns** from the current module) so amounts and frequency keywords are visible to the same regex/keyword logic already implemented on a single string.
- No migration from **`income_streams`** into **`user_income`** is proposed: onboarding does not populate that table; there is nothing actionable to merge for this bug class.

---

## Conversation-history extraction pattern (design sketch)

P3.2 will introduce a helper whose contract is fixed by this decision; implementation details belong in the PR.

```python
def extract_from_history(messages: list[dict], module_id: str) -> dict:
    """
    Extract module data from full conversation history (user turns only).

    Args:
        messages: ordered list of message dicts with at least 'role' and 'content' keys.
                  'role' is 'user' or 'assistant'.
        module_id: which module's extractor to dispatch to.

    Returns:
        dict of extracted fields, or empty dict if nothing matched.
    """
    # Concatenate all user turns since the module started, then run the
    # appropriate per-module extractor against the combined text.
```

**Commitment:** concatenate **user** messages for the active module (see session message shape in `modular_onboarding.py`), dispatch to the same per-module extractor functions used today, and merge or prefer history-derived fields per module rules. **`extract_module_data`** will gate on the ready token as today, then invoke history-aware extraction for Path 1 modules.

This is a **design sketch** only; P3.2 owns the concrete implementation and edge cases (ordering, deduplication, merge policy with `response_text` if needed).

---

## Scope boundaries (Path 1, pre-beta)

Per April 30 planning, **Option A** (conversation-history extraction) ships **before beta** for:

| Track | Module |
|-------|--------|
| P3.2a | **income** |
| P3.2b | **recurring_expenses** |
| P3.2c | **milestones** |

**housing**, **vehicle**, **roster**, and **career** share the same architectural limitation (extractors scan only the latest assistant text) and are deferred to **#60B** post-beta. Until then they may continue to return partial data and show incomplete dashboard state.

---

## Other onboarding paths

- **Quick Setup** writes coarse **`user_profiles.income_range`** (band), not detailed amounts. It is **not** a source of truth for analytics or dashboards that need dollar-level income.
- The **yes/no return-user prompt** (P4.4 design intent) does **not** write income records.
- **Structured income** for modular onboarding flows **only** through: **Modular Onboarding chat** → **`_extract_income`** (post-fix, history-aware) → **GC2 commit** → **`user_income`**.

---

## Expected codebase changes (P3.2)

Short list of intended diffs (no implementation in this document):

1. **New helper** — `extract_from_history` in `backend/routes/modular_onboarding.py` or a small utility module.
2. **`_extract_income`** — accept conversation history (or pre-merged text from the helper) and use **`extract_from_history`** so primary fields are recoverable from user turns.
3. **`extract_module_data`** — pass history through where applicable (signature/plumbing TBD in P3.2).
4. **Same pattern** for **`_extract_recurring_expenses`** and **`_extract_milestones`** within Path 1 scope.

---

## Explicit non-goals

- No step-by-step implementation, tests, or merge logic in this document (owned by P3.2).
- No **`income_streams` → `user_income`** migration narrative.
- No rollback or runbook content; the change is additive (helper + extractor wiring).
