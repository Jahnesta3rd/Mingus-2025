# Key Metrics Guide

## Overview

The Key Metrics system provides comprehensive analytics for customer acquisition, lifetime value, churn analysis, and revenue optimization. It offers detailed insights by channel, tier, and cohort to drive data-driven business decisions.

## Feature Overview

### Purpose
- **Customer Acquisition Analysis**: Track and optimize acquisition costs by channel
- **Customer Value Analysis**: Monitor lifetime value by customer tier
- **Churn Analysis**: Understand churn patterns by tier and cohort
- **Revenue Optimization**: Analyze revenue per user and tier distribution
- **Channel Performance**: Evaluate LTV/CAC ratios and channel efficiency
- **Business Intelligence**: Generate actionable insights and recommendations

### Key Benefits
- **Channel Optimization**: Identify most efficient acquisition channels
- **Tier Management**: Optimize customer tiers and pricing strategies
- **Churn Prevention**: Early detection and prevention of customer churn
- **Revenue Growth**: Maximize revenue per user and overall growth
- **Strategic Planning**: Data-driven decisions for business strategy
- **Performance Monitoring**: Real-time tracking of key business metrics

## Customer Acquisition Cost (CAC) by Channel

### Overview
CAC by channel measures the cost of acquiring a new customer through different marketing channels, helping optimize marketing spend and channel efficiency.

### Calculation Method
```python
def calculate_customer_acquisition_cost_by_channel(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
    """
    Calculate Customer Acquisition Cost (CAC) by channel
    
    CAC = Total Channel Cost / Number of New Customers
    """
```

### Supported Channels
- **Organic Search**: SEO, content marketing, technical SEO
- **Paid Advertising**: Google Ads, Facebook Ads, LinkedIn Ads
- **Referral**: Referral programs, partner commissions
- **Partnership**: Partner marketing, joint ventures
- **Social Media**: Organic social, paid social campaigns
- **Email Marketing**: Email campaigns, newsletters
- **Direct Traffic**: Direct website visits, brand awareness

### Usage Example
```python
# Calculate CAC by channel
analytics = SubscriptionAnalytics(db, config)
cac_by_channel = analytics.calculate_customer_acquisition_cost_by_channel(period_days=30)

for channel, cac_metric in cac_by_channel.items():
    print(f"Channel: {channel}")
    print(f"  CAC: ${cac_metric.value:.2f}")
    print(f"  Change: {cac_metric.change_percentage:+.1f}%")
    print(f"  Trend: {cac_metric.trend}")
    
    # Access detailed metadata
    metadata = cac_metric.metadata
    print(f"  Total Cost: ${metadata['total_cost']:,.2f}")
    print(f"  New Customers: {metadata['new_customers']}")
    print(f"  Conversion Rate: {metadata['conversion_rate']:.1%}")
    print(f"  Channel Efficiency: {metadata['channel_efficiency']:.1%}")
    
    # Cost breakdown
    cost_breakdown = metadata['cost_breakdown']
    for cost_type, amount in cost_breakdown.items():
        print(f"    {cost_type}: ${amount:,.2f}")
```

### Channel Performance Analysis

#### Cost Breakdown
```python
'cost_breakdown': {
    'seo_tools': 2000.0,
    'content_creation': 1500.0,
    'technical_seo': 1500.0,
    'google_ads': 8000.0,
    'facebook_ads': 5000.0,
    'linkedin_ads': 2000.0,
    'referral_program': 2000.0,
    'partner_commissions': 1000.0
}
```

#### Conversion Metrics
- **Conversion Rate**: Percentage of visitors who become customers
- **Channel Efficiency**: Overall effectiveness of the channel
- **Cost per Lead**: Cost to generate a qualified lead
- **Lead to Customer Rate**: Conversion from lead to customer

#### Optimization Opportunities
```python
def _identify_channel_optimization_opportunities(self, channel: str, ltv_cac_ratio: float) -> List[str]:
    """
    Identify optimization opportunities for a channel
    
    - Reduce acquisition costs
    - Improve conversion rates
    - Optimize targeting
    - Review ad spend allocation
    - Scale successful campaigns
    """
```

