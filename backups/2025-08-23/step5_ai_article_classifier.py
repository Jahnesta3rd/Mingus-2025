#!/usr/bin/env python3
"""
Step 5: AI Article Classifier for Mingus Financial Wellness App
Classifies scraped articles using OpenAI GPT-4 according to Be-Do-Have transformation framework
Target: African American professionals aged 25-35 earning $40K-$100K
"""

import os
import json
import csv
import time
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import pandas as pd
from pathlib import Path
import openai
from openai import AsyncOpenAI
import tiktoken
from concurrent.futures import ThreadPoolExecutor
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/step5_classification.log'),
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

class AIClassifier:
    """AI-powered article classifier using OpenAI GPT-4"""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        self.total_cost = 0.0
        self.total_tokens = 0
        self.processed_count = 0
        self.failed_count = 0
        self.start_time = time.time()
        
        # Rate limiting
        self.requests_per_second = 3
        self.last_request_time = 0
        
        # Cost tracking
        self.gpt4_cost_per_1k_tokens = 0.03
        self.gpt35_cost_per_1k_tokens = 0.002
        
    async def classify_article(self, article: Dict[str, Any]) -> Optional[ArticleClassification]:
        """Classify a single article using OpenAI GPT-4"""
        
        # Rate limiting
        await self._rate_limit()
        
        try:
            # Prepare article content
            title = article.get('title', '')
            author = article.get('author', '')
            url = article.get('url', '')
            content = article.get('content', '')
            
            # Truncate content for token efficiency
            content_preview = self._truncate_content(content, max_tokens=1500)
            
            # Determine which model to use based on content complexity
            model = self._select_model(content_preview)
            
            # Create classification prompt
            prompt = self._create_classification_prompt(title, author, content_preview, url)
            
            # Make API call
            response = await self._make_api_call(prompt, model)
            
            if response:
                # Parse and validate response
                classification_data = self._parse_classification_response(response, article)
                
                if classification_data:
                    # Calculate costs
                    token_count = len(self.encoding.encode(prompt + response))
                    cost = self._calculate_cost(token_count, model)
                    
                    self.total_tokens += token_count
                    self.total_cost += cost
                    self.processed_count += 1
                    
                    logger.info(f"Successfully classified: {title[:50]}... (Phase: {classification_data['primary_phase']}, Confidence: {classification_data['confidence_score']:.2f})")
                    
                    return ArticleClassification(
                        article_id=article.get('id', hashlib.md5(url.encode()).hexdigest()),
                        title=title,
                        author=author,
                        url=url,
                        content_preview=content_preview,
                        **classification_data,
                        processing_timestamp=datetime.now().isoformat(),
                        api_model_used=model,
                        token_count=token_count,
                        processing_cost=cost
                    )
            
        except Exception as e:
            logger.error(f"Error classifying article '{article.get('title', 'Unknown')}': {str(e)}")
            self.failed_count += 1
            
        return None
    
    def _select_model(self, content: str) -> str:
        """Select appropriate OpenAI model based on content complexity"""
        # Simple heuristic: use GPT-4 for longer, more complex content
        word_count = len(content.split())
        if word_count > 500 or any(keyword in content.lower() for keyword in 
                                 ['investment', 'portfolio', 'tax', 'estate', 'advanced']):
            return "gpt-4"
        else:
            return "gpt-3.5-turbo"
    
    def _truncate_content(self, content: str, max_tokens: int) -> str:
        """Truncate content to fit within token limits"""
        tokens = self.encoding.encode(content)
        if len(tokens) > max_tokens:
            truncated_tokens = tokens[:max_tokens]
            return self.encoding.decode(truncated_tokens)
        return content
    
    def _create_classification_prompt(self, title: str, author: str, content: str, url: str) -> str:
        """Create the classification prompt for OpenAI"""
        
        return f"""You are an expert financial wellness and career coach specializing in African American professionals aged 25-35 earning $40K-$100K annually. You understand the unique challenges this demographic faces including:

SYSTEMIC CHALLENGES:
- Limited access to generational wealth and family financial support
- Career advancement barriers in corporate environments
- Student loan debt burden significantly above national averages
- Workplace microaggressions and cultural navigation challenges
- Limited access to professional networks and mentorship
- Housing and homeownership barriers in desirable areas

CULTURAL CONTEXT:
- Strong community and family obligation values
- Emphasis on breaking generational cycles and creating legacy
- Professional excellence while maintaining cultural identity
- Community uplift and representation in corporate spaces
- Balancing individual success with community responsibility

FINANCIAL SITUATION:
- Income range: $40K-$100K (early to mid-career professionals)
- Often supporting family members financially
- Building first emergency funds and investment portfolios
- Navigating corporate benefits and compensation packages
- Planning for major purchases (home, car, family)

CLASSIFICATION TASK:
Analyze the following article and classify it using the Be-Do-Have transformation framework:

BE (Identity & Mindset): Building confidence, professional identity, overcoming limiting beliefs, developing executive presence, financial mindset transformation

DO (Skills & Actions): Acquiring specific skills, taking concrete actions, implementing strategies, building systems, executing plans

HAVE (Results & Management): Achieving outcomes, managing wealth, maintaining success, sophisticated strategies, advanced optimization

Article to Classify:
Title: {title}
Author: {author}
Content: {content}
URL: {url}

Response Format (JSON):
{{
"primary_phase": "BE|DO|HAVE",
"confidence_score": 0.0-1.0,
"difficulty_level": "Beginner|Intermediate|Advanced",
"demographic_relevance": 1-10,
"cultural_sensitivity": 1-10,
"income_impact_potential": 1-10,
"key_topics": ["topic1", "topic2", "topic3"],
"learning_objectives": ["objective1", "objective2", "objective3"],
"prerequisites": ["prerequisite1", "prerequisite2"],
"target_income_range": "$40K-$60K|$60K-$80K|$80K-$100K|All ranges",
"career_stage": "Early career|Mid-career|Advanced|All stages",
"cultural_relevance_keywords": ["keyword1", "keyword2"],
"actionability_score": 1-10,
"professional_development_value": 1-10,
"recommended_reading_order": 1-100,
"classification_reasoning": "Detailed explanation of classification decisions"
}}

Provide only the JSON response, no additional text."""

    async def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    async def _make_api_call(self, prompt: str, model: str) -> Optional[str]:
        """Make API call to OpenAI with retry logic"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a financial wellness expert specializing in African American professionals."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"API call failed (attempt {attempt + 1}): {str(e)}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"API call failed after {max_retries} attempts: {str(e)}")
                    return None
        
        return None
    
    def _parse_classification_response(self, response: str, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse and validate the classification response"""
        try:
            # Extract JSON from response
            if response.startswith('```json'):
                response = response[7:-3]
            elif response.startswith('```'):
                response = response[3:-3]
            
            data = json.loads(response)
            
            # Validate required fields
            required_fields = [
                'primary_phase', 'confidence_score', 'difficulty_level',
                'demographic_relevance', 'cultural_sensitivity', 'income_impact_potential'
            ]
            
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field '{field}' in classification response")
                    return None
            
            # Validate phase classification
            if data['primary_phase'] not in ['BE', 'DO', 'HAVE']:
                logger.warning(f"Invalid primary_phase: {data['primary_phase']}")
                return None
            
            # Validate score ranges
            score_fields = ['confidence_score', 'demographic_relevance', 'cultural_sensitivity', 
                          'income_impact_potential', 'actionability_score', 'professional_development_value']
            
            for field in score_fields:
                if field in data:
                    if field == 'confidence_score':
                        if not (0 <= data[field] <= 1):
                            data[field] = max(0, min(1, data[field]))
                    else:
                        if not (1 <= data[field] <= 10):
                            data[field] = max(1, min(10, data[field]))
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing classification response: {str(e)}")
            return None
    
    def _calculate_cost(self, token_count: int, model: str) -> float:
        """Calculate the cost of the API call"""
        if model == "gpt-4":
            return (token_count / 1000) * self.gpt4_cost_per_1k_tokens
        else:
            return (token_count / 1000) * self.gpt35_cost_per_1k_tokens
    
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
    
    def __init__(self, api_key: str):
        self.classifier = AIClassifier(api_key)
        self.output_dir = Path("data")
        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        
        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
    
    async def process_articles(self, input_file: str = "data/high_quality_articles.csv"):
        """Process all articles for classification"""
        
        logger.info("Starting article classification process...")
        
        # Load articles
        articles = self._load_articles(input_file)
        if not articles:
            logger.error("No articles found to process")
            return
        
        logger.info(f"Loaded {len(articles)} articles for classification")
        
        # Process articles in batches
        batch_size = 10
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
                    'author': str(row.get('author', '')),
                    'url': str(row.get('url', '')),
                    'content': str(row.get('content', '')),
                    'domain': str(row.get('domain', '')),
                    'published_date': str(row.get('published_date', '')),
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
            <title>Mingus Article Classification Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
                .phase {{ margin: 10px 0; padding: 10px; background: #e9ecef; border-radius: 3px; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .error {{ color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Mingus Article Classification Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
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
                    <strong>Total Cost:</strong> ${stats['total_cost']:.2f}
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
        </body>
        </html>
        """
        
        with open(self.reports_dir / "ai_classification_summary.html", 'w') as f:
            f.write(html_content)

async def main():
    """Main execution function"""
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        logger.info("Please set the environment variable: export OPENAI_API_KEY='your-api-key'")
        return
    
    # Validate API key format
    if not api_key.startswith('sk-'):
        logger.error("Invalid API key format. API key should start with 'sk-'")
        return
    
    logger.info("API key found and validated")
    
    # Initialize processor
    processor = ArticleProcessor(api_key)
    
    # Process articles
    await processor.process_articles()
    
    # Final statistics
    stats = processor.classifier.get_statistics()
    logger.info("=== FINAL STATISTICS ===")
    logger.info(f"Total processed: {stats['total_processed']}")
    logger.info(f"Success rate: {stats['success_rate']:.1%}")
    logger.info(f"Total cost: ${stats['total_cost']:.2f}")
    logger.info(f"Processing time: {stats['elapsed_time_seconds']:.1f} seconds")
    logger.info(f"Articles per minute: {stats['articles_per_minute']:.1f}")

if __name__ == "__main__":
    asyncio.run(main())
