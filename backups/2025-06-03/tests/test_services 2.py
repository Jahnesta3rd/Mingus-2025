import pytest
from datetime import date, timedelta
from backend.models.important_dates import ImportantDateCreate, ImportantDateUpdate

pytestmark = pytest.mark.asyncio

async def test_create_important_date(service, sample_date):
    date_data = ImportantDateCreate(**sample_date)
    result = await service.create_date("test-user", date_data)
    assert result.title == sample_date["title"]

async def test_create_duplicate_date(service, sample_date):
    date_data = ImportantDateCreate(**sample_date)
    await service.create_date("test-user", date_data)
    with pytest.raises(ValueError):
        await service.create_date("test-user", date_data)

async def test_get_dates_pagination(service, sample_date):
    # Create multiple dates
    date_data = ImportantDateCreate(**sample_date)
    for i in range(15):
        modified_date = {**sample_date}
        modified_date["title"] = f"Test {i}"
        modified_date["date"] = date(2024, 1, 1) + timedelta(days=i)
        await service.create_date("test-user", ImportantDateCreate(**modified_date))

    # Test first page
    result = await service.get_dates("test-user", page=1, size=10)
    assert len(result) == 10

    # Test second page
    result = await service.get_dates("test-user", page=2, size=10)
    assert len(result) == 5

async def test_update_important_date(service, sample_date):
    # Create initial date
    date_data = ImportantDateCreate(**sample_date)
    created = await service.create_date("test-user", date_data)

    # Update the date
    update_data = ImportantDateUpdate(
        title="Updated Birthday",
        amount=200.0
    )
    updated = await service.update_date("test-user", created.id, update_data)
    assert updated.title == "Updated Birthday"
    assert updated.amount == 200.0

async def test_delete_important_date(service, sample_date):
    # Create a date
    date_data = ImportantDateCreate(**sample_date)
    created = await service.create_date("test-user", date_data)

    # Delete the date
    await service.delete_date("test-user", created.id)

    # Verify it's deleted
    result = await service.get_dates("test-user")
    assert len(result) == 0

async def test_get_upcoming_dates(service, sample_date):
    # Create dates with different future dates
    today = date.today()

    # Past date
    past_date = {**sample_date, "date": today - timedelta(days=10)}
    await service.create_date("test-user", ImportantDateCreate(**past_date))

    # Future dates
    future_dates = [
        {**sample_date, "date": today + timedelta(days=i*10)}
        for i in range(1, 4)
    ]
    for date_data in future_dates:
        await service.create_date("test-user", ImportantDateCreate(**date_data))

    # Get upcoming dates
    result = await service.get_upcoming_dates("test-user", days=30)
    assert len(result) == 3

async def test_analyze_cash_impact(service, sample_date):
    # Create multiple dates with different amounts
    dates = [
        {**sample_date, "date": date(2024, 1, 1), "amount": 100.0},
        {**sample_date, "date": date(2024, 1, 15), "amount": 200.0},
        {**sample_date, "date": date(2024, 2, 1), "amount": 300.0}
    ]

    for date_data in dates:
        await service.create_date("test-user", ImportantDateCreate(**date_data))

    result = await service.analyze_cash_impact("test-user", balance=500.0)
    assert len(result) == 3
    assert result[0].amount == 100.0
    assert result[1].amount == 200.0
    assert result[2].amount == 300.0 