## Customer Lifetime Value (CLV) by Tier

### Overview
CLV by tier calculates the total revenue expected from customers in different tiers over their entire relationship with the business.

### Calculation Method
```python
def calculate_customer_lifetime_value_by_tier(self, date: datetime = None, cohort_periods: int = 12) -> Dict[str, MetricCalculation]:
    """
    Calculate Customer Lifetime Value (CLV) by tier
    
    CLV = Average Revenue per Customer × Average Customer Lifespan
    """
```

### Customer Tiers
- **Standard Tier**: Basic customers with core features
- **Premium Tier**: Mid-market customers with advanced features
- **Enterprise Tier**: Large customers with full feature access

### Usage Example
```python
# Calculate CLV by tier
clv_by_tier = analytics.calculate_customer_lifetime_value_by_tier(cohort_periods=12)

for tier, clv_metric in clv_by_tier.items():
    print(f"Tier: {tier}")
    print(f"  Average CLV: ${clv_metric.value:,.2f}")
    print(f"  Change: {clv_metric.change_percentage:+.1f}%")
    print(f"  Trend: {clv_metric.trend}")
    
    # Access detailed metadata
    metadata = clv_metric.metadata
    print(f"  Customer Count: {metadata['customer_count']}")
    print(f"  Total LTV: ${metadata['total_ltv']:,.2f}")
    print(f"  Tier Retention Rate: {metadata['tier_retention_rate']:.1f}%")
    print(f"  Tier Expansion Rate: {metadata['tier_expansion_rate']:.1f}%")
```

### Tier-Specific Analysis

#### Retention Analysis
```python
def _calculate_tier_retention_rate(self, tier: str, date: datetime) -> float:
    """
    Calculate retention rate for a specific tier
    
    - Standard tier: 85% retention
    - Premium tier: 90% retention
    - Enterprise tier: 95% retention
    """
```

#### Expansion Analysis
```python
def _calculate_tier_expansion_rate(self, tier: str, date: datetime) -> float:
    """
    Calculate expansion rate for a specific tier
    
    - Revenue growth within tier
    - Feature adoption rates
    - Upsell opportunities
    """
```

#### Tier Distribution
```python
def _get_tier_distribution(self, date: datetime) -> Dict[str, int]:
    """
    Get customer distribution by tier
    
    Returns:
        {
            'standard': 600,
            'premium': 300,
            'enterprise': 100
        }
    """
```

## Churn Rate by Tier and Cohort Analysis

### Overview
Churn rate by tier analyzes customer attrition patterns across different customer segments, enabling targeted retention strategies.

### Calculation Method
```python
def calculate_churn_rate_by_tier(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
    """
    Calculate churn rate by customer tier
    
    Churn Rate = (Churned Customers / Total Customers at Start) × 100
    """
```

### Usage Example
```python
# Calculate churn rate by tier
churn_by_tier = analytics.calculate_churn_rate_by_tier(period_days=30)

for tier, churn_metric in churn_by_tier.items():
    print(f"Tier: {tier}")
    print(f"  Churn Rate: {churn_metric.value:.2f}%")
    print(f"  Change: {churn_metric.change_percentage:+.1f}%")
    print(f"  Trend: {churn_metric.trend}")
    
    # Access detailed metadata
    metadata = churn_metric.metadata
    print(f"  Customers at Start: {metadata['customers_at_start']}")
    print(f"  Churned Customers: {metadata['churned_customers']}")
    print(f"  Churn Prediction Score: {metadata['churn_prediction_score']:.1%}")
    
    # Churn reasons
    churn_reasons = metadata['churn_reasons']
    for reason, count in churn_reasons.items():
        print(f"    {reason}: {count} customers")
    
    # Retention strategies
    strategies = metadata['tier_retention_strategies']
    for strategy in strategies:
        print(f"    - {strategy}")
```

### Churn Analysis Features

