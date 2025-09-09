#!/usr/bin/env python3
"""
Meme Analytics Reports and Sample Queries

This module provides pre-built reports and sample queries that non-technical users
can easily understand and use for analyzing meme performance.

Features:
- Simple, non-technical language reports
- Pre-built queries for common analysis needs
- Automated report generation
- Sample data for testing
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional
import json
from pathlib import Path
import logging

from meme_analytics_system import MemeAnalyticsSystem

logger = logging.getLogger(__name__)

class MemeAnalyticsReports:
    """Class for generating user-friendly analytics reports"""
    
    def __init__(self, db_path: str = "mingus_memes.db"):
        self.analytics = MemeAnalyticsSystem(db_path)
        self.db_path = db_path
    
    def generate_executive_summary(self, days: int = 30) -> str:
        """Generate an executive summary in plain English"""
        try:
            metrics = self.analytics.get_performance_metrics(days)
            category_data = self.analytics.get_category_performance(days)
            alerts = self.analytics.check_alerts()
            
            # Calculate key insights
            total_views = metrics.get('total_views', 0)
            skip_rate = metrics.get('skip_rate', 0)
            continue_rate = metrics.get('continue_rate', 0)
            avg_time = metrics.get('avg_time_spent', 0)
            
            # Find best and worst performing categories
            best_category = None
            worst_category = None
            if not category_data.empty:
                best_category = category_data.loc[category_data['continue_rate'].idxmax()]
                worst_category = category_data.loc[category_data['skip_rate'].idxmax()]
            
            summary = f"""
# 📊 Meme Analytics Executive Summary
**Period:** Last {days} days | **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## 🎯 Key Performance Indicators

### Overall Performance
- **Total Meme Views:** {total_views:,} views
- **User Engagement:** {continue_rate:.1f}% of users continue to the app after seeing a meme
- **Skip Rate:** {skip_rate:.1f}% of users skip the meme feature
- **Average Viewing Time:** {avg_time:.1f} seconds per meme
- **Active Users:** {metrics.get('unique_users', 0):,} unique users

### What This Means:
"""
            
            # Add insights based on performance
            if continue_rate > 60:
                summary += "✅ **Excellent Engagement:** Most users find the memes engaging and continue to use the app.\n"
            elif continue_rate > 40:
                summary += "⚠️ **Moderate Engagement:** About half of users continue after seeing memes. Consider improving content relevance.\n"
            else:
                summary += "❌ **Low Engagement:** Most users skip the meme feature. Immediate attention needed to improve content.\n"
            
            if skip_rate > 70:
                summary += "🚨 **High Skip Rate:** Users are skipping memes too frequently. Review content quality and timing.\n"
            elif skip_rate > 50:
                summary += "⚠️ **Moderate Skip Rate:** Some users skip memes. Monitor trends and consider content adjustments.\n"
            else:
                summary += "✅ **Low Skip Rate:** Users are engaging with memes well.\n"
            
            if avg_time < 5:
                summary += "⏱️ **Quick Views:** Users spend little time viewing memes. Consider if content is engaging enough.\n"
            elif avg_time > 15:
                summary += "⏱️ **Long Views:** Users spend significant time with memes. Great engagement!\n"
            
            # Category performance
            if best_category is not None:
                summary += f"""
## 🏆 Best Performing Category
**{best_category['category'].title()}** is your star performer:
- {best_category['total_views']:,} total views
- {best_category['continue_rate']:.1f}% continue rate
- {best_category['skip_rate']:.1f}% skip rate
- Users spend {best_category['avg_time_spent']:.1f} seconds on average

**Recommendation:** Create more content similar to this category.
"""
            
            if worst_category is not None and worst_category['skip_rate'] > 60:
                summary += f"""
## ⚠️ Category Needing Attention
**{worst_category['category'].title()}** has room for improvement:
- {worst_category['total_views']:,} total views
- {worst_category['continue_rate']:.1f}% continue rate
- {worst_category['skip_rate']:.1f}% skip rate (high!)

