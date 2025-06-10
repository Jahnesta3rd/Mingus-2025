import pytest
from backend.models.important_dates import DateType

pytestmark = pytest.mark.asyncio

async def test_list_dates_unauthorized(client):
    response = await client.get('/api/user_important_dates')
    assert response.status_code == 401

async def test_list_dates(client, auth_headers, sample_date):
    # Create some test dates
    for i in range(3):
        data = {**sample_date}
        data["title"] = f"Test {i}"
        response = await client.post(
            '/api/user_important_dates',
            headers=auth_headers,
            json=data
        )
        assert response.status_code == 201

    # Test listing all dates
    response = await client.get(
        '/api/user_important_dates',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3

async def test_create_date(client, auth_headers, sample_date):
    response = await client.post(
        '/api/user_important_dates',
        headers=auth_headers,
        json=sample_date
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["title"] == sample_date["title"]
    assert data["date_type"] == sample_date["date_type"]

async def test_create_invalid_date(client, auth_headers):
    invalid_date = {
        "title": "",  # Invalid empty title
        "date_type": DateType.BIRTHDAY,
        "date": "2024-05-15"
    }
    response = await client.post(
        '/api/user_important_dates',
        headers=auth_headers,
        json=invalid_date
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data

async def test_update_date(client, auth_headers, sample_date):
    # First create a date
    create_response = await client.post(
        '/api/user_important_dates',
        headers=auth_headers,
        json=sample_date
    )
    date_id = create_response.get_json()["id"]

    # Update the date
    update_data = {
        "title": "Updated Test",
        "amount": 200.0
    }
    response = await client.put(
        f'/api/user_important_dates/{date_id}',
        headers=auth_headers,
        json=update_data
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["title"] == "Updated Test"
    assert data["amount"] == 200.0

async def test_delete_date(client, auth_headers, sample_date):
    # First create a date
    create_response = await client.post(
        '/api/user_important_dates',
        headers=auth_headers,
        json=sample_date
    )
    date_id = create_response.get_json()["id"]

    # Delete the date
    response = await client.delete(
        f'/api/user_important_dates/{date_id}',
        headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's deleted
    response = await client.get(
        f'/api/user_important_dates/{date_id}',
        headers=auth_headers
    )
    assert response.status_code == 404

async def test_get_upcoming_dates(client, auth_headers, sample_date):
    # Create dates with different dates (using future dates)
    dates = [
        {**sample_date, "title": "Future Date 1", "date": "2025-07-01"},
        {**sample_date, "title": "Future Date 2", "date": "2025-08-01"},
        {**sample_date, "title": "Future Date 3", "date": "2025-09-01"}
    ]

    for date_data in dates:
        response = await client.post(
            '/api/user_important_dates',
            headers=auth_headers,
            json=date_data
        )
        assert response.status_code == 201

    # Get upcoming dates
    response = await client.get(
        '/api/user_important_dates/upcoming',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3

async def test_analyze_cash_impact(client, auth_headers, sample_date):
    # Create dates with different amounts
    dates = [
        {**sample_date, "date": "2024-01-01", "amount": 100.0},
        {**sample_date, "date": "2024-01-15", "amount": 200.0},
        {**sample_date, "date": "2024-02-01", "amount": 300.0}
    ]

    for date_data in dates:
        await client.post(
            '/api/user_important_dates',
            headers=auth_headers,
            json=date_data
        )

    response = await client.get(
        '/api/user_important_dates/cash-impact?balance=500.0',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 3

async def test_get_date_types(client, auth_headers):
    response = await client.get(
        '/api/date-types',
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "date_types" in data
    assert len(data["date_types"]) > 0 