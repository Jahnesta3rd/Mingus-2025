#!/usr/bin/env python3
"""
Daily Outlook API Test Examples

This file demonstrates how to use the Daily Outlook API endpoints
with proper authentication and error handling.
"""

import requests
import json
from datetime import datetime, date

class DailyOutlookAPIClient:
    """Client for testing Daily Outlook API endpoints"""
    
    def __init__(self, base_url: str, auth_token: str, csrf_token: str = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.csrf_token = csrf_token
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        if csrf_token:
            self.headers['X-CSRF-Token'] = csrf_token
    
    def get_todays_outlook(self):
        """Get today's daily outlook"""
        try:
            response = requests.get(
                f'{self.base_url}/api/daily-outlook/',
                headers=self.headers
            )
            return self._handle_response(response)
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def get_outlook_history(self, start_date=None, end_date=None, page=1, per_page=20):
        """Get outlook history with optional filtering"""
        try:
            params = {'page': page, 'per_page': per_page}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            response = requests.get(
                f'{self.base_url}/api/daily-outlook/history',
                headers=self.headers,
                params=params
            )
            return self._handle_response(response)
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def mark_action_completed(self, action_id: str, completion_status: bool, notes: str = None):
        """Mark an action as completed"""
        try:
            data = {
                'action_id': action_id,
                'completion_status': completion_status
            }
            if notes:
                data['completion_notes'] = notes
            
            response = requests.post(
                f'{self.base_url}/api/daily-outlook/action-completed',
                headers=self.headers,
                json=data
            )
            return self._handle_response(response)
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def submit_rating(self, rating: int, feedback: str = None):
        """Submit user rating for today's outlook"""
        try:
            data = {'rating': rating}
            if feedback:
                data['feedback'] = feedback
            
            response = requests.post(
                f'{self.base_url}/api/daily-outlook/rating',
                headers=self.headers,
                json=data
            )
            return self._handle_response(response)
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def get_streak_info(self):
        """Get current streak information"""
        try:
            response = requests.get(
                f'{self.base_url}/api/daily-outlook/streak',
                headers=self.headers
            )
            return self._handle_response(response)
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def update_relationship_status(self, status: str, satisfaction_score: int, financial_impact_score: int):
        """Update relationship status"""
        try:
            data = {
                'status': status,
                'satisfaction_score': satisfaction_score,
                'financial_impact_score': financial_impact_score
            }
            
            response = requests.post(
                f'{self.base_url}/api/relationship-status',
                headers=self.headers,
                json=data
            )
            return self._handle_response(response)
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def _handle_response(self, response):
        """Handle API response and return formatted result"""
        try:
            data = response.json()
            return {
                'status_code': response.status_code,
                'success': response.status_code < 400,
                'data': data
            }
        except json.JSONDecodeError:
            return {
                'status_code': response.status_code,
                'success': False,
                'data': {'error': 'Invalid JSON response', 'text': response.text}
            }

def run_api_tests():
    """Run example API tests"""
    
    # Configuration - replace with actual values
    BASE_URL = 'http://localhost:5000'
    AUTH_TOKEN = 'your-jwt-token-here'
    CSRF_TOKEN = 'your-csrf-token-here'
    
    # Initialize client
    client = DailyOutlookAPIClient(BASE_URL, AUTH_TOKEN, CSRF_TOKEN)
    
    print("=== Daily Outlook API Test Examples ===\n")
    
    # Test 1: Get today's outlook
    print("1. Getting today's outlook...")
    result = client.get_todays_outlook()
    print(f"Status: {result['status_code']}")
    print(f"Success: {result['success']}")
    if result['success']:
        outlook = result['data']['outlook']
        print(f"Balance Score: {outlook['balance_score']}")
        print(f"Streak Count: {outlook['streak_count']}")
        print(f"Primary Insight: {outlook['primary_insight'][:50]}...")
    else:
        print(f"Error: {result['data']}")
    print()
    
    # Test 2: Get outlook history
    print("2. Getting outlook history...")
    result = client.get_outlook_history(page=1, per_page=5)
    print(f"Status: {result['status_code']}")
    print(f"Success: {result['success']}")
    if result['success']:
        outlooks = result['data']['outlooks']
        print(f"Found {len(outlooks)} outlooks")
        if outlooks:
            print(f"Most recent date: {outlooks[0]['date']}")
            print(f"Average rating: {result['data']['engagement_metrics']['average_rating']}")
    else:
        print(f"Error: {result['data']}")
    print()
    
    # Test 3: Mark action completed
    print("3. Marking action as completed...")
    result = client.mark_action_completed(
        action_id='test_action_1',
        completion_status=True,
        notes='Test completion'
    )
    print(f"Status: {result['status_code']}")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Message: {result['data']['message']}")
    else:
        print(f"Error: {result['data']}")
    print()
    
    # Test 4: Submit rating
    print("4. Submitting rating...")
    result = client.submit_rating(
        rating=4,
        feedback='Great insights today!'
    )
    print(f"Status: {result['status_code']}")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Message: {result['data']['message']}")
        if 'ab_test_flags' in result['data']:
            print(f"AB Test Flags: {result['data']['ab_test_flags']}")
    else:
        print(f"Error: {result['data']}")
    print()
    
    # Test 5: Get streak info
    print("5. Getting streak information...")
    result = client.get_streak_info()
    print(f"Status: {result['status_code']}")
    print(f"Success: {result['success']}")
    if result['success']:
        streak_info = result['data']['streak_info']
        print(f"Current Streak: {streak_info['current_streak']}")
        print(f"Highest Streak: {streak_info['highest_streak']}")
        if streak_info['next_milestone']:
            print(f"Next Milestone: {streak_info['next_milestone']['name']} ({streak_info['next_milestone']['days']} days)")
    else:
        print(f"Error: {result['data']}")
    print()
    
    # Test 6: Update relationship status
    print("6. Updating relationship status...")
    result = client.update_relationship_status(
        status='dating',
        satisfaction_score=8,
        financial_impact_score=6
    )
    print(f"Status: {result['status_code']}")
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Message: {result['data']['message']}")
        if 'relationship_status' in result['data']:
            status = result['data']['relationship_status']
            print(f"Status: {status['status']}")
            print(f"Satisfaction: {status['satisfaction_score']}/10")
    else:
        print(f"Error: {result['data']}")
    print()
    
    print("=== Test Examples Complete ===")

if __name__ == '__main__':
    # Example usage
    run_api_tests()
    
    # Example of using the client in your application
    print("\n=== Example Integration ===")
    print("""
    # Initialize client in your application
    client = DailyOutlookAPIClient(
        base_url='https://your-api-domain.com',
        auth_token=user_jwt_token,
        csrf_token=csrf_token
    )
    
    # Get today's outlook
    outlook_result = client.get_todays_outlook()
    if outlook_result['success']:
        outlook = outlook_result['data']['outlook']
        # Process outlook data...
    
    # Submit user feedback
    rating_result = client.submit_rating(rating=5, feedback='Excellent!')
    if rating_result['success']:
        # Handle successful rating submission...
    """)
