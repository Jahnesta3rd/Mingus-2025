"""
Income Comparator for Demographic Analysis
Comprehensive income comparison tool for African American professionals (ages 25-35)
Uses 2022 American Community Survey data and demographic benchmarks
"""

import logging
import math
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ComparisonGroup(str, Enum):
    """Demographic comparison groups"""
    NATIONAL_MEDIAN = "national_median"
    AFRICAN_AMERICAN = "african_american"
    AGE_25_35 = "age_25_35"
    AFRICAN_AMERICAN_25_35 = "african_american_25_35"
    COLLEGE_GRADUATE = "college_graduate"
    AFRICAN_AMERICAN_COLLEGE = "african_american_college"
    METRO_AREA = "metro_area"
    AFRICAN_AMERICAN_METRO = "african_american_metro"

class EducationLevel(str, Enum):
    """Education level classifications"""
    HIGH_SCHOOL = "high_school"
    SOME_COLLEGE = "some_college"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    DOCTORATE = "doctorate"

@dataclass
class IncomeComparison:
    """Individual income comparison result"""
    comparison_group: ComparisonGroup
    group_name: str
    user_income: int
    median_income: int
    percentile_rank: float
    income_gap: int
    gap_percentage: float
    context_message: str
    motivational_insight: str
    action_item: str
    data_source: str
    confidence_level: float

@dataclass
class DemographicIncomeData:
    """Demographic income statistics"""
    group_name: str
    median_income: int
    mean_income: int
    percentile_25: int
    percentile_75: int
    sample_size: int
    year: int
    source: str

@dataclass
class IncomeAnalysisResult:
    """Complete income analysis results"""
    user_income: int
    comparisons: List[IncomeComparison]
    overall_percentile: float
    primary_gap: IncomeComparison
    career_opportunity_score: float
    motivational_summary: str
    action_plan: List[str]
    next_steps: List[str]
    generated_at: datetime = field(default_factory=datetime.now)