#### Churn Reasons by Tier
```python
def _get_churn_reasons_by_tier(self, tier: str, start_date: datetime, end_date: datetime) -> Dict[str, int]:
    """
    Get churn reasons by tier
    
    Returns:
        {
            'pricing': 15,
            'features': 8,
            'support': 5,
            'competition': 12,
            'business_closed': 3
        }
    """
```

#### Retention Strategies by Tier
```python
def _get_tier_retention_strategies(self, tier: str) -> List[str]:
    """
    Get retention strategies for a specific tier
    
    Returns:
        [
            'personalized_onboarding',
            'regular_check_ins',
            'feature_education',
            'success_planning',
            'exclusive_benefits'
        ]
    """
```

#### Churn Prediction
```python
def _calculate_churn_prediction_score(self, tier: str, date: datetime) -> float:
    """
    Calculate churn prediction score for a tier
    
    - Machine learning-based prediction
    - Risk scoring (0.0 to 1.0)
    - Early warning system
    """
```

### Cohort Analysis by Tier

#### Overview
Cohort analysis by tier groups customers within each tier by common characteristics and tracks their behavior over time.

#### Usage Example
```python
# Perform cohort analysis by tier
cohort_analysis = analytics.perform_cohort_analysis_by_tier(CohortType.SIGNUP_DATE)

for tier, cohort_analyses in cohort_analysis.items():
    print(f"Tier: {tier}")
    print(f"  Cohorts Analyzed: {len(cohort_analyses)}")
    
    for cohort in cohort_analyses:
        print(f"    Cohort: {cohort.cohort_period}")
        print(f"      Size: {cohort.cohort_size}")
        print(f"      Retention Rates: {cohort.retention_rates}")
        print(f"      Churn Rates: {cohort.churn_rates}")
        print(f"      Revenue Evolution: {cohort.revenue_evolution}")
        print(f"      LTV Evolution: {cohort.ltv_evolution}")
```

#### Cohort Types by Tier
- **Signup Date Cohorts**: Customer acquisition patterns
- **Plan Type Cohorts**: Subscription plan preferences
- **Customer Segment Cohorts**: Business segment behavior
- **Acquisition Channel Cohorts**: Channel-specific patterns
- **Geographic Region Cohorts**: Regional behavior differences

## Revenue Per User and Tier Distribution

### Overview
Revenue per user by tier analyzes the average revenue generated by customers in different tiers, helping optimize pricing and feature allocation.

### Calculation Method
```python
def calculate_revenue_per_user_by_tier(self, date: datetime = None) -> Dict[str, MetricCalculation]:
    """
    Calculate revenue per user by tier
    
    ARPU = Total Tier Revenue / Number of Customers in Tier
    """
```

### Usage Example
```python
# Calculate revenue per user by tier
revenue_by_tier = analytics.calculate_revenue_per_user_by_tier()

for tier, revenue_metric in revenue_by_tier.items():
    print(f"Tier: {tier}")
    print(f"  Average Revenue Per User: ${revenue_metric.value:.2f}")
    print(f"  Change: {revenue_metric.change_percentage:+.1f}%")
    print(f"  Trend: {revenue_metric.trend}")
    
    # Access detailed metadata
    metadata = revenue_metric.metadata
    print(f"  Customer Count: {metadata['customer_count']}")
    print(f"  Total Revenue: ${metadata['total_revenue']:,.2f}")
    
    # Revenue distribution
    revenue_dist = metadata['revenue_distribution']
    for level, percentage in revenue_dist.items():
        print(f"    {level}: {percentage:.1%}")
    
    # Usage patterns
    usage = metadata['usage_patterns']
    print(f"  Average Sessions/Month: {usage['average_sessions_per_month']}")
    print(f"  Average Session Duration: {usage['average_session_duration']} minutes")
    
    # Feature adoption
    adoption = metadata['feature_adoption']
    for feature, rate in adoption.items():
        print(f"    {feature}: {rate:.1%}")
```

### Revenue Analysis Features