**Recommendation:** Review and improve content in this category.
"""
            
            # Alerts section
            if alerts:
                summary += f"""
## 🚨 Active Alerts ({len(alerts)})
"""
                for alert in alerts:
                    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(alert.get('severity', 'low'), "⚪")
                    summary += f"- {severity_emoji} **{alert.get('title', 'Unknown Alert')}**\n"
                    summary += f"  {alert.get('description', 'No description available')}\n"
            else:
                summary += """
## ✅ No Active Alerts
All systems are performing within normal parameters.
"""
            
            # Recommendations
            summary += """
## 💡 Action Items
"""
            
            if skip_rate > 60:
                summary += "- **High Priority:** Reduce skip rate by improving meme relevance and quality\n"
            
            if best_category is not None and worst_category is not None:
                if worst_category['skip_rate'] - best_category['skip_rate'] > 30:
                    summary += "- **Content Strategy:** Study successful categories and apply learnings to underperforming ones\n"
            
            if avg_time < 5:
                summary += "- **Engagement:** Create more engaging content to increase viewing time\n"
            
            if len(alerts) > 0:
                summary += "- **Monitoring:** Address active alerts to maintain user experience\n"
            
            if continue_rate > 50 and skip_rate < 40:
                summary += "- **Success:** Current strategy is working well! Consider expanding successful content\n"
            
            summary += f"""
---
*This report was automatically generated by the Mingus Analytics System*
*For detailed technical analysis, contact your development team*
"""
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return f"Error generating report: {e}"
    
    def generate_category_analysis(self, days: int = 30) -> str:
        """Generate detailed category analysis"""
        try:
            category_data = self.analytics.get_category_performance(days)
            
            if category_data.empty:
                return "No category data available for the specified period."
            
            report = f"""
# 📈 Category Performance Analysis
**Period:** Last {days} days | **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## 📊 Category Rankings

### By Total Views (Popularity)
"""
            
            # Sort by views
            by_views = category_data.sort_values('total_views', ascending=False)
            for i, (_, row) in enumerate(by_views.iterrows(), 1):
                report += f"{i}. **{row['category'].title()}** - {row['total_views']:,} views\n"
            
            report += "\n### By Continue Rate (Engagement)\n"
            
            # Sort by continue rate
            by_continue = category_data.sort_values('continue_rate', ascending=False)
            for i, (_, row) in enumerate(by_continue.iterrows(), 1):
                report += f"{i}. **{row['category'].title()}** - {row['continue_rate']:.1f}% continue rate\n"
            
            report += "\n### By Skip Rate (Areas for Improvement)\n"
            
            # Sort by skip rate (ascending = best first)
            by_skip = category_data.sort_values('skip_rate', ascending=True)
            for i, (_, row) in enumerate(by_skip.iterrows(), 1):
                report += f"{i}. **{row['category'].title()}** - {row['skip_rate']:.1f}% skip rate\n"
            
            # Detailed analysis for each category
            report += "\n## 🔍 Detailed Category Analysis\n"
            
            for _, row in category_data.iterrows():
                category = row['category'].title()
                views = row['total_views']
                continue_rate = row['continue_rate']
                skip_rate = row['skip_rate']
                avg_time = row['avg_time_spent']
                unique_users = row['unique_users']
                
                report += f"""
### {category}
- **Total Views:** {views:,}
- **Unique Users:** {unique_users:,}
- **Continue Rate:** {continue_rate:.1f}%
- **Skip Rate:** {skip_rate:.1f}%
- **Average Viewing Time:** {avg_time:.1f} seconds

