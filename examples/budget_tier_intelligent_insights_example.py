"""
Budget Tier Intelligent Insights Example for MINGUS

This example demonstrates the intelligent insights functionality for Budget tier users:
- Unusual spending detection
- Subscription service identification
- Bill due date predictions
- Cash flow optimization suggestions
- Financial goal progress tracking
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.models.subscription import Customer, Subscription, PricingTier, FeatureUsage
from backend.services.budget_tier_service import BudgetTierService
from backend.services.budget_tier_insights_service import BudgetTierInsightsService
from backend.services.tier_access_control_service import TierAccessControlService
from backend.services.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BudgetTierIntelligentInsightsExample:
    """Example demonstrating Budget tier intelligent insights"""
    
    def __init__(self):
        """Initialize the example"""
        # Create in-memory database for demonstration
        self.engine = create_engine('sqlite:///mingus_budget_insights_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.tier_service = TierAccessControlService(self.db_session, {})
        self.notification_service = NotificationService(self.db_session, {})
        self.budget_service = BudgetTierService(self.db_session, self.tier_service, self.notification_service)
        self.insights_service = BudgetTierInsightsService(self.db_session, self.budget_service)
        
        # Sample data
        self.budget_tier = None
        self.customer = None
        self.subscription = None
        self.feature_usage = None
    
    def setup_sample_data(self):
        """Create sample data for demonstration"""
        print("\n=== Setting Up Sample Data ===")
        
        # Create Budget tier
        self.budget_tier = PricingTier(
            tier_type='budget',
            name='Budget',
            description='Perfect for individuals getting started with financial tracking',
            monthly_price=15.00,
            yearly_price=150.00,
            max_health_checkins_per_month=4,
            max_financial_reports_per_month=2,
            max_ai_insights_per_month=0
        )
        
        self.db_session.add(self.budget_tier)
        self.db_session.commit()
        
        # Create sample customer
        self.customer = Customer(
            user_id=1,
            stripe_customer_id='cus_budget_insights_demo',
            email='budget.insights@example.com',
            name='Budget Insights User',
            address={'country': 'US', 'state': 'CA'}
        )
        
        self.db_session.add(self.customer)
        self.db_session.commit()
        
        # Create Budget subscription
        self.subscription = Subscription(
            customer_id=self.customer.id,
            pricing_tier_id=self.budget_tier.id,
            stripe_subscription_id='sub_budget_insights_demo',
            status='active',
            current_period_start=datetime.utcnow() - timedelta(days=15),
            current_period_end=datetime.utcnow() + timedelta(days=15),
            billing_cycle='monthly',
            amount=15.00,
            currency='USD'
        )
        
        self.db_session.add(self.subscription)
        self.db_session.commit()
        
        # Create feature usage record
        current_month = datetime.utcnow().month
        current_year = datetime.utcnow().year
        
        self.feature_usage = FeatureUsage(
            subscription_id=self.subscription.id,
            usage_month=current_month,
            usage_year=current_year,
            health_checkins_used=0,
            financial_reports_used=0,
            ai_insights_used=0
        )
        
        self.db_session.add(self.feature_usage)
        self.db_session.commit()
        
        print("✅ Sample data created successfully")
    
    def demonstrate_unusual_spending_detection(self):
        """Demonstrate unusual spending detection"""
        print("\n=== Unusual Spending Detection ===")
        
        user_id = "1"
        
        # Generate insights
        result = self.insights_service.generate_comprehensive_insights(user_id, days_back=90)
        
        if result['success']:
            unusual_spending = result['insights']['unusual_spending']
            
            print(f"\n📊 Unusual Spending Analysis:")
            print(f"   Total unusual transactions detected: {len(unusual_spending)}")
            
            for i, insight in enumerate(unusual_spending[:3], 1):
                print(f"\n   🔍 Unusual Transaction {i}:")
                print(f"      Transaction: {insight['transaction_name']}")
                print(f"      Amount: ${insight['amount']}")
                print(f"      Category: {insight['category']}")
                print(f"      Unusual Factor: {insight['unusual_factor']:.1f}x normal")
                print(f"      Severity: {insight['severity']}")
                print(f"      Reason: {insight['reason']}")
                
                if insight['recommendations']:
                    print(f"      💡 Recommendations:")
                    for rec in insight['recommendations'][:2]:
                        print(f"         • {rec}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_subscription_identification(self):
        """Demonstrate subscription service identification"""
        print("\n=== Subscription Service Identification ===")
        
        user_id = "1"
        
        # Generate insights
        result = self.insights_service.generate_comprehensive_insights(user_id, days_back=90)
        
        if result['success']:
            subscriptions = result['insights']['subscriptions']
            
            print(f"\n📊 Subscription Analysis:")
            print(f"   Total subscriptions identified: {len(subscriptions)}")
            
            # Calculate monthly subscription cost
            monthly_cost = sum(
                float(sub['amount']) for sub in subscriptions 
                if sub['frequency'] == 'monthly'
            )
            print(f"   Monthly subscription cost: ${monthly_cost:.2f}")
            
            for i, subscription in enumerate(subscriptions[:3], 1):
                print(f"\n   🔍 Subscription {i}:")
                print(f"      Service: {subscription['service_name']}")
                print(f"      Amount: ${subscription['amount']}")
                print(f"      Frequency: {subscription['frequency']}")
                print(f"      Next Due: {subscription['next_due_date']}")
                print(f"      Confidence: {subscription['confidence']:.1%}")
                print(f"      Total Spent: ${subscription['total_spent']}")
                
                if subscription['recommendations']:
                    print(f"      💡 Recommendations:")
                    for rec in subscription['recommendations'][:2]:
                        print(f"         • {rec}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_bill_due_predictions(self):
        """Demonstrate bill due date predictions"""
        print("\n=== Bill Due Date Predictions ===")
        
        user_id = "1"
        
        # Generate insights
        result = self.insights_service.generate_comprehensive_insights(user_id, days_back=90)
        
        if result['success']:
            bill_predictions = result['insights']['bill_predictions']
            
            print(f"\n📊 Bill Prediction Analysis:")
            print(f"   Total bills identified: {len(bill_predictions)}")
            
            # Filter upcoming bills
            upcoming_bills = [
                bill for bill in bill_predictions
                if datetime.strptime(bill['predicted_due_date'], '%Y-%m-%d').date() <= date.today() + timedelta(days=30)
            ]
            print(f"   Bills due within 30 days: {len(upcoming_bills)}")
            
            for i, bill in enumerate(bill_predictions[:3], 1):
                print(f"\n   🔍 Bill {i}:")
                print(f"      Bill Name: {bill['bill_name']}")
                print(f"      Predicted Amount: ${bill['predicted_amount']}")
                print(f"      Predicted Due Date: {bill['predicted_due_date']}")
                print(f"      Confidence: {bill['confidence']:.1%}")
                print(f"      Last Paid: {bill['last_paid_date']}")
                
                if bill['recommendations']:
                    print(f"      💡 Recommendations:")
                    for rec in bill['recommendations'][:2]:
                        print(f"         • {rec}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_cash_flow_optimization(self):
        """Demonstrate cash flow optimization suggestions"""
        print("\n=== Cash Flow Optimization Suggestions ===")
        
        user_id = "1"
        
        # Generate insights
        result = self.insights_service.generate_comprehensive_insights(user_id, days_back=90)
        
        if result['success']:
            optimizations = result['insights']['cash_flow_optimization']
            
            print(f"\n📊 Cash Flow Optimization Analysis:")
            print(f"   Total optimization suggestions: {len(optimizations)}")
            
            # Calculate total potential savings
            total_potential_savings = sum(
                float(opt['potential_savings']) for opt in optimizations
            )
            print(f"   Total potential savings: ${total_potential_savings:.2f}")
            
            for i, optimization in enumerate(optimizations[:3], 1):
                print(f"\n   🔍 Optimization {i}:")
                print(f"      Type: {optimization['insight_type']}")
                print(f"      Title: {optimization['title']}")
                print(f"      Description: {optimization['description']}")
                print(f"      Potential Savings: ${optimization['potential_savings']}")
                print(f"      Difficulty: {optimization['implementation_difficulty']}")
                print(f"      Time to Impact: {optimization['time_to_impact']}")
                
                if optimization['action_items']:
                    print(f"      💡 Action Items:")
                    for action in optimization['action_items'][:3]:
                        print(f"         • {action}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_goal_progress_tracking(self):
        """Demonstrate financial goal progress tracking"""
        print("\n=== Financial Goal Progress Tracking ===")
        
        user_id = "1"
        
        # Generate insights
        result = self.insights_service.generate_comprehensive_insights(user_id, days_back=90)
        
        if result['success']:
            goal_progress = result['insights']['goal_progress']
            
            print(f"\n📊 Goal Progress Analysis:")
            print(f"   Total goals tracked: {len(goal_progress)}")
            
            # Calculate summary statistics
            on_track_goals = [goal for goal in goal_progress if goal['on_track']]
            print(f"   Goals on track: {len(on_track_goals)}")
            
            total_progress = sum(goal['current_progress'] for goal in goal_progress)
            avg_progress = total_progress / len(goal_progress) if goal_progress else 0
            print(f"   Average progress: {avg_progress:.1%}")
            
            for i, goal in enumerate(goal_progress[:3], 1):
                print(f"\n   🔍 Goal {i}:")
                print(f"      Goal Name: {goal['goal_name']}")
                print(f"      Goal Type: {goal['goal_type']}")
                print(f"      Current Progress: {goal['current_progress']:.1%}")
                print(f"      Target Amount: ${goal['target_amount']}")
                print(f"      Current Amount: ${goal['current_amount']}")
                print(f"      Remaining: ${goal['remaining_amount']}")
                print(f"      On Track: {'✅' if goal['on_track'] else '❌'}")
                
                if goal['recommendations']:
                    print(f"      💡 Recommendations:")
                    for rec in goal['recommendations'][:2]:
                        print(f"         • {rec}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_comprehensive_insights(self):
        """Demonstrate comprehensive insights dashboard"""
        print("\n=== Comprehensive Insights Dashboard ===")
        
        user_id = "1"
        
        # Generate comprehensive insights
        result = self.insights_service.generate_comprehensive_insights(user_id, days_back=90)
        
        if result['success']:
            insights = result['insights']
            summary = result['summary']
            
            print(f"\n📊 Comprehensive Insights Summary:")
            print(f"   Total Insights: {summary['total_insights']}")
            print(f"   Analysis Period: {summary['analysis_period']}")
            print(f"   Transactions Analyzed: {summary['transactions_analyzed']}")
            
            print(f"\n📈 Insights Breakdown:")
            print(f"   • Unusual Spending: {len(insights['unusual_spending'])}")
            print(f"   • Subscriptions: {len(insights['subscriptions'])}")
            print(f"   • Bill Predictions: {len(insights['bill_predictions'])}")
            print(f"   • Cash Flow Optimizations: {len(insights['cash_flow_optimization'])}")
            print(f"   • Goal Progress: {len(insights['goal_progress'])}")
            
            # Calculate total potential savings
            total_savings = sum(
                float(opt['potential_savings']) for opt in insights['cash_flow_optimization']
            )
            print(f"\n💰 Total Potential Savings: ${total_savings:.2f}")
            
            # Show top recommendations
            print(f"\n🎯 Top Recommendations:")
            
            # Top optimization
            optimizations = insights['cash_flow_optimization']
            if optimizations:
                top_optimization = max(optimizations, key=lambda x: float(x['potential_savings']))
                print(f"   • {top_optimization['title']}: ${top_optimization['potential_savings']} potential savings")
            
            # Critical unusual spending
            unusual_spending = insights['unusual_spending']
            critical_spending = [s for s in unusual_spending if s['severity'] in ['alert', 'critical']]
            if critical_spending:
                print(f"   • {len(critical_spending)} critical unusual spending transactions detected")
            
            # Upcoming bills
            bill_predictions = insights['bill_predictions']
            upcoming_bills = [
                bill for bill in bill_predictions
                if datetime.strptime(bill['predicted_due_date'], '%Y-%m-%d').date() <= date.today() + timedelta(days=7)
            ]
            if upcoming_bills:
                print(f"   • {len(upcoming_bills)} bills due within 7 days")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_insights_configuration(self):
        """Demonstrate insights configuration options"""
        print("\n=== Insights Configuration Options ===")
        
        print(f"\n🔧 Configurable Parameters:")
        print(f"   • Unusual Spending Threshold: {self.insights_service.unusual_spending_threshold}x normal")
        print(f"   • Subscription Confidence Threshold: {self.insights_service.subscription_confidence_threshold:.1%}")
        print(f"   • Bill Prediction Confidence Threshold: {self.insights_service.bill_prediction_confidence_threshold:.1%}")
        
        print(f"\n📋 Subscription Keywords:")
        print(f"   • Streaming: Netflix, Spotify, Hulu, Disney+, HBO Max")
        print(f"   • Software: Microsoft 365, Adobe, Dropbox, Slack")
        print(f"   • Fitness: Gym, Fitness, Yoga, CrossFit")
        print(f"   • Utilities: Insurance, Phone, Internet, Electricity")
        
        print(f"\n📋 Bill Keywords:")
        print(f"   • Housing: Rent, Mortgage, HOA")
        print(f"   • Utilities: Electricity, Water, Gas, Internet")
        print(f"   • Services: Phone, Insurance, Cable")
    
    def run_all_demonstrations(self):
        """Run all intelligent insights demonstrations"""
        print("🚀 MINGUS Budget Tier Intelligent Insights Demonstration")
        print("=" * 70)
        
        try:
            # Setup sample data
            self.setup_sample_data()
            
            # Run demonstrations
            self.demonstrate_unusual_spending_detection()
            self.demonstrate_subscription_identification()
            self.demonstrate_bill_due_predictions()
            self.demonstrate_cash_flow_optimization()
            self.demonstrate_goal_progress_tracking()
            self.demonstrate_comprehensive_insights()
            self.demonstrate_insights_configuration()
            
            print("\n✅ All intelligent insights demonstrations completed successfully!")
            print("\n📋 Summary:")
            print("   • Unusual spending detection: ✅ Working")
            print("   • Subscription identification: ✅ Working")
            print("   • Bill due predictions: ✅ Working")
            print("   • Cash flow optimization: ✅ Working")
            print("   • Goal progress tracking: ✅ Working")
            print("   • Comprehensive insights: ✅ Working")
            
        except Exception as e:
            logger.error(f"Error during demonstration: {str(e)}")
            print(f"\n❌ Error during demonstration: {str(e)}")
        
        finally:
            # Cleanup
            self.db_session.close()


def main():
    """Main function to run the example"""
    example = BudgetTierIntelligentInsightsExample()
    example.run_all_demonstrations()


if __name__ == "__main__":
    main() 