#### Revenue Distribution by Tier
```python
def _get_revenue_distribution_by_tier(self, tier: str, date: datetime) -> Dict[str, float]:
    """
    Get revenue distribution within a tier
    
    Returns:
        {
            'low_revenue': 0.30,
            'medium_revenue': 0.45,
            'high_revenue': 0.25
        }
    """
```

#### Usage Patterns by Tier
```python
def _get_usage_patterns_by_tier(self, tier: str, date: datetime) -> Dict[str, Any]:
    """
    Get usage patterns for a tier
    
    Returns:
        {
            'average_sessions_per_month': 25,
            'average_session_duration': 45,
            'feature_usage_distribution': {
                'core_features': 0.80,
                'advanced_features': 0.60,
                'premium_features': 0.40
            }
        }
    """
```

#### Feature Adoption by Tier
```python
def _get_feature_adoption_by_tier(self, tier: str, date: datetime) -> Dict[str, float]:
    """
    Get feature adoption rates by tier
    
    Returns:
        {
            'feature_a': 0.85,
            'feature_b': 0.70,
            'feature_c': 0.55,
            'feature_d': 0.40,
            'feature_e': 0.25
        }
    """
```

### Tier Distribution Analysis

#### Comprehensive Analysis
```python
def get_tier_distribution_analysis(self, date: datetime = None) -> Dict[str, Any]:
    """
    Get comprehensive tier distribution analysis
    
    - Current vs previous distribution
    - Tier-specific metrics
    - Migration patterns
    - Performance ranking
    - Recommendations
    """
```

#### Usage Example
```python
# Get tier distribution analysis
tier_analysis = analytics.get_tier_distribution_analysis()

print(f"Total Customers: {tier_analysis['total_customers']:,}")

# Current distribution
current_dist = tier_analysis['tier_distribution']
for tier, count in current_dist.items():
    print(f"  {tier}: {count} customers")

# Tier metrics
tier_metrics = tier_analysis['tier_metrics']
for tier, metrics in tier_metrics.items():
    print(f"  {tier.upper()} Tier:")
    print(f"    Growth Rate: {metrics['growth_rate']:.1f}%")
    print(f"    Revenue Contribution: {metrics['revenue_contribution']:.1f}%")
    print(f"    Upgrade Rate: {metrics['upgrade_rate']:.1f}%")
    print(f"    Downgrade Rate: {metrics['downgrade_rate']:.1f}%")

# Performance ranking
ranking = tier_analysis['tier_performance_ranking']
print("Performance Ranking:")
for i, tier in enumerate(ranking, 1):
    print(f"  {i}. {tier}")

# Recommendations
recommendations = tier_analysis['recommendations']
for rec in recommendations:
    print(f"  {rec['priority'].upper()} - {rec['title']}: {rec['description']}")
```

## LTV/CAC Ratio by Channel

### Overview
LTV/CAC ratio by channel measures the relationship between customer lifetime value and acquisition cost for each marketing channel, indicating channel profitability.

### Calculation Method
```python
def calculate_ltv_cac_ratio_by_channel(self, date: datetime = None, period_days: int = 30) -> Dict[str, MetricCalculation]:
    """
    Calculate LTV/CAC ratio by acquisition channel
    
    LTV/CAC Ratio = Customer Lifetime Value / Customer Acquisition Cost
    """
```

### Health Status Classification
- **Excellent (≥3.0)**: Highly profitable channels
- **Good (1.0-3.0)**: Profitable channels with room for improvement
- **Poor (<1.0)**: Unprofitable channels requiring optimization