**Performance Assessment:** """
                
                if continue_rate > 60 and skip_rate < 30:
                    report += "🌟 **Excellent** - High engagement, low skip rate\n"
                elif continue_rate > 40 and skip_rate < 50:
                    report += "✅ **Good** - Solid performance with room for improvement\n"
                elif skip_rate > 60:
                    report += "⚠️ **Needs Attention** - High skip rate indicates content issues\n"
                else:
                    report += "📊 **Average** - Typical performance, monitor trends\n"
                
                # Specific recommendations
                if skip_rate > 70:
                    report += "   - **Action:** Review and refresh content in this category\n"
                elif continue_rate > 60:
                    report += "   - **Action:** Create more content in this successful category\n"
                elif avg_time < 5:
                    report += "   - **Action:** Improve content engagement to increase viewing time\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating category analysis: {e}")
            return f"Error generating category analysis: {e}"
    
    def generate_user_behavior_report(self, days: int = 30) -> str:
        """Generate user behavior analysis report"""
        try:
            retention_data = self.analytics.get_user_retention_analysis(days)
            metrics = self.analytics.get_performance_metrics(days)
            
            report = f"""
# 👥 User Behavior Analysis
**Period:** Last {days} days | **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## 📊 User Engagement Overview
- **Total Users:** {metrics.get('unique_users', 0):,}
- **Total Sessions:** {metrics.get('total_sessions', 0):,}
- **Average Interactions per User:** {retention_data.get('avg_interactions', 0):.1f}
- **Average Active Days:** {retention_data.get('avg_active_days', 0):.1f}
- **Average Days Since First Use:** {retention_data.get('avg_days_since_first_use', 0):.1f}

## 🎯 User Behavior Insights
"""
            
            avg_interactions = retention_data.get('avg_interactions', 0)
            avg_active_days = retention_data.get('avg_active_days', 0)
            avg_days_since_first = retention_data.get('avg_days_since_first_use', 0)
            
            # Analyze user behavior patterns
            if avg_interactions > 10:
                report += "✅ **High Engagement:** Users interact with memes frequently, indicating strong feature adoption\n"
            elif avg_interactions > 5:
                report += "📊 **Moderate Engagement:** Users interact with memes regularly, good feature usage\n"
            else:
                report += "⚠️ **Low Engagement:** Users interact with memes infrequently, consider improving feature visibility\n"
            
            if avg_active_days > 7:
                report += "✅ **Consistent Usage:** Users engage with memes across multiple days, showing habit formation\n"
            elif avg_active_days > 3:
                report += "📊 **Regular Usage:** Users engage with memes on several days, good retention\n"
            else:
                report += "⚠️ **Limited Usage:** Users engage with memes on few days, consider improving retention\n"
            
            if avg_days_since_first > 14:
                report += "✅ **Long-term Users:** Many users have been using the feature for weeks, indicating good retention\n"
            elif avg_days_since_first > 7:
                report += "📊 **Established Users:** Users have been using the feature for about a week, good early retention\n"
            else:
                report += "📈 **New Users:** Many users are new to the feature, focus on onboarding and engagement\n"
            
            # Session analysis
            sessions_per_user = metrics.get('total_sessions', 0) / max(metrics.get('unique_users', 1), 1)
            if sessions_per_user > 3:
                report += "✅ **Multiple Sessions:** Users return multiple times, indicating feature value\n"
            elif sessions_per_user > 1.5:
                report += "📊 **Regular Sessions:** Users have multiple sessions, good engagement\n"
            else:
                report += "⚠️ **Single Sessions:** Most users have only one session, consider improving return engagement\n"
            
            # Recommendations based on behavior
            report += """
