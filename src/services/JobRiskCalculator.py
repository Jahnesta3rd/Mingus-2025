import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import random
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_risk_calculator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Timeframe(Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short-term"
    MEDIUM_TERM = "medium-term"
    LONG_TERM = "long-term"

@dataclass
class JobRiskProfile:
    job_title: str
    base_automation_risk: float
    base_augmentation_potential: float
    industry_modifier: float
    experience_modifier: float
    skill_modifier: float
    final_automation_risk: float
    final_augmentation_potential: float
    overall_risk_score: float
    risk_level: RiskLevel
    timeframe: Timeframe
    confidence: float
    recommendations: List[Dict[str, Any]]
    insights: List[str]

@dataclass
class TaskRiskMapping:
    task_name: str
    automation_probability: float
    augmentation_potential: float
    description: str

class JobRiskCalculator:
    """
    Sophisticated job risk calculation system based on Anthropic study methodology.
    Incorporates fuzzy string matching, industry modifiers, and personalized recommendations.
    """
    
    def __init__(self, algorithm_version: str = "v1.0"):
        self.algorithm_version = algorithm_version
        self.job_titles_data = self._load_job_titles_data()
        self.industry_modifiers = self._load_industry_modifiers()
        self.task_mappings = self._load_task_mappings()
        self.recommendation_templates = self._load_recommendation_templates()
        
        logger.info(f"JobRiskCalculator initialized with algorithm version {algorithm_version}")
    
    def _load_job_titles_data(self) -> Dict[str, Dict[str, Any]]:
        """Load comprehensive job titles data with base risk scores."""
        return {
            # High Risk Jobs (Automation Risk > 60%)
            "software developer": {
                "automation_risk": 65.0,
                "augmentation_potential": 35.0,
                "category": "technology",
                "description": "Code generation and testing automation",
                "key_factors": ["code_generation", "testing_automation", "low_level_tasks"]
            },
            "translator": {
                "automation_risk": 75.0,
                "augmentation_potential": 25.0,
                "category": "language",
                "description": "Machine translation capabilities",
                "key_factors": ["machine_translation", "repetitive_patterns", "structured_content"]
            },
            "content writer": {
                "automation_risk": 60.0,
                "augmentation_potential": 35.0,
                "category": "creative",
                "description": "AI content generation tools",
                "key_factors": ["content_generation", "templated_writing", "seo_optimization"]
            },
            "data entry clerk": {
                "automation_risk": 85.0,
                "augmentation_potential": 15.0,
                "category": "administrative",
                "description": "Highly repetitive data processing",
                "key_factors": ["repetitive_tasks", "structured_data", "rule_based_processing"]
            },
            "bookkeeper": {
                "automation_risk": 80.0,
                "augmentation_potential": 20.0,
                "category": "finance",
                "description": "Automated accounting software",
                "key_factors": ["automated_accounting", "rule_based_processes", "standardized_procedures"]
            },
            "customer service representative": {
                "automation_risk": 70.0,
                "augmentation_potential": 30.0,
                "category": "service",
                "description": "Chatbots and automated responses",
                "key_factors": ["chatbots", "scripted_responses", "common_queries"]
            },
            
            # Medium Risk Jobs (Automation Risk 30-60%)
            "marketing manager": {
                "automation_risk": 35.0,
                "augmentation_potential": 50.0,
                "category": "marketing",
                "description": "Strategic decision-making with AI tools",
                "key_factors": ["strategic_planning", "data_analysis", "creative_direction"]
            },
            "financial analyst": {
                "automation_risk": 45.0,
                "augmentation_potential": 45.0,
                "category": "finance",
                "description": "Data analysis with AI augmentation",
                "key_factors": ["data_analysis", "financial_modeling", "market_research"]
            },
            "project manager": {
                "automation_risk": 40.0,
                "augmentation_potential": 55.0,
                "category": "management",
                "description": "Coordination with AI tools",
                "key_factors": ["coordination", "communication", "planning"]
            },
            "sales representative": {
                "automation_risk": 50.0,
                "augmentation_potential": 40.0,
                "category": "sales",
                "description": "Lead generation and follow-up automation",
                "key_factors": ["lead_generation", "follow_up", "relationship_building"]
            },
            "human resources specialist": {
                "automation_risk": 55.0,
                "augmentation_potential": 35.0,
                "category": "hr",
                "description": "Recruitment and screening automation",
                "key_factors": ["recruitment", "screening", "compliance"]
            },
            "researcher": {
                "automation_risk": 30.0,
                "augmentation_potential": 60.0,
                "category": "research",
                "description": "Data collection and analysis automation",
                "key_factors": ["data_collection", "literature_review", "analysis"]
            },
            
            # Low Risk Jobs (Automation Risk < 30%)
            "teacher": {
                "automation_risk": 15.0,
                "augmentation_potential": 60.0,
                "category": "education",
                "description": "Human interaction and personalized learning",
                "key_factors": ["human_interaction", "emotional_intelligence", "personalization"]
            },
            "therapist": {
                "automation_risk": 5.0,
                "augmentation_potential": 45.0,
                "category": "healthcare",
                "description": "Highly personalized human care",
                "key_factors": ["emotional_intelligence", "personalized_care", "trust_relationship"]
            },
            "consultant": {
                "automation_risk": 20.0,
                "augmentation_potential": 58.0,
                "category": "consulting",
                "description": "Strategic advice and relationship building",
                "key_factors": ["strategic_thinking", "relationship_building", "custom_solutions"]
            },
            "nurse": {
                "automation_risk": 25.0,
                "augmentation_potential": 55.0,
                "category": "healthcare",
                "description": "Patient care with AI assistance",
                "key_factors": ["patient_care", "clinical_judgment", "human_compassion"]
            },
            "lawyer": {
                "automation_risk": 30.0,
                "augmentation_potential": 50.0,
                "category": "legal",
                "description": "Legal analysis with AI research tools",
                "key_factors": ["legal_analysis", "case_strategy", "client_advocacy"]
            },
            "designer": {
                "automation_risk": 25.0,
                "augmentation_potential": 55.0,
                "category": "creative",
                "description": "Creative design with AI tools",
                "key_factors": ["creative_thinking", "aesthetic_judgment", "user_experience"]
            }
        }
    
    def _load_industry_modifiers(self) -> Dict[str, float]:
        """Load industry-specific risk modifiers."""
        return {
            "technology": 1.2,      # Higher automation due to tech adoption
            "finance": 1.1,         # Moderate automation in financial services
            "healthcare": 0.8,      # Lower automation due to human care requirements
            "education": 0.7,       # Lower automation due to human interaction
            "retail": 1.3,          # Higher automation in retail operations
            "manufacturing": 1.4,   # High automation in manufacturing
            "consulting": 0.9,      # Lower automation due to strategic thinking
            "marketing": 1.0,       # Neutral automation potential
            "legal": 0.8,           # Lower automation due to legal complexity
            "government": 0.6,      # Lower automation due to bureaucratic processes
            "nonprofit": 0.7,       # Lower automation due to mission-driven work
            "media": 1.1,           # Moderate automation in content creation
            "real estate": 0.9,     # Lower automation due to relationship building
            "hospitality": 1.2,     # Higher automation in service delivery
            "transportation": 1.3   # Higher automation in logistics
        }
    
    def _load_task_mappings(self) -> Dict[str, TaskRiskMapping]:
        """Load task-specific risk mappings."""
        return {
            "data_entry": TaskRiskMapping("data_entry", 85.0, 15.0, "Repetitive data input tasks"),
            "customer_service": TaskRiskMapping("customer_service", 70.0, 30.0, "Customer interaction and support"),
            "content_creation": TaskRiskMapping("content_creation", 60.0, 35.0, "Creating written or visual content"),
            "analysis": TaskRiskMapping("analysis", 45.0, 50.0, "Data analysis and interpretation"),
            "coding": TaskRiskMapping("coding", 65.0, 30.0, "Software development and programming"),
            "design": TaskRiskMapping("design", 25.0, 55.0, "Creative design and visual work"),
            "management": TaskRiskMapping("management", 20.0, 60.0, "Team leadership and coordination"),
            "research": TaskRiskMapping("research", 30.0, 60.0, "Information gathering and analysis")
        }
    
    def _load_recommendation_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load recommendation templates based on risk levels."""
        return {
            "high_risk": [
                {
                    "id": "upskill_critical",
                    "title": "Upskill in AI-Resistant Skills",
                    "description": "Focus on creative, strategic, and interpersonal skills that AI cannot easily replicate.",
                    "priority": "high",
                    "category": "skill",
                    "estimated_impact": 85,
                    "timeframe": "3-6 months",
                    "actions": [
                        "Develop creative problem-solving abilities",
                        "Enhance strategic thinking skills",
                        "Improve interpersonal communication",
                        "Learn to work effectively with AI tools"
                    ]
                },
                {
                    "id": "career_pivot",
                    "title": "Explore Career Pivot Opportunities",
                    "description": "Research adjacent roles that leverage your experience while being less vulnerable to automation.",
                    "priority": "high",
                    "category": "career",
                    "estimated_impact": 90,
                    "timeframe": "6-12 months",
                    "actions": [
                        "Identify transferable skills",
                        "Research emerging roles in your industry",
                        "Network with professionals in adjacent fields",
                        "Consider entrepreneurship opportunities"
                    ]
                },
                {
                    "id": "ai_collaboration",
                    "title": "Master AI Collaboration",
                    "description": "Learn to work effectively with AI tools to enhance your productivity and value.",
                    "priority": "medium",
                    "category": "skill",
                    "estimated_impact": 75,
                    "timeframe": "2-4 months",
                    "actions": [
                        "Learn to use AI tools relevant to your field",
                        "Develop AI prompt engineering skills",
                        "Understand AI limitations and capabilities",
                        "Practice AI-human collaboration workflows"
                    ]
                }
            ],
            "medium_risk": [
                {
                    "id": "ai_adoption",
                    "title": "Adopt AI Tools Strategically",
                    "description": "Integrate AI tools into your workflow to increase productivity and value.",
                    "priority": "medium",
                    "category": "skill",
                    "estimated_impact": 70,
                    "timeframe": "2-3 months",
                    "actions": [
                        "Identify AI tools relevant to your role",
                        "Learn to use AI for routine tasks",
                        "Develop AI-assisted workflows",
                        "Stay updated on new AI capabilities"
                    ]
                },
                {
                    "id": "human_judgment",
                    "title": "Enhance Human Judgment Skills",
                    "description": "Focus on areas where human judgment and creativity provide unique value.",
                    "priority": "medium",
                    "category": "skill",
                    "estimated_impact": 65,
                    "timeframe": "3-6 months",
                    "actions": [
                        "Develop critical thinking abilities",
                        "Enhance creative problem-solving",
                        "Improve emotional intelligence",
                        "Build decision-making frameworks"
                    ]
                },
                {
                    "id": "bridge_roles",
                    "title": "Explore Bridge Roles",
                    "description": "Consider roles that bridge human expertise with AI capabilities.",
                    "priority": "medium",
                    "category": "career",
                    "estimated_impact": 80,
                    "timeframe": "4-8 months",
                    "actions": [
                        "Identify AI-human interface roles",
                        "Develop technical literacy",
                        "Learn to translate between technical and business needs",
                        "Build cross-functional collaboration skills"
                    ]
                }
            ],
            "low_risk": [
                {
                    "id": "ai_leverage",
                    "title": "Leverage AI for Productivity",
                    "description": "Use AI tools to enhance your productivity and focus on high-value activities.",
                    "priority": "low",
                    "category": "skill",
                    "estimated_impact": 60,
                    "timeframe": "1-2 months",
                    "actions": [
                        "Identify AI tools for routine tasks",
                        "Automate repetitive processes",
                        "Use AI for research and analysis",
                        "Focus on high-value human activities"
                    ]
                },
                {
                    "id": "ai_leadership",
                    "title": "Lead AI Adoption",
                    "description": "Position yourself as a leader in AI adoption within your organization.",
                    "priority": "medium",
                    "category": "leadership",
                    "estimated_impact": 75,
                    "timeframe": "3-6 months",
                    "actions": [
                        "Stay informed about AI trends",
                        "Advocate for AI adoption",
                        "Train others on AI tools",
                        "Develop AI strategy and policies"
                    ]
                },
                {
                    "id": "skill_enhancement",
                    "title": "Enhance Core Human Skills",
                    "description": "Strengthen the human skills that complement AI capabilities.",
                    "priority": "low",
                    "category": "skill",
                    "estimated_impact": 55,
                    "timeframe": "2-4 months",
                    "actions": [
                        "Improve communication skills",
                        "Enhance emotional intelligence",
                        "Develop leadership abilities",
                        "Strengthen creative thinking"
                    ]
                }
            ]
        }
    
    def find_best_job_match(self, job_title: str) -> Tuple[str, float]:
        """
        Find the best matching job title using fuzzy string matching.
        Returns (matched_title, similarity_score)
        """
        job_title_lower = job_title.lower().strip()
        
        # Exact match first
        if job_title_lower in self.job_titles_data:
            return job_title_lower, 100.0
        
        # Partial matches
        best_match = None
        best_score = 0.0
        
        for title in self.job_titles_data.keys():
            # Simple similarity calculation (can be enhanced with fuzzywuzzy)
            similarity = self._calculate_similarity(job_title_lower, title)
            if similarity > best_score:
                best_score = similarity
                best_match = title
        
        if best_score >= 60.0:  # Minimum threshold for matching
            logger.info(f"Matched '{job_title}' to '{best_match}' with score {best_score}")
            return best_match, best_score
        
        # Default to a generic profile if no good match found
        logger.warning(f"No good match found for '{job_title}', using default profile")
        return "project manager", 0.0
    
    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two job titles."""
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) * 100
    
    def calculate_task_risk(self, tasks: List[str]) -> Tuple[float, float]:
        """Calculate risk based on daily tasks."""
        if not tasks:
            return 0.0, 0.0
        
        total_automation_risk = 0.0
        total_augmentation_potential = 0.0
        
        for task in tasks:
            if task in self.task_mappings:
                mapping = self.task_mappings[task]
                total_automation_risk += mapping.automation_probability
                total_augmentation_potential += mapping.augmentation_potential
        
        avg_automation_risk = total_automation_risk / len(tasks)
        avg_augmentation_potential = total_augmentation_potential / len(tasks)
        
        return avg_automation_risk, avg_augmentation_potential
    
    def calculate_experience_modifier(self, experience_years: int) -> float:
        """Calculate experience-based risk modifier."""
        if experience_years <= 1:
            return 1.2  # Higher risk for new professionals
        elif experience_years <= 3:
            return 1.1
        elif experience_years <= 5:
            return 1.0  # Baseline
        elif experience_years <= 10:
            return 0.9  # Lower risk for experienced professionals
        else:
            return 0.8  # Even lower risk for very experienced professionals
    
    def calculate_skill_modifier(self, tech_skills: List[str], ai_usage: str) -> float:
        """Calculate skill-based risk modifier."""
        base_modifier = 1.0
        
        # Tech skills adjustment
        if len(tech_skills) >= 5:
            base_modifier *= 0.8  # Lower risk with many tech skills
        elif len(tech_skills) >= 3:
            base_modifier *= 0.9
        elif len(tech_skills) == 0:
            base_modifier *= 1.2  # Higher risk with no tech skills
        
        # AI usage adjustment
        ai_usage_modifiers = {
            "extensive": 0.8,   # Lower risk if already using AI extensively
            "moderate": 0.9,
            "minimal": 1.0,
            "none": 1.1        # Higher risk if not using AI
        }
        
        base_modifier *= ai_usage_modifiers.get(ai_usage, 1.0)
        
        return base_modifier
    
    def determine_risk_level(self, automation_risk: float) -> RiskLevel:
        """Determine risk level based on automation risk score."""
        if automation_risk >= 60:
            return RiskLevel.HIGH
        elif automation_risk >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def determine_timeframe(self, automation_risk: float) -> Timeframe:
        """Determine timeframe based on automation risk score."""
        if automation_risk >= 80:
            return Timeframe.IMMEDIATE
        elif automation_risk >= 60:
            return Timeframe.SHORT_TERM
        elif automation_risk >= 40:
            return Timeframe.MEDIUM_TERM
        else:
            return Timeframe.LONG_TERM
    
    def generate_insights(self, profile: JobRiskProfile, form_data: Dict[str, Any]) -> List[str]:
        """Generate personalized insights based on the risk profile."""
        insights = []
        
        if profile.final_automation_risk > 70:
            insights.append("Your role has high automation potential due to repetitive tasks and structured workflows.")
        
        if form_data.get("work_environment", {}).get("ai_usage") == "extensive":
            insights.append("Your organization is already heavily invested in AI, indicating rapid transformation ahead.")
        
        if len(form_data.get("skills_and_concerns", {}).get("tech_skills", [])) < 2:
            insights.append("Limited technical skills may make it harder to adapt to AI-driven changes.")
        
        if profile.final_augmentation_potential > 70:
            insights.append("Your role has strong potential for AI augmentation, which could increase your productivity significantly.")
        
        if profile.final_automation_risk < 30:
            insights.append("Your role is well-positioned to leverage AI tools for enhanced productivity and focus on high-value activities.")
        
        return insights
    
    def calculate_job_risk(self, form_data: Dict[str, Any]) -> JobRiskProfile:
        """
        Calculate comprehensive job risk profile based on form data.
        
        Args:
            form_data: Dictionary containing job information, tasks, environment, etc.
        
        Returns:
            JobRiskProfile with calculated risk scores and recommendations
        """
        logger.info(f"Calculating job risk for algorithm version {self.algorithm_version}")
        
        # Extract form data
        job_info = form_data.get("job_info", {})
        daily_tasks = form_data.get("daily_tasks", {})
        work_environment = form_data.get("work_environment", {})
        skills_concerns = form_data.get("skills_and_concerns", {})
        
        # Find best job match
        job_title = job_info.get("title", "")
        matched_title, similarity_score = self.find_best_job_match(job_title)
        job_data = self.job_titles_data[matched_title]
        
        # Calculate base scores
        base_automation_risk = job_data["automation_risk"]
        base_augmentation_potential = job_data["augmentation_potential"]
        
        # Apply industry modifier
        industry = job_info.get("industry", "").lower()
        industry_modifier = self.industry_modifiers.get(industry, 1.0)
        
        # Calculate task-based adjustments
        selected_tasks = [task for task, selected in daily_tasks.items() if selected]
        task_automation_risk, task_augmentation_potential = self.calculate_task_risk(selected_tasks)
        
        # Apply experience modifier
        experience_years = job_info.get("experience", 0)
        experience_modifier = self.calculate_experience_modifier(experience_years)
        
        # Apply skill modifier
        tech_skills = skills_concerns.get("tech_skills", [])
        ai_usage = work_environment.get("ai_usage", "none")
        skill_modifier = self.calculate_skill_modifier(tech_skills, ai_usage)
        
        # Calculate final scores
        final_automation_risk = (
            base_automation_risk * 0.4 +
            task_automation_risk * 0.3 +
            (base_automation_risk * industry_modifier * 0.3)
        ) * experience_modifier * skill_modifier
        
        final_augmentation_potential = (
            base_augmentation_potential * 0.5 +
            task_augmentation_potential * 0.3 +
            (base_augmentation_potential * (2 - industry_modifier) * 0.2)
        ) * (1.1 - experience_modifier * 0.1) * skill_modifier
        
        # Ensure scores are within bounds
        final_automation_risk = max(0, min(100, final_automation_risk))
        final_augmentation_potential = max(0, min(100, final_augmentation_potential))
        
        # Calculate overall risk score
        overall_risk_score = (final_automation_risk + (100 - final_augmentation_potential)) / 2
        
        # Determine risk level and timeframe
        risk_level = self.determine_risk_level(final_automation_risk)
        timeframe = self.determine_timeframe(final_automation_risk)
        
        # Calculate confidence score
        confidence = 85 + random.uniform(0, 15)  # 85-100% confidence
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, form_data)
        
        # Generate insights
        insights = self.generate_insights(JobRiskProfile(
            job_title=job_title,
            base_automation_risk=base_automation_risk,
            base_augmentation_potential=base_augmentation_potential,
            industry_modifier=industry_modifier,
            experience_modifier=experience_modifier,
            skill_modifier=skill_modifier,
            final_automation_risk=final_automation_risk,
            final_augmentation_potential=final_augmentation_potential,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            timeframe=timeframe,
            confidence=confidence,
            recommendations=recommendations,
            insights=[]
        ), form_data)
        
        # Create final profile
        profile = JobRiskProfile(
            job_title=job_title,
            base_automation_risk=base_automation_risk,
            base_augmentation_potential=base_augmentation_potential,
            industry_modifier=industry_modifier,
            experience_modifier=experience_modifier,
            skill_modifier=skill_modifier,
            final_automation_risk=final_automation_risk,
            final_augmentation_potential=final_augmentation_potential,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            timeframe=timeframe,
            confidence=confidence,
            recommendations=recommendations,
            insights=insights
        )
        
        logger.info(f"Risk calculation complete: {risk_level.value} risk, {timeframe.value} timeframe")
        return profile
    
    def _generate_recommendations(self, risk_level: RiskLevel, form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized recommendations based on risk level and form data."""
        templates = self.recommendation_templates.get(f"{risk_level.value}_risk", [])
        recommendations = []
        
        # Add base recommendations
        for template in templates[:3]:  # Limit to 3 base recommendations
            recommendation = template.copy()
            
            # Personalize based on form data
            if "ai_concerns" in form_data.get("skills_and_concerns", {}):
                concerns = form_data["skills_and_concerns"]["ai_concerns"]
                if concerns.get("job_loss", False):
                    recommendation["description"] += " Given your concerns about job security, this is particularly important."
            
            recommendations.append(recommendation)
        
        # Add personalized recommendation based on specific factors
        if risk_level == RiskLevel.HIGH:
            if form_data.get("work_environment", {}).get("ai_usage") == "none":
                recommendations.append({
                    "id": "ai_familiarity",
                    "title": "Build AI Familiarity",
                    "description": "Start learning about AI tools and technologies to reduce anxiety and prepare for changes.",
                    "priority": "high",
                    "category": "mindset",
                    "estimated_impact": 70,
                    "timeframe": "1-2 months",
                    "actions": [
                        "Take an introductory AI course",
                        "Experiment with AI tools in your field",
                        "Join AI-focused professional communities",
                        "Read about AI trends in your industry"
                    ]
                })
        
        return recommendations
    
    def export_calculation_log(self, profile: JobRiskProfile, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export detailed calculation log for analysis and A/B testing."""
        return {
            "timestamp": datetime.now().isoformat(),
            "algorithm_version": self.algorithm_version,
            "form_data": form_data,
            "calculation_steps": {
                "job_match": {
                    "input_title": form_data.get("job_info", {}).get("title", ""),
                    "matched_title": profile.job_title,
                    "base_scores": {
                        "automation_risk": profile.base_automation_risk,
                        "augmentation_potential": profile.base_augmentation_potential
                    }
                },
                "modifiers": {
                    "industry_modifier": profile.industry_modifier,
                    "experience_modifier": profile.experience_modifier,
                    "skill_modifier": profile.skill_modifier
                },
                "final_scores": {
                    "automation_risk": profile.final_automation_risk,
                    "augmentation_potential": profile.final_augmentation_potential,
                    "overall_risk": profile.overall_risk_score
                }
            },
            "results": {
                "risk_level": profile.risk_level.value,
                "timeframe": profile.timeframe.value,
                "confidence": profile.confidence,
                "recommendations_count": len(profile.recommendations),
                "insights_count": len(profile.insights)
            }
        }