### Usage Example
```python
# Calculate LTV/CAC ratio by channel
ltv_cac_ratios = analytics.calculate_ltv_cac_ratio_by_channel(period_days=30)

for channel, ratio_metric in ltv_cac_ratios.items():
    print(f"Channel: {channel}")
    print(f"  LTV/CAC Ratio: {ratio_metric.value:.2f}")
    print(f"  Health Status: {ratio_metric.metadata['health_status']}")
    print(f"  CAC: ${ratio_metric.metadata['cac']:.2f}")
    print(f"  CLV: ${ratio_metric.metadata['clv']:.2f}")
    print(f"  Payback Period: {ratio_metric.metadata['payback_period']:.1f} months")
    print(f"  Channel Efficiency: {ratio_metric.metadata['channel_efficiency']:.1%}")
    
    # Optimization opportunities
    opportunities = ratio_metric.metadata['optimization_opportunities']
    for opportunity in opportunities:
        print(f"    - {opportunity}")
```

### Channel Optimization Features

#### Payback Period Calculation
```python
def _calculate_payback_period(self, cac: float, clv: float) -> float:
    """
    Calculate payback period in months
    
    Payback Period = CAC / Monthly Revenue
    """
```

#### Channel Efficiency Scoring
```python
def _calculate_channel_efficiency(self, channel: str, date: datetime) -> float:
    """
    Calculate channel efficiency score
    
    - Conversion rate optimization
    - Cost efficiency
    - Quality of acquired customers
    - Long-term value generation
    """
```

#### Optimization Opportunities
```python
def _identify_channel_optimization_opportunities(self, channel: str, ltv_cac_ratio: float) -> List[str]:
    """
    Identify optimization opportunities for a channel
    
    Based on LTV/CAC ratio:
    - < 1.0: Focus on cost reduction and conversion improvement
    - 1.0-3.0: Scale successful campaigns and improve retention
    - ≥ 3.0: Increase budget allocation and expand reach
    """
```

## Comprehensive Key Metrics Report

### Overview
The comprehensive key metrics report combines all metrics into a single analysis, providing a complete view of business performance and actionable insights.

### Report Generation
```python
def generate_comprehensive_key_metrics_report(self, date: datetime = None) -> Dict[str, Any]:
    """
    Generate comprehensive key metrics report
    
    - All key metrics by channel and tier
    - Cohort analysis results
    - Performance insights
    - Strategic recommendations
    """
```

### Report Structure
```python
report = {
    'date': '2024-01-15T00:00:00Z',
    'metrics': {
        'cac_by_channel': {...},
        'clv_by_tier': {...},
        'churn_by_tier': {...},
        'revenue_by_tier': {...},
        'ltv_cac_ratios': {...}
    },
    'cohort_analysis': {...},
    'tier_distribution': {...},
    'insights': [...],
    'recommendations': [...],
    'performance_summary': {...}
}
```

### Usage Example
```python
# Generate comprehensive report
report = analytics.generate_comprehensive_key_metrics_report()

print(f"Report Date: {report['date']}")

# Metrics summary
metrics = report['metrics']
print(f"CAC by Channel: {len(metrics['cac_by_channel'])} channels")
print(f"CLV by Tier: {len(metrics['clv_by_tier'])} tiers")
print(f"Churn by Tier: {len(metrics['churn_by_tier'])} tiers")
print(f"Revenue by Tier: {len(metrics['revenue_by_tier'])} tiers")
print(f"LTV/CAC Ratios: {len(metrics['ltv_cac_ratios'])} channels")

# Insights
insights = report['insights']
for insight in insights:
    print(f"{insight['type'].upper()} - {insight['title']}: {insight['description']}")

# Recommendations
recommendations = report['recommendations']
for rec in recommendations:
    print(f"{rec['priority'].upper()} - {rec['title']}: {rec['description']}")
    for action in rec['actions']:
        print(f"  - {action}")
```

## Configuration and Performance

### Analytics Configuration
```python
@dataclass
class AnalyticsConfig:
    """Configuration for key metrics analytics"""
    # Time periods
    default_period_days: int = 90
    cohort_analysis_periods: int = 12
    
    # Churn analysis
    churn_definition_days: int = 30
    churn_grace_period_days: int = 7
    
    # Cohort analysis
    cohort_retention_periods: int = 12
    cohort_minimum_size: int = 10
    
    # Performance
    cache_results: bool = True
    cache_ttl_hours: int = 24
    batch_processing: bool = True
    batch_size: int = 1000
```

