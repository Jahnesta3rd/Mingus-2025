#!/usr/bin/env python3
"""
MINGUS User Journey Test Runner
==============================

This script provides a flexible way to run user journey tests, either complete
or individual steps for debugging and development purposes.

Usage:
    python run_user_journey_tests.py --step all                    # Run all steps
    python run_user_journey_tests.py --step 1                     # Run only step 1
    python run_user_journey_tests.py --step 1,2,3                 # Run steps 1, 2, and 3
    python run_user_journey_tests.py --url http://localhost:5001  # Custom URL
"""

import sys
import argparse
import json
from datetime import datetime
from user_journey_simulation import MingusUserJourneySimulator

def run_specific_steps(simulator, step_numbers):
    """Run specific steps of the user journey"""
    steps = {
        1: ("Step 1: App Discovery", simulator.step_1_discover_app),
        2: ("Step 2: Budget Tier Signup", simulator.step_2_signup_budget_tier),
        3: ("Step 3: Profile Setup", simulator.step_3_profile_setup),
        4: ("Step 4: Weekly Check-in", simulator.step_4_weekly_checkin),
        5: ("Step 5: Financial Forecast", simulator.step_5_financial_forecast),
        6: ("Step 6: Mid-Tier Upgrade", simulator.step_6_upgrade_mid_tier),
        7: ("Step 7: Career Recommendations", simulator.step_7_career_recommendations),
        8: ("Step 8: Monthly Report", simulator.step_8_monthly_report)
    }
    
    results = {}
    all_passed = True
    
    for step_num in step_numbers:
        if step_num not in steps:
            print(f"Error: Step {step_num} does not exist. Available steps: 1-8")
            return False
        
        step_name, step_func = steps[step_num]
        print(f"\n{'='*60}")
        print(f"RUNNING {step_name}")
        print(f"{'='*60}")
        
        try:
            success = step_func()
            results[step_name] = "PASS" if success else "FAIL"
            if not success:
                all_passed = False
        except Exception as e:
            print(f"Error in {step_name}: {str(e)}")
            results[step_name] = "ERROR"
            all_passed = False
    
    # Print results
    print(f"\n{'='*60}")
    print("TEST RESULTS")
    print(f"{'='*60}")
    for step_name, result in results.items():
        print(f"{step_name}: {result}")
    
    print(f"\nOverall Status: {'PASS' if all_passed else 'FAIL'}")
    return all_passed

def main():
    parser = argparse.ArgumentParser(description="MINGUS User Journey Test Runner")
    parser.add_argument("--step", default="all", help="Step(s) to run: all, 1-8, or comma-separated list (e.g., 1,2,3)")
    parser.add_argument("--url", default="http://localhost:5001", help="Base URL of the MINGUS application")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize simulator
    simulator = MingusUserJourneySimulator(args.url)
    
    # Parse step argument
    if args.step.lower() == "all":
        step_numbers = list(range(1, 9))
    else:
        try:
            step_numbers = [int(s.strip()) for s in args.step.split(",")]
        except ValueError:
            print("Error: Invalid step format. Use 'all' or comma-separated numbers (e.g., 1,2,3)")
            return 1
    
    # Validate step numbers
    for step_num in step_numbers:
        if step_num < 1 or step_num > 8:
            print(f"Error: Step {step_num} is out of range. Available steps: 1-8")
            return 1
    
    print(f"MINGUS User Journey Test Runner")
    print(f"URL: {args.url}")
    print(f"Steps to run: {step_numbers}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test health check first
    if not simulator.test_health_check():
        print("Error: Application health check failed. Please ensure the application is running.")
        return 1
    
    # Run tests
    if len(step_numbers) == 8:
        # Run complete journey
        results = simulator.run_complete_journey()
        success = results["status"] == "PASS"
    else:
        # Run specific steps
        success = run_specific_steps(simulator, step_numbers)
        results = {
            "status": "PASS" if success else "FAIL",
            "timestamp": datetime.now().isoformat(),
            "base_url": args.url,
            "steps_run": step_numbers,
            "detailed_results": simulator.test_results
        }
    
    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")
    
    # Exit with appropriate code
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
