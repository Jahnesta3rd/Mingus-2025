#!/usr/bin/env python3
"""
Job Problem Extractor - Phase 1 of Job Description to Problem Statement Analysis
Transforms job descriptions from keyword lists into actionable problem statements
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProblemCategory(Enum):
    """Categories of business problems identified in job descriptions"""
    OPERATIONAL_CHALLENGES = "operational_challenges"
    GROWTH_OBSTACLES = "growth_obstacles"
    SKILL_GAPS = "skill_gaps"
    STRATEGIC_NEEDS = "strategic_needs"

class IndustryContext(Enum):
    """Industry context for problem analysis"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    EDUCATION = "education"
    CONSULTING = "consulting"
    GOVERNMENT = "government"

class CompanyStage(Enum):
    """Company stage for context analysis"""
    STARTUP = "startup"  # 0-50 employees
    SCALE_UP = "scale_up"  # 50-500 employees
    ENTERPRISE = "enterprise"  # 500+ employees

@dataclass
class ProblemStatement:
    """Structured problem statement with context and impact"""
    context: str  # Company description
    challenge: str  # Primary challenge
    impact: str  # Business impact
    desired_outcome: str  # What they want to achieve
    timeframe: str  # When they need it
    constraints: List[str]  # Any limitations

@dataclass
class ProblemAnalysis:
    """Complete problem analysis for a job description"""
    problem_statement: ProblemStatement
    primary_problems: List[Dict[str, Any]]
    secondary_problems: List[Dict[str, Any]]
    tertiary_problems: List[Dict[str, Any]]
    industry_context: IndustryContext
    company_stage: CompanyStage
    confidence_score: float
    extracted_at: datetime

