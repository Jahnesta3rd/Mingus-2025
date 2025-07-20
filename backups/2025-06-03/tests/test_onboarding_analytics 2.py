import pytest
import uuid
import os
import csv
import json
from datetime import datetime, timedelta
from backend.models.onboarding import (
    AnonymousOnboardingCreate,
    FinancialChallengeType,
    StressHandlingType,
    MotivationType
)
from backend.services.onboarding_service import OnboardingService
import time
import random
import asyncio
import tracemalloc

pytestmark = pytest.mark.asyncio

@pytest.fixture
def onboarding_service(supabase_client):
    return OnboardingService(supabase_client)

@pytest.fixture
def varied_onboarding_data():
    """Generate a variety of onboarding responses for analytics tests."""
    base = {
        'monthly_expenses': 3000.0,
        'savings_goal': 20000.0,
        'risk_tolerance': 7,
        'financial_knowledge': 6,
        'preferred_contact_method': 'email',
        'contact_info': 'test@example.com',
        'ip_address': '127.0.0.1',
        'user_agent': 'TestAgent',
        'referrer': 'https://test.com'
    }
    return [
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'debt_management',
            'stress_handling': ['budgeting', 'automation'],
            'motivation': ['financial_freedom'],
            'monthly_income': 5000.0
        },
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'emergency_savings',
            'stress_handling': ['education'],
            'motivation': ['wealth_building'],
            'monthly_income': 7000.0
        },
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'debt_management',
            'stress_handling': ['budgeting'],
            'motivation': ['debt_free'],
            'monthly_income': 6000.0
        },
    ]

@pytest.fixture
def diverse_onboarding_data():
    """Generate onboarding responses for different user segments and locations."""
    now = datetime.now()
    base = {
        'monthly_expenses': 3000.0,
        'savings_goal': 20000.0,
        'risk_tolerance': 7,
        'financial_knowledge': 6,
        'preferred_contact_method': 'email',
        'contact_info': 'test@example.com',
        'user_agent': 'TestAgent',
        'referrer': 'https://test.com'
    }
    return [
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'debt_management',
            'stress_handling': ['budgeting'],
            'motivation': ['financial_freedom'],
            'monthly_income': 5000.0,
            'ip_address': '192.168.1.1',
            'created_at': (now - timedelta(days=1)).isoformat()
        },
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'emergency_savings',
            'stress_handling': ['automation'],
            'motivation': ['wealth_building'],
            'monthly_income': 7000.0,
            'ip_address': '10.0.0.2',
            'created_at': (now - timedelta(days=2)).isoformat()
        },
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'retirement_planning',
            'stress_handling': ['education'],
            'motivation': ['retirement'],
            'monthly_income': 8000.0,
            'ip_address': '172.16.0.3',
            'created_at': (now - timedelta(weeks=1)).isoformat()
        },
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'debt_management',
            'stress_handling': ['tracking'],
            'motivation': ['debt_free'],
            'monthly_income': 6000.0,
            'ip_address': '192.168.1.1',
            'created_at': (now - timedelta(days=1)).isoformat()
        },
        {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': 'budgeting',
            'stress_handling': ['budgeting'],
            'motivation': ['security'],
            'monthly_income': 4000.0,
            'ip_address': '8.8.8.8',
            'created_at': now.isoformat()
        },
    ]

@pytest.fixture(autouse=True)
def clear_supabase_data(supabase_client):
    supabase_client.clear_data()

async def create_varied_responses(service, varied_data):
    for entry in varied_data:
        onboarding = AnonymousOnboardingCreate(**entry)
        await service.create_anonymous_onboarding(onboarding)

async def create_diverse_responses(service, diverse_data):
    for entry in diverse_data:
        onboarding = AnonymousOnboardingCreate(**entry)
        # Patch created_at in the mock after insert
        await service.create_anonymous_onboarding(onboarding)
        table = service.db.table(service.anonymous_table)
        for row in table.data:
            if row['session_id'] == entry['session_id']:
                row['created_at'] = entry['created_at']

async def test_count_responses_by_option(onboarding_service, varied_onboarding_data):
    await create_varied_responses(onboarding_service, varied_onboarding_data)
    counts = await onboarding_service.count_responses_by_option('financial_challenge', table='anonymous_onboarding_responses')
    assert counts['debt_management'] == 2
    assert counts['emergency_savings'] == 1

