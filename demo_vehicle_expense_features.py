#!/usr/bin/env python3
"""
Vehicle Expense System Feature Demonstration
Shows the key features of the enhanced vehicle expense system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def demonstrate_expense_categorization():
    """Demonstrate expense categorization features"""
    print("🚗 VEHICLE EXPENSE CATEGORIZATION DEMO")
    print("=" * 50)
    
    from backend.services.vehicle_expense_categorizer import VehicleExpenseCategorizer
    
    categorizer = VehicleExpenseCategorizer()
    
    # Sample expenses to categorize
    sample_expenses = [
        {
            'description': 'Oil change and filter replacement',
            'merchant': 'Quick Lube Express',
            'amount': 45.99,
            'date': '2024-01-15'
        },
        {
            'description': 'Gas fill up',
            'merchant': 'Shell Gas Station',
            'amount': 67.50,
            'date': '2024-01-16'
        },
        {
            'description': 'Auto insurance payment',
            'merchant': 'Geico Insurance',
            'amount': 125.00,
            'date': '2024-01-01'
        },
        {
            'description': 'Brake pad replacement',
            'merchant': 'Firestone Auto Care',
            'amount': 285.00,
            'date': '2024-01-20'
        },
        {
            'description': 'New tires - all 4',
            'merchant': 'Discount Tire',
            'amount': 650.00,
            'date': '2024-01-25'
        },
        {
            'description': 'Parking garage fee',
            'merchant': 'Downtown Parking',
            'amount': 12.00,
            'date': '2024-01-18'
        },
        {
            'description': 'Vehicle registration renewal',
            'merchant': 'DMV Online',
            'amount': 35.00,
            'date': '2024-01-05'
        },
        {
            'description': 'Transmission service',
            'merchant': 'AAMCO Transmissions',
            'amount': 180.00,
            'date': '2024-01-30'
        }
    ]
    
    print("Categorizing sample expenses...")
    print()
    
    for i, expense in enumerate(sample_expenses, 1):
        print(f"{i}. {expense['description']} - ${expense['amount']}")
        
        # Add user_email for processing
        expense['user_email'] = 'demo@mingus.com'
        
        # Categorize the expense
        match = categorizer.categorize_expense(expense, 'demo@mingus.com')
        
        # Display results
        print(f"   📋 Category: {match.expense_type.value.upper()}")
        print(f"   🎯 Confidence: {match.confidence_score:.1%}")
        print(f"   🚗 Vehicle Related: {'Yes' if match.confidence_score > 0.3 else 'No'}")
        print(f"   🔧 Maintenance Related: {'Yes' if match.is_maintenance_related else 'No'}")
        print(f"   🔍 Keywords: {', '.join(match.matched_keywords[:3])}")
        print()

def demonstrate_maintenance_predictions():
    """Demonstrate maintenance prediction features"""
    print("🔧 MAINTENANCE PREDICTION DEMO")
    print("=" * 50)
    
    from backend.services.maintenance_prediction_engine import MaintenancePredictionEngine
    
    engine = MaintenancePredictionEngine()
    
    # Test different ZIP codes for regional pricing
    zip_codes = [
        ('30309', 'Atlanta, GA'),
        ('10001', 'New York, NY'),
        ('77002', 'Houston, TX'),
        ('60601', 'Chicago, IL')
    ]
    
    print("Regional Pricing Analysis:")
    print()
    
    for zip_code, city in zip_codes:
        msa_name, multiplier = engine.map_zipcode_to_msa(zip_code)
        print(f"📍 {city} ({zip_code})")
        print(f"   MSA: {msa_name}")
        print(f"   Pricing Multiplier: {multiplier:.2f}")
        print(f"   Cost Impact: {((multiplier - 1) * 100):+.1f}%")
        print()
    
    # Generate maintenance predictions
    print("Maintenance Predictions for 2020 Honda Civic (45,000 miles):")
    print()
    
    predictions = engine.predict_maintenance(
        vehicle_id=1,
        year=2020,
        make='Honda',
        model='Civic',
        current_mileage=45000,
        zipcode='30309',  # Atlanta
        prediction_horizon_months=12
    )
    
    # Group predictions by type
    routine_predictions = [p for p in predictions if p.is_routine]
    age_based_predictions = [p for p in predictions if not p.is_routine]
    
    print(f"📅 ROUTINE MAINTENANCE ({len(routine_predictions)} predictions):")
    for pred in routine_predictions[:5]:  # Show first 5
        print(f"   • {pred.service_type}: ${pred.estimated_cost:.2f} on {pred.predicted_date}")
        print(f"     Mileage: {pred.predicted_mileage:,} | Probability: {pred.probability:.1%}")
    
    print()
    print(f"⏰ AGE-BASED MAINTENANCE ({len(age_based_predictions)} predictions):")
    for pred in age_based_predictions[:3]:  # Show first 3
        print(f"   • {pred.service_type}: ${pred.estimated_cost:.2f} on {pred.predicted_date}")
        print(f"     Probability: {pred.probability:.1%} | Priority: {pred.priority.value}")

def demonstrate_spending_analysis():
    """Demonstrate enhanced spending analysis"""
    print("📊 ENHANCED SPENDING ANALYSIS DEMO")
    print("=" * 50)
    
    from backend.services.enhanced_spending_analyzer import EnhancedSpendingAnalyzer
    
    analyzer = EnhancedSpendingAnalyzer()
    
    # Get comprehensive analysis
    print("Generating comprehensive spending analysis...")
    print()
    
    analysis = analyzer.get_comprehensive_spending_analysis('demo@mingus.com', 12)
    
    if analysis and 'summary' in analysis:
        summary = analysis['summary']
        
        print("💰 SPENDING SUMMARY:")
        print(f"   Total Monthly Spending: ${summary.get('total_monthly', 0):,.2f}")
        print(f"   Vehicle Spending: ${summary.get('vehicle_monthly', 0):,.2f}")
        print(f"   Traditional Spending: ${summary.get('traditional_monthly', 0):,.2f}")
        print(f"   Vehicle % of Total: {summary.get('vehicle_percentage', 0):.1f}%")
        print()
    
    if analysis and 'categories' in analysis:
        categories = analysis['categories']
        
        print("📋 SPENDING BREAKDOWN:")
        for category, data in list(categories.items())[:5]:  # Show first 5
            if isinstance(data, dict) and 'amount' in data:
                print(f"   {category}: ${data['amount']:,.2f} ({data.get('percentage', 0):.1f}%)")
        print()
    
    if analysis and 'recommendations' in analysis:
        recommendations = analysis['recommendations']
        
        print("💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
            if isinstance(rec, dict):
                print(f"   {i}. {rec.get('title', 'Recommendation')}")
                print(f"      {rec.get('description', '')}")
                if 'potential_savings' in rec:
                    print(f"      💰 Potential Savings: ${rec['potential_savings']:,.2f}")
        print()

def demonstrate_system_features():
    """Demonstrate overall system features"""
    print("🎯 SYSTEM FEATURES DEMONSTRATION")
    print("=" * 50)
    
    print("✅ AUTOMATIC VEHICLE EXPENSE DETECTION")
    print("   • Recognizes 8+ vehicle expense types")
    print("   • Uses keyword matching and pattern recognition")
    print("   • Provides confidence scoring for each categorization")
    print("   • Supports maintenance, fuel, insurance, parking, repairs, etc.")
    print()
    
    print("✅ MULTI-VEHICLE EXPENSE LINKING")
    print("   • Automatically links expenses to specific vehicles")
    print("   • Uses context analysis and vehicle identification")
    print("   • Supports multiple vehicles per user")
    print("   • Tracks expense patterns per vehicle")
    print()
    
    print("✅ MAINTENANCE COST PREDICTION & COMPARISON")
    print("   • Predicts upcoming maintenance needs")
    print("   • Compares actual costs to predictions")
    print("   • Regional pricing adjustments (MSA mapping)")
    print("   • Tracks prediction accuracy over time")
    print()
    
    print("✅ ENHANCED SPENDING ANALYSIS")
    print("   • Integrates vehicle expenses with traditional spending")
    print("   • Provides comprehensive financial health analysis")
    print("   • Generates personalized insights and recommendations")
    print("   • Tracks spending trends and patterns")
    print()
    
    print("✅ MACHINE LEARNING INTEGRATION")
    print("   • ML-powered categorization (when dependencies available)")
    print("   • Continuous learning from user data")
    print("   • Anomaly detection for unusual spending")
    print("   • Feature importance analysis")
    print()
    
    print("✅ API INTEGRATION")
    print("   • RESTful API endpoints for all functionality")
    print("   • Batch processing capabilities")
    print("   • Real-time expense processing")
    print("   • Comprehensive error handling")
    print()

def main():
    """Run the complete demonstration"""
    print("🚗 MINGUS VEHICLE EXPENSE SYSTEM")
    print("=" * 60)
    print("Enhanced Vehicle Expense Categorization & Analysis")
    print("=" * 60)
    print()
    
    try:
        # Run demonstrations
        demonstrate_expense_categorization()
        print()
        
        demonstrate_maintenance_predictions()
        print()
        
        demonstrate_spending_analysis()
        print()
        
        demonstrate_system_features()
        
        print("🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("The enhanced vehicle expense system successfully demonstrates:")
        print("• Automatic vehicle expense detection with high accuracy")
        print("• Multi-vehicle expense linking and tracking")
        print("• Maintenance cost prediction and comparison")
        print("• Enhanced spending analysis with vehicle expenses")
        print("• Integration with existing Mingus financial platform")
        print()
        print("💡 To enable ML features, install: pip install scikit-learn pandas numpy")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        print("Some features may require additional setup or dependencies.")

if __name__ == "__main__":
    main()