## 💡 User Behavior Recommendations
"""
            
            if avg_interactions < 5:
                report += "- **Increase Engagement:** Make memes more prominent in the user journey\n"
            
            if avg_active_days < 3:
                report += "- **Improve Retention:** Consider daily or weekly meme features to increase usage frequency\n"
            
            if sessions_per_user < 2:
                report += "- **Encourage Return Visits:** Add features that encourage users to come back for more memes\n"
            
            if avg_days_since_first < 7:
                report += "- **Onboarding:** Focus on helping new users understand the value of the meme feature\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating user behavior report: {e}")
            return f"Error generating user behavior report: {e}"
    
    def generate_weekly_trend_report(self, weeks: int = 4) -> str:
        """Generate weekly trend analysis"""
        try:
            # Get daily data for the specified number of weeks
            days = weeks * 7
            daily_data = self.analytics.get_daily_engagement_rates(days)
            
            if daily_data.empty:
                return "No daily data available for trend analysis."
            
            # Convert to weekly data
            daily_data['date'] = pd.to_datetime(daily_data['date'])
            daily_data['week'] = daily_data['date'].dt.isocalendar().week
            daily_data['year'] = daily_data['date'].dt.isocalendar().year
            daily_data['week_key'] = daily_data['year'].astype(str) + '-W' + daily_data['week'].astype(str)
            
            weekly_data = daily_data.groupby('week_key').agg({
                'total_views': 'sum',
                'total_continues': 'sum',
                'total_skips': 'sum',
                'unique_users': 'sum',
                'avg_time_spent': 'mean',
                'skip_rate': 'mean',
                'continue_rate': 'mean',
                'engagement_rate': 'mean'
            }).reset_index()
            
            report = f"""
# 📈 Weekly Trend Analysis
**Period:** Last {weeks} weeks | **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

## 📊 Weekly Performance Summary
"""
            
            for _, row in weekly_data.iterrows():
                week = row['week_key']
                views = row['total_views']
                continues = row['total_continues']
                skips = row['total_skips']
                users = row['unique_users']
                avg_time = row['avg_time_spent']
                skip_rate = row['skip_rate']
                continue_rate = row['continue_rate']
                
                report += f"""
### Week {week}
- **Total Views:** {views:,}
- **Unique Users:** {users:,}
- **Continue Rate:** {continue_rate:.1f}%
- **Skip Rate:** {skip_rate:.1f}%
- **Average Time Spent:** {avg_time:.1f} seconds
"""
            
            # Trend analysis
            if len(weekly_data) >= 2:
                latest_week = weekly_data.iloc[-1]
                previous_week = weekly_data.iloc[-2]
                
                views_change = latest_week['total_views'] - previous_week['total_views']
                continue_rate_change = latest_week['continue_rate'] - previous_week['continue_rate']
                skip_rate_change = latest_week['skip_rate'] - previous_week['skip_rate']
                
                report += """
## 📈 Week-over-Week Changes
"""
                
                if views_change > 0:
                    report += f"📈 **Views:** Increased by {views_change:,} ({views_change/previous_week['total_views']*100:.1f}%)\n"
                elif views_change < 0:
                    report += f"📉 **Views:** Decreased by {abs(views_change):,} ({abs(views_change)/previous_week['total_views']*100:.1f}%)\n"
                else:
                    report += "➡️ **Views:** No change\n"
                
                if continue_rate_change > 0:
                    report += f"📈 **Continue Rate:** Improved by {continue_rate_change:.1f} percentage points\n"
                elif continue_rate_change < 0:
                    report += f"📉 **Continue Rate:** Declined by {abs(continue_rate_change):.1f} percentage points\n"
                else:
                    report += "➡️ **Continue Rate:** No change\n"
                
                if skip_rate_change > 0:
                    report += f"📉 **Skip Rate:** Increased by {skip_rate_change:.1f} percentage points (concerning)\n"
                elif skip_rate_change < 0:
                    report += f"📈 **Skip Rate:** Decreased by {abs(skip_rate_change):.1f} percentage points (good)\n"
                else:
                    report += "➡️ **Skip Rate:** No change\n"
            
            # Overall trend recommendations
            report += """
