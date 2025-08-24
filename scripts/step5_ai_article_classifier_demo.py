#!/usr/bin/env python3
"""
Step 5: AI Article Classifier Demo for Mingus Financial Wellness App
Demonstrates the classification system with mock data and simulated API responses
Target: African American professionals aged 25-35 earning $40K-$100K
"""

import os
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import pandas as pd
from pathlib import Path
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/step5_classification_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ArticleClassification:
    """Data structure for article classification results"""
    article_id: str
    title: str
    author: str
    url: str
    content_preview: str
    primary_phase: str
    confidence_score: float
    difficulty_level: str
    demographic_relevance: int
    cultural_sensitivity: int
    income_impact_potential: int
    key_topics: List[str]
    learning_objectives: List[str]
    prerequisites: List[str]
    target_income_range: str
    career_stage: str
    cultural_relevance_keywords: List[str]
    actionability_score: int
    professional_development_value: int
    recommended_reading_order: int
    classification_reasoning: str
    processing_timestamp: str
    api_model_used: str
    token_count: int
    processing_cost: float

class MockAIClassifier:
    """Mock AI classifier that simulates OpenAI GPT-4 responses"""
    
    def __init__(self):
        self.total_cost = 0.0
        self.total_tokens = 0
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = time.time()
        
        # Mock responses based on content analysis
        self.mock_responses = {
            'mindset': {
                'primary_phase': 'BE',
                'confidence_score': 0.85,
                'difficulty_level': 'Beginner',
                'demographic_relevance': 8,
                'cultural_sensitivity': 7,
                'income_impact_potential': 6,
                'key_topics': ['confidence building', 'professional identity', 'mindset transformation'],
                'learning_objectives': ['Develop professional confidence', 'Overcome limiting beliefs', 'Build executive presence'],
                'prerequisites': ['Basic self-awareness', 'Desire for growth'],
                'target_income_range': 'All ranges',
                'career_stage': 'All stages',
                'cultural_relevance_keywords': ['professional confidence', 'cultural identity', 'executive presence'],
                'actionability_score': 7,
                'professional_development_value': 8,
                'recommended_reading_order': 1,
                'classification_reasoning': 'This article focuses on building professional confidence and developing the right mindset for career success, which aligns with the BE (Identity & Mindset) phase of the transformation framework.'
            },
            'skills': {
                'primary_phase': 'DO',
                'confidence_score': 0.92,
                'difficulty_level': 'Intermediate',
                'demographic_relevance': 9,
                'cultural_sensitivity': 8,
                'income_impact_potential': 8,
                'key_topics': ['salary negotiation', 'career advancement', 'skill development'],
                'learning_objectives': ['Master salary negotiation techniques', 'Develop career advancement strategies', 'Build professional skills'],
                'prerequisites': ['Basic professional experience', 'Understanding of industry standards'],
                'target_income_range': '$40K-$80K',
                'career_stage': 'Early career',
                'cultural_relevance_keywords': ['salary negotiation', 'career advancement', 'professional skills'],
                'actionability_score': 9,
                'professional_development_value': 9,
                'recommended_reading_order': 2,
                'classification_reasoning': 'This article provides concrete, actionable strategies for salary negotiation and career advancement, making it a perfect fit for the DO (Skills & Actions) phase.'
            },
            'wealth': {
                'primary_phase': 'HAVE',
                'confidence_score': 0.88,
                'difficulty_level': 'Advanced',
                'demographic_relevance': 7,
                'cultural_sensitivity': 6,
                'income_impact_potential': 9,
                'key_topics': ['investment strategies', 'wealth management', 'financial planning'],
                'learning_objectives': ['Understand advanced investment strategies', 'Develop wealth management skills', 'Create long-term financial plans'],
                'prerequisites': ['Basic financial literacy', 'Investment experience', 'Higher income level'],
                'target_income_range': '$80K-$100K',
                'career_stage': 'Mid-career',
                'cultural_relevance_keywords': ['wealth building', 'investment strategies', 'financial independence'],
                'actionability_score': 8,
                'professional_development_value': 7,
                'recommended_reading_order': 3,
                'classification_reasoning': 'This article covers advanced wealth management and investment strategies, representing the HAVE (Results & Management) phase where individuals focus on maintaining and growing their wealth.'
            }
        }
    
    async def classify_article(self, article: Dict[str, Any]) -> Optional[ArticleClassification]:
        """Classify a single article using mock AI responses"""
        
        try:
            # Simulate API processing time
            await asyncio.sleep(0.5)
            
            # Prepare article content
            title = article.get('title', '')
            author = article.get('author', '')
            url = article.get('url', '')
            content = article.get('content', '')
            
            # Truncate content for demo
            content_preview = content[:500] + "..." if len(content) > 500 else content
            
            # Determine classification based on content keywords
            classification_type = self._determine_classification_type(content.lower())
            mock_data = self.mock_responses[classification_type]
            
            # Calculate mock costs
            token_count = len(content.split()) * 2  # Rough estimate
            cost = token_count * 0.00003  # Mock cost calculation
            
            self.total_tokens += token_count
            self.total_cost += cost
            self.processed_count += 1
            
            logger.info(f"Successfully classified: {title[:50]}... (Phase: {mock_data['primary_phase']}, Confidence: {mock_data['confidence_score']:.2f})")
            
            return ArticleClassification(
                article_id=article.get('id', hashlib.md5(url.encode()).hexdigest()),
                title=title,
                author=author,
                url=url,
                content_preview=content_preview,
                **mock_data,
                processing_timestamp=datetime.now().isoformat(),
                api_model_used="gpt-4-mock",
                token_count=token_count,
                processing_cost=cost
            )
            
        except Exception as e:
            logger.error(f"Error classifying article '{article.get('title', 'Unknown')}': {str(e)}")
            self.failed_count += 1
            
        return None
    
    def _determine_classification_type(self, content: str) -> str:
        """Determine classification type based on content keywords"""
        mindset_keywords = ['confidence', 'mindset', 'belief', 'identity', 'presence', 'mental']
        skills_keywords = ['negotiation', 'skill', 'strategy', 'action', 'technique', 'how to']
        wealth_keywords = ['investment', 'wealth', 'portfolio', 'million', 'financial', 'money']
        
        mindset_score = sum(1 for keyword in mindset_keywords if keyword in content)
        skills_score = sum(1 for keyword in skills_keywords if keyword in content)
        wealth_score = sum(1 for keyword in wealth_keywords if keyword in content)
        
        if wealth_score > skills_score and wealth_score > mindset_score:
            return 'wealth'
        elif skills_score > mindset_score:
            return 'skills'
        else:
            return 'mindset'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        elapsed_time = time.time() - self.start_time
        return {
            'total_processed': self.processed_count,
            'total_failed': self.failed_count,
            'success_rate': self.processed_count / (self.processed_count + self.failed_count) if (self.processed_count + self.failed_count) > 0 else 0,
            'total_tokens': self.total_tokens,
            'total_cost': self.total_cost,
            'elapsed_time_seconds': elapsed_time,
            'articles_per_minute': (self.processed_count / elapsed_time) * 60 if elapsed_time > 0 else 0
        }

