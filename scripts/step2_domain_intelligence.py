#!/usr/bin/env python3
"""
Step 2: Domain Intelligence Analysis for Mingus Financial Wellness App

This script analyzes domain data from Step 1 and provides comprehensive intelligence
for the Step 3 domain approval interface. It focuses on cultural relevance for
African American professionals aged 25-35 earning $40K-$100K.

Author: Mingus Development Team
Date: 2025-01-15
"""

import pandas as pd
import numpy as np
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter, defaultdict
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/step2_intelligence.log'),
        logging.StreamHandler()
    ]
)

class DomainIntelligenceAnalyzer:
    """Comprehensive domain intelligence analysis for Mingus financial wellness app."""
    
    def __init__(self):
        self.data_dir = Path('data')
        self.reports_dir = Path('reports')
        self.reports_dir.mkdir(exist_ok=True)
        
        # Cultural relevance keywords for African American professionals
        self.cultural_keywords = {
            'identity': [
                'black', 'african american', 'african-american', 'black professionals',
                'black entrepreneurs', 'black business', 'black community',
                'diversity', 'inclusion', 'representation', 'equity'
            ],
            'career': [
                'corporate culture', 'workplace navigation', 'career advancement',
                'professional development', 'leadership', 'executive',
                'corporate ladder', 'glass ceiling', 'workplace discrimination',
                'salary negotiation', 'income optimization'
            ],
            'financial': [
                'generational wealth', 'community investment', 'financial equity',
                'systemic barriers', 'wealth gap', 'financial literacy',
                'student loan debt', 'credit repair', 'homeownership',
                'investment strategies', 'retirement planning'
            ],
            'challenges': [
                'systemic racism', 'discrimination', 'bias', 'barriers',
                'inequality', 'disparities', 'access', 'opportunity',
                'representation', 'inclusion', 'diversity'
            ]
        }
        
        # Domain quality indicators
        self.quality_indicators = {
            'high_value': [
                'financial', 'education', 'career', 'professional', 'business',
                'investment', 'wealth', 'money', 'finance', 'economics',
                'news', 'media', 'journalism', 'research', 'university',
                'college', 'institute', 'foundation', 'organization'
            ],
            'medium_value': [
                'blog', 'article', 'guide', 'tips', 'advice', 'strategy',
                'platform', 'community', 'network', 'forum', 'discussion'
            ],
            'low_value': [
                'shop', 'store', 'buy', 'sale', 'deal', 'discount', 'offer',
                'product', 'service', 'affiliate', 'referral', 'tracking',
                'analytics', 'pixel', 'beacon', 'cookie', 'advertisement'
            ],
            'suspicious': [
                'bit.ly', 'tinyurl', 'goo.gl', 't.co', 'shortened',
                'track', 'pixel', 'beacon', 'analytics', 'monitoring',
                'random', 'gibberish', 'suspicious'
            ]
        }
        
        # URL pattern analysis
        self.url_patterns = {
            'article': [
                r'/article/', r'/post/', r'/blog/', r'/story/', r'/news/',
                r'/analysis/', r'/opinion/', r'/commentary/', r'/feature/',
                r'/\d{4}/\d{2}/', r'/\d{4}-\d{2}-\d{2}/', r'/page/\d+/'
            ],
            'product': [
                r'/product/', r'/shop/', r'/store/', r'/buy/', r'/purchase/',
                r'/cart/', r'/checkout/', r'/order/', r'/price/', r'/sale/',
                r'/deal/', r'/offer/', r'/discount/'
            ],
            'tracking': [
                r'utm_source=', r'utm_medium=', r'utm_campaign=', r'utm_term=',
                r'utm_content=', r'gclid=', r'fbclid=', r'msclkid=',
                r'track/', r'pixel/', r'beacon/', r'analytics/'
            ],
            'newsletter': [
                r'/newsletter/', r'/email/', r'/subscribe/', r'/signup/',
                r'/optin/', r'/lead/', r'/capture/', r'/form/'
            ]
        }
        
        self.results = {
            'summary': {},
            'domains': {},
            'recommendations': {},
            'cultural_analysis': {},
            'bulk_actions': {}
        }

    def load_step1_data(self) -> Dict[str, Any]:
        """Load all data files from Step 1."""
        logging.info("Loading Step 1 data files...")
        
        try:
            # Load processing summary
            with open(self.data_dir / 'email_processing_summary.json', 'r') as f:
                summary = json.load(f)
            
            # Load domain analysis
            domains_df = pd.read_csv(self.data_dir / 'domain_analysis_report.csv')
            
            # Load raw URLs
            urls_df = pd.read_csv(self.data_dir / 'raw_urls_complete.csv')
            
            logging.info(f"Loaded {len(domains_df)} domains and {len(urls_df)} URLs")
            
            return {
                'summary': summary,
                'domains': domains_df,
                'urls': urls_df
            }
        except Exception as e:
            logging.error(f"Error loading Step 1 data: {e}")
            raise

    def analyze_domain_quality(self, domain: str, urls: List[str]) -> Dict[str, Any]:
        """Analyze domain quality based on URL patterns and content indicators."""
        domain_lower = domain.lower()
        url_text = ' '.join(urls).lower()
        
        # Quality scoring
        high_value_score = sum(1 for keyword in self.quality_indicators['high_value'] 
                              if keyword in domain_lower or keyword in url_text)
        medium_value_score = sum(1 for keyword in self.quality_indicators['medium_value'] 
                                if keyword in domain_lower or keyword in url_text)
        low_value_score = sum(1 for keyword in self.quality_indicators['low_value'] 
                             if keyword in domain_lower or keyword in url_text)
        suspicious_score = sum(1 for keyword in self.quality_indicators['suspicious'] 
                              if keyword in domain_lower or keyword in url_text)
        
        # URL pattern analysis
        pattern_scores = {}
        for pattern_type, patterns in self.url_patterns.items():
            pattern_scores[pattern_type] = sum(
                1 for pattern in patterns 
                if any(re.search(pattern, url, re.IGNORECASE) for url in urls)
            )
        
        # Calculate overall quality score
        total_score = high_value_score + medium_value_score + low_value_score + suspicious_score
        if total_score == 0:
            quality_score = 0.5  # Neutral if no indicators found
        else:
            quality_score = (high_value_score * 0.8 + medium_value_score * 0.5 - 
                           low_value_score * 0.3 - suspicious_score * 0.7) / total_score
        
        # Determine quality category
        if quality_score >= 0.6:
            quality_category = 'HIGH_VALUE'
        elif quality_score >= 0.2:
            quality_category = 'MEDIUM_VALUE'
        elif quality_score >= -0.2:
            quality_category = 'LOW_VALUE'
        else:
            quality_category = 'SUSPICIOUS'
        
        return {
            'quality_score': quality_score,
            'quality_category': quality_category,
            'high_value_indicators': high_value_score,
            'medium_value_indicators': medium_value_score,
            'low_value_indicators': low_value_score,
            'suspicious_indicators': suspicious_score,
            'pattern_scores': pattern_scores,
            'confidence': min(0.95, abs(quality_score) + 0.3)
        }

    def analyze_cultural_relevance(self, domain: str, urls: List[str]) -> Dict[str, Any]:
        """Analyze cultural relevance for African American professionals."""
        domain_lower = domain.lower()
        url_text = ' '.join(urls).lower()
        
        cultural_scores = {}
        total_relevance = 0
        
        for category, keywords in self.cultural_keywords.items():
            category_score = sum(
                1 for keyword in keywords 
                if keyword in domain_lower or keyword in url_text
            )
            cultural_scores[category] = category_score
            total_relevance += category_score
        
        # Calculate overall cultural relevance score
        max_possible = sum(len(keywords) for keywords in self.cultural_keywords.values())
        cultural_relevance_score = total_relevance / max_possible if max_possible > 0 else 0
        
        # Determine cultural category
        if cultural_relevance_score >= 0.1:
            cultural_category = 'HIGH_RELEVANCE'
        elif cultural_relevance_score >= 0.05:
            cultural_category = 'MEDIUM_RELEVANCE'
        else:
            cultural_category = 'LOW_RELEVANCE'
        
        return {
            'cultural_relevance_score': cultural_relevance_score,
            'cultural_category': cultural_category,
            'category_scores': cultural_scores,
            'total_relevance': total_relevance,
            'confidence': min(0.95, cultural_relevance_score * 5 + 0.3)
        }

    def generate_recommendations(self, domain_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent recommendations for domain approval."""
        quality = domain_data['quality_analysis']
        cultural = domain_data['cultural_analysis']
        
        # Combined scoring
        combined_score = (quality['quality_score'] * 0.7 + 
                         cultural['cultural_relevance_score'] * 0.3)
        
        # Recommendation logic
        if quality['quality_category'] == 'SUSPICIOUS':
            recommendation = 'AUTO_REJECT'
            confidence = quality['confidence']
            reasoning = 'Suspicious domain with tracking/security concerns'
        elif quality['quality_category'] == 'HIGH_VALUE' and cultural['cultural_category'] in ['HIGH_RELEVANCE', 'MEDIUM_RELEVANCE']:
            recommendation = 'AUTO_APPROVE'
            confidence = min(0.95, (quality['confidence'] + cultural['confidence']) / 2)
            reasoning = 'High-quality domain with cultural relevance'
        elif quality['quality_category'] == 'HIGH_VALUE':
            recommendation = 'AUTO_APPROVE'
            confidence = quality['confidence']
            reasoning = 'High-quality educational/financial content'
        elif quality['quality_category'] == 'LOW_VALUE':
            recommendation = 'AUTO_REJECT'
            confidence = quality['confidence']
            reasoning = 'Low-value commercial/tracking content'
        elif cultural['cultural_category'] == 'HIGH_RELEVANCE':
            recommendation = 'MANUAL_REVIEW'
            confidence = cultural['confidence']
            reasoning = 'High cultural relevance - requires quality review'
        else:
            recommendation = 'MANUAL_REVIEW'
            confidence = 0.5
            reasoning = 'Medium value domain requiring human assessment'
        
        return {
            'recommendation': recommendation,
            'confidence': confidence,
            'reasoning': reasoning,
            'combined_score': combined_score,
            'priority': 'HIGH' if cultural['cultural_category'] == 'HIGH_RELEVANCE' else 'NORMAL'
        }

    def analyze_all_domains(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all domains and generate comprehensive intelligence."""
        logging.info("Starting comprehensive domain analysis...")
        
        domains_df = data['domains']
        urls_df = data['urls']
        
        domain_analyses = {}
        
        for _, domain_row in domains_df.iterrows():
            domain = domain_row['domain']
            
            # Get URLs for this domain
            domain_urls = urls_df[urls_df['domain'] == domain]['url'].tolist()
            sample_urls = domain_urls[:5]  # First 5 URLs for analysis
            
            # Analyze domain quality
            quality_analysis = self.analyze_domain_quality(domain, sample_urls)
            
            # Analyze cultural relevance
            cultural_analysis = self.analyze_cultural_relevance(domain, sample_urls)
            
            # Generate recommendations
            recommendations = self.generate_recommendations({
                'quality_analysis': quality_analysis,
                'cultural_analysis': cultural_analysis
            })
            
            domain_analyses[domain] = {
                'domain_info': domain_row.to_dict(),
                'quality_analysis': quality_analysis,
                'cultural_analysis': cultural_analysis,
                'recommendations': recommendations,
                'url_count': len(domain_urls),
                'sample_urls': sample_urls
            }
        
        return domain_analyses

    def generate_bulk_actions(self, domain_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bulk action suggestions for efficient processing."""
        logging.info("Generating bulk action recommendations...")
        
        # Categorize domains
        auto_approve = []
        auto_reject = []
        manual_review = []
        high_priority = []
        
        for domain, analysis in domain_analyses.items():
            rec = analysis['recommendations']
            
            if rec['recommendation'] == 'AUTO_APPROVE':
                auto_approve.append(domain)
            elif rec['recommendation'] == 'AUTO_REJECT':
                auto_reject.append(domain)
            else:
                manual_review.append(domain)
            
            if rec['priority'] == 'HIGH':
                high_priority.append(domain)
        
        # Generate bulk action suggestions
        bulk_actions = {
            'auto_approve_all_high_quality': {
                'action': 'Approve all high-quality educational domains',
                'domains': auto_approve,
                'count': len(auto_approve),
                'confidence': 0.85,
                'description': f'Automatically approve {len(auto_approve)} high-quality domains'
            },
            'auto_reject_all_low_quality': {
                'action': 'Reject all low-quality commercial domains',
                'domains': auto_reject,
                'count': len(auto_reject),
                'confidence': 0.90,
                'description': f'Automatically reject {len(auto_reject)} low-quality domains'
            },
            'review_high_cultural_relevance': {
                'action': 'Prioritize review of culturally relevant domains',
                'domains': high_priority,
                'count': len(high_priority),
                'confidence': 0.75,
                'description': f'Review {len(high_priority)} culturally relevant domains first'
            },
            'review_remaining_manual': {
                'action': 'Manual review of remaining domains',
                'domains': manual_review,
                'count': len(manual_review),
                'confidence': 0.60,
                'description': f'Manual review required for {len(manual_review)} domains'
            }
        }
        
        return bulk_actions

    def create_visualizations(self, domain_analyses: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Create comprehensive visualizations for the dashboard."""
        logging.info("Creating visualizations...")
        
        # Prepare data for plotting
        domains = list(domain_analyses.keys())
        quality_scores = [domain_analyses[d]['quality_analysis']['quality_score'] for d in domains]
        cultural_scores = [domain_analyses[d]['cultural_analysis']['cultural_relevance_score'] for d in domains]
        recommendations = [domain_analyses[d]['recommendations']['recommendation'] for d in domains]
        url_counts = [domain_analyses[d]['url_count'] for d in domains]
        
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Mingus Domain Intelligence Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Quality vs Cultural Relevance Scatter Plot
        ax1 = axes[0, 0]
        scatter = ax1.scatter(quality_scores, cultural_scores, c=url_counts, 
                            cmap='viridis', alpha=0.7, s=50)
        ax1.set_xlabel('Quality Score')
        ax1.set_ylabel('Cultural Relevance Score')
        ax1.set_title('Domain Quality vs Cultural Relevance')
        ax1.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax1, label='URL Count')
        
        # 2. Recommendation Distribution
        ax2 = axes[0, 1]
        rec_counts = Counter(recommendations)
        ax2.pie(rec_counts.values(), labels=rec_counts.keys(), autopct='%1.1f%%')
        ax2.set_title('Recommendation Distribution')
        
        # 3. Top Domains by URL Count
        ax3 = axes[0, 2]
        top_domains = sorted(domains, key=lambda x: domain_analyses[x]['url_count'], reverse=True)[:10]
        top_counts = [domain_analyses[d]['url_count'] for d in top_domains]
        ax3.barh(range(len(top_domains)), top_counts)
        ax3.set_yticks(range(len(top_domains)))
        ax3.set_yticklabels([d[:30] + '...' if len(d) > 30 else d for d in top_domains])
        ax3.set_xlabel('URL Count')
        ax3.set_title('Top 10 Domains by URL Count')
        
        # 4. Quality Score Distribution
        ax4 = axes[1, 0]
        ax4.hist(quality_scores, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax4.set_xlabel('Quality Score')
        ax4.set_ylabel('Number of Domains')
        ax4.set_title('Quality Score Distribution')
        ax4.grid(True, alpha=0.3)
        
        # 5. Cultural Relevance Distribution
        ax5 = axes[1, 1]
        ax5.hist(cultural_scores, bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
        ax5.set_xlabel('Cultural Relevance Score')
        ax5.set_ylabel('Number of Domains')
        ax5.set_title('Cultural Relevance Distribution')
        ax5.grid(True, alpha=0.3)
        
        # 6. Combined Score vs URL Count
        ax6 = axes[1, 2]
        combined_scores = [domain_analyses[d]['recommendations']['combined_score'] for d in domains]
        ax6.scatter(combined_scores, url_counts, alpha=0.6, color='green')
        ax6.set_xlabel('Combined Score')
        ax6.set_ylabel('URL Count')
        ax6.set_title('Combined Score vs URL Count')
        ax6.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.reports_dir / 'domain_intelligence_visualizations.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()

    def generate_html_dashboard(self, domain_analyses: Dict[str, Any], 
                              bulk_actions: Dict[str, Any], data: Dict[str, Any]) -> str:
        """Generate interactive HTML dashboard."""
        logging.info("Generating HTML dashboard...")
        
        # Prepare data for dashboard
        summary_stats = {
            'total_domains': len(domain_analyses),
            'auto_approve': len([d for d in domain_analyses.values() 
                               if d['recommendations']['recommendation'] == 'AUTO_APPROVE']),
            'auto_reject': len([d for d in domain_analyses.values() 
                              if d['recommendations']['recommendation'] == 'AUTO_REJECT']),
            'manual_review': len([d for d in domain_analyses.values() 
                                if d['recommendations']['recommendation'] == 'MANUAL_REVIEW']),
            'high_cultural_relevance': len([d for d in domain_analyses.values() 
                                          if d['cultural_analysis']['cultural_category'] == 'HIGH_RELEVANCE'])
        }
        
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mingus Domain Intelligence Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .bulk-actions {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .action-card {{
            background: #f8f9fa;
            border-left: 5px solid #3498db;
            padding: 20px;
            border-radius: 5px;
        }}
        .action-card h3 {{
            margin: 0 0 10px 0;
            color: #2c3e50;
        }}
        .action-count {{
            font-size: 1.5em;
            font-weight: bold;
            color: #3498db;
        }}
        .domain-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .domain-table th, .domain-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .domain-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        .domain-table tr:hover {{
            background: #f5f5f5;
        }}
        .recommendation-badge {{
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .auto-approve {{ background: #d4edda; color: #155724; }}
        .auto-reject {{ background: #f8d7da; color: #721c24; }}
        .manual-review {{ background: #fff3cd; color: #856404; }}
        .high-priority {{ background: #cce5ff; color: #004085; }}
        .visualization {{
            text-align: center;
            margin: 30px 0;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Mingus Domain Intelligence Dashboard</h1>
            <p>Comprehensive analysis of {summary_stats['total_domains']} domains for African American professional financial wellness</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{summary_stats['total_domains']}</div>
                <div class="stat-label">Total Domains</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary_stats['auto_approve']}</div>
                <div class="stat-label">Auto-Approve</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary_stats['auto_reject']}</div>
                <div class="stat-label">Auto-Reject</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary_stats['manual_review']}</div>
                <div class="stat-label">Manual Review</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{summary_stats['high_cultural_relevance']}</div>
                <div class="stat-label">High Cultural Relevance</div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📊 Bulk Action Recommendations</h2>
                <div class="bulk-actions">
        """
        
        for action_key, action_data in bulk_actions.items():
            html_content += f"""
                    <div class="action-card">
                        <h3>{action_data['action']}</h3>
                        <div class="action-count">{action_data['count']} domains</div>
                        <p>{action_data['description']}</p>
                        <small>Confidence: {action_data['confidence']:.1%}</small>
                    </div>
            """
        
        html_content += """
                </div>
            </div>
            
            <div class="section">
                <h2>📈 Analysis Visualizations</h2>
                <div class="visualization">
                    <img src="domain_intelligence_visualizations.png" alt="Domain Intelligence Visualizations">
                </div>
            </div>
            
            <div class="section">
                <h2>🔍 Top Domains Analysis</h2>
                <table class="domain-table">
                    <thead>
                        <tr>
                            <th>Domain</th>
                            <th>URL Count</th>
                            <th>Quality Score</th>
                            <th>Cultural Relevance</th>
                            <th>Recommendation</th>
                            <th>Confidence</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add top 20 domains to table
        sorted_domains = sorted(domain_analyses.items(), 
                              key=lambda x: x[1]['url_count'], reverse=True)[:20]
        
        for domain, analysis in sorted_domains:
            rec = analysis['recommendations']
            quality = analysis['quality_analysis']
            cultural = analysis['cultural_analysis']
            
            rec_class = rec['recommendation'].lower().replace('_', '-')
            priority_class = 'high-priority' if rec['priority'] == 'HIGH' else ''
            
            html_content += f"""
                        <tr class="{priority_class}">
                            <td><strong>{domain}</strong></td>
                            <td>{analysis['url_count']}</td>
                            <td>{quality['quality_score']:.2f}</td>
                            <td>{cultural['cultural_relevance_score']:.2f}</td>
                            <td><span class="recommendation-badge {rec_class}">{rec['recommendation']}</span></td>
                            <td>{rec['confidence']:.1%}</td>
                        </tr>
            """
        
        html_content += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content

    def export_results(self, domain_analyses: Dict[str, Any], 
                      bulk_actions: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Export all analysis results to files."""
        logging.info("Exporting analysis results...")
        
        # 1. Domain recommendations JSON
        recommendations = {}
        for domain, analysis in domain_analyses.items():
            recommendations[domain] = {
                'recommendation': analysis['recommendations']['recommendation'],
                'confidence': analysis['recommendations']['confidence'],
                'reasoning': analysis['recommendations']['reasoning'],
                'quality_score': analysis['quality_analysis']['quality_score'],
                'cultural_relevance_score': analysis['cultural_analysis']['cultural_relevance_score'],
                'url_count': analysis['url_count'],
                'priority': analysis['recommendations']['priority']
            }
        
        with open(self.data_dir / 'domain_recommendations.json', 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        # 2. High value domains CSV
        high_value_domains = []
        for domain, analysis in domain_analyses.items():
            if analysis['recommendations']['recommendation'] == 'AUTO_APPROVE':
                high_value_domains.append({
                    'domain': domain,
                    'url_count': analysis['url_count'],
                    'quality_score': analysis['quality_analysis']['quality_score'],
                    'cultural_relevance_score': analysis['cultural_analysis']['cultural_relevance_score'],
                    'confidence': analysis['recommendations']['confidence'],
                    'reasoning': analysis['recommendations']['reasoning'],
                    'sample_urls': '; '.join(analysis['sample_urls'][:3])
                })
        
        pd.DataFrame(high_value_domains).to_csv(
            self.data_dir / 'high_value_domains.csv', index=False
        )
        
        # 3. Medium value domains CSV
        medium_value_domains = []
        for domain, analysis in domain_analyses.items():
            if analysis['recommendations']['recommendation'] == 'MANUAL_REVIEW':
                medium_value_domains.append({
                    'domain': domain,
                    'url_count': analysis['url_count'],
                    'quality_score': analysis['quality_analysis']['quality_score'],
                    'cultural_relevance_score': analysis['cultural_analysis']['cultural_relevance_score'],
                    'confidence': analysis['recommendations']['confidence'],
                    'reasoning': analysis['recommendations']['reasoning'],
                    'priority': analysis['recommendations']['priority'],
                    'sample_urls': '; '.join(analysis['sample_urls'][:3])
                })
        
        pd.DataFrame(medium_value_domains).to_csv(
            self.data_dir / 'medium_value_domains.csv', index=False
        )
        
        # 4. Low value domains CSV
        low_value_domains = []
        for domain, analysis in domain_analyses.items():
            if analysis['recommendations']['recommendation'] == 'AUTO_REJECT':
                low_value_domains.append({
                    'domain': domain,
                    'url_count': analysis['url_count'],
                    'quality_score': analysis['quality_analysis']['quality_score'],
                    'cultural_relevance_score': analysis['cultural_analysis']['cultural_relevance_score'],
                    'confidence': analysis['recommendations']['confidence'],
                    'reasoning': analysis['recommendations']['reasoning'],
                    'sample_urls': '; '.join(analysis['sample_urls'][:3])
                })
        
        pd.DataFrame(low_value_domains).to_csv(
            self.data_dir / 'low_value_domains.csv', index=False
        )
        
        # 5. Cultural relevance analysis JSON
        cultural_analysis = {
            'summary': {
                'high_relevance_count': len([d for d in domain_analyses.values() 
                                           if d['cultural_analysis']['cultural_category'] == 'HIGH_RELEVANCE']),
                'medium_relevance_count': len([d for d in domain_analyses.values() 
                                             if d['cultural_analysis']['cultural_category'] == 'MEDIUM_RELEVANCE']),
                'low_relevance_count': len([d for d in domain_analyses.values() 
                                          if d['cultural_analysis']['cultural_category'] == 'LOW_RELEVANCE'])
            },
            'high_relevance_domains': [
                {
                    'domain': domain,
                    'cultural_relevance_score': analysis['cultural_analysis']['cultural_relevance_score'],
                    'category_scores': analysis['cultural_analysis']['category_scores'],
                    'url_count': analysis['url_count']
                }
                for domain, analysis in domain_analyses.items()
                if analysis['cultural_analysis']['cultural_category'] == 'HIGH_RELEVANCE'
            ]
        }
        
        with open(self.data_dir / 'cultural_relevance_analysis.json', 'w') as f:
            json.dump(cultural_analysis, f, indent=2)
        
        # 6. Bulk action suggestions JSON
        with open(self.data_dir / 'bulk_action_suggestions.json', 'w') as f:
            json.dump(bulk_actions, f, indent=2)
        
        # 7. Step 2 intelligence summary JSON
        summary = {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_domains_analyzed': len(domain_analyses),
            'recommendation_breakdown': {
                'auto_approve': len([d for d in domain_analyses.values() 
                                   if d['recommendations']['recommendation'] == 'AUTO_APPROVE']),
                'auto_reject': len([d for d in domain_analyses.values() 
                                  if d['recommendations']['recommendation'] == 'AUTO_REJECT']),
                'manual_review': len([d for d in domain_analyses.values() 
                                    if d['recommendations']['recommendation'] == 'MANUAL_REVIEW'])
            },
            'cultural_relevance_breakdown': {
                'high_relevance': len([d for d in domain_analyses.values() 
                                     if d['cultural_analysis']['cultural_category'] == 'HIGH_RELEVANCE']),
                'medium_relevance': len([d for d in domain_analyses.values() 
                                       if d['cultural_analysis']['cultural_category'] == 'MEDIUM_RELEVANCE']),
                'low_relevance': len([d for d in domain_analyses.values() 
                                    if d['cultural_analysis']['cultural_category'] == 'LOW_RELEVANCE'])
            },
            'quality_breakdown': {
                'high_quality': len([d for d in domain_analyses.values() 
                                   if d['quality_analysis']['quality_category'] == 'HIGH_VALUE']),
                'medium_quality': len([d for d in domain_analyses.values() 
                                     if d['quality_analysis']['quality_category'] == 'MEDIUM_VALUE']),
                'low_quality': len([d for d in domain_analyses.values() 
                                  if d['quality_analysis']['quality_category'] == 'LOW_VALUE']),
                'suspicious': len([d for d in domain_analyses.values() 
                                 if d['quality_analysis']['quality_category'] == 'SUSPICIOUS'])
            },
            'estimated_articles_after_filtering': sum(
                analysis['url_count'] for domain, analysis in domain_analyses.items()
                if analysis['recommendations']['recommendation'] in ['AUTO_APPROVE', 'MANUAL_REVIEW']
            ),
            'processing_efficiency': {
                'auto_approve_percentage': len([d for d in domain_analyses.values() 
                                              if d['recommendations']['recommendation'] == 'AUTO_APPROVE']) / len(domain_analyses) * 100,
                'auto_reject_percentage': len([d for d in domain_analyses.values() 
                                             if d['recommendations']['recommendation'] == 'AUTO_REJECT']) / len(domain_analyses) * 100,
                'manual_review_percentage': len([d for d in domain_analyses.values() 
                                               if d['recommendations']['recommendation'] == 'MANUAL_REVIEW']) / len(domain_analyses) * 100
            }
        }
        
        with open(self.data_dir / 'step2_intelligence_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)

    def run_analysis(self) -> None:
        """Run the complete domain intelligence analysis."""
        logging.info("Starting Step 2: Domain Intelligence Analysis")
        
        try:
            # Load Step 1 data
            data = self.load_step1_data()
            
            # Analyze all domains
            domain_analyses = self.analyze_all_domains(data)
            
            # Generate bulk actions
            bulk_actions = self.generate_bulk_actions(domain_analyses)
            
            # Create visualizations
            self.create_visualizations(domain_analyses, data)
            
            # Generate HTML dashboard
            html_content = self.generate_html_dashboard(domain_analyses, bulk_actions, data)
            with open(self.reports_dir / 'domain_intelligence_dashboard.html', 'w') as f:
                f.write(html_content)
            
            # Export all results
            self.export_results(domain_analyses, bulk_actions, data)
            
            # Print summary
            self.print_summary(domain_analyses, bulk_actions, data)
            
            logging.info("Step 2 analysis completed successfully!")
            
        except Exception as e:
            logging.error(f"Error in Step 2 analysis: {e}")
            raise

    def print_summary(self, domain_analyses: Dict[str, Any], 
                     bulk_actions: Dict[str, Any], data: Dict[str, Any]) -> None:
        """Print a comprehensive summary of the analysis."""
        print("\n" + "="*80)
        print("🎯 MINGUS DOMAIN INTELLIGENCE ANALYSIS - STEP 2 COMPLETE")
        print("="*80)
        
        # Basic statistics
        total_domains = len(domain_analyses)
        auto_approve = len([d for d in domain_analyses.values() 
                           if d['recommendations']['recommendation'] == 'AUTO_APPROVE'])
        auto_reject = len([d for d in domain_analyses.values() 
                          if d['recommendations']['recommendation'] == 'AUTO_REJECT'])
        manual_review = len([d for d in domain_analyses.values() 
                            if d['recommendations']['recommendation'] == 'MANUAL_REVIEW'])
        high_cultural = len([d for d in domain_analyses.values() 
                            if d['cultural_analysis']['cultural_category'] == 'HIGH_RELEVANCE'])
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   Total domains analyzed: {total_domains}")
        print(f"   Auto-approve candidates: {auto_approve} ({auto_approve/total_domains*100:.1f}%)")
        print(f"   Auto-reject candidates: {auto_reject} ({auto_reject/total_domains*100:.1f}%)")
        print(f"   Manual review required: {manual_review} ({manual_review/total_domains*100:.1f}%)")
        print(f"   High cultural relevance: {high_cultural} ({high_cultural/total_domains*100:.1f}%)")
        
        # Top domains by cultural relevance
        print(f"\n🌟 TOP CULTURALLY RELEVANT DOMAINS:")
        cultural_domains = sorted(
            [(domain, analysis) for domain, analysis in domain_analyses.items()
             if analysis['cultural_analysis']['cultural_category'] == 'HIGH_RELEVANCE'],
            key=lambda x: x[1]['cultural_analysis']['cultural_relevance_score'],
            reverse=True
        )[:10]
        
        for i, (domain, analysis) in enumerate(cultural_domains, 1):
            score = analysis['cultural_analysis']['cultural_relevance_score']
            url_count = analysis['url_count']
            print(f"   {i:2d}. {domain:<40} (Score: {score:.3f}, URLs: {url_count})")
        
        # Bulk action recommendations
        print(f"\n⚡ BULK ACTION RECOMMENDATIONS:")
        for action_key, action_data in bulk_actions.items():
            print(f"   • {action_data['action']}: {action_data['count']} domains "
                  f"(Confidence: {action_data['confidence']:.1%})")
        
        # Estimated efficiency
        estimated_articles = sum(
            analysis['url_count'] for domain, analysis in domain_analyses.items()
            if analysis['recommendations']['recommendation'] in ['AUTO_APPROVE', 'MANUAL_REVIEW']
        )
        
        print(f"\n📈 EFFICIENCY METRICS:")
        print(f"   Estimated articles after filtering: {estimated_articles:,}")
        print(f"   Processing efficiency: {auto_approve/total_domains*100:.1f}% auto-approve, "
              f"{auto_reject/total_domains*100:.1f}% auto-reject")
        print(f"   Manual review burden: {manual_review} domains ({manual_review/total_domains*100:.1f}%)")
        
        # Output files
        print(f"\n📁 OUTPUT FILES GENERATED:")
        print(f"   • reports/domain_intelligence_dashboard.html - Interactive dashboard")
        print(f"   • data/domain_recommendations.json - Structured recommendations")
        print(f"   • data/high_value_domains.csv - Auto-approval candidates")
        print(f"   • data/medium_value_domains.csv - Manual review queue")
        print(f"   • data/low_value_domains.csv - Auto-rejection candidates")
        print(f"   • data/cultural_relevance_analysis.json - Cultural scoring")
        print(f"   • data/bulk_action_suggestions.json - Bulk operations")
        print(f"   • data/step2_intelligence_summary.json - Complete statistics")
        
        print(f"\n🚀 READY FOR STEP 3: DOMAIN APPROVAL INTERFACE")
        print("="*80)


def main():
    """Main execution function."""
    analyzer = DomainIntelligenceAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
