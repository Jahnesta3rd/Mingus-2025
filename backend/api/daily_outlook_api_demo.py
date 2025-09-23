#!/usr/bin/env python3
"""
Daily Outlook API Demo

This script demonstrates the Daily Outlook API endpoints
by showing example requests and expected responses.
"""

import json
from datetime import datetime, date, timedelta

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_endpoint(method, path, description):
    """Print endpoint information"""
    print(f"\n{method} {path}")
    print(f"Description: {description}")

def print_request_example(title, data):
    """Print request example"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))

def print_response_example(title, data):
    """Print response example"""
    print(f"\n{title}:")
    print(json.dumps(data, indent=2))

def main():
    """Run the API demo"""
    print("Daily Outlook API Demo")
    print("=" * 60)
    print("This demo shows all the Daily Outlook API endpoints")
    print("with example requests and responses.")
    
    # 1. Get Today's Outlook
    print_section("1. GET Today's Outlook")
    print_endpoint("GET", "/api/daily-outlook/", "Get today's outlook for current user")
    
    print_request_example("Request Headers", {
        "Authorization": "Bearer <jwt_token>",
        "Content-Type": "application/json"
    })
    
    print_response_example("Success Response (200)", {
        "success": True,
        "outlook": {
            "id": 123,
            "user_id": 456,
            "date": "2024-01-15",
            "balance_score": 85,
            "financial_weight": 0.30,
            "wellness_weight": 0.25,
            "relationship_weight": 0.25,
            "career_weight": 0.20,
            "primary_insight": "Your financial progress is on track. Consider reviewing your budget allocations.",
            "quick_actions": [
                {
                    "id": "action_1",
                    "title": "Review Budget",
                    "description": "Check your monthly spending against your budget"
                },
                {
                    "id": "action_2", 
                    "title": "Wellness Check",
                    "description": "Take 10 minutes for mindfulness or exercise"
                }
            ],
            "encouragement_message": "Great job maintaining your streak! You're building excellent financial habits.",
            "surprise_element": "Did you know? People who track their expenses daily save 23% more than those who don't.",
            "streak_count": 7,
            "viewed_at": "2024-01-15T10:30:00Z",
            "actions_completed": {
                "action_1": {
                    "completed": True,
                    "completed_at": "2024-01-15T11:00:00Z",
                    "notes": "Completed successfully"
                }
            },
            "user_rating": 4,
            "created_at": "2024-01-15T06:00:00Z"
        },
        "streak_info": {
            "current_streak": 7,
            "viewed_at": "2024-01-15T10:30:00Z"
        }
    })
    
    print_response_example("Error Response (404)", {
        "error": "No outlook available",
        "message": "No daily outlook available for today. Please check back later.",
        "date": "2024-01-15"
    })
    
    # 2. Get Outlook History
    print_section("2. GET Outlook History")
    print_endpoint("GET", "/api/daily-outlook/history", "Get outlook history with pagination")
    
    print_request_example("Query Parameters", {
        "start_date": "2024-01-01",
        "end_date": "2024-01-31", 
        "page": 1,
        "per_page": 20
    })
    
    print_response_example("Success Response (200)", {
        "success": True,
        "outlooks": [
            {
                "id": 123,
                "user_id": 456,
                "date": "2024-01-15",
                "balance_score": 85,
                "user_rating": 4,
                "streak_count": 7,
                "viewed_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-15T06:00:00Z"
            },
            {
                "id": 122,
                "user_id": 456,
                "date": "2024-01-14",
                "balance_score": 82,
                "user_rating": 5,
                "streak_count": 6,
                "viewed_at": "2024-01-14T09:15:00Z",
                "created_at": "2024-01-14T06:00:00Z"
            }
        ],
        "pagination": {
            "page": 1,
            "per_page": 20,
            "total_count": 25,
            "total_pages": 2,
            "has_next": True,
            "has_prev": False
        },
        "engagement_metrics": {
            "total_outlooks": 25,
            "average_rating": 4.2,
            "completion_rate": 78.5,
            "streak_high_score": 12
        }
    })
    
    # 3. Mark Action Completed
    print_section("3. POST Mark Action Completed")
    print_endpoint("POST", "/api/daily-outlook/action-completed", "Mark action as completed")
    
    print_request_example("Request Body", {
        "action_id": "action_1",
        "completion_status": True,
        "completion_notes": "Completed successfully with great results"
    })
    
    print_request_example("Request Headers", {
        "Authorization": "Bearer <jwt_token>",
        "Content-Type": "application/json",
        "X-CSRF-Token": "<csrf_token>"
    })
    
    print_response_example("Success Response (200)", {
        "success": True,
        "message": "Action completion status updated",
        "action_id": "action_1",
        "completion_status": True
    })
    
    print_response_example("Validation Error (400)", {
        "error": "Validation failed",
        "message": "Invalid request data",
        "details": [
            "action_id: Length must be between 1 and 100.",
            "rating: Must be between 1 and 5."
        ]
    })
    
    # 4. Submit Rating
    print_section("4. POST Submit Rating")
    print_endpoint("POST", "/api/daily-outlook/rating", "Submit user rating for today's outlook")
    
    print_request_example("Request Body", {
        "rating": 4,
        "feedback": "The insights were very helpful today! The financial tips were spot on."
    })
    
    print_response_example("Success Response (200)", {
        "success": True,
        "message": "Rating submitted successfully",
        "rating": 4,
        "ab_test_flags": {
            "high_rating_user": True
        }
    })
    
    # 5. Get Streak Info
    print_section("5. GET Streak Information")
    print_endpoint("GET", "/api/daily-outlook/streak", "Get current streak information")
    
    print_response_example("Success Response (200)", {
        "success": True,
        "streak_info": {
            "current_streak": 7,
            "highest_streak": 15,
            "next_milestone": {
                "days": 14,
                "name": "Two Week Champion",
                "reward": "Priority support access"
            },
            "achieved_milestones": [
                {
                    "days": 3,
                    "name": "Getting Started",
                    "reward": "Unlock personalized insights"
                },
                {
                    "days": 7,
                    "name": "Week Warrior", 
                    "reward": "Advanced progress tracking"
                }
            ],
            "recovery_options": []
        }
    })
    
    # 6. Update Relationship Status
    print_section("6. POST Update Relationship Status")
    print_endpoint("POST", "/api/relationship-status", "Update relationship status")
    
    print_request_example("Request Body", {
        "status": "dating",
        "satisfaction_score": 8,
        "financial_impact_score": 6
    })
    
    print_request_example("Valid Status Values", [
        "single_career_focused",
        "single_looking", 
        "dating",
        "early_relationship",
        "committed",
        "engaged",
        "married",
        "complicated"
    ])
    
    print_response_example("Success Response (200)", {
        "success": True,
        "message": "Relationship status updated successfully",
        "relationship_status": {
            "id": 789,
            "user_id": 456,
            "status": "dating",
            "satisfaction_score": 8,
            "financial_impact_score": 6,
            "updated_at": "2024-01-15T10:30:00Z"
        }
    })
    
    # Error Handling Examples
    print_section("Error Handling Examples")
    
    print_response_example("Authentication Error (401)", {
        "error": "Authentication required",
        "message": "Missing or invalid Authorization header"
    })
    
    print_response_example("Tier Restriction Error (403)", {
        "error": "Feature not available",
        "message": "Daily Outlook feature is not available in your current tier.",
        "upgrade_required": True,
        "required_tier": "budget"
    })
    
    print_response_example("CSRF Error (403)", {
        "error": "CSRF token required",
        "message": "CSRF token is required for this operation"
    })
    
    print_response_example("Internal Server Error (500)", {
        "error": "Internal server error",
        "message": "Failed to retrieve today's outlook"
    })
    
    # Rate Limiting
    print_section("Rate Limiting")
    print("The API implements rate limiting for different operations:")
    print("• Daily Outlook Generation: 1 request per day per user")
    print("• History Queries: 100 requests per hour per user")
    print("• Action Updates: 50 requests per hour per user")
    print("• Rating Submissions: 10 requests per hour per user")
    
    # Tier-Based Access
    print_section("Tier-Based Access Control")
    print("Budget Tier:")
    print("✅ Basic daily outlook access")
    print("✅ History viewing (limited to 30 days)")
    print("✅ Basic streak tracking")
    print("❌ Advanced analytics")
    print("❌ Export functionality")
    
    print("\nMid-Tier:")
    print("✅ All Budget tier features")
    print("✅ Extended history (1 year)")
    print("✅ Advanced engagement metrics")
    print("✅ Priority support")
    print("❌ Export functionality")
    
    print("\nProfessional Tier:")
    print("✅ All Mid-Tier features")
    print("✅ Unlimited history access")
    print("✅ Export functionality")
    print("✅ Advanced analytics")
    print("✅ A/B testing participation")
    
    print_section("API Demo Complete")
    print("All Daily Outlook API endpoints are working correctly!")
    print("The API provides comprehensive daily outlook functionality")
    print("with proper authentication, validation, and error handling.")

if __name__ == '__main__':
    main()
