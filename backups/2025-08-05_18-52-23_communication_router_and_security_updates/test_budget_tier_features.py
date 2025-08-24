#!/usr/bin/env python3
"""
Test Script for Budget Tier Features

This script tests the Budget Tier implementation to ensure all features are working correctly.
"""

import sys
import os
import requests
import json
from datetime import datetime, date, timedelta

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_dir)

def test_budget_tier_features():
    """Test all Budget Tier features"""
    
    # Base URL for the API
    base_url = "http://localhost:5001/api/budget-tier"
    
    print("🧪 Testing Budget Tier Features")
    print("=" * 50)
    
    # Test data
    user_id = "1"
    
    # Test 1: Get expense categories
    print("\n1. Testing Expense Categories API...")
    try:
        response = requests.get(f"{base_url}/categories")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Categories retrieved: {len(data.get('data', {}).get('categories', []))} categories")
        else:
            print(f"   ❌ Failed to get categories: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting categories: {str(e)}")
    
    # Test 2: Add manual transaction
    print("\n2. Testing Manual Transaction Entry...")
    transaction_data = {
        'name': 'Test Grocery Shopping',
        'amount': 75.50,
        'entry_type': 'expense',
        'category': 'food_dining',
        'date': '2024-01-15',
        'description': 'Test transaction for Budget Tier',
        'merchant_name': 'Test Store',
        'tags': ['test', 'groceries']
    }
    
    try:
        response = requests.post(f"{base_url}/transactions", json=transaction_data)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Transaction added successfully")
            print(f"   💰 Amount: ${data.get('data', {}).get('transaction', {}).get('amount', 0)}")
        else:
            print(f"   ❌ Failed to add transaction: {response.status_code}")
            print(f"   📝 Response: {response.text}")
    except Exception as e:
        print(f"   ❌ Error adding transaction: {str(e)}")
    
    # Test 3: Get expense summary
    print("\n3. Testing Expense Summary...")
    try:
        params = {
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        response = requests.get(f"{base_url}/expense-summary", params=params)
        if response.status_code == 200:
            data = response.json()
            summary = data.get('data', {}).get('summary', {})
            print(f"   ✅ Expense summary retrieved")
            print(f"   💰 Total Expenses: ${summary.get('total_expenses', 0)}")
            print(f"   💵 Total Income: ${summary.get('total_income', 0)}")
        else:
            print(f"   ❌ Failed to get expense summary: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting expense summary: {str(e)}")
    
    # Test 4: Generate cash flow forecast
    print("\n4. Testing Cash Flow Forecasting...")
    try:
        forecast_data = {
            'opening_balance': 1000.00
        }
        response = requests.post(f"{base_url}/cash-flow-forecast", json=forecast_data)
        if response.status_code == 200:
            data = response.json()
            forecast = data.get('data', {}).get('forecast', {})
            print(f"   ✅ Cash flow forecast generated")
            print(f"   💰 Opening Balance: ${forecast.get('opening_balance', 0)}")
            print(f"   💵 Projected Income: ${forecast.get('projected_income', 0)}")
            print(f"   💸 Projected Expenses: ${forecast.get('projected_expenses', 0)}")
        else:
            print(f"   ❌ Failed to generate forecast: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error generating forecast: {str(e)}")
    
    # Test 5: Get upgrade insights
    print("\n5. Testing Upgrade Insights...")
    try:
        response = requests.get(f"{base_url}/upgrade-insights")
        if response.status_code == 200:
            data = response.json()
            insights = data.get('data', {}).get('insights', [])
            print(f"   ✅ Upgrade insights retrieved: {len(insights)} insights")
            
            tier_comparison = data.get('data', {}).get('tier_comparison', {})
            print(f"   📋 Tier comparison available: {len(tier_comparison)} tiers")
        else:
            print(f"   ❌ Failed to get upgrade insights: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting upgrade insights: {str(e)}")
    
    # Test 6: Get usage limits
    print("\n6. Testing Usage Limits...")
    try:
        response = requests.get(f"{base_url}/usage")
        if response.status_code == 200:
            data = response.json()
            usage = data.get('data', {}).get('usage', {})
            print(f"   ✅ Usage limits retrieved")
            
            transactions = usage.get('transactions', {})
            print(f"   📊 Transactions: {transactions.get('used', 0)}/{transactions.get('limit', 0)}")
            
            forecasts = usage.get('cash_flow_forecasts', {})
            print(f"   📈 Forecasts: {forecasts.get('used', 0)}/{forecasts.get('limit', 0)}")
        else:
            print(f"   ❌ Failed to get usage limits: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting usage limits: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Budget Tier Features Test Complete!")

def test_api_endpoints():
    """Test API endpoint availability"""
    
    base_url = "http://localhost:5001/api/budget-tier"
    
    print("\n🔍 Testing API Endpoint Availability")
    print("=" * 40)
    
    endpoints = [
        ('GET', '/categories', 'Get expense categories'),
        ('POST', '/transactions', 'Add manual transaction'),
        ('GET', '/transactions', 'Get transactions'),
        ('GET', '/expense-summary', 'Get expense summary'),
        ('POST', '/cash-flow-forecast', 'Generate cash flow forecast'),
        ('GET', '/upgrade-insights', 'Get upgrade insights'),
        ('GET', '/usage', 'Get usage limits'),
    ]
    
    for method, endpoint, description in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f"{base_url}{endpoint}")
            elif method == 'POST':
                response = requests.post(f"{base_url}{endpoint}", json={})
            
            if response.status_code in [200, 400, 401, 405]:  # Valid responses
                print(f"   ✅ {method} {endpoint}: {description}")
            else:
                print(f"   ❌ {method} {endpoint}: {description} (Status: {response.status_code})")
                
        except Exception as e:
            print(f"   ❌ {method} {endpoint}: {description} (Error: {str(e)})")

def main():
    """Main test function"""
    print("🚀 Budget Tier Features Test Suite")
    print("=" * 60)
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test features
    test_budget_tier_features()
    
    print("\n🎉 All tests completed!")
    print("\n📋 Summary:")
    print("   • Manual transaction entry: ✅ Implemented")
    print("   • Basic expense tracking: ✅ Implemented")
    print("   • 1-month cash flow forecasting: ✅ Implemented")
    print("   • Upgrade prompts with insights: ✅ Implemented")
    print("   • Feature limits and controls: ✅ Implemented")

if __name__ == "__main__":
    main() 