async def test_aggregation_queries(onboarding_service, varied_onboarding_data):
    await create_varied_responses(onboarding_service, varied_onboarding_data)
    # Financial challenges
    challenge_counts = await onboarding_service.count_responses_by_option('financial_challenge', table='anonymous_onboarding_responses')
    assert sum(challenge_counts.values()) == 3
    # Stress handling
    stress_counts = await onboarding_service.count_responses_by_option('stress_handling', table='anonymous_onboarding_responses')
    assert stress_counts['budgeting'] >= 2
    # Motivations
    motivation_counts = await onboarding_service.count_responses_by_option('motivation', table='anonymous_onboarding_responses')
    assert motivation_counts['financial_freedom'] == 1

async def test_timestamp_tracking(onboarding_service, varied_onboarding_data):
    # Simulate onboarding and conversion with timestamps
    now = datetime.now()
    for i, entry in enumerate(varied_onboarding_data):
        onboarding = AnonymousOnboardingCreate(**entry)
        await onboarding_service.create_anonymous_onboarding(onboarding)
        # Simulate conversion
        session_id = entry['session_id']
        user_id = f'user-{i}'
        # Patch the mock table for timestamps
        table = onboarding_service.db.table(onboarding_service.anonymous_table)
        for row in table.data:
            if row['session_id'] == session_id:
                row['converted_to_user_id'] = user_id
                row['created_at'] = (now - timedelta(minutes=10*(i+1))).isoformat()
                row['converted_at'] = (now - timedelta(minutes=5*(i+1))).isoformat()
    stats = await onboarding_service.time_to_signup_stats(table='anonymous_onboarding_responses')
    assert stats['average'] > 0
    assert stats['min'] >= 0
    assert stats['max'] >= stats['min']

async def test_dashboard_aggregates(onboarding_service, varied_onboarding_data):
    await create_varied_responses(onboarding_service, varied_onboarding_data)
    dashboard = await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    assert 'top_challenges' in dashboard
    assert 'conversion_by_motivation' in dashboard
    assert 'geo_distribution' in dashboard
    assert isinstance(dashboard['top_challenges'], dict)

async def test_large_dataset_aggregation(onboarding_service, varied_onboarding_data):
    # Create a larger dataset
    large_data = []
    for i in range(50):
        entry = varied_onboarding_data[i % len(varied_onboarding_data)].copy()
        entry['session_id'] = str(uuid.uuid4())
        entry['monthly_income'] += i * 100
        large_data.append(entry)
    await create_varied_responses(onboarding_service, large_data)
    counts = await onboarding_service.count_responses_by_option('financial_challenge', table='anonymous_onboarding_responses')
    assert sum(counts.values()) == 50
    dashboard = await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    assert dashboard['top_challenges']
    assert dashboard['geo_distribution']

async def test_dashboard_challenge_aggregation(onboarding_service, diverse_onboarding_data):
    await create_diverse_responses(onboarding_service, diverse_onboarding_data)
    dashboard = await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    assert 'top_challenges' in dashboard
    assert dashboard['top_challenges']['debt_management'] >= 2
    assert dashboard['top_challenges']['budgeting'] == 1

async def test_dashboard_geo_distribution(onboarding_service, diverse_onboarding_data):
    await create_diverse_responses(onboarding_service, diverse_onboarding_data)
    dashboard = await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    geo = dashboard['geo_distribution']
    assert geo['192.168.1.1'] == 2
    assert geo['10.0.0.2'] == 1
    assert geo['8.8.8.8'] == 1

async def test_time_based_analytics(onboarding_service, diverse_onboarding_data):
    await create_diverse_responses(onboarding_service, diverse_onboarding_data)
    # Aggregate by day
    table = onboarding_service.db.table(onboarding_service.anonymous_table)
    by_day = {}
    for row in table.data:
        day = row['created_at'][:10]
        by_day[day] = by_day.get(day, 0) + 1
    assert any(v >= 1 for v in by_day.values())
    # Aggregate by week
    by_week = {}
    for row in table.data:
        dt = datetime.fromisoformat(row['created_at'])
        week = dt.strftime('%Y-%U')
        by_week[week] = by_week.get(week, 0) + 1
    assert any(v >= 1 for v in by_week.values())
    # Aggregate by month
    by_month = {}
    for row in table.data:
        month = row['created_at'][:7]
        by_month[month] = by_month.get(month, 0) + 1
    assert any(v >= 1 for v in by_month.values())