## 💡 Trend-Based Recommendations
"""
            
            if len(weekly_data) >= 3:
                # Calculate overall trend
                first_week = weekly_data.iloc[0]
                last_week = weekly_data.iloc[-1]
                
                overall_views_trend = (last_week['total_views'] - first_week['total_views']) / first_week['total_views'] * 100
                overall_continue_trend = last_week['continue_rate'] - first_week['continue_rate']
                overall_skip_trend = last_week['skip_rate'] - first_week['skip_rate']
                
                if overall_views_trend > 20:
                    report += "- **Growing Popularity:** Views are increasing significantly. Consider scaling content production.\n"
                elif overall_views_trend < -20:
                    report += "- **Declining Interest:** Views are decreasing. Review content strategy and user engagement.\n"
                
                if overall_continue_trend > 5:
                    report += "- **Improving Engagement:** Continue rates are trending up. Keep current strategy.\n"
                elif overall_continue_trend < -5:
                    report += "- **Declining Engagement:** Continue rates are trending down. Immediate action needed.\n"
                
                if overall_skip_trend > 10:
                    report += "- **Increasing Frustration:** Skip rates are trending up. Review content quality and relevance.\n"
                elif overall_skip_trend < -10:
                    report += "- **Improving Content:** Skip rates are trending down. Content improvements are working.\n"
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating weekly trend report: {e}")
            return f"Error generating weekly trend report: {e}"
    
    def generate_sample_queries_guide(self) -> str:
        """Generate a guide with sample queries for non-technical users"""
        
        guide = """
# 📋 Meme Analytics - Sample Queries Guide

This guide provides simple, non-technical explanations of common analytics queries you can use to understand your meme performance.

## 🎯 Common Questions and How to Answer Them

### 1. "How popular are our memes overall?"
**What to look for:** Total views, unique users, and sessions
**What it means:** Higher numbers indicate more people are seeing your memes
**Good indicators:** 
- Increasing view counts over time
- High number of unique users
- Multiple sessions per user

### 2. "Are people actually engaging with our memes?"
**What to look for:** Continue rate vs. skip rate
**What it means:** 
- Continue rate = % of people who proceed to use the app after seeing a meme
- Skip rate = % of people who skip the meme feature
**Good indicators:**
- Continue rate > 50%
- Skip rate < 40%
- Continue rate increasing over time

### 3. "Which meme categories work best?"
**What to look for:** Category performance comparison
**What it means:** Some topics resonate more with your users than others
**Good indicators:**
- High continue rates for specific categories
- Low skip rates for specific categories
- Consistent performance across time periods

### 4. "How long do people spend looking at memes?"
**What to look for:** Average time spent viewing
**What it means:** Longer times suggest more engaging content
**Good indicators:**
- 5-15 seconds average viewing time
- Increasing viewing time over time
- Consistent viewing time across categories

### 5. "Are we retaining users with memes?"
**What to look for:** User retention metrics
**What it means:** Do people come back to use the meme feature?
**Good indicators:**
- Multiple interactions per user
- Users active across multiple days
- Increasing user retention over time

## 📊 Key Metrics Explained (Simple Terms)

### Views
- **What it is:** How many times memes were displayed
- **Why it matters:** Shows reach and visibility
- **What's good:** Steady or increasing numbers

### Continue Rate
- **What it is:** Percentage of people who continue to the app after seeing a meme
- **Why it matters:** Shows if memes are helping user engagement
- **What's good:** Above 50%

### Skip Rate
- **What it is:** Percentage of people who skip the meme feature
- **Why it matters:** High skip rates indicate content issues
- **What's good:** Below 40%

### Time Spent
- **What it is:** How long people look at memes
- **Why it matters:** Shows content engagement level
- **What's good:** 5-15 seconds average

### Unique Users
- **What it is:** Number of different people using the feature
- **Why it matters:** Shows feature adoption
- **What's good:** Growing over time

## 🚨 Warning Signs to Watch For

### Red Flags (Immediate Attention Needed)
- Skip rate > 70%
- Continue rate < 30%
- Average viewing time < 3 seconds
- Declining user numbers
- High error rates

### Yellow Flags (Monitor Closely)
- Skip rate 50-70%
- Continue rate 30-50%
- Average viewing time 3-5 seconds
- Flat or slowly declining metrics

### Green Flags (Good Performance)
- Skip rate < 40%
- Continue rate > 50%
- Average viewing time 5-15 seconds
- Growing user numbers
- Low error rates

## 💡 Action Items Based on Metrics

### If Skip Rate is High (>60%)
1. Review meme content quality
2. Check if memes are relevant to your audience
3. Consider reducing meme frequency
4. Survey users about their preferences