class IncomeComparator:
    """
    Comprehensive income comparator for African American professionals
    Analyzes income against multiple demographic benchmarks
    """
    
    def __init__(self):
        """Initialize the income comparator with demographic data"""
        self.demographic_data = self._initialize_demographic_data()
        self.metro_areas = self._initialize_metro_areas()
        self.target_metros = [
            'Atlanta', 'Houston', 'Washington DC', 'Dallas', 'New York City',
            'Philadelphia', 'Chicago', 'Charlotte', 'Miami', 'Baltimore'
        ]
        
        logger.info("IncomeComparator initialized with demographic benchmarks")
    
    def _initialize_demographic_data(self) -> Dict[str, DemographicIncomeData]:
        """Initialize demographic income data from 2022 ACS"""
        return {
            # National benchmarks
            ComparisonGroup.NATIONAL_MEDIAN: DemographicIncomeData(
                group_name="National Median",
                median_income=74580,
                mean_income=102430,
                percentile_25=45000,
                percentile_75=120000,
                sample_size=150000000,
                year=2022,
                source="2022 American Community Survey"
            ),
            
            # African American benchmarks
            ComparisonGroup.AFRICAN_AMERICAN: DemographicIncomeData(
                group_name="African American",
                median_income=52000,
                mean_income=68000,
                percentile_25=32000,
                percentile_75=85000,
                sample_size=42000000,
                year=2022,
                source="2022 American Community Survey"
            ),
            
            # Age group benchmarks (25-35)
            ComparisonGroup.AGE_25_35: DemographicIncomeData(
                group_name="Ages 25-35",
                median_income=58000,
                mean_income=72000,
                percentile_25=38000,
                percentile_75=95000,
                sample_size=45000000,
                year=2022,
                source="2022 American Community Survey"
            ),
            
            # African American ages 25-35
            ComparisonGroup.AFRICAN_AMERICAN_25_35: DemographicIncomeData(
                group_name="African American Ages 25-35",
                median_income=48000,
                mean_income=62000,
                percentile_25=30000,
                percentile_75=78000,
                sample_size=8500000,
                year=2022,
                source="2022 American Community Survey"
            ),
            
            # College graduate benchmarks
            ComparisonGroup.COLLEGE_GRADUATE: DemographicIncomeData(
                group_name="College Graduates",
                median_income=85000,
                mean_income=105000,
                percentile_25=55000,
                percentile_75=130000,
                sample_size=75000000,
                year=2022,
                source="2022 American Community Survey"
            ),
            
            # African American college graduates
            ComparisonGroup.AFRICAN_AMERICAN_COLLEGE: DemographicIncomeData(
                group_name="African American College Graduates",
                median_income=65000,
                mean_income=82000,
                percentile_25=42000,
                percentile_75=105000,
                sample_size=12000000,
                year=2022,
                source="2022 American Community Survey"
            )
        }
    
    def _initialize_metro_areas(self) -> Dict[str, Dict[str, DemographicIncomeData]]:
        """Initialize metro area income data"""
        return {
            'Atlanta': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Atlanta Metro",
                    median_income=72000,
                    mean_income=95000,
                    percentile_25=45000,
                    percentile_75=115000,
                    sample_size=6200000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Atlanta African American",
                    median_income=55000,
                    mean_income=72000,
                    percentile_25=35000,
                    percentile_75=90000,
                    sample_size=2100000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Houston': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Houston Metro",
                    median_income=68000,
                    mean_income=88000,
                    percentile_25=42000,
                    percentile_75=110000,
                    sample_size=7200000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Houston African American",
                    median_income=52000,
                    mean_income=68000,
                    percentile_25=32000,
                    percentile_75=85000,
                    sample_size=1800000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Washington DC': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Washington DC Metro",
                    median_income=95000,
                    mean_income=125000,
                    percentile_25=60000,
                    percentile_75=150000,
                    sample_size=6300000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Washington DC African American",
                    median_income=72000,
                    mean_income=95000,
                    percentile_25=45000,
                    percentile_75=120000,
                    sample_size=1800000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Dallas': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Dallas Metro",
                    median_income=70000,
                    mean_income=92000,
                    percentile_25=44000,
                    percentile_75=115000,
                    sample_size=7600000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Dallas African American",
                    median_income=54000,
                    mean_income=70000,
                    percentile_25=33000,
                    percentile_75=88000,
                    sample_size=1600000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'New York City': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="New York City Metro",
                    median_income=85000,
                    mean_income=115000,
                    percentile_25=52000,
                    percentile_75=140000,
                    sample_size=20000000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="New York City African American",
                    median_income=62000,
                    mean_income=82000,
                    percentile_25=38000,
                    percentile_75=105000,
                    sample_size=3200000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Philadelphia': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Philadelphia Metro",
                    median_income=72000,
                    mean_income=95000,
                    percentile_25=45000,
                    percentile_75=115000,
                    sample_size=6100000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Philadelphia African American",
                    median_income=55000,
                    mean_income=72000,
                    percentile_25=35000,
                    percentile_75=90000,
                    sample_size=1200000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Chicago': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Chicago Metro",
                    median_income=75000,
                    mean_income=98000,
                    percentile_25=47000,
                    percentile_75=120000,
                    sample_size=9500000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Chicago African American",
                    median_income=56000,
                    mean_income=73000,
                    percentile_25=35000,
                    percentile_75=92000,
                    sample_size=1700000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Charlotte': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Charlotte Metro",
                    median_income=68000,
                    mean_income=88000,
                    percentile_25=42000,
                    percentile_75=110000,
                    sample_size=2600000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Charlotte African American",
                    median_income=52000,
                    mean_income=68000,
                    percentile_25=32000,
                    percentile_75=85000,
                    sample_size=650000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Miami': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Miami Metro",
                    median_income=65000,
                    mean_income=85000,
                    percentile_25=40000,
                    percentile_75=105000,
                    sample_size=6100000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Miami African American",
                    median_income=49000,
                    mean_income=64000,
                    percentile_25=30000,
                    percentile_75=80000,
                    sample_size=1100000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            },
            'Baltimore': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Baltimore Metro",
                    median_income=75000,
                    mean_income=98000,
                    percentile_25=47000,
                    percentile_75=120000,
                    sample_size=2800000,
                    year=2022,
                    source="2022 American Community Survey"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Baltimore African American",
                    median_income=57000,
                    mean_income=74000,
                    percentile_25=35000,
                    percentile_75=93000,
                    sample_size=900000,
                    year=2022,
                    source="2022 American Community Survey"
                )
            }
        }
    
    def analyze_income(self, 
                      user_income: int,
                      location: Optional[str] = None,
                      education_level: Optional[EducationLevel] = None,
                      age_group: Optional[str] = "25-35") -> IncomeAnalysisResult:
        """
        Comprehensive income analysis against demographic benchmarks
        
        Args:
            user_income: User's current annual income
            location: Metro area for location-specific comparison
            education_level: User's education level
            age_group: Age group for comparison (default: 25-35)
        
        Returns:
            IncomeAnalysisResult with comprehensive comparisons
        """
        try:
            logger.info(f"Starting income analysis for ${user_income:,}")
            
            comparisons = []
            
            # National comparisons
            comparisons.extend([
                self._compare_national_median(user_income),
                self._compare_african_american(user_income),
                self._compare_age_group(user_income, age_group),
                self._compare_african_american_age_group(user_income, age_group)
            ])
            
            # Education-based comparisons
            if education_level:
                comparisons.extend([
                    self._compare_education_level(user_income, education_level),
                    self._compare_african_american_education(user_income, education_level)
                ])
            
            # Location-based comparisons
            if location:
                comparisons.extend(self._compare_location(user_income, location))
            
            # Calculate overall percentile
            overall_percentile = self._calculate_overall_percentile(comparisons)
            
            # Find primary gap (largest opportunity)
            primary_gap = max(comparisons, key=lambda x: x.income_gap)
            
            # Calculate career opportunity score
            career_opportunity_score = self._calculate_career_opportunity_score(comparisons)
            
            # Generate motivational content
            motivational_summary = self._generate_motivational_summary(comparisons, primary_gap)
            action_plan = self._generate_action_plan(comparisons, primary_gap)
            next_steps = self._generate_next_steps(primary_gap, career_opportunity_score)
            
            result = IncomeAnalysisResult(
                user_income=user_income,
                comparisons=comparisons,
                overall_percentile=overall_percentile,
                primary_gap=primary_gap,
                career_opportunity_score=career_opportunity_score,
                motivational_summary=motivational_summary,
                action_plan=action_plan,
                next_steps=next_steps
            )
            
            logger.info(f"Income analysis completed. Overall percentile: {overall_percentile:.1f}%")
            return result
            
        except Exception as e:
            logger.error(f"Error in income analysis: {str(e)}")
            raise
    
    def _compare_national_median(self, user_income: int) -> IncomeComparison:
        """Compare against national median income"""
        data = self.demographic_data[ComparisonGroup.NATIONAL_MEDIAN]
        percentile = self._calculate_percentile(user_income, data)
        gap = data.median_income - user_income
        gap_percentage = (gap / data.median_income) * 100
        
        context = f"National median income is ${data.median_income:,}"
        insight = self._generate_insight(user_income, data.median_income, "national median")
        action = self._generate_action_item(gap, "national median", data.median_income)
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=context,
            motivational_insight=insight,
            action_item=action,
            data_source=data.source,
            confidence_level=0.95
        )
    
    def _compare_african_american(self, user_income: int) -> IncomeComparison:
        """Compare against African American median income"""
        data = self.demographic_data[ComparisonGroup.AFRICAN_AMERICAN]
        percentile = self._calculate_percentile(user_income, data)
        gap = data.median_income - user_income
        gap_percentage = (gap / data.median_income) * 100
        
        context = f"African American median income is ${data.median_income:,}"
        insight = self._generate_insight(user_income, data.median_income, "African American median")
        action = self._generate_action_item(gap, "African American median", data.median_income)
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AFRICAN_AMERICAN,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=context,
            motivational_insight=insight,
            action_item=action,
            data_source=data.source,
            confidence_level=0.90
        )
    
    def _compare_age_group(self, user_income: int, age_group: str) -> IncomeComparison:
        """Compare against age group median income"""
        data = self.demographic_data[ComparisonGroup.AGE_25_35]
        percentile = self._calculate_percentile(user_income, data)
        gap = data.median_income - user_income
        gap_percentage = (gap / data.median_income) * 100
        
        context = f"Median income for ages {age_group} is ${data.median_income:,}"
        insight = self._generate_insight(user_income, data.median_income, f"ages {age_group} median")
        action = self._generate_action_item(gap, f"ages {age_group} median", data.median_income)
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AGE_25_35,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=context,
            motivational_insight=insight,
            action_item=action,
            data_source=data.source,
            confidence_level=0.92
        )
    
    def _compare_african_american_age_group(self, user_income: int, age_group: str) -> IncomeComparison:
        """Compare against African American age group median income"""
        data = self.demographic_data[ComparisonGroup.AFRICAN_AMERICAN_25_35]
        percentile = self._calculate_percentile(user_income, data)
        gap = data.median_income - user_income
        gap_percentage = (gap / data.median_income) * 100
        
        context = f"African American median income for ages {age_group} is ${data.median_income:,}"
        insight = self._generate_insight(user_income, data.median_income, f"African American ages {age_group} median")
        action = self._generate_action_item(gap, f"African American ages {age_group} median", data.median_income)
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AFRICAN_AMERICAN_25_35,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=context,
            motivational_insight=insight,
            action_item=action,
            data_source=data.source,
            confidence_level=0.88
        )
    
    def _compare_education_level(self, user_income: int, education_level: EducationLevel) -> IncomeComparison:
        """Compare against education level median income"""
        data = self.demographic_data[ComparisonGroup.COLLEGE_GRADUATE]
        percentile = self._calculate_percentile(user_income, data)
        gap = data.median_income - user_income
        gap_percentage = (gap / data.median_income) * 100
        
        context = f"College graduate median income is ${data.median_income:,}"
        insight = self._generate_insight(user_income, data.median_income, "college graduate median")
        action = self._generate_action_item(gap, "college graduate median", data.median_income)
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.COLLEGE_GRADUATE,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=context,
            motivational_insight=insight,
            action_item=action,
            data_source=data.source,
            confidence_level=0.93
        )
    
    def _compare_african_american_education(self, user_income: int, education_level: EducationLevel) -> IncomeComparison:
        """Compare against African American education level median income"""
        data = self.demographic_data[ComparisonGroup.AFRICAN_AMERICAN_COLLEGE]
        percentile = self._calculate_percentile(user_income, data)
        gap = data.median_income - user_income
        gap_percentage = (gap / data.median_income) * 100
        
        context = f"African American college graduate median income is ${data.median_income:,}"
        insight = self._generate_insight(user_income, data.median_income, "African American college graduate median")
        action = self._generate_action_item(gap, "African American college graduate median", data.median_income)
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AFRICAN_AMERICAN_COLLEGE,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=context,
            motivational_insight=insight,
            action_item=action,
            data_source=data.source,
            confidence_level=0.89
        )
    
    def _compare_location(self, user_income: int, location: str) -> List[IncomeComparison]:
        """Compare against location-specific median incomes"""
        comparisons = []
        
        # Normalize location name
        location_key = self._normalize_location(location)
        
        if location_key in self.metro_areas:
            metro_data = self.metro_areas[location_key]
            
            # Metro area comparison
            metro_data_obj = metro_data[ComparisonGroup.METRO_AREA]
            percentile = self._calculate_percentile(user_income, metro_data_obj)
            gap = metro_data_obj.median_income - user_income
            gap_percentage = (gap / metro_data_obj.median_income) * 100
            
            context = f"{location} metro median income is ${metro_data_obj.median_income:,}"
            insight = self._generate_insight(user_income, metro_data_obj.median_income, f"{location} metro median")
            action = self._generate_action_item(gap, f"{location} metro median", metro_data_obj.median_income)
            
            comparisons.append(IncomeComparison(
                comparison_group=ComparisonGroup.METRO_AREA,
                group_name=metro_data_obj.group_name,
                user_income=user_income,
                median_income=metro_data_obj.median_income,
                percentile_rank=percentile,
                income_gap=gap,
                gap_percentage=gap_percentage,
                context_message=context,
                motivational_insight=insight,
                action_item=action,
                data_source=metro_data_obj.source,
                confidence_level=0.91
            ))
            
            # African American metro comparison
            if ComparisonGroup.AFRICAN_AMERICAN_METRO in metro_data:
                aa_metro_data = metro_data[ComparisonGroup.AFRICAN_AMERICAN_METRO]
                percentile = self._calculate_percentile(user_income, aa_metro_data)
                gap = aa_metro_data.median_income - user_income
                gap_percentage = (gap / aa_metro_data.median_income) * 100
                
                context = f"African American median income in {location} is ${aa_metro_data.median_income:,}"
                insight = self._generate_insight(user_income, aa_metro_data.median_income, f"African American {location} median")
                action = self._generate_action_item(gap, f"African American {location} median", aa_metro_data.median_income)
                
                comparisons.append(IncomeComparison(
                    comparison_group=ComparisonGroup.AFRICAN_AMERICAN_METRO,
                    group_name=aa_metro_data.group_name,
                    user_income=user_income,
                    median_income=aa_metro_data.median_income,
                    percentile_rank=percentile,
                    income_gap=gap,
                    gap_percentage=gap_percentage,
                    context_message=context,
                    motivational_insight=insight,
                    action_item=action,
                    data_source=aa_metro_data.source,
                    confidence_level=0.87
                ))
        
        return comparisons
    
    def _calculate_percentile(self, user_income: int, data: DemographicIncomeData) -> float:
        """Calculate percentile rank using log-normal distribution approximation"""
        try:
            # Use log-normal distribution for income percentiles
            log_income = math.log(user_income)
            log_median = math.log(data.median_income)
            log_mean = math.log(data.mean_income)
            
            # Calculate standard deviation from mean and median
            sigma = math.sqrt(2 * (log_mean - log_median))
            
            # Calculate percentile using normal distribution
            z_score = (log_income - log_median) / sigma
            percentile = self._normal_cdf(z_score) * 100
            
            return max(0.1, min(99.9, percentile))
            
        except Exception as e:
            logger.warning(f"Error calculating percentile: {e}. Using fallback method.")
            # Fallback: simple linear interpolation
            if user_income <= data.percentile_25:
                return 25 * (user_income / data.percentile_25)
            elif user_income <= data.median_income:
                return 25 + 25 * ((user_income - data.percentile_25) / (data.median_income - data.percentile_25))
            elif user_income <= data.percentile_75:
                return 50 + 25 * ((user_income - data.median_income) / (data.percentile_75 - data.median_income))
            else:
                return 75 + 25 * min(1, (user_income - data.percentile_75) / (data.percentile_75 * 0.5))
    
    def _normal_cdf(self, z: float) -> float:
        """Calculate cumulative distribution function for standard normal distribution"""
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    def _calculate_overall_percentile(self, comparisons: List[IncomeComparison]) -> float:
        """Calculate weighted overall percentile across all comparisons"""
        if not comparisons:
            return 50.0
        
        # Weight by confidence level and importance
        weights = []
        percentiles = []
        
        for comp in comparisons:
            weight = comp.confidence_level
            if comp.comparison_group in [ComparisonGroup.AFRICAN_AMERICAN_25_35, ComparisonGroup.AFRICAN_AMERICAN_METRO]:
                weight *= 1.2  # Higher weight for most relevant comparisons
            
            weights.append(weight)
            percentiles.append(comp.percentile_rank)
        
        # Calculate weighted average
        total_weight = sum(weights)
        if total_weight == 0:
            return 50.0
        
        weighted_percentile = sum(w * p for w, p in zip(weights, percentiles)) / total_weight
        return weighted_percentile
    
    def _calculate_career_opportunity_score(self, comparisons: List[IncomeComparison]) -> float:
        """Calculate career opportunity score (0-100) based on income gaps"""
        if not comparisons:
            return 50.0
        
        # Calculate average gap percentage (positive gaps indicate opportunity)
        positive_gaps = [comp.gap_percentage for comp in comparisons if comp.gap_percentage > 0]
        
        if not positive_gaps:
            return 25.0  # No gaps = limited opportunity
        
        avg_gap = sum(positive_gaps) / len(positive_gaps)
        
        # Convert to opportunity score (0-100)
        # Higher gaps = higher opportunity
        opportunity_score = min(100, max(0, avg_gap * 2))
        
        return opportunity_score
    
    def _generate_insight(self, user_income: int, benchmark_income: int, benchmark_name: str) -> str:
        """Generate motivational insight based on income comparison"""
        if user_income >= benchmark_income:
            gap = user_income - benchmark_income
            return f"You're earning ${gap:,} more than the {benchmark_name}! This shows strong career positioning."
        else:
            gap = benchmark_income - user_income
            return f"There's a ${gap:,} opportunity gap compared to the {benchmark_name}. This represents significant career advancement potential."
    
    def _generate_action_item(self, gap: int, benchmark_name: str, benchmark_income: int) -> str:
        """Generate specific action item based on income gap"""
        if gap <= 0:
            return f"Leverage your strong position above the {benchmark_name} to negotiate for leadership roles."
        else:
            gap_abs = abs(gap)
            if gap_abs > 20000:
                return f"Target roles with ${gap_abs:,} higher compensation to close the gap with {benchmark_name}."
            elif gap_abs > 10000:
                return f"Focus on skill development and networking to bridge the ${gap_abs:,} gap with {benchmark_name}."
            else:
                return f"Small adjustments in negotiation or role selection can close the ${gap_abs:,} gap with {benchmark_name}."
    
    def _generate_motivational_summary(self, comparisons: List[IncomeComparison], primary_gap: IncomeComparison) -> str:
        """Generate overall motivational summary"""
        if primary_gap.income_gap <= 0:
            return "You're performing above key benchmarks! Focus on leveraging your strong position for leadership opportunities."
        
        gap_amount = abs(primary_gap.income_gap)
        benchmark_name = primary_gap.group_name
        
        return f"Your biggest opportunity is closing the ${gap_amount:,} gap with {benchmark_name}. This represents significant career advancement potential that can transform your financial future."
    
    def _generate_action_plan(self, comparisons: List[IncomeComparison], primary_gap: IncomeComparison) -> List[str]:
        """Generate comprehensive action plan"""
        actions = []
        
        # Primary gap action
        if primary_gap.income_gap > 0:
            actions.append(f"Target roles offering ${abs(primary_gap.income_gap):,} more than your current salary")
        
        # Skill development
        actions.append("Develop in-demand skills identified in your target roles")
        
        # Networking
        actions.append("Build professional network in your target industry and location")
        
        # Negotiation
        actions.append("Practice salary negotiation skills for your next role")
        
        # Education/certification
        actions.append("Consider additional certifications or education if relevant")
        
        return actions
    
    def _generate_next_steps(self, primary_gap: IncomeComparison, opportunity_score: float) -> List[str]:
        """Generate specific next steps based on opportunity score"""
        steps = []
        
        if opportunity_score >= 75:
            steps.extend([
                "Immediately update your resume and LinkedIn profile",
                "Start applying to roles with 20-30% higher compensation",
                "Schedule informational interviews with professionals in target roles"
            ])
        elif opportunity_score >= 50:
            steps.extend([
                "Research target companies and roles in your field",
                "Identify skill gaps and create a development plan",
                "Begin networking in your target industry"
            ])
        else:
            steps.extend([
                "Focus on skill development and career positioning",
                "Build your professional brand and online presence",
                "Consider lateral moves to gain new experience"
            ])
        
        return steps
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location name for lookup"""
        location_lower = location.lower()
        
        # Map common variations to standard names
        location_map = {
            'atlanta': 'Atlanta',
            'houston': 'Houston',
            'washington dc': 'Washington DC',
            'washington d.c.': 'Washington DC',
            'dc': 'Washington DC',
            'dallas': 'Dallas',
            'new york': 'New York City',
            'nyc': 'New York City',
            'new york city': 'New York City',
            'philadelphia': 'Philadelphia',
            'philly': 'Philadelphia',
            'chicago': 'Chicago',
            'charlotte': 'Charlotte',
            'miami': 'Miami',
            'baltimore': 'Baltimore'
        }
        
        return location_map.get(location_lower, location)
    
    def get_available_locations(self) -> List[str]:
        """Get list of available metro areas for comparison"""
        return list(self.metro_areas.keys())
    
    def get_demographic_summary(self) -> Dict[str, Any]:
        """Get summary of available demographic data"""
        return {
            'national_groups': list(self.demographic_data.keys()),
            'metro_areas': self.get_available_locations(),
            'data_year': 2022,
            'data_source': 'American Community Survey'
        }


# Example usage and testing
def example_usage():
    """Example usage of the IncomeComparator"""
    
    # Initialize comparator
    comparator = IncomeComparator()
    
    # Example user profile
    user_income = 65000
    location = "Atlanta"
    education_level = EducationLevel.BACHELORS
    
    print("🎯 Income Comparator Example")
    print("=" * 50)
    print(f"User Income: ${user_income:,}")
    print(f"Location: {location}")
    print(f"Education: {education_level.value}")
    print()
    
    # Run analysis
    result = comparator.analyze_income(
        user_income=user_income,
        location=location,
        education_level=education_level
    )
    
    # Display results
    print("📊 COMPARISON RESULTS")
    print("=" * 50)
    
    for comparison in result.comparisons:
        print(f"\n{comparison.group_name}:")
        print(f"  Median: ${comparison.median_income:,}")
        print(f"  Your Percentile: {comparison.percentile_rank:.1f}%")
        print(f"  Gap: ${comparison.income_gap:,} ({comparison.gap_percentage:+.1f}%)")
        print(f"  Insight: {comparison.motivational_insight}")
        print(f"  Action: {comparison.action_item}")
    
    print(f"\n🎯 OVERALL SUMMARY")
    print("=" * 50)
    print(f"Overall Percentile: {result.overall_percentile:.1f}%")
    print(f"Career Opportunity Score: {result.career_opportunity_score:.1f}/100")
    print(f"Primary Gap: {result.primary_gap.group_name}")
    print(f"Motivational Summary: {result.motivational_summary}")
    
    print(f"\n📋 ACTION PLAN")
    print("=" * 50)
    for i, action in enumerate(result.action_plan, 1):
        print(f"{i}. {action}")
    
    print(f"\n🚀 NEXT STEPS")
    print("=" * 50)
    for i, step in enumerate(result.next_steps, 1):
        print(f"{i}. {step}")


if __name__ == "__main__":
    example_usage() 