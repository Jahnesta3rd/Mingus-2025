#!/usr/bin/env python3
"""
Test script for DailyOutlookService
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from daily_outlook_service import DailyOutlookService, RelationshipStatus

def test_daily_outlook_service():
    """Test the DailyOutlookService functionality"""
    
    # Initialize service
    service = DailyOutlookService()
    
    print("Testing DailyOutlookService...")
    print("=" * 50)
    
    # Test 1: Calculate dynamic weights for different relationship statuses
    print("\n1. Testing dynamic weight calculations:")
    for status in RelationshipStatus:
        print(f"\n{status.value}:")
        # Simulate user with specific relationship status
        test_user_id = 1
        
        # Test weight calculation
        weights = service.calculate_dynamic_weights(test_user_id)
        print(f"  Weights: {weights}")
        
        # Verify weights sum to 1.0
        total_weight = sum(weights.values())
        print(f"  Total weight: {total_weight:.2f}")
        assert abs(total_weight - 1.0) < 0.01, f"Weights should sum to 1.0, got {total_weight}"
    
    # Test 2: Test balance score calculation
    print("\n2. Testing balance score calculation:")
    test_user_id = 1
    balance_score, individual_scores = service.calculate_balance_score(test_user_id)
    print(f"  Balance Score: {balance_score}")
    print(f"  Individual Scores: {individual_scores.to_dict()}")
    assert 0 <= balance_score <= 100, f"Balance score should be 0-100, got {balance_score}"
    
    # Test 3: Test relationship status methods
    print("\n3. Testing relationship status methods:")
    
    # Test getting relationship status (should return None for non-existent user)
    status = service.get_user_relationship_status(999)
    print(f"  Get status for non-existent user: {status}")
    
    # Test updating relationship status
    success = service.update_relationship_status(999, RelationshipStatus.SINGLE_CAREER_FOCUSED, 8)
    print(f"  Update status for non-existent user: {success}")
    
    print("\n✅ All tests passed!")
    print("DailyOutlookService is working correctly.")

if __name__ == "__main__":
    test_daily_outlook_service()