### If Continue Rate is Low (<40%)
1. Make memes more engaging
2. Ensure memes add value to user experience
3. Test different meme styles and formats
4. Improve timing of meme display

### If Viewing Time is Short (<5 seconds)
1. Create more compelling content
2. Improve meme visual design
3. Test different caption styles
4. Consider interactive elements

### If User Numbers are Declining
1. Check for technical issues
2. Review user onboarding process
3. Ensure memes are visible in user flow
4. Gather user feedback

## 📈 Success Metrics to Track

### Daily Monitoring
- Total views
- Skip rate
- Continue rate
- Error count

### Weekly Review
- User retention
- Category performance
- Trend analysis
- Alert status

### Monthly Analysis
- Overall performance trends
- User behavior patterns
- Content effectiveness
- Strategic recommendations

## 🔧 How to Use This Information

### For Product Managers
- Use metrics to guide content strategy
- Identify successful categories for expansion
- Monitor user satisfaction indicators
- Plan feature improvements

### For Content Creators
- Focus on high-performing categories
- Improve content in low-performing areas
- Test different styles and formats
- Monitor engagement metrics

### For Business Stakeholders
- Track user engagement trends
- Monitor feature adoption
- Identify growth opportunities
- Measure ROI of meme feature

## 📞 When to Get Help

Contact your development team if you see:
- Sudden dramatic changes in metrics
- Technical errors or system issues
- Need for custom analysis
- Questions about data interpretation

Remember: Analytics are tools to help you make better decisions. Focus on trends and patterns rather than individual data points.
"""
        
        return guide
    
    def save_report(self, report: str, filename: str) -> bool:
        """Save a report to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False
    
    def generate_all_reports(self, days: int = 30, output_dir: str = "analytics_reports") -> Dict[str, bool]:
        """Generate all reports and save them"""
        try:
            Path(output_dir).mkdir(exist_ok=True)
            
            results = {}
            
            # Generate executive summary
            exec_summary = self.generate_executive_summary(days)
            results['executive_summary'] = self.save_report(
                exec_summary, 
                f"{output_dir}/executive_summary_{days}days_{datetime.now().strftime('%Y%m%d')}.md"
            )
            
            # Generate category analysis
            category_analysis = self.generate_category_analysis(days)
            results['category_analysis'] = self.save_report(
                category_analysis,
                f"{output_dir}/category_analysis_{days}days_{datetime.now().strftime('%Y%m%d')}.md"
            )
            
            # Generate user behavior report
            user_behavior = self.generate_user_behavior_report(days)
            results['user_behavior'] = self.save_report(
                user_behavior,
                f"{output_dir}/user_behavior_{days}days_{datetime.now().strftime('%Y%m%d')}.md"
            )
            
            # Generate weekly trend report
            weekly_trends = self.generate_weekly_trend_report(4)
            results['weekly_trends'] = self.save_report(
                weekly_trends,
                f"{output_dir}/weekly_trends_{datetime.now().strftime('%Y%m%d')}.md"
            )
            
            # Generate sample queries guide
            queries_guide = self.generate_sample_queries_guide()
            results['queries_guide'] = self.save_report(
                queries_guide,
                f"{output_dir}/sample_queries_guide.md"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating all reports: {e}")
            return {}

def main():
    """Main function for testing the reports system"""
    try:
        # Initialize reports system
        reports = MemeAnalyticsReports()
        
        # Generate all reports
        print("Generating analytics reports...")
        results = reports.generate_all_reports(30, "analytics_reports")
        
        print("\nReport generation results:")
        for report_type, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"- {report_type}: {status}")
        
        # Generate a quick executive summary for console
        print("\n" + "="*50)
        print("EXECUTIVE SUMMARY PREVIEW")
        print("="*50)
        summary = reports.generate_executive_summary(30)
        print(summary[:1000] + "..." if len(summary) > 1000 else summary)
        
        print(f"\nAll reports saved to 'analytics_reports/' directory")
        
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()
