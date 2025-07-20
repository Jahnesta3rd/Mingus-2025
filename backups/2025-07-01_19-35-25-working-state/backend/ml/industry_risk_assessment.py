"""
Industry Risk Assessment System
Comprehensive analysis of industry risks including NAICS mapping, employment trends,
automation/AI replacement risks, and career advancement insights for African American professionals.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import requests
from loguru import logger
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class EconomicCycle(Enum):
    """Economic cycle phases"""
    EXPANSION = "expansion"
    PEAK = "peak"
    CONTRACTION = "contraction"
    TROUGH = "trough"

@dataclass
class IndustryRiskProfile:
    """Comprehensive industry risk profile"""
    naics_code: str
    industry_name: str
    risk_level: RiskLevel
    overall_score: float  # 0-100, higher = more risk
    
    # Employment metrics
    employment_trend: float  # -100 to 100, negative = declining
    job_growth_rate: float  # Annual percentage
    unemployment_rate: float
    labor_force_participation: float
    
    # Automation/AI risks
    automation_risk_score: float  # 0-100
    ai_replacement_probability: float  # 0-1
    routine_task_percentage: float  # 0-100
    cognitive_skill_requirement: float  # 0-100
    
    # Economic sensitivity
    economic_cycle_sensitivity: float  # 0-100
    recession_resilience: float  # 0-100
    gdp_correlation: float  # -1 to 1
    
    # Geographic factors
    geographic_concentration: float  # 0-100
    remote_work_adoption: float  # 0-100
    location_flexibility: float  # 0-100
    
    # Career advancement
    advancement_opportunities: float  # 0-100
    skill_development_potential: float  # 0-100
    salary_growth_potential: float  # 0-100
    leadership_representation: float  # 0-100
    
    # Risk factors
    risk_factors: List[str] = field(default_factory=list)
    positive_indicators: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.utcnow)
    data_sources: List[str] = field(default_factory=list)
    confidence_level: float = 0.0  # 0-1

@dataclass
class IndustryTrends:
    """Historical and projected industry trends"""
    industry_code: str
    time_period: str
    employment_level: int
    employment_change: float
    wage_growth: float
    productivity_growth: float
    automation_investment: float
    remote_work_percentage: float

class IndustryRiskAssessor:
    """
    Comprehensive industry risk assessment system for African American professionals
    targeting industries with high representation and growth potential.
    """
    
    def __init__(self, bls_api_key: Optional[str] = None):
        self.bls_api_key = bls_api_key
        self.naics_mapping = self._load_naics_mapping()
        self.industry_profiles = self._initialize_industry_profiles()
        self.trend_data = {}
        self.scaler = StandardScaler()
        
    def _load_naics_mapping(self) -> Dict[str, Dict[str, Any]]:
        """Load NAICS code mapping with industry classifications"""
        return {
            # Technology/Software
            "511200": {
                "name": "Software Publishers",
                "category": "Technology",
                "target_demographic_relevance": 0.9,
                "growth_potential": 0.85
            },
            "541500": {
                "name": "Computer Systems Design and Related Services",
                "category": "Technology", 
                "target_demographic_relevance": 0.9,
                "growth_potential": 0.8
            },
            "518200": {
                "name": "Data Processing, Hosting, and Related Services",
                "category": "Technology",
                "target_demographic_relevance": 0.85,
                "growth_potential": 0.9
            },
            
            # Healthcare
            "621100": {
                "name": "Offices of Physicians",
                "category": "Healthcare",
                "target_demographic_relevance": 0.8,
                "growth_potential": 0.75
            },
            "621300": {
                "name": "Offices of Other Health Practitioners",
                "category": "Healthcare",
                "target_demographic_relevance": 0.75,
                "growth_potential": 0.8
            },
            "622000": {
                "name": "Hospitals",
                "category": "Healthcare",
                "target_demographic_relevance": 0.8,
                "growth_potential": 0.7
            },
            
            # Financial Services
            "522100": {
                "name": "Depository Credit Intermediation",
                "category": "Financial Services",
                "target_demographic_relevance": 0.7,
                "growth_potential": 0.6
            },
            "523100": {
                "name": "Securities and Commodity Contracts Intermediation and Brokerage",
                "category": "Financial Services",
                "target_demographic_relevance": 0.65,
                "growth_potential": 0.7
            },
            "524100": {
                "name": "Insurance Carriers",
                "category": "Financial Services",
                "target_demographic_relevance": 0.7,
                "growth_potential": 0.65
            },
            
            # Education
            "611100": {
                "name": "Elementary and Secondary Schools",
                "category": "Education",
                "target_demographic_relevance": 0.85,
                "growth_potential": 0.6
            },
            "611300": {
                "name": "Colleges, Universities, and Professional Schools",
                "category": "Education",
                "target_demographic_relevance": 0.8,
                "growth_potential": 0.7
            },
            
            # Government/Public Sector
            "921000": {
                "name": "Executive, Legislative, and Other General Government Support",
                "category": "Government",
                "target_demographic_relevance": 0.8,
                "growth_potential": 0.5
            },
            "922000": {
                "name": "Justice, Public Order, and Safety Activities",
                "category": "Government",
                "target_demographic_relevance": 0.75,
                "growth_potential": 0.6
            },
            
            # Retail/Hospitality
            "445000": {
                "name": "Food and Beverage Stores",
                "category": "Retail",
                "target_demographic_relevance": 0.6,
                "growth_potential": 0.4
            },
            "722000": {
                "name": "Food Services and Drinking Places",
                "category": "Hospitality",
                "target_demographic_relevance": 0.5,
                "growth_potential": 0.3
            },
            
            # Manufacturing
            "332000": {
                "name": "Fabricated Metal Product Manufacturing",
                "category": "Manufacturing",
                "target_demographic_relevance": 0.4,
                "growth_potential": 0.5
            },
            "333000": {
                "name": "Machinery Manufacturing",
                "category": "Manufacturing",
                "target_demographic_relevance": 0.45,
                "growth_potential": 0.6
            },
            
            # Professional Services
            "541100": {
                "name": "Legal Services",
                "category": "Professional Services",
                "target_demographic_relevance": 0.75,
                "growth_potential": 0.7
            },
            "541200": {
                "name": "Accounting, Tax Preparation, Bookkeeping, and Payroll Services",
                "category": "Professional Services",
                "target_demographic_relevance": 0.7,
                "growth_potential": 0.75
            },
            "541600": {
                "name": "Management, Scientific, and Technical Consulting Services",
                "category": "Professional Services",
                "target_demographic_relevance": 0.8,
                "growth_potential": 0.8
            }
        }
    
    def _initialize_industry_profiles(self) -> Dict[str, IndustryRiskProfile]:
        """Initialize comprehensive industry risk profiles"""
        profiles = {}
        
        # Technology/Software - High growth, moderate automation risk
        profiles["511200"] = IndustryRiskProfile(
            naics_code="511200",
            industry_name="Software Publishers",
            risk_level=RiskLevel.LOW,
            overall_score=25.0,
            employment_trend=15.0,
            job_growth_rate=8.5,
            unemployment_rate=2.1,
            labor_force_participation=85.0,
            automation_risk_score=35.0,
            ai_replacement_probability=0.3,
            routine_task_percentage=25.0,
            cognitive_skill_requirement=85.0,
            economic_cycle_sensitivity=40.0,
            recession_resilience=75.0,
            gdp_correlation=0.6,
            geographic_concentration=60.0,
            remote_work_adoption=90.0,
            location_flexibility=85.0,
            advancement_opportunities=85.0,
            skill_development_potential=90.0,
            salary_growth_potential=80.0,
            leadership_representation=65.0,
            risk_factors=[
                "High competition for top talent",
                "Rapid technology changes",
                "Age discrimination in some companies"
            ],
            positive_indicators=[
                "Strong remote work adoption",
                "High salary growth potential",
                "Excellent skill development opportunities",
                "Growing demand for diverse talent"
            ],
            recommendations=[
                "Focus on emerging technologies (AI/ML, cloud, cybersecurity)",
                "Build strong professional networks",
                "Continuously update technical skills",
                "Seek mentorship from senior professionals",
                "Consider startup opportunities for faster advancement"
            ]
        )
        
        # Healthcare - Stable, low automation risk
        profiles["621100"] = IndustryRiskProfile(
            naics_code="621100",
            industry_name="Offices of Physicians",
            risk_level=RiskLevel.VERY_LOW,
            overall_score=15.0,
            employment_trend=8.0,
            job_growth_rate=6.2,
            unemployment_rate=1.8,
            labor_force_participation=88.0,
            automation_risk_score=20.0,
            ai_replacement_probability=0.15,
            routine_task_percentage=15.0,
            cognitive_skill_requirement=90.0,
            economic_cycle_sensitivity=25.0,
            recession_resilience=90.0,
            gdp_correlation=0.3,
            geographic_concentration=45.0,
            remote_work_adoption=40.0,
            location_flexibility=60.0,
            advancement_opportunities=75.0,
            skill_development_potential=80.0,
            salary_growth_potential=70.0,
            leadership_representation=70.0,
            risk_factors=[
                "High educational requirements",
                "Long training periods",
                "High stress levels"
            ],
            positive_indicators=[
                "Recession-resistant industry",
                "Strong job security",
                "High social impact",
                "Growing demand for diverse healthcare providers"
            ],
            recommendations=[
                "Pursue specialized certifications",
                "Focus on underserved communities",
                "Build patient relationships",
                "Consider telehealth opportunities",
                "Join professional medical associations"
            ]
        )
        
        # Financial Services - Moderate risk, high compensation
        profiles["522100"] = IndustryRiskProfile(
            naics_code="522100",
            industry_name="Depository Credit Intermediation",
            risk_level=RiskLevel.MODERATE,
            overall_score=45.0,
            employment_trend=-2.0,
            job_growth_rate=2.1,
            unemployment_rate=3.2,
            labor_force_participation=82.0,
            automation_risk_score=55.0,
            ai_replacement_probability=0.45,
            routine_task_percentage=40.0,
            cognitive_skill_requirement=75.0,
            economic_cycle_sensitivity=70.0,
            recession_resilience=60.0,
            gdp_correlation=0.8,
            geographic_concentration=75.0,
            remote_work_adoption=70.0,
            location_flexibility=65.0,
            advancement_opportunities=80.0,
            skill_development_potential=75.0,
            salary_growth_potential=85.0,
            leadership_representation=60.0,
            risk_factors=[
                "High automation risk for routine tasks",
                "Economic cycle sensitivity",
                "Regulatory changes",
                "Consolidation trends"
            ],
            positive_indicators=[
                "High compensation potential",
                "Strong analytical skill development",
                "Diverse career paths",
                "Growing fintech opportunities"
            ],
            recommendations=[
                "Develop quantitative and analytical skills",
                "Focus on relationship management roles",
                "Stay updated on regulatory changes",
                "Consider fintech and digital banking",
                "Build expertise in risk management"
            ]
        )
        
        # Education - Stable, moderate growth
        profiles["611100"] = IndustryRiskProfile(
            naics_code="611100",
            industry_name="Elementary and Secondary Schools",
            risk_level=RiskLevel.LOW,
            overall_score=30.0,
            employment_trend=5.0,
            job_growth_rate=3.8,
            unemployment_rate=2.5,
            labor_force_participation=85.0,
            automation_risk_score=25.0,
            ai_replacement_probability=0.2,
            routine_task_percentage=20.0,
            cognitive_skill_requirement=80.0,
            economic_cycle_sensitivity=35.0,
            recession_resilience=85.0,
            gdp_correlation=0.4,
            geographic_concentration=30.0,
            remote_work_adoption=50.0,
            location_flexibility=70.0,
            advancement_opportunities=70.0,
            skill_development_potential=75.0,
            salary_growth_potential=60.0,
            leadership_representation=75.0,
            risk_factors=[
                "Budget constraints in public schools",
                "Political influence on education",
                "Moderate salary growth"
            ],
            positive_indicators=[
                "High job security",
                "Strong community impact",
                "Good work-life balance",
                "Growing demand for diverse educators"
            ],
            recommendations=[
                "Pursue advanced degrees for higher pay",
                "Specialize in high-demand subjects (STEM, special education)",
                "Build strong relationships with students and parents",
                "Consider administrative leadership roles",
                "Explore charter school opportunities"
            ]
        )
        
        # Government - Very stable, moderate growth
        profiles["921000"] = IndustryRiskProfile(
            naics_code="921000",
            industry_name="Executive, Legislative, and Other General Government Support",
            risk_level=RiskLevel.VERY_LOW,
            overall_score=20.0,
            employment_trend=2.0,
            job_growth_rate=1.5,
            unemployment_rate=1.2,
            labor_force_participation=90.0,
            automation_risk_score=30.0,
            ai_replacement_probability=0.25,
            routine_task_percentage=35.0,
            cognitive_skill_requirement=70.0,
            economic_cycle_sensitivity=20.0,
            recession_resilience=95.0,
            gdp_correlation=0.2,
            geographic_concentration=25.0,
            remote_work_adoption=60.0,
            location_flexibility=75.0,
            advancement_opportunities=65.0,
            skill_development_potential=70.0,
            salary_growth_potential=55.0,
            leadership_representation=80.0,
            risk_factors=[
                "Slow advancement in some agencies",
                "Political changes can affect priorities",
                "Bureaucratic processes"
            ],
            positive_indicators=[
                "Excellent job security",
                "Good benefits and retirement",
                "Strong diversity initiatives",
                "Meaningful public service"
            ],
            recommendations=[
                "Focus on policy analysis and program management",
                "Build relationships across agencies",
                "Pursue leadership development programs",
                "Consider specialized government consulting",
                "Stay informed about policy changes"
            ]
        )
        
        # Retail/Hospitality - Higher risk, lower compensation
        profiles["445000"] = IndustryRiskProfile(
            naics_code="445000",
            industry_name="Food and Beverage Stores",
            risk_level=RiskLevel.HIGH,
            overall_score=65.0,
            employment_trend=-3.0,
            job_growth_rate=-1.2,
            unemployment_rate=4.8,
            labor_force_participation=75.0,
            automation_risk_score=70.0,
            ai_replacement_probability=0.6,
            routine_task_percentage=60.0,
            cognitive_skill_requirement=45.0,
            economic_cycle_sensitivity=80.0,
            recession_resilience=40.0,
            gdp_correlation=0.9,
            geographic_concentration=20.0,
            remote_work_adoption=10.0,
            location_flexibility=90.0,
            advancement_opportunities=50.0,
            skill_development_potential=55.0,
            salary_growth_potential=40.0,
            leadership_representation=45.0,
            risk_factors=[
                "High automation risk",
                "Low wages and benefits",
                "Economic sensitivity",
                "Limited advancement opportunities"
            ],
            positive_indicators=[
                "High location flexibility",
                "Entry-level accessibility",
                "Customer service skill development"
            ],
            recommendations=[
                "Use as stepping stone to other industries",
                "Develop transferable customer service skills",
                "Seek management training programs",
                "Consider specialized retail (luxury, specialty)",
                "Build strong work ethic and reliability"
            ]
        )
        
        # Manufacturing - Moderate risk, good benefits
        profiles["332000"] = IndustryRiskProfile(
            naics_code="332000",
            industry_name="Fabricated Metal Product Manufacturing",
            risk_level=RiskLevel.MODERATE,
            overall_score=50.0,
            employment_trend=1.0,
            job_growth_rate=2.5,
            unemployment_rate=3.5,
            labor_force_participation=80.0,
            automation_risk_score=60.0,
            ai_replacement_probability=0.5,
            routine_task_percentage=50.0,
            cognitive_skill_requirement=60.0,
            economic_cycle_sensitivity=75.0,
            recession_resilience=50.0,
            gdp_correlation=0.7,
            geographic_concentration=60.0,
            remote_work_adoption=20.0,
            location_flexibility=40.0,
            advancement_opportunities=65.0,
            skill_development_potential=70.0,
            salary_growth_potential=65.0,
            leadership_representation=55.0,
            risk_factors=[
                "High automation risk",
                "Economic cycle sensitivity",
                "Geographic concentration",
                "Physical work requirements"
            ],
            positive_indicators=[
                "Good benefits and union representation",
                "Technical skill development",
                "Stable employment in specialized areas"
            ],
            recommendations=[
                "Develop technical and engineering skills",
                "Focus on specialized manufacturing",
                "Pursue supervisory and management roles",
                "Consider advanced manufacturing technologies",
                "Build safety and quality expertise"
            ]
        )
        
        # Professional Services - Low risk, high growth
        profiles["541600"] = IndustryRiskProfile(
            naics_code="541600",
            industry_name="Management, Scientific, and Technical Consulting Services",
            risk_level=RiskLevel.LOW,
            overall_score=30.0,
            employment_trend=12.0,
            job_growth_rate=7.8,
            unemployment_rate=2.3,
            labor_force_participation=87.0,
            automation_risk_score=35.0,
            ai_replacement_probability=0.3,
            routine_task_percentage=25.0,
            cognitive_skill_requirement=85.0,
            economic_cycle_sensitivity=45.0,
            recession_resilience=70.0,
            gdp_correlation=0.6,
            geographic_concentration=70.0,
            remote_work_adoption=85.0,
            location_flexibility=80.0,
            advancement_opportunities=85.0,
            skill_development_potential=90.0,
            salary_growth_potential=85.0,
            leadership_representation=70.0,
            risk_factors=[
                "High competition for projects",
                "Client dependency",
                "Economic sensitivity"
            ],
            positive_indicators=[
                "High compensation potential",
                "Excellent skill development",
                "Diverse project exposure",
                "Strong networking opportunities"
            ],
            recommendations=[
                "Develop specialized expertise in high-demand areas",
                "Build strong client relationships",
                "Focus on strategic and analytical skills",
                "Consider independent consulting",
                "Stay updated on industry trends"
            ]
        )
        
        return profiles
    
    def map_industry_to_naics(self, industry_name: str, job_title: str = "") -> Optional[str]:
        """
        Map industry name and job title to NAICS code
        
        Args:
            industry_name: Industry name or description
            job_title: Job title for additional context
            
        Returns:
            NAICS code if found, None otherwise
        """
        industry_lower = industry_name.lower()
        job_lower = job_title.lower()
        
        # Direct mapping based on keywords
        mappings = {
            # Technology
            "software": "511200",
            "technology": "541500",
            "tech": "541500",
            "programming": "541500",
            "developer": "541500",
            "engineer": "541500",
            "data": "518200",
            "ai": "541500",
            "machine learning": "541500",
            
            # Healthcare
            "healthcare": "621100",
            "health": "621100",
            "medical": "621100",
            "hospital": "622000",
            "nursing": "621100",
            "physician": "621100",
            "doctor": "621100",
            
            # Financial Services
            "banking": "522100",
            "finance": "522100",
            "financial": "522100",
            "investment": "523100",
            "insurance": "524100",
            "accounting": "541200",
            "audit": "541200",
            
            # Education
            "education": "611100",
            "teaching": "611100",
            "teacher": "611100",
            "school": "611100",
            "university": "611300",
            "college": "611300",
            
            # Government
            "government": "921000",
            "public": "921000",
            "federal": "921000",
            "state": "921000",
            "municipal": "921000",
            "policy": "921000",
            
            # Retail/Hospitality
            "retail": "445000",
            "hospitality": "722000",
            "restaurant": "722000",
            "hotel": "722000",
            "food": "445000",
            "sales": "445000",
            
            # Manufacturing
            "manufacturing": "332000",
            "factory": "332000",
            "production": "332000",
            "assembly": "332000",
            "machinery": "333000",
            "industrial": "332000",
            
            # Professional Services
            "consulting": "541600",
            "legal": "541100",
            "law": "541100",
            "attorney": "541100",
            "management": "541600",
            "strategy": "541600"
        }
        
        # Check for exact matches first
        for keyword, naics_code in mappings.items():
            if keyword in industry_lower or keyword in job_lower:
                return naics_code
        
        # Fuzzy matching for partial matches
        for keyword, naics_code in mappings.items():
            if any(word in industry_lower for word in keyword.split()):
                return naics_code
        
        return None
    
    def get_industry_risk_profile(self, naics_code: str) -> Optional[IndustryRiskProfile]:
        """Get comprehensive risk profile for industry"""
        return self.industry_profiles.get(naics_code)
    
    def analyze_employment_trends(self, naics_code: str) -> Dict[str, Any]:
        """
        Analyze employment trends for industry
        
        Args:
            naics_code: NAICS code for industry
            
        Returns:
            Dictionary with trend analysis
        """
        # This would integrate with BLS API for real data
        # For now, return simulated data based on profiles
        
        profile = self.get_industry_risk_profile(naics_code)
        if not profile:
            return {}
        
        return {
            "employment_trend": profile.employment_trend,
            "job_growth_rate": profile.job_growth_rate,
            "unemployment_rate": profile.unemployment_rate,
            "labor_force_participation": profile.labor_force_participation,
            "trend_direction": "increasing" if profile.employment_trend > 0 else "decreasing",
            "growth_category": self._categorize_growth(profile.job_growth_rate)
        }
    
    def _categorize_growth(self, growth_rate: float) -> str:
        """Categorize job growth rate"""
        if growth_rate >= 5.0:
            return "very_high"
        elif growth_rate >= 3.0:
            return "high"
        elif growth_rate >= 1.0:
            return "moderate"
        elif growth_rate >= -1.0:
            return "low"
        else:
            return "declining"
    
    def assess_automation_risk(self, naics_code: str, job_title: str = "") -> Dict[str, Any]:
        """
        Assess automation and AI replacement risk
        
        Args:
            naics_code: NAICS code for industry
            job_title: Job title for specific analysis
            
        Returns:
            Dictionary with automation risk assessment
        """
        profile = self.get_industry_risk_profile(naics_code)
        if not profile:
            return {}
        
        # Job-specific automation risk adjustments
        job_risk_multiplier = self._get_job_automation_multiplier(job_title)
        
        adjusted_automation_risk = min(100, profile.automation_risk_score * job_risk_multiplier)
        adjusted_ai_probability = min(1.0, profile.ai_replacement_probability * job_risk_multiplier)
        
        return {
            "automation_risk_score": adjusted_automation_risk,
            "ai_replacement_probability": adjusted_ai_probability,
            "routine_task_percentage": profile.routine_task_percentage,
            "cognitive_skill_requirement": profile.cognitive_skill_requirement,
            "risk_level": self._get_risk_level(adjusted_automation_risk),
            "mitigation_strategies": self._get_automation_mitigation_strategies(adjusted_automation_risk)
        }
    
    def _get_job_automation_multiplier(self, job_title: str) -> float:
        """Get automation risk multiplier based on job title"""
        job_lower = job_title.lower()
        
        # High automation risk jobs
        high_risk_keywords = ["data entry", "cashier", "assembly", "receptionist", "bookkeeper"]
        for keyword in high_risk_keywords:
            if keyword in job_lower:
                return 1.3
        
        # Low automation risk jobs
        low_risk_keywords = ["manager", "director", "strategist", "consultant", "analyst", "designer"]
        for keyword in low_risk_keywords:
            if keyword in job_lower:
                return 0.7
        
        return 1.0
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level"""
        if risk_score < 20:
            return "very_low"
        elif risk_score < 40:
            return "low"
        elif risk_score < 60:
            return "moderate"
        elif risk_score < 80:
            return "high"
        else:
            return "very_high"
    
    def _get_automation_mitigation_strategies(self, risk_score: float) -> List[str]:
        """Get strategies to mitigate automation risk"""
        strategies = []
        
        if risk_score >= 60:
            strategies.extend([
                "Develop skills that complement AI rather than compete with it",
                "Focus on creative problem-solving and strategic thinking",
                "Build strong interpersonal and leadership skills",
                "Stay updated on emerging technologies in your field"
            ])
        elif risk_score >= 40:
            strategies.extend([
                "Enhance analytical and decision-making capabilities",
                "Develop expertise in areas requiring human judgment",
                "Build strong professional networks",
                "Consider roles that involve managing AI systems"
            ])
        else:
            strategies.extend([
                "Continue developing specialized expertise",
                "Focus on innovation and creative thinking",
                "Build strong client/customer relationships"
            ])
        
        return strategies
    
    def analyze_economic_sensitivity(self, naics_code: str) -> Dict[str, Any]:
        """Analyze industry sensitivity to economic cycles"""
        profile = self.get_industry_risk_profile(naics_code)
        if not profile:
            return {}
        
        return {
            "economic_cycle_sensitivity": profile.economic_cycle_sensitivity,
            "recession_resilience": profile.recession_resilience,
            "gdp_correlation": profile.gdp_correlation,
            "sensitivity_category": self._categorize_sensitivity(profile.economic_cycle_sensitivity),
            "resilience_category": self._categorize_resilience(profile.recession_resilience)
        }
    
    def _categorize_sensitivity(self, sensitivity: float) -> str:
        """Categorize economic sensitivity"""
        if sensitivity < 30:
            return "very_low"
        elif sensitivity < 50:
            return "low"
        elif sensitivity < 70:
            return "moderate"
        else:
            return "high"
    
    def _categorize_resilience(self, resilience: float) -> str:
        """Categorize recession resilience"""
        if resilience >= 80:
            return "very_high"
        elif resilience >= 60:
            return "high"
        elif resilience >= 40:
            return "moderate"
        else:
            return "low"
    
    def analyze_geographic_factors(self, naics_code: str, location: str = "") -> Dict[str, Any]:
        """Analyze geographic concentration and remote work factors"""
        profile = self.get_industry_risk_profile(naics_code)
        if not profile:
            return {}
        
        return {
            "geographic_concentration": profile.geographic_concentration,
            "remote_work_adoption": profile.remote_work_adoption,
            "location_flexibility": profile.location_flexibility,
            "concentration_risk": self._assess_concentration_risk(profile.geographic_concentration),
            "remote_work_potential": self._assess_remote_potential(profile.remote_work_adoption)
        }
    
    def _assess_concentration_risk(self, concentration: float) -> str:
        """Assess geographic concentration risk"""
        if concentration < 30:
            return "very_low"
        elif concentration < 50:
            return "low"
        elif concentration < 70:
            return "moderate"
        else:
            return "high"
    
    def _assess_remote_potential(self, adoption: float) -> str:
        """Assess remote work potential"""
        if adoption >= 80:
            return "very_high"
        elif adoption >= 60:
            return "high"
        elif adoption >= 40:
            return "moderate"
        else:
            return "low"
    
    def get_career_advancement_insights(self, naics_code: str) -> Dict[str, Any]:
        """Get industry-specific career advancement insights"""
        profile = self.get_industry_risk_profile(naics_code)
        if not profile:
            return {}
        
        return {
            "advancement_opportunities": profile.advancement_opportunities,
            "skill_development_potential": profile.skill_development_potential,
            "salary_growth_potential": profile.salary_growth_potential,
            "leadership_representation": profile.leadership_representation,
            "recommendations": profile.recommendations,
            "positive_indicators": profile.positive_indicators,
            "advancement_category": self._categorize_advancement(profile.advancement_opportunities)
        }
    
    def _categorize_advancement(self, opportunities: float) -> str:
        """Categorize advancement opportunities"""
        if opportunities >= 80:
            return "excellent"
        elif opportunities >= 60:
            return "good"
        elif opportunities >= 40:
            return "moderate"
        else:
            return "limited"
    
    def get_comprehensive_risk_assessment(self, 
                                        industry_name: str, 
                                        job_title: str = "",
                                        location: str = "") -> Dict[str, Any]:
        """
        Get comprehensive risk assessment for industry and job
        
        Args:
            industry_name: Industry name or description
            job_title: Job title for specific analysis
            location: Geographic location
            
        Returns:
            Comprehensive risk assessment dictionary
        """
        # Map to NAICS code
        naics_code = self.map_industry_to_naics(industry_name, job_title)
        if not naics_code:
            return {"error": "Industry not found in database"}
        
        profile = self.get_industry_risk_profile(naics_code)
        if not profile:
            return {"error": "Risk profile not available"}
        
        # Gather all analyses
        employment_trends = self.analyze_employment_trends(naics_code)
        automation_risk = self.assess_automation_risk(naics_code, job_title)
        economic_sensitivity = self.analyze_economic_sensitivity(naics_code)
        geographic_factors = self.analyze_geographic_factors(naics_code, location)
        career_insights = self.get_career_advancement_insights(naics_code)
        
        return {
            "naics_code": naics_code,
            "industry_name": profile.industry_name,
            "overall_risk_level": profile.risk_level.value,
            "overall_risk_score": profile.overall_score,
            "employment_trends": employment_trends,
            "automation_risk": automation_risk,
            "economic_sensitivity": economic_sensitivity,
            "geographic_factors": geographic_factors,
            "career_advancement": career_insights,
            "risk_factors": profile.risk_factors,
            "positive_indicators": profile.positive_indicators,
            "recommendations": profile.recommendations,
            "last_updated": profile.last_updated.isoformat(),
            "confidence_level": profile.confidence_level
        }
    
    def get_industry_comparison(self, naics_codes: List[str]) -> Dict[str, Any]:
        """
        Compare multiple industries
        
        Args:
            naics_codes: List of NAICS codes to compare
            
        Returns:
            Comparison analysis
        """
        comparisons = {}
        
        for naics_code in naics_codes:
            profile = self.get_industry_risk_profile(naics_code)
            if profile:
                comparisons[naics_code] = {
                    "industry_name": profile.industry_name,
                    "risk_level": profile.risk_level.value,
                    "overall_score": profile.overall_score,
                    "employment_trend": profile.employment_trend,
                    "automation_risk": profile.automation_risk_score,
                    "advancement_opportunities": profile.advancement_opportunities,
                    "salary_growth_potential": profile.salary_growth_potential
                }
        
        return {
            "comparisons": comparisons,
            "summary": self._generate_comparison_summary(comparisons)
        }
    
    def _generate_comparison_summary(self, comparisons: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of industry comparisons"""
        if not comparisons:
            return {}
        
        scores = [comp["overall_score"] for comp in comparisons.values()]
        automation_risks = [comp["automation_risk"] for comp in comparisons.values()]
        advancement_opportunities = [comp["advancement_opportunities"] for comp in comparisons.values()]
        
        return {
            "lowest_risk_industry": min(comparisons.items(), key=lambda x: x[1]["overall_score"])[0],
            "highest_risk_industry": max(comparisons.items(), key=lambda x: x[1]["overall_score"])[0],
            "best_advancement_opportunities": max(comparisons.items(), key=lambda x: x[1]["advancement_opportunities"])[0],
            "lowest_automation_risk": min(comparisons.items(), key=lambda x: x[1]["automation_risk"])[0],
            "average_risk_score": np.mean(scores),
            "risk_score_range": max(scores) - min(scores)
        }
    
    def update_industry_data(self):
        """Update industry data with fresh economic data (monthly)"""
        # This would integrate with BLS API and other data sources
        # For now, update timestamps
        current_time = datetime.utcnow()
        
        for profile in self.industry_profiles.values():
            profile.last_updated = current_time
        
        logger.info("Industry risk profiles updated")
    
    def get_target_demographic_insights(self) -> Dict[str, Any]:
        """Get insights specifically for African American professionals aged 25-35"""
        insights = {
            "high_growth_industries": [],
            "low_risk_industries": [],
            "high_advancement_industries": [],
            "diversity_friendly_industries": [],
            "recommendations": []
        }
        
        for naics_code, profile in self.industry_profiles.items():
            naics_info = self.naics_mapping.get(naics_code, {})
            
            # High growth industries
            if profile.job_growth_rate >= 5.0:
                insights["high_growth_industries"].append({
                    "naics_code": naics_code,
                    "industry_name": profile.industry_name,
                    "growth_rate": profile.job_growth_rate,
                    "demographic_relevance": naics_info.get("target_demographic_relevance", 0.5)
                })
            
            # Low risk industries
            if profile.overall_score <= 30:
                insights["low_risk_industries"].append({
                    "naics_code": naics_code,
                    "industry_name": profile.industry_name,
                    "risk_score": profile.overall_score,
                    "demographic_relevance": naics_info.get("target_demographic_relevance", 0.5)
                })
            
            # High advancement opportunities
            if profile.advancement_opportunities >= 75:
                insights["high_advancement_industries"].append({
                    "naics_code": naics_code,
                    "industry_name": profile.industry_name,
                    "advancement_score": profile.advancement_opportunities,
                    "demographic_relevance": naics_info.get("target_demographic_relevance", 0.5)
                })
        
        # Sort by demographic relevance
        for key in ["high_growth_industries", "low_risk_industries", "high_advancement_industries"]:
            insights[key].sort(key=lambda x: x["demographic_relevance"], reverse=True)
        
        insights["recommendations"] = [
            "Focus on industries with strong growth and advancement opportunities",
            "Develop skills that complement automation rather than compete with it",
            "Build strong professional networks in target industries",
            "Consider industries with strong diversity initiatives",
            "Stay updated on emerging trends in high-growth sectors"
        ]
        
        return insights

# Global industry risk assessor instance
_industry_risk_assessor = None

def get_industry_risk_assessor(bls_api_key: Optional[str] = None) -> IndustryRiskAssessor:
    """Get or create global industry risk assessor instance"""
    global _industry_risk_assessor
    if _industry_risk_assessor is None:
        _industry_risk_assessor = IndustryRiskAssessor(bls_api_key=bls_api_key)
    return _industry_risk_assessor

# Convenience functions
def assess_industry_risk(industry_name: str, 
                        job_title: str = "",
                        location: str = "") -> Dict[str, Any]:
    """Get comprehensive industry risk assessment"""
    assessor = get_industry_risk_assessor()
    return assessor.get_comprehensive_risk_assessment(industry_name, job_title, location)

def get_industry_comparison(naics_codes: List[str]) -> Dict[str, Any]:
    """Compare multiple industries"""
    assessor = get_industry_risk_assessor()
    return assessor.get_industry_comparison(naics_codes)

def get_target_demographic_insights() -> Dict[str, Any]:
    """Get insights for African American professionals aged 25-35"""
    assessor = get_industry_risk_assessor()
    return assessor.get_target_demographic_insights() 