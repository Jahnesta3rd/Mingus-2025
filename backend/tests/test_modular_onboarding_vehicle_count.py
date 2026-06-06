"""Tests for _validate_and_cast vehicle_count (GC2 modular onboarding commit)."""

from __future__ import annotations

from backend.routes._modular_onboarding_gc2_commit import _validate_and_cast

_FIELD = "vehicle_count"


def _assert_validation_error(err, scenario: str) -> dict:
    assert err is not None, f"{scenario}: expected error tuple, got None"
    assert isinstance(err, tuple) and len(err) == 2, (
        f"{scenario}: expected (dict, int) error tuple, got {err!r}"
    )
    body, status = err
    assert isinstance(body, dict), f"{scenario}: error body should be dict, got {type(body)}"
    assert body["error"] == "validation_failed", (
        f"{scenario}: expected error validation_failed, got {body.get('error')!r}"
    )
    assert "reason" in body, f"{scenario}: error dict missing 'reason' key: {body!r}"
    assert body["reason"] in ("type_mismatch", "out_of_range"), (
        f"{scenario}: expected reason type_mismatch or out_of_range, got {body['reason']!r}"
    )
    assert status == 400, f"{scenario}: expected HTTP status 400, got {status}"
    return body


# --- Positive: (value, None) ---


def test_vehicle_count_scenario_1_int_zero():
    val, err = _validate_and_cast(_FIELD, 0)
    assert err is None, f"expected success for value=0, got err={err!r}"
    assert val == 0, f"expected coerced value 0, got {val!r}"


def test_vehicle_count_scenario_2_int_two():
    val, err = _validate_and_cast(_FIELD, 2)
    assert err is None, f"expected success for value=2, got err={err!r}"
    assert val == 2, f"expected coerced value 2, got {val!r}"


def test_vehicle_count_scenario_3_int_upper_bound_five():
    val, err = _validate_and_cast(_FIELD, 5)
    assert err is None, f"expected success for value=5 (upper bound), got err={err!r}"
    assert val == 5, f"expected coerced value 5, got {val!r}"


def test_vehicle_count_scenario_4_float_integer_valued_coerced():
    val, err = _validate_and_cast(_FIELD, 2.0)
    assert err is None, f"expected success for value=2.0, got err={err!r}"
    assert val == 2, f"expected float 2.0 coerced to int 2, got {val!r}"


def test_vehicle_count_scenario_5_numeric_string_coerced():
    val, err = _validate_and_cast(_FIELD, "2")
    assert err is None, f"expected success for value='2', got err={err!r}"
    assert val == 2, f"expected string '2' coerced to int 2, got {val!r}"


def test_vehicle_count_scenario_6_string_with_whitespace_coerced():
    val, err = _validate_and_cast(_FIELD, "  3  ")
    assert err is None, f"expected success for value='  3  ', got err={err!r}"
    assert val == 3, f"expected stripped string coerced to int 3, got {val!r}"


def test_vehicle_count_scenario_7_zero_float_coerced():
    val, err = _validate_and_cast(_FIELD, 0.0)
    assert err is None, f"expected success for value=0.0, got err={err!r}"
    assert val == 0, f"expected 0.0 coerced to int 0, got {val!r}"


# --- Negative: (None, error) ---


def test_vehicle_count_scenario_8_none_rejected():
    val, err = _validate_and_cast(_FIELD, None)
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_8_none")


def test_vehicle_count_scenario_9_empty_string_rejected():
    val, err = _validate_and_cast(_FIELD, "")
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_9_empty_string")


def test_vehicle_count_scenario_10_true_rejected():
    val, err = _validate_and_cast(_FIELD, True)
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_10_true")


def test_vehicle_count_scenario_11_false_rejected():
    val, err = _validate_and_cast(_FIELD, False)
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_11_false")


def test_vehicle_count_scenario_12_non_integer_float_rejected():
    val, err = _validate_and_cast(_FIELD, 2.5)
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_12_non_integer_float")


def test_vehicle_count_scenario_13_non_numeric_string_rejected():
    val, err = _validate_and_cast(_FIELD, "abc")
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_13_non_numeric_string")


def test_vehicle_count_scenario_14_below_range_rejected():
    val, err = _validate_and_cast(_FIELD, -1)
    assert val is None, f"expected value None on failure, got {val!r}"
    body = _assert_validation_error(err, "scenario_14_below_range")
    assert body["reason"] == "out_of_range", (
        "scenario_14: expected out_of_range for -1, "
        f"got {body.get('reason')!r}"
    )


def test_vehicle_count_scenario_15_above_range_rejected():
    val, err = _validate_and_cast(_FIELD, 6)
    assert val is None, f"expected value None on failure, got {val!r}"
    body = _assert_validation_error(err, "scenario_15_above_range")
    assert body["reason"] == "out_of_range", (
        "scenario_15: expected out_of_range for 6, "
        f"got {body.get('reason')!r}"
    )


def test_vehicle_count_scenario_16_list_rejected():
    val, err = _validate_and_cast(_FIELD, [])
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_16_list")


def test_vehicle_count_scenario_17_dict_rejected():
    val, err = _validate_and_cast(_FIELD, {})
    assert val is None, f"expected value None on failure, got {val!r}"
    _assert_validation_error(err, "scenario_17_dict")
