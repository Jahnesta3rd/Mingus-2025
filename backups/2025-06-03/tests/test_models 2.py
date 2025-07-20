import pytest
from datetime import date
from pydantic import ValidationError
from backend.models.important_dates import (
    ImportantDateCreate,
    ImportantDateUpdate,
    DateType,
    DateStatus
)

def test_create_valid_important_date(sample_date):
    date_model = ImportantDateCreate(**sample_date)
    assert date_model.title == "Test Birthday"
    assert date_model.date_type == DateType.BIRTHDAY
    assert date_model.date == date(2024, 5, 15)
    assert date_model.amount == 100.0
    assert date_model.is_recurring is True
    assert date_model.recurrence_interval == 365

def test_create_important_date_without_optional_fields():
    minimal_date = {
        "title": "Test Date",
        "date_type": DateType.OTHER,
        "date": date(2024, 1, 1)
    }
    date_model = ImportantDateCreate(**minimal_date)
    assert date_model.title == "Test Date"
    assert date_model.amount is None
    assert date_model.description is None
    assert date_model.is_recurring is False
    assert date_model.recurrence_interval is None

def test_create_important_date_invalid_title():
    with pytest.raises(ValidationError) as exc_info:
        ImportantDateCreate(
            title="",  # Empty title
            date_type=DateType.BIRTHDAY,
            date=date(2024, 5, 15)
        )
    assert "title" in str(exc_info.value)

def test_create_important_date_invalid_amount():
    with pytest.raises(ValidationError) as exc_info:
        ImportantDateCreate(
            title="Test",
            date_type=DateType.BIRTHDAY,
            date=date(2024, 5, 15),
            amount=-100  # Negative amount
        )
    assert "amount" in str(exc_info.value)

def test_create_important_date_invalid_recurrence():
    with pytest.raises(ValidationError) as exc_info:
        ImportantDateCreate(
            title="Test",
            date_type=DateType.BIRTHDAY,
            date=date(2024, 5, 15),
            is_recurring=True,
            recurrence_interval=0  # Invalid interval
        )
    assert "recurrence_interval" in str(exc_info.value)

def test_update_important_date_partial():
    update_data = {
        "title": "Updated Title",
        "amount": 200.0
    }
    date_model = ImportantDateUpdate(**update_data)
    assert date_model.title == "Updated Title"
    assert date_model.amount == 200.0
    assert date_model.date_type is None
    assert date_model.date is None

def test_date_type_enum():
    assert DateType.BIRTHDAY.value == "birthday"
    assert DateType.ANNIVERSARY.value == "anniversary"
    assert DateType.BILL_DUE.value == "bill_due"
    assert DateType.INCOME.value == "income"
    assert DateType.OTHER.value == "other"

def test_date_status_enum():
    assert DateStatus.GREEN.value == "green"
    assert DateStatus.YELLOW.value == "yellow"
    assert DateStatus.RED.value == "red" 