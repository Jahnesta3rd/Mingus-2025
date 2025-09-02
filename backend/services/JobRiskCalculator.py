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
            # Medium Risk Jobs (Automation Risk 30-60%)
            "accountant": {
                "automation_risk": 45.0,
                "augmentation_potential": 55.0,
                "category": "finance",
                "description": "Automated bookkeeping and reporting",
                "key_factors": ["automated_bookkeeping", "financial_analysis", "compliance_reporting"]
            },
            "marketing manager": {
                "automation_risk": 35.0,
                "augmentation_potential": 65.0,
                "category": "marketing",
                "description": "AI-powered campaign optimization",
                "key_factors": ["campaign_optimization", "data_analysis", "content_personalization"]
            },
            "sales representative": {
                "automation_risk": 40.0,
                "augmentation_potential": 60.0,
                "category": "sales",
                "description": "Lead scoring and customer insights",
                "key_factors": ["lead_scoring", "customer_insights", "sales_automation"]
            },
            # Low Risk Jobs (Automation Risk < 30%)
            "nurse": {
                "automation_risk": 20.0,
                "augmentation_potential": 80.0,
                "category": "healthcare",
                "description": "Patient care and medical decision support",
                "key_factors": ["patient_care", "medical_decision_support", "healthcare_technology"]
            },
            "teacher": {
                "automation_risk": 25.0,
                "augmentation_potential": 75.0,
                "category": "education",
                "description": "Personalized learning and assessment",
                "key_factors": ["personalized_learning", "assessment_tools", "curriculum_development"]
            },
            "psychologist": {
                "automation_risk": 15.0,
                "augmentation_potential": 85.0,
                "category": "mental_health",
                "description": "Therapeutic support and assessment tools",
                "key_factors": ["therapeutic_support", "assessment_tools", "mental_health_technology"]
            }
        }
    
    def _load_industry_modifiers(self) -> Dict[str, float]:
        """Load industry-specific risk modifiers."""
        return {
            "technology": 1.2,      # Higher automation risk
            "finance": 1.1,         # Moderate automation risk
            "healthcare": 0.8,      # Lower automation risk
            "education": 0.7,       # Lower automation risk
            "manufacturing": 1.3,   # Higher automation risk
            "retail": 1.0,          # Standard automation risk
            "consulting": 0.9,      # Lower automation risk
            "creative": 0.8,        # Lower automation risk
            "legal": 0.6,           # Lower automation risk
            "government": 0.7       # Lower automation risk
        }
    
    def _load_task_mappings(self) -> Dict[str, TaskRiskMapping]:
        """Load task-specific risk mappings."""
        return {
            "coding": TaskRiskMapping(
                task_name="coding",
                automation_probability=0.7,
                augmentation_potential=0.8,
                description="Software development and programming tasks"
            ),
            "testing": TaskRiskMapping(
                task_name="testing",
                automation_probability=0.8,
                augmentation_potential=0.6,
                description="Quality assurance and testing procedures"
            ),
            "meetings": TaskRiskMapping(
                task_name="meetings",
                automation_probability=0.3,
                augmentation_potential=0.9,
                description="Team collaboration and communication"
            ),
            "documentation": TaskRiskMapping(
                task_name="documentation",
                automation_probability=0.6,
                augmentation_potential=0.7,
                description="Technical writing and documentation"
            ),
            "code_review": TaskRiskMapping(
                task_name="code_review",
                automation_probability=0.5,
                augmentation_potential=0.8,
                description="Code quality assessment and feedback"
            ),
            "planning": TaskRiskMapping(
                task_name="planning",
                automation_probability=0.4,
                augmentation_potential=0.9,
                description="Strategic planning and project management"
            )
        }
    
    def _load_recommendation_templates(self) -> Dict[str, List[str]]:
        """Load recommendation templates for different risk levels."""
        return {
            "high_risk": [
                "Consider upskilling in areas that complement AI tools",
                "Focus on high-value, creative, and strategic work",
                "Develop expertise in AI-human collaboration",
                "Explore emerging roles in AI oversight and governance"
            ],
            "medium_risk": [
                "Enhance skills that leverage AI augmentation",
                "Focus on relationship building and strategic thinking",
                "Develop expertise in data interpretation and decision-making",
                "Stay current with industry-specific AI applications"
            ],
            "low_risk": [
                "Continue developing human-centric skills",
                "Focus on emotional intelligence and empathy",
                "Develop expertise in AI tool integration",
                "Leverage technology to enhance service delivery"
            ]
        }
    
    def find_best_job_match(self, job_title: str) -> Tuple[str, float]:
        """
        Find the best matching job title using fuzzy string matching.
        
        Args:
            job_title: Input job title to match
            
        Returns:
            Tuple of (matched_job_title, similarity_score)
        """
        job_title_lower = job_title.lower().strip()
        
        # Exact match
        if job_title_lower in self.job_titles_data:
            return job_title_lower, 1.0
        
        # Fuzzy matching
        best_match = None
        best_similarity = 0.0
        
        for known_title in self.job_titles_data.keys():
            similarity = self._calculate_string_similarity(job_title_lower, known_title)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = known_title
        
        # Return best match if similarity is above threshold
        if best_similarity > 0.3:
            return best_match, best_similarity
        
        # Return default job title if no good match found
        return "software developer", 0.1
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using simple algorithm."""
        if str1 == str2:
            return 1.0
        
        # Simple word-based similarity
        words1 = set(str1.split())
        words2 = set(str2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_task_risk(self, selected_tasks: List[str]) -> Tuple[float, float]:
        """
        Calculate automation risk and augmentation potential based on selected tasks.
        
        Args:
            selected_tasks: List of task names
            
        Returns:
            Tuple of (automation_risk, augmentation_potential)
        """
        if not selected_tasks:
            return 0.0, 0.0
        
        total_automation = 0.0
        total_augmentation = 0.0
        
        for task in selected_tasks:
            if task in self.task_mappings:
                mapping = self.task_mappings[task]
                total_automation += mapping.automation_probability
                total_augmentation += mapping.augmentation_potential
        
        avg_automation = total_automation / len(selected_tasks)
        avg_augmentation = total_augmentation / len(selected_tasks)
        
        return avg_automation * 100, avg_augmentation * 100
    
    def calculate_experience_modifier(self, experience_years: int) -> float:
        """
        Calculate experience-based risk modifier.
        
        Args:
            experience_years: Years of professional experience
            
        Returns:
            Experience modifier value
        """
        if experience_years <= 2:
            return 1.2  # Higher risk for junior positions
        elif experience_years <= 5:
            return 1.0  # Standard risk for mid-level positions
        elif experience_years <= 10:
            return 0.9  # Lower risk for senior positions
        else:
            return 0.8  # Lower risk for expert positions
    
    def calculate_skill_modifier(self, tech_skills: List[str], soft_skills: List[str]) -> float:
        """
        Calculate skill-based risk modifier.
        
        Args:
            tech_skills: List of technical skills
            soft_skills: List of soft skills
            
        Returns:
            Skill modifier value
        """
        # Technical skills can increase automation risk but also augmentation potential
        tech_score = len(tech_skills) * 0.05
        
        # Soft skills generally reduce automation risk
        soft_score = len(soft_skills) * 0.03
        
        # Balance the modifiers
        modifier = 1.0 + tech_score - soft_score
        
        # Clamp to reasonable range
        return max(0.7, min(1.3, modifier))
    
    def calculate_industry_modifier(self, industry: str) -> float:
        """
        Calculate industry-specific risk modifier.
        
        Args:
            industry: Industry name
            
        Returns:
            Industry modifier value
        """
        return self.industry_modifiers.get(industry.lower(), 1.0)
    
    def generate_job_risk_profile(self, form_data: Dict[str, Any]) -> JobRiskProfile:
        """
        Generate comprehensive job risk profile from form data.
        
        Args:
            form_data: Dictionary containing job information
            
        Returns:
            JobRiskProfile object with calculated risk assessment
        """
        # Extract data from form
        job_info = form_data.get("job_info", {})
        daily_tasks = form_data.get("daily_tasks", {})
        work_environment = form_data.get("work_environment", {})
        skills_and_concerns = form_data.get("skills_and_concerns", {})
        
        # Find best job match
        job_title = job_info.get("title", "software developer")
        matched_title, similarity = self.find_best_job_match(job_title)
        
        # Get base risk scores
        base_data = self.job_titles_data.get(matched_title, self.job_titles_data["software developer"])
        base_automation_risk = base_data["automation_risk"]
        base_augmentation_potential = base_data["augmentation_potential"]
        
        # Calculate modifiers
        industry = job_info.get("industry", "technology")
        industry_modifier = self.calculate_industry_modifier(industry)
        
        experience_years = job_info.get("experience", 5)
        experience_modifier = self.calculate_experience_modifier(experience_years)
        
        tech_skills = skills_and_concerns.get("tech_skills", [])
        soft_skills = skills_and_concerns.get("soft_skills", [])
        skill_modifier = self.calculate_skill_modifier(tech_skills, soft_skills)
        
        # Calculate task-based adjustments
        selected_tasks = [task for task, selected in daily_tasks.items() if selected]
        task_automation_risk, task_augmentation_potential = self.calculate_task_risk(selected_tasks)
        
        # Apply modifiers
        final_automation_risk = base_automation_risk * industry_modifier * experience_modifier * skill_modifier
        final_augmentation_potential = base_augmentation_potential * (1.0 / industry_modifier) * (1.0 / experience_modifier) * skill_modifier
        
        # Blend with task-based scores
        final_automation_risk = (final_automation_risk * 0.7) + (task_automation_risk * 0.3)
        final_augmentation_potential = (final_augmentation_potential * 0.7) + (task_augmentation_potential * 0.3)
        
        # Calculate overall risk score
        overall_risk_score = (final_automation_risk * 0.6) + (final_augmentation_potential * 0.4)
        
        # Determine risk level
        if overall_risk_score >= 60:
            risk_level = RiskLevel.HIGH
            timeframe = Timeframe.SHORT_TERM
        elif overall_risk_score >= 40:
            risk_level = RiskLevel.MEDIUM
            timeframe = Timeframe.MEDIUM_TERM
        else:
            risk_level = RiskLevel.LOW
            timeframe = Timeframe.LONG_TERM
        
        # Calculate confidence based on data quality
        confidence = min(0.95, 0.7 + (similarity * 0.2) + (len(selected_tasks) * 0.05))
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, form_data)
        
        # Generate insights
        insights = self._generate_insights(form_data, final_automation_risk, final_augmentation_potential)
        
        return JobRiskProfile(
            job_title=matched_title,
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
    
    def _generate_recommendations(self, risk_level: RiskLevel, form_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized recommendations based on risk level and form data."""
        recommendations = []
        
        # Get base recommendations for risk level
        risk_key = f"{risk_level.value}_risk"
        base_recommendations = self.recommendation_templates.get(risk_key, [])
        
        for rec in base_recommendations:
            recommendations.append({
                "type": "general",
                "priority": "medium",
                "description": rec,
                "estimated_impact": "moderate"
            })
        
        # Add specific recommendations based on form data
        if "ai_usage" in form_data.get("work_environment", {}):
            ai_usage = form_data["work_environment"]["ai_usage"]
            if ai_usage == "low":
                recommendations.append({
                    "type": "skill_development",
                    "priority": "high",
                    "description": "Start exploring AI tools relevant to your field",
                    "estimated_impact": "high"
                })
            elif ai_usage == "high":
                recommendations.append({
                    "type": "strategy",
                    "priority": "high",
                    "description": "Develop expertise in AI oversight and human-AI collaboration",
                    "estimated_impact": "high"
                })
        
        # Add recommendations based on concerns
        concerns = form_data.get("skills_and_concerns", {}).get("concerns", [])
        for concern in concerns:
            if "automation" in concern.lower():
                recommendations.append({
                    "type": "skill_development",
                    "priority": "high",
                    "description": "Focus on developing skills that complement automation",
                    "estimated_impact": "high"
                })
            elif "skill_gaps" in concern.lower():
                recommendations.append({
                    "type": "skill_development",
                    "priority": "medium",
                    "description": "Identify and address specific skill gaps in your field",
                    "estimated_impact": "moderate"
                })
        
        return recommendations
    
    def _generate_insights(self, form_data: Dict[str, Any], automation_risk: float, augmentation_potential: float) -> List[str]:
        """Generate insights based on form data and calculated risks."""
        insights = []
        
        # Industry insights
        industry = form_data.get("job_info", {}).get("industry", "")
        if industry == "technology":
            insights.append("Technology sector shows high automation potential but also high augmentation opportunities")
        elif industry == "healthcare":
            insights.append("Healthcare sector maintains strong human-centric focus with AI augmentation")
        
        # Experience insights
        experience = form_data.get("job_info", {}).get("experience", 0)
        if experience < 3:
            insights.append("Early career positions may face higher automation risk - focus on skill development")
        elif experience > 10:
            insights.append("Senior experience provides strategic value that's difficult to automate")
        
        # Task insights
        daily_tasks = form_data.get("daily_tasks", {})
        automated_tasks = sum(1 for task, selected in daily_tasks.items() if selected and self.task_mappings.get(task, TaskRiskMapping("", 0, 0, "")).automation_probability > 0.6)
        if automated_tasks > 3:
            insights.append("Many of your daily tasks have high automation potential - consider strategic repositioning")
        
        # Risk level insights
        if automation_risk > 60:
            insights.append("High automation risk detected - focus on uniquely human skills and strategic thinking")
        elif automation_risk < 30:
            insights.append("Low automation risk - continue developing human-centric expertise")
        
        return insights
    
    def get_algorithm_version(self) -> str:
        """Get the current algorithm version."""
        return self.algorithm_version
    
    def update_algorithm_version(self, new_version: str):
        """Update the algorithm version."""
        self.algorithm_version = new_version
        logger.info(f"Algorithm version updated to {new_version}")
    
    def export_profile_to_json(self, profile: JobRiskProfile) -> str:
        """Export job risk profile to JSON format."""
        try:
            # Convert enum values to strings for JSON serialization
            profile_dict = {
                "job_title": profile.job_title,
                "base_automation_risk": profile.base_automation_risk,
                "base_augmentation_potential": profile.base_augmentation_potential,
                "industry_modifier": profile.industry_modifier,
                "experience_modifier": profile.experience_modifier,
                "skill_modifier": profile.skill_modifier,
                "final_automation_risk": profile.final_automation_risk,
                "final_augmentation_potential": profile.final_augmentation_potential,
                "overall_risk_score": profile.overall_risk_score,
                "risk_level": profile.risk_level.value,
                "timeframe": profile.timeframe.value,
                "confidence": profile.confidence,
                "recommendations": profile.recommendations,
                "insights": profile.insights
            }
            
            return json.dumps(profile_dict, indent=2)
        except Exception as e:
            logger.error(f"Error exporting profile to JSON: {e}")
            return "{}"
    
    def validate_form_data(self, form_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate form data for completeness and correctness.
        
        Args:
            form_data: Dictionary containing form data
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        required_fields = ["job_info", "daily_tasks", "work_environment", "skills_and_concerns"]
        for field in required_fields:
            if field not in form_data:
                errors.append(f"Missing required field: {field}")
        
        # Check job_info subfields
        if "job_info" in form_data:
            job_info = form_data["job_info"]
            if "title" not in job_info:
                errors.append("Missing job title in job_info")
            if "industry" not in job_info:
                errors.append("Missing industry in job_info")
            if "experience" not in job_info:
                errors.append("Missing experience in job_info")
        
        # Check daily_tasks
        if "daily_tasks" in form_data:
            daily_tasks = form_data["daily_tasks"]
            if not isinstance(daily_tasks, dict):
                errors.append("daily_tasks must be a dictionary")
            elif not daily_tasks:
                errors.append("At least one daily task must be selected")
        
        # Check skills_and_concerns
        if "skills_and_concerns" in form_data:
            skills_concerns = form_data["skills_and_concerns"]
            if "tech_skills" not in skills_concerns:
                errors.append("Missing tech_skills in skills_and_concerns")
            if "soft_skills" not in skills_concerns:
                errors.append("Missing soft_skills in skills_and_concerns")
        
        return len(errors) == 0, errors