### Performance Optimization
- **Caching**: TTL-based result caching for frequently accessed metrics
- **Batch Processing**: Efficient handling of large datasets
- **Database Optimization**: Optimized queries with proper indexing
- **Memory Management**: Efficient data structures and cleanup

## Integration Examples

### Dashboard Integration
```python
def get_dashboard_key_metrics():
    """Get key metrics for dashboard display"""
    analytics = SubscriptionAnalytics(db, config)
    
    dashboard_data = {
        'cac_by_channel': analytics.calculate_customer_acquisition_cost_by_channel(),
        'clv_by_tier': analytics.calculate_customer_lifetime_value_by_tier(),
        'churn_by_tier': analytics.calculate_churn_rate_by_tier(),
        'revenue_by_tier': analytics.calculate_revenue_per_user_by_tier(),
        'ltv_cac_ratios': analytics.calculate_ltv_cac_ratio_by_channel(),
        'tier_distribution': analytics.get_tier_distribution_analysis()
    }
    
    return dashboard_data
```

### Alert System Integration
```python
def check_key_metrics_alerts():
    """Check conditions for key metrics alerts"""
    analytics = SubscriptionAnalytics(db, config)
    
    alerts = []
    
    # Check CAC by channel
    cac_by_channel = analytics.calculate_customer_acquisition_cost_by_channel()
    for channel, cac_metric in cac_by_channel.items():
        if cac_metric.value > 200:  # High CAC threshold
            alerts.append({
                'type': 'warning',
                'metric': 'cac',
                'channel': channel,
                'value': cac_metric.value,
                'threshold': 200,
                'message': f'High CAC in {channel} channel'
            })
    
    # Check churn by tier
    churn_by_tier = analytics.calculate_churn_rate_by_tier()
    for tier, churn_metric in churn_by_tier.items():
        if churn_metric.value > 5:  # High churn threshold
            alerts.append({
                'type': 'critical',
                'metric': 'churn',
                'tier': tier,
                'value': churn_metric.value,
                'threshold': 5,
                'message': f'High churn rate in {tier} tier'
            })
    
    # Check LTV/CAC ratios
    ltv_cac_ratios = analytics.calculate_ltv_cac_ratio_by_channel()
    for channel, ratio_metric in ltv_cac_ratios.items():
        if ratio_metric.value < 1.0:  # Poor ratio threshold
            alerts.append({
                'type': 'critical',
                'metric': 'ltv_cac_ratio',
                'channel': channel,
                'value': ratio_metric.value,
                'threshold': 1.0,
                'message': f'Poor LTV/CAC ratio in {channel} channel'
            })
    
    return alerts
```

### API Integration
```python
def api_get_key_metrics(channel: str = None, tier: str = None, date: str = None):
    """API endpoint for key metrics"""
    analytics = SubscriptionAnalytics(db, config)
    
    if date:
        report_date = datetime.fromisoformat(date)
    else:
        report_date = datetime.now(timezone.utc)
    
    # Get specific metrics based on parameters
    if channel:
        cac_data = analytics.calculate_customer_acquisition_cost_by_channel(report_date)
        ltv_cac_data = analytics.calculate_ltv_cac_ratio_by_channel(report_date)
        return {
            'success': True,
            'channel': channel,
            'cac': cac_data.get(channel),
            'ltv_cac_ratio': ltv_cac_data.get(channel)
        }
    
    if tier:
        clv_data = analytics.calculate_customer_lifetime_value_by_tier(report_date)
        churn_data = analytics.calculate_churn_rate_by_tier(report_date)
        revenue_data = analytics.calculate_revenue_per_user_by_tier(report_date)
        return {
            'success': True,
            'tier': tier,
            'clv': clv_data.get(tier),
            'churn_rate': churn_data.get(tier),
            'revenue_per_user': revenue_data.get(tier)
        }
    
    # Return comprehensive report
    report = analytics.generate_comprehensive_key_metrics_report(report_date)
    return {
        'success': True,
        'data': report,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }
```