async def test_export_functions(onboarding_service, diverse_onboarding_data):
    await create_diverse_responses(onboarding_service, diverse_onboarding_data)
    # Test CSV export
    csv_path = await onboarding_service.export_onboarding_data(format='csv', table='anonymous_onboarding_responses')
    assert os.path.exists(csv_path)
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == len(diverse_onboarding_data)
    os.remove(csv_path)
    # Test JSON export
    json_path = await onboarding_service.export_onboarding_data(format='json', table='anonymous_onboarding_responses')
    assert os.path.exists(json_path)
    with open(json_path, 'r') as f:
        data = json.load(f)
        assert len(data) == len(diverse_onboarding_data)
    os.remove(json_path)

@pytest.fixture
def large_onboarding_data():
    """Generate 1000+ onboarding responses with random data."""
    now = datetime.now()
    base = {
        'monthly_expenses': 3000.0,
        'savings_goal': 20000.0,
        'risk_tolerance': 7,
        'financial_knowledge': 6,
        'preferred_contact_method': 'email',
        'contact_info': 'test@example.com',
        'user_agent': 'TestAgent',
        'referrer': 'https://test.com'
    }
    challenges = ['debt_management', 'emergency_savings', 'retirement_planning', 'budgeting', 'investing']
    motivations = ['financial_freedom', 'wealth_building', 'retirement', 'debt_free', 'security']
    stress_handlings = [['budgeting'], ['automation'], ['education'], ['tracking'], ['mindfulness']]
    ip_addresses = ['192.168.1.1', '10.0.0.2', '172.16.0.3', '8.8.8.8', '127.0.0.1']
    data = []
    for i in range(1100):
        entry = {
            **base,
            'session_id': str(uuid.uuid4()),
            'financial_challenge': random.choice(challenges),
            'stress_handling': random.choice(stress_handlings),
            'motivation': [random.choice(motivations)],
            'monthly_income': random.randint(3000, 10000),
            'ip_address': random.choice(ip_addresses),
            'created_at': (now - timedelta(days=random.randint(0, 30))).isoformat()
        }
        data.append(entry)
    return data

async def create_large_responses(service, large_data):
    for entry in large_data:
        onboarding = AnonymousOnboardingCreate(**entry)
        await service.create_anonymous_onboarding(onboarding)
        table = service.db.table(service.anonymous_table)
        for row in table.data:
            if row['session_id'] == entry['session_id']:
                row['created_at'] = entry['created_at']

@pytest.mark.asyncio
async def test_dashboard_performance(onboarding_service, large_onboarding_data):
    await create_large_responses(onboarding_service, large_onboarding_data)
    start = time.time()
    dashboard = await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    elapsed = time.time() - start
    assert elapsed < 1.5, f"Dashboard aggregation took too long: {elapsed:.2f}s"
    assert 'top_challenges' in dashboard
    assert sum(dashboard['top_challenges'].values()) == 1100

@pytest.mark.asyncio
async def test_complex_aggregation_performance(onboarding_service, large_onboarding_data):
    await create_large_responses(onboarding_service, large_onboarding_data)
    start = time.time()
    result = await onboarding_service.conversion_rates_by_combination(table='anonymous_onboarding_responses')
    elapsed = time.time() - start
    assert elapsed < 2.0, f"Complex aggregation took too long: {elapsed:.2f}s"
    assert isinstance(result, dict)

@pytest.mark.asyncio
async def test_concurrent_analytics_queries(onboarding_service, large_onboarding_data):
    await create_large_responses(onboarding_service, large_onboarding_data)
    async def run_dashboard():
        return await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    async def run_conversion():
        return await onboarding_service.conversion_rates_by_combination(table='anonymous_onboarding_responses')
    start = time.time()
    results = await asyncio.gather(run_dashboard(), run_conversion(), run_dashboard(), run_conversion())
    elapsed = time.time() - start
    assert elapsed < 3.0, f"Concurrent analytics queries took too long: {elapsed:.2f}s"
    for r in results:
        assert isinstance(r, dict)

@pytest.mark.asyncio
async def test_memory_usage_during_large_analytics(onboarding_service, large_onboarding_data):
    await create_large_responses(onboarding_service, large_onboarding_data)
    tracemalloc.start()
    await onboarding_service.dashboard_aggregates(table='anonymous_onboarding_responses')
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    # Allow up to 100MB for analytics in test
    assert peak < 100 * 1024 * 1024, f"Memory usage too high: {peak / (1024*1024):.2f}MB" 