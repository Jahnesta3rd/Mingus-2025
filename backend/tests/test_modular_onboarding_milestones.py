"""Regression tests for milestones extraction (meaningful event names, token gating)."""

from __future__ import annotations

import pytest

from backend.routes.modular_onboarding import (
    _milestone_event_name_meaningful,
    extract_module_data,
)


def _milestones_event_summaries(data: dict) -> list[str]:
    """One-line summaries per extracted event for assertion diagnostics."""
    rows: list[str] = []
    for ev in data.get("events") or []:
        if isinstance(ev, dict):
            rows.append(
                f"name={ev.get('name')!r} cost={ev.get('cost')!r} date={ev.get('date')!r}"
            )
        else:
            rows.append(repr(ev))
    return rows


def _events_by_name(data: dict) -> dict[str, list[dict]]:
    """Group milestone event dicts by stringified name (repr for None) for diagnostics."""
    out: dict[str, list[dict]] = {}
    for ev in data.get("events") or []:
        if not isinstance(ev, dict):
            continue
        n = ev.get("name")
        key = repr(n) if n is None else str(n)
        out.setdefault(key, []).append(ev)
    return out


def test_scenario_1_nothing_upcoming_without_token_returns_empty():
    text = "Great — nothing upcoming for you then."
    got = extract_module_data(text, "milestones")
    assert got == {}, (
        "expected {} when [MODULE_COMPLETE:milestones] is absent even if "
        f"'nothing upcoming' appears; got keys={list(got.keys()) if isinstance(got, dict) else type(got)}"
    )


def test_scenario_2_nothing_upcoming_with_token_returns_empty_events():
    text = (
        "Great — nothing upcoming for you then.\n"
        "[MODULE_COMPLETE:milestones]"
    )
    got = extract_module_data(text, "milestones")
    assert got == {"events": []}, (
        "expected explicit empty milestones list when user has nothing upcoming and token present; "
        f"got {got!r}"
    )


def test_scenario_3_token_one_event_meaningful_name():
    text = (
        "Got it, you have a trip to Miami on 2026-07-15 for $1200.\n"
        "[MODULE_COMPLETE:milestones]"
    )
    got = extract_module_data(text, "milestones")
    assert got, f"expected non-empty extraction; got {got!r}"
    events = got.get("events") or []
    assert len(events) == 1, (
        f"expected exactly 1 event; got {len(events)} summaries={_milestones_event_summaries(got)}"
    )
    name = (events[0].get("name") or "").lower()
    assert "miami" in name or "trip" in name, (
        f"expected name to mention Miami or trip; got name={events[0].get('name')!r} "
        f"summaries={_milestones_event_summaries(got)}"
    )


def test_scenario_4_token_present_cost_but_no_usable_name_returns_empty():
    # Note: "Got it — $500 for that." still parses a name ("Got it") because strip() trims
    # trailing punctuation from the pre-$ segment; use a punctuation-only prefix instead.
    text = ": — $500 for that. [MODULE_COMPLETE:milestones]"
    got = extract_module_data(text, "milestones")
    assert got == {}, (
        "expected {} when token is present but pre-$ text has no >=3 alphanumeric name; "
        f"got {got!r} summaries={_milestones_event_summaries(got) if isinstance(got, dict) else 'n/a'}"
    )


def test_scenario_5_token_multiple_fragments_one_good_one_bad_returns_one_event():
    text = (
        "Got it — car registration 2026-06-01 for $200, and also $300.\n"
        "[MODULE_COMPLETE:milestones]"
    )
    got = extract_module_data(text, "milestones")
    assert got, f"expected non-empty extraction; got {got!r}"
    events = got.get("events") or []
    assert len(events) == 1, (
        f"expected exactly 1 event after filtering junk name fragments; got {len(events)} "
        f"by_name={_events_by_name(got)} summaries={_milestones_event_summaries(got)}"
    )
    name = (events[0].get("name") or "").lower()
    assert "registration" in name or "car" in name, (
        f"expected surviving event to be car registration; name={events[0].get('name')!r} "
        f"summaries={_milestones_event_summaries(got)}"
    )


def test_scenario_6_name_only_punctuation_returns_empty():
    text = "—: $400 for it. [MODULE_COMPLETE:milestones]"
    got = extract_module_data(text, "milestones")
    assert got == {}, (
        "expected {} when pre-$ text has no alphanumeric name; "
        f"got {got!r} summaries={_milestones_event_summaries(got) if isinstance(got, dict) else 'n/a'}"
    )


def test_scenario_7_single_word_trip_passes_threshold():
    text = "Trip $500 on 2026-08-01. [MODULE_COMPLETE:milestones]"
    got = extract_module_data(text, "milestones")
    assert got, f"expected non-empty extraction; got {got!r}"
    events = got.get("events") or []
    assert len(events) == 1, (
        f"expected 1 event; got {len(events)} summaries={_milestones_event_summaries(got)}"
    )
    assert events[0].get("name") == "Trip", (
        f"expected name 'Trip'; got {events[0].get('name')!r} "
        f"summaries={_milestones_event_summaries(got)}"
    )


def test_scenario_8_two_letter_name_fails_threshold_returns_empty():
    text = "AB $500 on 2026-08-01. [MODULE_COMPLETE:milestones]"
    got = extract_module_data(text, "milestones")
    assert got == {}, (
        "expected {} when name has fewer than 3 alphanumeric characters; "
        f"got {got!r} summaries={_milestones_event_summaries(got) if isinstance(got, dict) else 'n/a'}"
    )


def test_scenario_9_no_token_returns_empty():
    text = "When is your next milestone?"
    got = extract_module_data(text, "milestones")
    assert got == {}, (
        "expected {} without completion token; "
        f"got keys={list(got.keys()) if isinstance(got, dict) else type(got)}"
    )


def test_scenario_10_nothing_planned_variant_returns_empty_events():
    text = "Got it, nothing planned. [MODULE_COMPLETE:milestones]"
    got = extract_module_data(text, "milestones")
    assert got == {"events": []}, (
        "expected {'events': []} for nothing_planned escape hatch with token; "
        f"got {got!r}"
    )


def test_scenario_11_milestone_name_meaningful_three_plus_alnum():
    assert _milestone_event_name_meaningful("Car registration") is True, (
        "multi-word label with many letters should be meaningful"
    )


def test_scenario_12_milestone_name_meaningful_only_punctuation():
    assert _milestone_event_name_meaningful("—$!") is False, (
        "punctuation-only string should not count as meaningful"
    )


def test_scenario_13_milestone_name_meaningful_none():
    assert _milestone_event_name_meaningful(None) is False, (
        "None must not be treated as a meaningful name"
    )
