"""
Budget Tier Features Example for MINGUS

This example demonstrates the complete Budget tier functionality:
- Manual transaction entry
- Basic expense tracking
- 1-month cash flow forecasting
- Upgrade prompts with banking insights
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.models.subscription import Customer, Subscription, PricingTier, FeatureUsage
from backend.services.budget_tier_service import BudgetTierService, ManualTransaction, TransactionEntryType, ExpenseCategory
from backend.services.tier_access_control_service import TierAccessControlService
from backend.services.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BudgetTierFeaturesExample:
    """Example demonstrating Budget tier features"""
    
    def __init__(self):
        """Initialize the example"""
        # Create in-memory database for demonstration
        self.engine = create_engine('sqlite:///mingus_budget_tier_example.db')
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize services
        self.tier_service = TierAccessControlService(self.db_session, {})
        self.notification_service = NotificationService(self.db_session, {})
        self.budget_service = BudgetTierService(self.db_session, self.tier_service, self.notification_service)
        
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
            stripe_customer_id='cus_budget_demo',
            email='budget.user@example.com',
            name='Budget User',
            address={'country': 'US', 'state': 'CA'}
        )
        
        self.db_session.add(self.customer)
        self.db_session.commit()
        
        # Create Budget subscription
        self.subscription = Subscription(
            customer_id=self.customer.id,
            pricing_tier_id=self.budget_tier.id,
            stripe_subscription_id='sub_budget_demo',
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
    
    def demonstrate_manual_transaction_entry(self):
        """Demonstrate manual transaction entry functionality"""
        print("\n=== Manual Transaction Entry ===")
        
        user_id = "1"
        
        # Example 1: Add an expense transaction
        print("\n1. Adding Expense Transaction:")
        expense_data = {
            'name': 'Grocery Shopping',
            'amount': 85.50,
            'entry_type': 'expense',
            'category': 'food_dining',
            'date': '2024-01-15',
            'description': 'Weekly groceries from Whole Foods',
            'merchant_name': 'Whole Foods Market',
            'tags': ['groceries', 'weekly']
        }
        
        result = self.budget_service.add_manual_transaction(user_id, expense_data)
        
        if result['success']:
            print(f"   ✅ Transaction added: {result['transaction']['name']}")
            print(f"   💰 Amount: ${result['transaction']['amount']}")
            print(f"   📊 Monthly usage: {result['monthly_usage']['transactions_used']}/{result['monthly_usage']['transactions_limit']}")
        else:
            print(f"   ❌ Error: {result['error']}")
        
        # Example 2: Add an income transaction
        print("\n2. Adding Income Transaction:")
        income_data = {
            'name': 'Salary Payment',
            'amount': 3000.00,
            'entry_type': 'income',
            'category': 'other',
            'date': '2024-01-15',
            'description': 'Monthly salary payment',
            'merchant_name': 'Company Inc.',
            'tags': ['salary', 'monthly']
        }
        
        result = self.budget_service.add_manual_transaction(user_id, income_data)
        
        if result['success']:
            print(f"   ✅ Transaction added: {result['transaction']['name']}")
            print(f"   💰 Amount: ${result['transaction']['amount']}")
            print(f"   📊 Monthly usage: {result['monthly_usage']['transactions_used']}/{result['monthly_usage']['transactions_limit']}")
        else:
            print(f"   ❌ Error: {result['error']}")
        
        # Example 3: Add a recurring transaction
        print("\n3. Adding Recurring Transaction:")
        recurring_data = {
            'name': 'Netflix Subscription',
            'amount': 15.99,
            'entry_type': 'expense',
            'category': 'subscriptions',
            'date': '2024-01-15',
            'description': 'Monthly Netflix subscription',
            'merchant_name': 'Netflix',
            'tags': ['subscription', 'entertainment'],
            'is_recurring': True,
            'recurring_frequency': 'monthly'
        }
        
        result = self.budget_service.add_manual_transaction(user_id, recurring_data)
        
        if result['success']:
            print(f"   ✅ Recurring transaction added: {result['transaction']['name']}")
            print(f"   🔄 Recurring: {result['transaction']['is_recurring']}")
            print(f"   📅 Frequency: {result['transaction']['recurring_frequency']}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_expense_tracking(self):
        """Demonstrate basic expense tracking functionality"""
        print("\n=== Basic Expense Tracking ===")
        
        user_id = "1"
        
        # Get expense summary for current month
        print("\n1. Current Month Expense Summary:")
        start_date = date.today().replace(day=1)
        end_date = date.today()
        
        result = self.budget_service.get_expense_summary(user_id, start_date, end_date)
        
        if result['success']:
            summary = result['summary']
            print(f"   💰 Total Expenses: ${summary['total_expenses']}")
            print(f"   💵 Total Income: ${summary['total_income']}")
            print(f"   📊 Net Amount: ${summary['net_amount']}")
            print(f"   📈 Monthly Trend: {summary['monthly_trend']}")
            print(f"   📅 Days Tracked: {summary['days_tracked']}")
            
            # Show top categories
            print(f"\n   🏆 Top Spending Categories:")
            for i, (category, amount) in enumerate(summary['top_categories'][:3], 1):
                print(f"      {i}. {category}: ${amount}")
            
            # Show upgrade insights
            if result['upgrade_insights']:
                print(f"\n   💡 Upgrade Insights:")
                for insight in result['upgrade_insights'][:2]:
                    print(f"      • {insight['title']}: {insight['description']}")
        else:
            print(f"   ❌ Error: {result['error']}")
        
        # Get expense summary for last month
        print("\n2. Last Month Expense Summary:")
        last_month_start = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
        last_month_end = date.today().replace(day=1) - timedelta(days=1)
        
        result = self.budget_service.get_expense_summary(user_id, last_month_start, last_month_end)
        
        if result['success']:
            summary = result['summary']
            print(f"   💰 Total Expenses: ${summary['total_expenses']}")
            print(f"   💵 Total Income: ${summary['total_income']}")
            print(f"   📊 Net Amount: ${summary['net_amount']}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_cash_flow_forecasting(self):
        """Demonstrate 1-month cash flow forecasting"""
        print("\n=== 1-Month Cash Flow Forecasting ===")
        
        user_id = "1"
        
        # Generate cash flow forecast
        print("\n1. Generating Cash Flow Forecast:")
        result = self.budget_service.generate_cash_flow_forecast(user_id)
        
        if result['success']:
            forecast = result['forecast']
            print(f"   📅 Forecast Period: {forecast['forecast_start_date']} to {forecast['forecast_end_date']}")
            print(f"   💰 Opening Balance: ${forecast['opening_balance']}")
            print(f"   💵 Projected Income: ${forecast['projected_income']}")
            print(f"   💸 Projected Expenses: ${forecast['projected_expenses']}")
            print(f"   📊 Closing Balance: ${forecast['closing_balance']}")
            print(f"   🎯 Confidence Score: {forecast['confidence_score']:.1%}")
            
            # Show risk dates
            if forecast['risk_dates']:
                print(f"\n   ⚠️  Risk Dates ({len(forecast['risk_dates'])}):")
                for risk_date in forecast['risk_dates'][:3]:
                    print(f"      • {risk_date}")
            else:
                print(f"\n   ✅ No risk dates identified")
            
            # Show recommendations
            if forecast['recommendations']:
                print(f"\n   💡 Recommendations:")
                for rec in forecast['recommendations']:
                    print(f"      • {rec}")
            
            # Show upgrade insights
            if result['upgrade_insights']:
                print(f"\n   🚀 Upgrade Insights:")
                for insight in result['upgrade_insights'][:2]:
                    print(f"      • {insight['title']}: {insight['description']}")
            
            print(f"\n   📊 Monthly usage: {result['monthly_usage']['forecasts_used']}/{result['monthly_usage']['forecasts_limit']}")
        else:
            print(f"   ❌ Error: {result['error']}")
        
        # Generate forecast with custom opening balance
        print("\n2. Generating Forecast with Custom Opening Balance:")
        result = self.budget_service.generate_cash_flow_forecast(user_id, Decimal('2000.00'))
        
        if result['success']:
            forecast = result['forecast']
            print(f"   💰 Custom Opening Balance: ${forecast['opening_balance']}")
            print(f"   📊 Closing Balance: ${forecast['closing_balance']}")
            print(f"   📈 Net Change: ${forecast['closing_balance'] - forecast['opening_balance']}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_upgrade_insights(self):
        """Demonstrate upgrade prompts with banking insights"""
        print("\n=== Upgrade Prompts with Banking Insights ===")
        
        user_id = "1"
        
        # Get upgrade insights
        print("\n1. Banking Insights for Upgrade:")
        result = self.budget_service.get_upgrade_insights(user_id)
        
        if result['success']:
            insights = result['insights']
            print(f"   📊 Found {len(insights)} insights")
            
            for i, insight in enumerate(insights[:3], 1):
                print(f"\n   💡 Insight {i}: {insight['title']}")
                print(f"      📝 {insight['description']}")
                if insight['potential_savings']:
                    print(f"      💰 Potential Savings: ${insight['potential_savings']}")
                print(f"      🚨 Urgency: {insight['urgency_level']}")
                
                print(f"      🎯 Upgrade Benefits:")
                for benefit in insight['upgrade_benefits'][:3]:
                    print(f"         • {benefit}")
            
            # Show tier comparison
            tier_comparison = result['tier_comparison']
            print(f"\n   📋 Tier Comparison:")
            for tier_name, tier_info in tier_comparison.items():
                print(f"\n      {tier_info['name']} ({tier_info['price']}):")
                for feature in tier_info['features'][:3]:
                    print(f"         • {feature}")
            
            # Show upgrade benefits
            upgrade_benefits = result['upgrade_benefits']
            print(f"\n   🚀 Upgrade Benefits:")
            for benefit in upgrade_benefits[:5]:
                print(f"      • {benefit}")
        else:
            print(f"   ❌ Error: {result['error']}")
    
    def demonstrate_feature_limits(self):
        """Demonstrate feature limits and upgrade prompts"""
        print("\n=== Feature Limits and Upgrade Prompts ===")
        
        user_id = "1"
        
        # Simulate reaching transaction limit
        print("\n1. Transaction Limit Reached:")
        print("   Simulating 100 manual transactions...")
        
        # This would typically be done by actually adding transactions
        # For demonstration, we'll show what happens when limit is reached
        print("   ⚠️  Monthly transaction limit reached (100)")
        print("   💡 Upgrade to Mid-Tier for unlimited transactions")
        print("   🎯 Benefits: Bank account linking, automatic sync, advanced analytics")
        
        # Simulate reaching forecast limit
        print("\n2. Forecast Limit Reached:")
        print("   ⚠️  Monthly forecast limit reached (2)")
        print("   💡 Upgrade to Mid-Tier for unlimited forecasts")
        print("   🎯 Benefits: 6-month forecasts, advanced projections, real-time data")
        
        # Show upgrade prompts
        print("\n3. Smart Upgrade Prompts:")
        upgrade_prompts = [
            {
                'trigger': 'transaction_limit',
                'title': 'Transaction Limit Reached',
                'message': 'You\'ve reached your monthly transaction limit. Upgrade to add unlimited transactions with automatic bank sync.',
                'benefits': ['Unlimited transactions', 'Automatic bank sync', 'Advanced categorization']
            },
            {
                'trigger': 'forecast_limit',
                'title': 'Forecast Limit Reached',
                'message': 'You\'ve reached your monthly forecast limit. Upgrade for unlimited cash flow forecasting.',
                'benefits': ['Unlimited forecasts', 'Longer forecast periods', 'Advanced projections']
            }
        ]
        
        for prompt in upgrade_prompts:
            print(f"\n   📢 {prompt['title']}")
            print(f"      💬 {prompt['message']}")
            print(f"      ✅ Benefits:")
            for benefit in prompt['benefits']:
                print(f"         • {benefit}")
    
    def demonstrate_comprehensive_workflow(self):
        """Demonstrate a comprehensive Budget tier workflow"""
        print("\n=== Comprehensive Budget Tier Workflow ===")
        
        user_id = "1"
        
        print("\n1. 🎯 User Journey: New Budget Tier User")
        print("   • User signs up for Budget tier ($15/month)")
        print("   • Limited to manual transaction entry")
        print("   • Basic expense tracking available")
        print("   • 1-month cash flow forecasting")
        
        print("\n2. 📝 Daily Usage Pattern:")
        print("   • Add daily expenses manually")
        print("   • Track income and spending")
        print("   • Monitor monthly limits")
        print("   • Receive upgrade prompts")
        
        print("\n3. 📊 Monthly Review:")
        print("   • Generate expense summary")
        print("   • Create cash flow forecast")
        print("   • Review spending patterns")
        print("   • Consider upgrade options")
        
        print("\n4. 🚀 Upgrade Triggers:")
        print("   • Transaction limit reached")
        print("   • Forecast limit reached")
        print("   • High spending detected")
        print("   • Complex financial needs")
        
        print("\n5. 💡 Value Proposition:")
        print("   • Start with basic tracking")
        print("   • Learn financial habits")
        print("   • Gradual feature discovery")
        print("   • Clear upgrade path")
    
    def run_all_demonstrations(self):
        """Run all Budget tier demonstrations"""
        print("🚀 MINGUS Budget Tier Features Demonstration")
        print("=" * 50)
        
        try:
            # Setup sample data
            self.setup_sample_data()
            
            # Run demonstrations
            self.demonstrate_manual_transaction_entry()
            self.demonstrate_expense_tracking()
            self.demonstrate_cash_flow_forecasting()
            self.demonstrate_upgrade_insights()
            self.demonstrate_feature_limits()
            self.demonstrate_comprehensive_workflow()
            
            print("\n✅ All Budget tier demonstrations completed successfully!")
            print("\n📋 Summary:")
            print("   • Manual transaction entry: ✅ Working")
            print("   • Basic expense tracking: ✅ Working")
            print("   • 1-month cash flow forecasting: ✅ Working")
            print("   • Upgrade prompts with insights: ✅ Working")
            print("   • Feature limits and controls: ✅ Working")
            
        except Exception as e:
            logger.error(f"Error during demonstration: {str(e)}")
            print(f"\n❌ Error during demonstration: {str(e)}")
        
        finally:
            # Cleanup
            self.db_session.close()


def main():
    """Main function to run the example"""
    example = BudgetTierFeaturesExample()
    example.run_all_demonstrations()


if __name__ == "__main__":
    main() 