class ArticleProcessor:
    """Main processor for article classification"""
    
    def __init__(self):
        self.classifier = MockAIClassifier()
        self.output_dir = Path("data")
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        
        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    async def process_articles(self, input_file: str = "data/high_quality_articles.csv"):
        """Process all articles for classification"""
        
        logger.info("Starting article classification process (DEMO MODE)...")
        
        # Load articles
        articles = self._load_articles(input_file)
        if not articles:
            logger.error("No articles found to process")
            return
        
        logger.info(f"Loaded {len(articles)} articles for classification")
        
        # Process articles in batches
        batch_size = 5
        all_classifications = []
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(articles) + batch_size - 1)//batch_size}")
            
            # Process batch concurrently
            tasks = [self.classifier.classify_article(article) for article in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out None results and exceptions
            valid_results = [result for result in batch_results if result is not None and not isinstance(result, Exception)]
            all_classifications.extend(valid_results)
            
            # Progress update
            logger.info(f"Completed batch. Total processed: {len(all_classifications)}/{len(articles)}")
        
        # Generate output files
        await self._generate_output_files(all_classifications)
        
        # Generate reports
        self._generate_reports(all_classifications)
        
        logger.info("Article classification process completed!")
    
    def _load_articles(self, input_file: str) -> List[Dict[str, Any]]:
        """Load articles from CSV file"""
        try:
            df = pd.read_csv(input_file)
            articles = []
            
            for _, row in df.iterrows():
                article = {
                    'id': str(row.get('id', '')),
                    'title': str(row.get('title', '')),
                    'author': str(row.get('authors', '')),
                    'url': str(row.get('url', '')),
                    'content': str(row.get('content', '')),
                    'domain': str(row.get('domain', '')),
                    'published_date': str(row.get('publish_date', '')),
                    'word_count': int(row.get('word_count', 0)),
                    'quality_score': float(row.get('quality_score', 0.0))
                }
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error loading articles from {input_file}: {str(e)}")
            return []
    
    async def _generate_output_files(self, classifications: List[ArticleClassification]):
        """Generate all output files"""
        
        # Convert to dictionaries
        classification_dicts = [asdict(classification) for classification in classifications]
        
        # 1. Complete classifications
        with open(self.output_dir / "classified_articles_complete.json", 'w') as f:
            json.dump(classification_dicts, f, indent=2)
        
        # 2. Phase-specific files
        phases = ['BE', 'DO', 'HAVE']
        for phase in phases:
            phase_articles = [c for c in classification_dicts if c['primary_phase'] == phase]
            with open(self.output_dir / f"{phase.lower()}_phase_articles.json", 'w') as f:
                json.dump(phase_articles, f, indent=2)
        
        # 3. Confidence-based files
        high_confidence = [c for c in classification_dicts if c['confidence_score'] >= 0.8]
        review_queue = [c for c in classification_dicts if c['confidence_score'] < 0.7]
        
        with open(self.output_dir / "high_confidence_classifications.json", 'w') as f:
            json.dump(high_confidence, f, indent=2)
        
        with open(self.output_dir / "review_queue_classifications.json", 'w') as f:
            json.dump(review_queue, f, indent=2)
        
        # 4. Cultural relevance report
        cultural_report = self._generate_cultural_relevance_report(classifications)
        with open(self.output_dir / "cultural_relevance_report.json", 'w') as f:
            json.dump(cultural_report, f, indent=2)
        
        # 5. Classification statistics
        stats = self.classifier.get_statistics()
        stats['classification_distribution'] = self._get_phase_distribution(classifications)
        stats['quality_metrics'] = self._get_quality_metrics(classifications)
        
        with open(self.output_dir / "classification_statistics.json", 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Generated {len(classification_dicts)} classified articles")
        logger.info(f"High confidence: {len(high_confidence)}, Review queue: {len(review_queue)}")
    
    def _generate_cultural_relevance_report(self, classifications: List[ArticleClassification]) -> Dict[str, Any]:
        """Generate cultural relevance analysis report"""
        
        cultural_scores = [c.cultural_sensitivity for c in classifications]
        demographic_scores = [c.demographic_relevance for c in classifications]
        
        # Cultural keywords analysis
        all_keywords = []
        for c in classifications:
            all_keywords.extend(c.cultural_relevance_keywords)
        
        keyword_freq = {}
        for keyword in all_keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
        
        return {
            'summary': {
                'total_articles': len(classifications),
                'avg_cultural_sensitivity': sum(cultural_scores) / len(cultural_scores) if cultural_scores else 0,
                'avg_demographic_relevance': sum(demographic_scores) / len(demographic_scores) if demographic_scores else 0,
                'high_cultural_relevance_count': len([s for s in cultural_scores if s >= 8]),
                'high_demographic_relevance_count': len([s for s in demographic_scores if s >= 8])
            },
            'cultural_keywords': dict(sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]),
            'phase_cultural_analysis': {
                'BE': {
                    'count': len([c for c in classifications if c.primary_phase == 'BE']),
                    'avg_cultural_score': sum([c.cultural_sensitivity for c in classifications if c.primary_phase == 'BE']) / len([c for c in classifications if c.primary_phase == 'BE']) if any(c.primary_phase == 'BE' for c in classifications) else 0
                },
                'DO': {
                    'count': len([c for c in classifications if c.primary_phase == 'DO']),
                    'avg_cultural_score': sum([c.cultural_sensitivity for c in classifications if c.primary_phase == 'DO']) / len([c for c in classifications if c.primary_phase == 'DO']) if any(c.primary_phase == 'DO' for c in classifications) else 0
                },
                'HAVE': {
                    'count': len([c for c in classifications if c.primary_phase == 'HAVE']),
                    'avg_cultural_score': sum([c.cultural_sensitivity for c in classifications if c.primary_phase == 'HAVE']) / len([c for c in classifications if c.primary_phase == 'HAVE']) if any(c.primary_phase == 'HAVE' for c in classifications) else 0
                }
            }
        }
    
    def _get_phase_distribution(self, classifications: List[ArticleClassification]) -> Dict[str, Any]:
        """Get distribution of articles across phases"""
        total = len(classifications)
        if total == 0:
            return {}
        
        phase_counts = {}
        for phase in ['BE', 'DO', 'HAVE']:
            count = len([c for c in classifications if c.primary_phase == phase])
            phase_counts[phase] = {
                'count': count,
                'percentage': (count / total) * 100
            }
        
        return phase_counts
    
    def _get_quality_metrics(self, classifications: List[ArticleClassification]) -> Dict[str, Any]:
        """Get quality metrics for classifications"""
        if not classifications:
            return {}
        
        high_confidence = len([c for c in classifications if c.confidence_score >= 0.8])
        strong_cultural = len([c for c in classifications if c.cultural_sensitivity >= 8])
        high_actionability = len([c for c in classifications if c.actionability_score >= 7])
        high_professional = len([c for c in classifications if c.professional_development_value >= 8])
        
        total = len(classifications)
        
        return {
            'high_confidence_percentage': (high_confidence / total) * 100,
            'strong_cultural_relevance_percentage': (strong_cultural / total) * 100,
            'high_actionability_percentage': (high_actionability / total) * 100,
            'high_professional_development_percentage': (high_professional / total) * 100
        }
    
    def _generate_reports(self, classifications: List[ArticleClassification]):
        """Generate HTML report"""
        
        stats = self.classifier.get_statistics()
        phase_dist = self._get_phase_distribution(classifications)
        quality_metrics = self._get_quality_metrics(classifications)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mingus Article Classification Report (DEMO)</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                .phase {{ margin: 10px 0; padding: 10px; background: #e9ecef; border-radius: 3px; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
                .demo-notice {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mingus Article Classification Report (DEMO MODE)</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="demo-notice">
                <strong>DEMO MODE:</strong> This is a demonstration of the AI classification system using mock data. 
                In production, this would use OpenAI GPT-4 for real article classification.
            </div>
            
            <div class="section">
                <h2>Processing Statistics</h2>
                <div class="metric">
                    <strong>Total Processed:</strong> {stats['total_processed']}
                </div>
                <div class="metric">
                    <strong>Success Rate:</strong> {stats['success_rate']:.1%}
                </div>
                <div class="metric">
                    <strong>Total Cost:</strong> ${stats['total_cost']:.2f} (mock)
                </div>
                <div class="metric">
                    <strong>Processing Time:</strong> {stats['elapsed_time_seconds']:.1f} seconds
                </div>
            </div>
            
            <div class="section">
                <h2>Phase Distribution</h2>
                <div class="phase">
                    <strong>BE (Identity & Mindset):</strong> {phase_dist.get('BE', {}).get('count', 0)} articles ({phase_dist.get('BE', {}).get('percentage', 0):.1f}%)
                </div>
                <div class="phase">
                    <strong>DO (Skills & Actions):</strong> {phase_dist.get('DO', {}).get('count', 0)} articles ({phase_dist.get('DO', {}).get('percentage', 0):.1f}%)
                </div>
                <div class="phase">
                    <strong>HAVE (Results & Management):</strong> {phase_dist.get('HAVE', {}).get('count', 0)} articles ({phase_dist.get('HAVE', {}).get('percentage', 0):.1f}%)
                </div>
            </div>
            
            <div class="section">
                <h2>Quality Metrics</h2>
                <div class="metric">
                    <strong>High Confidence:</strong> {quality_metrics.get('high_confidence_percentage', 0):.1f}%
                </div>
                <div class="metric">
                    <strong>Strong Cultural Relevance:</strong> {quality_metrics.get('strong_cultural_relevance_percentage', 0):.1f}%
                </div>
                <div class="metric">
                    <strong>High Actionability:</strong> {quality_metrics.get('high_actionability_percentage', 0):.1f}%
                </div>
                <div class="metric">
                    <strong>High Professional Development:</strong> {quality_metrics.get('high_professional_development_percentage', 0):.1f}%
                </div>
            </div>
            
            <div class="section">
                <h2>Next Steps</h2>
                <p>To run the full AI classification system:</p>
                <ol>
                    <li>Obtain a valid OpenAI API key</li>
                    <li>Set the OPENAI_API_KEY environment variable</li>
                    <li>Run the main script: <code>python3 scripts/step5_ai_article_classifier.py</code></li>
                    <li>Review the generated classification files in the <code>data/</code> directory</li>
                </ol>
            </div>
        </body>
        </html>
        """
        
        with open(self.reports_dir / "ai_classification_summary_demo.html", 'w') as f:
            f.write(html_content)

async def main():
    """Main execution function"""
    
    logger.info("Starting AI Article Classifier Demo...")
    
    # Initialize processor
    processor = ArticleProcessor()
    
    # Process articles
    await processor.process_articles()
    
    # Final statistics
    stats = processor.classifier.get_statistics()
    logger.info("=== FINAL STATISTICS (DEMO MODE) ===")
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Success rate: {stats['success_rate']:.1%}")
    logger.info(f"Total cost: ${stats['total_cost']:.2f} (mock)")
    logger.info(f"Processing time: {stats['elapsed_time_seconds']:.1f} seconds")
    logger.info(f"Articles per minute: {stats['articles_per_minute']:.1f}")
    logger.info("Demo completed successfully! Check the generated files in data/ and reports/ directories.")

if __name__ == "__main__":
    asyncio.run(main())