class JobProblemExtractor:
    """
    Extracts business problems from job descriptions using linguistic analysis
    and AI-powered problem statement formulation
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the problem extractor"""
        self.problem_indicators = {
            'pain_points': [
                'challenging', 'complex', 'difficult', 'struggling', 'bottleneck',
                'inefficient', 'manual', 'time-consuming', 'costly', 'risk',
                'problem', 'issue', 'barrier', 'obstacle', 'hindrance',
                'slow', 'outdated', 'legacy', 'broken', 'failing'
            ],
            'growth_signals': [
                'expanding', 'scaling', 'growing', 'new market', 'launch',
                'increase', 'improve', 'optimize', 'modernize', 'transform',
                'accelerate', 'boost', 'enhance', 'upgrade', 'evolve',
                'develop', 'build', 'create', 'establish', 'implement'
            ],
            'gap_indicators': [
                'need', 'require', 'lack', 'missing', 'without', 'seeking',
                'looking for', 'must have', 'essential', 'critical',
                'necessary', 'important', 'vital', 'key', 'mandatory',
                'should have', 'preferred', 'desired', 'wanted'
            ],
            'outcome_goals': [
                'reduce', 'increase', 'improve', 'achieve', 'deliver',
                'ensure', 'maintain', 'drive', 'enable', 'support',
                'facilitate', 'streamline', 'enhance', 'optimize', 'maximize',
                'minimize', 'eliminate', 'prevent', 'secure', 'guarantee'
            ]
        }
        
        self.industry_contexts = {
            IndustryContext.TECHNOLOGY: [
                'software', 'technology', 'tech', 'digital', 'IT', 'engineering',
                'development', 'programming', 'data', 'cloud', 'cybersecurity',
                'artificial intelligence', 'machine learning', 'blockchain'
            ],
            IndustryContext.FINANCE: [
                'finance', 'financial', 'banking', 'investment', 'accounting',
                'trading', 'risk management', 'compliance', 'audit', 'treasury',
                'capital', 'revenue', 'profit', 'ROI', 'budget'
            ],
            IndustryContext.HEALTHCARE: [
                'healthcare', 'medical', 'health', 'clinical', 'patient',
                'hospital', 'pharmaceutical', 'biotech', 'medical device',
                'HIPAA', 'FDA', 'clinical trial', 'diagnosis', 'treatment'
            ],
            IndustryContext.MANUFACTURING: [
                'manufacturing', 'production', 'factory', 'assembly', 'quality',
                'supply chain', 'logistics', 'operations', 'machinery',
                'automation', 'lean', 'six sigma', 'continuous improvement'
            ],
            IndustryContext.RETAIL: [
                'retail', 'e-commerce', 'customer', 'sales', 'marketing',
                'inventory', 'supply chain', 'omnichannel', 'customer experience',
                'merchandising', 'distribution', 'fulfillment'
            ]
        }
        
        self.company_stage_indicators = {
            CompanyStage.STARTUP: [
                'startup', 'early stage', 'founding', 'pioneering', 'innovative',
                'disruptive', 'agile', 'fast-paced', 'dynamic', 'entrepreneurial'
            ],
            CompanyStage.SCALE_UP: [
                'growing', 'scaling', 'expanding', 'mid-stage', 'established',
                'proven', 'mature', 'stable', 'successful', 'leading'
            ],
            CompanyStage.ENTERPRISE: [
                'enterprise', 'fortune', 'global', 'multinational', 'corporate',
                'large-scale', 'established', 'industry leader', 'blue chip',
                'public company', 'conglomerate'
            ]
        }
        
        # Initialize OpenAI if API key provided
        if openai_api_key:
            openai.api_key = openai_api_key
            self.use_ai = True
        else:
            self.use_ai = False
            logger.warning("OpenAI API key not provided. Using rule-based extraction only.")
    
    def extract_problems(self, job_description: str) -> ProblemAnalysis:
        """
        Extract business problems from job description using linguistic analysis
        
        Args:
            job_description: Raw job description text
            
        Returns:
            ProblemAnalysis object with extracted problems and context
        """
        try:
            logger.info("Starting problem extraction from job description")
            
            # Step 1: Clean and preprocess job description
            cleaned_description = self._clean_job_description(job_description)
            
            # Step 2: Extract industry context
            industry_context = self._identify_industry_context(cleaned_description)
            
            # Step 3: Identify company stage
            company_stage = self._identify_company_stage(cleaned_description)
            
            # Step 4: Extract problems using linguistic analysis
            problems = self._extract_problems_linguistic(cleaned_description)
            
            # Step 5: Generate problem statement using AI or rule-based approach
            if self.use_ai:
                problem_statement = self._generate_problem_statement_ai(
                    problems, industry_context, company_stage, cleaned_description
                )
            else:
                problem_statement = self._generate_problem_statement_rule_based(
                    problems, industry_context, company_stage, cleaned_description
                )
            
            # Step 6: Calculate confidence score
            confidence_score = self._calculate_confidence_score(problems, problem_statement)
            
            # Step 7: Categorize problems by importance
            categorized_problems = self._categorize_problems(problems)
            
            return ProblemAnalysis(
                problem_statement=problem_statement,
                primary_problems=categorized_problems['primary'],
                secondary_problems=categorized_problems['secondary'],
                tertiary_problems=categorized_problems['tertiary'],
                industry_context=industry_context,
                company_stage=company_stage,
                confidence_score=confidence_score,
                extracted_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error extracting problems: {str(e)}")
            return self._create_fallback_analysis(job_description)
    
    def _clean_job_description(self, job_description: str) -> str:
        """Clean and preprocess job description text"""
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', job_description.strip())
        
        # Remove common job board formatting
        cleaned = re.sub(r'\[.*?\]', '', cleaned)  # Remove [brackets]
        cleaned = re.sub(r'<.*?>', '', cleaned)  # Remove HTML tags
        cleaned = re.sub(r'https?://\S+', '', cleaned)  # Remove URLs
        
        return cleaned
    
    def _identify_industry_context(self, job_description: str) -> IndustryContext:
        """Identify industry context from job description"""
        description_lower = job_description.lower()
        
        industry_scores = {}
        for industry, keywords in self.industry_contexts.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores, key=industry_scores.get)
        else:
            return IndustryContext.TECHNOLOGY  # Default fallback
    
    def _identify_company_stage(self, job_description: str) -> CompanyStage:
        """Identify company stage from job description"""
        description_lower = job_description.lower()
        
        stage_scores = {}
        for stage, keywords in self.company_stage_indicators.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            stage_scores[stage] = score
        
        if stage_scores:
            return max(stage_scores, key=stage_scores.get)
        else:
            return CompanyStage.SCALE_UP  # Default fallback
    
    def _extract_problems_linguistic(self, job_description: str) -> Dict[str, List[Dict[str, Any]]]:
        """Extract problems using linguistic analysis"""
        problems = {
            'operational_challenges': [],
            'growth_obstacles': [],
            'skill_gaps': [],
            'strategic_needs': []
        }
        
        description_lower = job_description.lower()
        sentences = re.split(r'[.!?]+', job_description)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_lower = sentence.lower()
            
            # Check for pain points
            pain_point_matches = [word for word in self.problem_indicators['pain_points'] 
                                if word in sentence_lower]
            if pain_point_matches:
                problems['operational_challenges'].append({
                    'sentence': sentence,
                    'indicators': pain_point_matches,
                    'category': 'operational_challenges',
                    'confidence': len(pain_point_matches) / len(self.problem_indicators['pain_points'])
                })
            
            # Check for growth signals
            growth_matches = [word for word in self.problem_indicators['growth_signals'] 
                            if word in sentence_lower]
            if growth_matches:
                problems['growth_obstacles'].append({
                    'sentence': sentence,
                    'indicators': growth_matches,
                    'category': 'growth_obstacles',
                    'confidence': len(growth_matches) / len(self.problem_indicators['growth_signals'])
                })
            
            # Check for gap indicators
            gap_matches = [word for word in self.problem_indicators['gap_indicators'] 
                          if word in sentence_lower]
            if gap_matches:
                problems['skill_gaps'].append({
                    'sentence': sentence,
                    'indicators': gap_matches,
                    'category': 'skill_gaps',
                    'confidence': len(gap_matches) / len(self.problem_indicators['gap_indicators'])
                })
            
            # Check for outcome goals
            outcome_matches = [word for word in self.problem_indicators['outcome_goals'] 
                             if word in sentence_lower]
            if outcome_matches:
                problems['strategic_needs'].append({
                    'sentence': sentence,
                    'indicators': outcome_matches,
                    'category': 'strategic_needs',
                    'confidence': len(outcome_matches) / len(self.problem_indicators['outcome_goals'])
                })
        
        return problems
    
    def _generate_problem_statement_ai(self, problems: Dict, industry_context: IndustryContext, 
                                     company_stage: CompanyStage, job_description: str) -> ProblemStatement:
        """Generate problem statement using AI"""
        try:
            prompt = f"""
            Analyze this job description and create a problem statement following this format:
            "[Company] is a [industry] [company stage] facing [primary challenge] 
            which is causing [business impact]. They need [solution category] 
            to achieve [desired outcome] within [timeframe/constraints]."
            
            Job Description: {job_description}
            
            Industry Context: {industry_context.value}
            Company Stage: {company_stage.value}
            
            Extracted Problems: {json.dumps(problems, indent=2)}
            
            Return a JSON object with: context, challenge, impact, desired_outcome, timeframe, constraints
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return ProblemStatement(
                context=result.get('context', ''),
                challenge=result.get('challenge', ''),
                impact=result.get('impact', ''),
                desired_outcome=result.get('desired_outcome', ''),
                timeframe=result.get('timeframe', ''),
                constraints=result.get('constraints', [])
            )
            
        except Exception as e:
            logger.error(f"Error generating AI problem statement: {str(e)}")
            return self._generate_problem_statement_rule_based(problems, industry_context, company_stage, job_description)
    
    def _generate_problem_statement_rule_based(self, problems: Dict, industry_context: IndustryContext,
                                             company_stage: CompanyStage, job_description: str) -> ProblemStatement:
        """Generate problem statement using rule-based approach"""
        
        # Extract company name (simple heuristic)
        company_name = self._extract_company_name(job_description)
        
        # Identify primary challenge
        primary_challenge = self._identify_primary_challenge(problems)
        
        # Generate context
        context = f"{company_name} is a {industry_context.value} {company_stage.value}"
        
        # Generate challenge description
        challenge = primary_challenge if primary_challenge else "operational efficiency challenges"
        
        # Generate impact
        impact = "reduced productivity and increased costs"
        
        # Generate desired outcome
        desired_outcome = "improved efficiency and competitive advantage"
        
        # Generate timeframe
        timeframe = "immediate to 6 months"
        
        # Generate constraints
        constraints = ["budget limitations", "resource constraints"]
        
        return ProblemStatement(
            context=context,
            challenge=challenge,
            impact=impact,
            desired_outcome=desired_outcome,
            timeframe=timeframe,
            constraints=constraints
        )
    
    def _extract_company_name(self, job_description: str) -> str:
        """Extract company name from job description"""
        # Simple heuristic - look for common patterns
        patterns = [
            r'at\s+([A-Z][a-zA-Z\s&]+)',
            r'with\s+([A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-zA-Z\s&]+)\s+is\s+looking',
            r'([A-Z][a-zA-Z\s&]+)\s+seeks'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description)
            if match:
                return match.group(1).strip()
        
        return "Company"
    
    def _identify_primary_challenge(self, problems: Dict) -> str:
        """Identify the primary challenge from extracted problems"""
        all_problems = []
        for category, problem_list in problems.items():
            all_problems.extend(problem_list)
        
        if not all_problems:
            return "operational efficiency challenges"
        
        # Sort by confidence and return highest
        all_problems.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return all_problems[0]['sentence'][:100] + "..." if len(all_problems[0]['sentence']) > 100 else all_problems[0]['sentence']
    
    def _categorize_problems(self, problems: Dict) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize problems by importance (primary, secondary, tertiary)"""
        all_problems = []
        for category, problem_list in problems.items():
            for problem in problem_list:
                problem['original_category'] = category
                all_problems.append(problem)
        
        # Sort by confidence score
        all_problems.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Categorize by confidence thresholds
        primary = [p for p in all_problems if p.get('confidence', 0) >= 0.7]
        secondary = [p for p in all_problems if 0.4 <= p.get('confidence', 0) < 0.7]
        tertiary = [p for p in all_problems if p.get('confidence', 0) < 0.4]
        
        return {
            'primary': primary,
            'secondary': secondary,
            'tertiary': tertiary
        }
    
    def _calculate_confidence_score(self, problems: Dict, problem_statement: ProblemStatement) -> float:
        """Calculate confidence score for the problem analysis"""
        total_problems = sum(len(problem_list) for problem_list in problems.values())
        
        if total_problems == 0:
            return 0.3  # Low confidence if no problems found
        
        # Base confidence on number of problems found and statement quality
        problem_score = min(1.0, total_problems / 10)  # Normalize to 0-1
        
        # Statement quality score (simple heuristic)
        statement_score = 0.5
        if problem_statement.challenge and problem_statement.impact:
            statement_score = 0.8
        if problem_statement.desired_outcome:
            statement_score = 1.0
        
        return (problem_score + statement_score) / 2
    
    def _create_fallback_analysis(self, job_description: str) -> ProblemAnalysis:
        """Create fallback analysis when extraction fails"""
        return ProblemAnalysis(
            problem_statement=ProblemStatement(
                context="Company is a technology scale-up",
                challenge="operational efficiency challenges",
                impact="reduced productivity",
                desired_outcome="improved efficiency",
                timeframe="immediate",
                constraints=["resource limitations"]
            ),
            primary_problems=[],
            secondary_problems=[],
            tertiary_problems=[],
            industry_context=IndustryContext.TECHNOLOGY,
            company_stage=CompanyStage.SCALE_UP,
            confidence_score=0.3,
            extracted_at=datetime.now()
        )

# Example usage and testing
if __name__ == "__main__":
    # Test the problem extractor
    extractor = JobProblemExtractor()
    
    sample_job_description = """
    We're looking for a Senior Data Analyst to help us understand customer behavior 
    and improve campaign performance. You'll work with large datasets, create dashboards, 
    and provide insights to drive marketing strategy. The role involves challenging 
    data integration problems and requires someone who can optimize our reporting processes.
    """
    
    analysis = extractor.extract_problems(sample_job_description)
    print("Problem Analysis Results:")
    print(f"Industry Context: {analysis.industry_context.value}")
    print(f"Company Stage: {analysis.company_stage.value}")
    print(f"Confidence Score: {analysis.confidence_score:.2f}")
    print(f"Problem Statement: {analysis.problem_statement.context} facing {analysis.problem_statement.challenge}")
    print(f"Primary Problems: {len(analysis.primary_problems)}")
    print(f"Secondary Problems: {len(analysis.secondary_problems)}")
    print(f"Tertiary Problems: {len(analysis.tertiary_problems)}")