## Best Practices

### Data Quality
1. **Regular Validation**: Ensure data accuracy and completeness
2. **Consistent Definitions**: Use standardized metric definitions
3. **Data Retention**: Maintain historical data for trend analysis
4. **Real-time Updates**: Update metrics in real-time for accuracy

### Performance Optimization
1. **Caching**: Cache frequently accessed metrics
2. **Batch Processing**: Process large datasets in batches
3. **Indexing**: Optimize database queries with proper indexing
4. **Compression**: Compress historical data for storage efficiency

### Reporting
1. **Regular Reports**: Generate reports on a consistent schedule
2. **Customization**: Allow customization of report content and format
3. **Distribution**: Automate report distribution to stakeholders
4. **Archiving**: Archive historical reports for compliance

### Actionability
1. **Clear Insights**: Provide clear, actionable insights
2. **Specific Recommendations**: Generate specific, implementable recommendations
3. **Priority Ranking**: Rank recommendations by impact and effort
4. **Follow-up Tracking**: Track implementation and results of recommendations

## Troubleshooting

### Common Issues

#### Data Accuracy Issues
```python
def validate_key_metrics_data():
    """Validate data quality for key metrics"""
    analytics = SubscriptionAnalytics(db, config)
    
    # Check for missing data
    missing_data = analytics._check_missing_data()
    if missing_data:
        print(f"Missing data detected: {missing_data}")
    
    # Check for data consistency
    consistency_issues = analytics._check_data_consistency()
    if consistency_issues:
        print(f"Data consistency issues: {consistency_issues}")
    
    # Check for outliers
    outliers = analytics._detect_outliers()
    if outliers:
        print(f"Outliers detected: {outliers}")
```

#### Performance Issues
```python
def optimize_key_metrics_performance():
    """Optimize key metrics performance"""
    config = AnalyticsConfig(
        cache_results=True,
        cache_ttl_hours=24,
        batch_processing=True,
        batch_size=1000
    )
    
    analytics = SubscriptionAnalytics(db, config)
    
    # Monitor performance
    performance_metrics = analytics._get_performance_metrics()
    print(f"Average query time: {performance_metrics['avg_query_time']}ms")
    print(f"Cache hit rate: {performance_metrics['cache_hit_rate']:.1%}")
    print(f"Memory usage: {performance_metrics['memory_usage']}MB")
```

#### Metric Calculation Issues
```python
def debug_metric_calculations():
    """Debug metric calculation issues"""
    analytics = SubscriptionAnalytics(db, config)
    
    # Test individual metric calculations
    try:
        cac_result = analytics.calculate_customer_acquisition_cost_by_channel()
        print(f"CAC calculation: {'Success' if cac_result else 'Failed'}")
    except Exception as e:
        print(f"CAC calculation error: {e}")
    
    try:
        clv_result = analytics.calculate_customer_lifetime_value_by_tier()
        print(f"CLV calculation: {'Success' if clv_result else 'Failed'}")
    except Exception as e:
        print(f"CLV calculation error: {e}")
    
    try:
        churn_result = analytics.calculate_churn_rate_by_tier()
        print(f"Churn calculation: {'Success' if churn_result else 'Failed'}")
    except Exception as e:
        print(f"Churn calculation error: {e}")
```

## Conclusion

The Key Metrics system provides comprehensive analytics for customer acquisition, lifetime value, churn analysis, and revenue optimization. Key features include:

- **Customer Acquisition Cost (CAC) by Channel**: Track and optimize acquisition costs
- **Customer Lifetime Value (CLV) by Tier**: Monitor customer value by tier
- **Churn Rate by Tier and Cohort Analysis**: Understand churn patterns
- **Revenue Per User and Tier Distribution**: Analyze revenue optimization
- **LTV/CAC Ratio by Channel**: Evaluate channel profitability
- **Comprehensive Reporting**: Generate actionable insights and recommendations

This system enables data-driven decision making, channel optimization, tier management, and strategic planning for sustainable business growth. 