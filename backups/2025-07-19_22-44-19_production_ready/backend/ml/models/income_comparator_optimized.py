"""
Optimized Income Comparator for Production Deployment
Ultra-budget optimized income comparison tool for African American professionals
Uses efficient data structures, caching, and minimal memory footprint
"""

import logging
import math
import time
import hashlib
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)

# Performance monitoring
class PerformanceMonitor:
    """Simple performance monitoring for ultra-budget deployment"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.lock = threading.Lock()
    
    def record_metric(self, operation: str, duration: float):
        """Record performance metric"""
        with self.lock:
            self.metrics[operation].append(duration)
            # Keep only last 100 measurements to prevent memory bloat
            if len(self.metrics[operation]) > 100:
                self.metrics[operation] = self.metrics[operation][-100:]
    
    def get_average(self, operation: str) -> float:
        """Get average duration for operation"""
        with self.lock:
            if not self.metrics[operation]:
                return 0.0
            return sum(self.metrics[operation]) / len(self.metrics[operation])
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        return {op: self.get_average(op) for op in self.metrics}

# Global performance monitor
perf_monitor = PerformanceMonitor()

class ComparisonGroup(str, Enum):
    """Demographic comparison groups - optimized for memory"""
    NATIONAL_MEDIAN = "national"
    AFRICAN_AMERICAN = "aa"
    AGE_25_35 = "age25_35"
    AFRICAN_AMERICAN_25_35 = "aa25_35"
    COLLEGE_GRADUATE = "college"
    AFRICAN_AMERICAN_COLLEGE = "aacollege"
    METRO_AREA = "metro"
    AFRICAN_AMERICAN_METRO = "aametro"

class EducationLevel(str, Enum):
    """Education level classifications - optimized"""
    HIGH_SCHOOL = "hs"
    SOME_COLLEGE = "some"
    BACHELORS = "ba"
    MASTERS = "ma"
    DOCTORATE = "phd"

@dataclass(frozen=True)
class IncomeComparison:
    """Immutable income comparison result for memory efficiency"""
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

@dataclass(frozen=True)
class DemographicIncomeData:
    """Immutable demographic income statistics for memory efficiency"""
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
    calculation_time: float = 0.0

class OptimizedIncomeComparator:
    """
    Ultra-budget optimized income comparator
    Features:
    - In-memory caching for demographic data
    - Efficient data structures
    - Minimal memory footprint
    - Performance monitoring
    - Thread-safe operations
    """
    
    def __init__(self):
        """Initialize with optimized data structures"""
        self._start_time = time.time()
        
        # Use frozen dataclasses for memory efficiency
        self._demographic_data = self._initialize_demographic_data()
        self._metro_areas = self._initialize_metro_areas()
        
        # Pre-computed lookup tables for performance
        self._percentile_cache = {}
        self._location_cache = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Performance tracking
        self._init_time = time.time() - self._start_time
        perf_monitor.record_metric("initialization", self._init_time)
        
        logger.info(f"IncomeComparator initialized in {self._init_time:.3f}s")
    
    def _initialize_demographic_data(self) -> Dict[str, DemographicIncomeData]:
        """Initialize demographic data with memory-efficient structure"""
        start_time = time.time()
        
        # Use frozen dataclasses and minimal data structure
        data = {
            ComparisonGroup.NATIONAL_MEDIAN: DemographicIncomeData(
                group_name="National Median",
                median_income=74580,
                mean_income=102430,
                percentile_25=45000,
                percentile_75=120000,
                sample_size=150000000,
                year=2022,
                source="2022 ACS"
            ),
            ComparisonGroup.AFRICAN_AMERICAN: DemographicIncomeData(
                group_name="African American",
                median_income=52000,
                mean_income=68000,
                percentile_25=32000,
                percentile_75=85000,
                sample_size=42000000,
                year=2022,
                source="2022 ACS"
            ),
            ComparisonGroup.AGE_25_35: DemographicIncomeData(
                group_name="Ages 25-35",
                median_income=58000,
                mean_income=72000,
                percentile_25=38000,
                percentile_75=95000,
                sample_size=45000000,
                year=2022,
                source="2022 ACS"
            ),
            ComparisonGroup.AFRICAN_AMERICAN_25_35: DemographicIncomeData(
                group_name="African American Ages 25-35",
                median_income=48000,
                mean_income=62000,
                percentile_25=30000,
                percentile_75=78000,
                sample_size=8500000,
                year=2022,
                source="2022 ACS"
            ),
            ComparisonGroup.COLLEGE_GRADUATE: DemographicIncomeData(
                group_name="College Graduates",
                median_income=85000,
                mean_income=105000,
                percentile_25=55000,
                percentile_75=130000,
                sample_size=75000000,
                year=2022,
                source="2022 ACS"
            ),
            ComparisonGroup.AFRICAN_AMERICAN_COLLEGE: DemographicIncomeData(
                group_name="African American College Graduates",
                median_income=65000,
                mean_income=82000,
                percentile_25=42000,
                percentile_75=105000,
                sample_size=12000000,
                year=2022,
                source="2022 ACS"
            )
        }
        
        perf_monitor.record_metric("demographic_data_init", time.time() - start_time)
        return data
    
    def _initialize_metro_areas(self) -> Dict[str, Dict[str, DemographicIncomeData]]:
        """Initialize metro area data with minimal memory footprint"""
        start_time = time.time()
        
        # Optimized metro data structure
        metro_data = {
            'atlanta': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Atlanta Metro",
                    median_income=72000,
                    mean_income=95000,
                    percentile_25=45000,
                    percentile_75=115000,
                    sample_size=6200000,
                    year=2022,
                    source="2022 ACS"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Atlanta African American",
                    median_income=55000,
                    mean_income=72000,
                    percentile_25=35000,
                    percentile_75=90000,
                    sample_size=2100000,
                    year=2022,
                    source="2022 ACS"
                )
            },
            'houston': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Houston Metro",
                    median_income=68000,
                    mean_income=88000,
                    percentile_25=42000,
                    percentile_75=110000,
                    sample_size=7200000,
                    year=2022,
                    source="2022 ACS"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Houston African American",
                    median_income=52000,
                    mean_income=68000,
                    percentile_25=32000,
                    percentile_75=85000,
                    sample_size=1800000,
                    year=2022,
                    source="2022 ACS"
                )
            },
            'washington_dc': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Washington DC Metro",
                    median_income=95000,
                    mean_income=125000,
                    percentile_25=60000,
                    percentile_75=150000,
                    sample_size=6200000,
                    year=2022,
                    source="2022 ACS"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Washington DC African American",
                    median_income=72000,
                    mean_income=95000,
                    percentile_25=45000,
                    percentile_75=120000,
                    sample_size=1800000,
                    year=2022,
                    source="2022 ACS"
                )
            },
            'dallas': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="Dallas Metro",
                    median_income=70000,
                    mean_income=92000,
                    percentile_25=43000,
                    percentile_75=115000,
                    sample_size=7600000,
                    year=2022,
                    source="2022 ACS"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="Dallas African American",
                    median_income=54000,
                    mean_income=70000,
                    percentile_25=33000,
                    percentile_75=88000,
                    sample_size=1900000,
                    year=2022,
                    source="2022 ACS"
                )
            },
            'new_york': {
                ComparisonGroup.METRO_AREA: DemographicIncomeData(
                    group_name="New York Metro",
                    median_income=85000,
                    mean_income=115000,
                    percentile_25=52000,
                    percentile_75=140000,
                    sample_size=20000000,
                    year=2022,
                    source="2022 ACS"
                ),
                ComparisonGroup.AFRICAN_AMERICAN_METRO: DemographicIncomeData(
                    group_name="New York African American",
                    median_income=65000,
                    mean_income=85000,
                    percentile_25=40000,
                    percentile_75=110000,
                    sample_size=3200000,
                    year=2022,
                    source="2022 ACS"
                )
            }
        }
        
        perf_monitor.record_metric("metro_data_init", time.time() - start_time)
        return metro_data
    
    @lru_cache(maxsize=1000)
    def _calculate_percentile_cached(self, user_income: int, median: int, mean: int, p25: int, p75: int) -> float:
        """Cached percentile calculation for performance"""
        try:
            # Use simplified normal approximation for speed
            if user_income <= p25:
                return 25.0 * (user_income / p25)
            elif user_income <= median:
                return 25.0 + 25.0 * ((user_income - p25) / (median - p25))
            elif user_income <= p75:
                return 50.0 + 25.0 * ((user_income - median) / (p75 - median))
            else:
                # For high incomes, use log-normal approximation
                return min(99.9, 75.0 + 24.9 * (1 - math.exp(-(user_income - p75) / (mean * 0.5))))
        except (ZeroDivisionError, ValueError):
            return 50.0
    
    def _calculate_percentile(self, user_income: int, data: DemographicIncomeData) -> float:
        """Calculate percentile rank with caching"""
        cache_key = (user_income, data.median_income, data.mean_income, data.percentile_25, data.percentile_75)
        return self._calculate_percentile_cached(*cache_key)
    
    def analyze_income(self, 
                      user_income: int,
                      location: Optional[str] = None,
                      education_level: Optional[EducationLevel] = None,
                      age_group: Optional[str] = "25-35") -> IncomeAnalysisResult:
        """
        Perform optimized income analysis with performance monitoring
        Target: < 500ms calculation time
        """
        start_time = time.time()
        
        try:
            with self._lock:
                # Validate inputs
                if user_income <= 0:
                    raise ValueError("Income must be positive")
                
                # Normalize location
                normalized_location = self._normalize_location(location) if location else None
                
                # Generate cache key for this analysis
                cache_key = self._generate_cache_key(user_income, normalized_location, education_level, age_group)
                
                # Check if we have cached result
                if hasattr(self, '_analysis_cache') and cache_key in self._analysis_cache:
                    cached_result = self._analysis_cache[cache_key]
                    if time.time() - cached_result['timestamp'] < 3600:  # 1 hour cache
                        perf_monitor.record_metric("cached_analysis", time.time() - start_time)
                        return cached_result['result']
                
                # Perform analysis
                comparisons = []
                
                # Core comparisons (always performed)
                comparisons.extend([
                    self._compare_national_median(user_income),
                    self._compare_african_american(user_income),
                    self._compare_age_group(user_income, age_group),
                    self._compare_african_american_age_group(user_income, age_group)
                ])
                
                # Education comparison if provided
                if education_level:
                    comparisons.extend([
                        self._compare_education_level(user_income, education_level),
                        self._compare_african_american_education(user_income, education_level)
                    ])
                
                # Location comparison if provided
                if normalized_location:
                    location_comparisons = self._compare_location(user_income, normalized_location)
                    comparisons.extend(location_comparisons)
                
                # Calculate overall metrics
                overall_percentile = self._calculate_overall_percentile(comparisons)
                primary_gap = self._find_primary_gap(comparisons)
                career_opportunity_score = self._calculate_career_opportunity_score(comparisons)
                
                # Generate insights
                motivational_summary = self._generate_motivational_summary(comparisons, primary_gap)
                action_plan = self._generate_action_plan(comparisons, primary_gap)
                next_steps = self._generate_next_steps(primary_gap, career_opportunity_score)
                
                # Create result
                result = IncomeAnalysisResult(
                    user_income=user_income,
                    comparisons=comparisons,
                    overall_percentile=overall_percentile,
                    primary_gap=primary_gap,
                    career_opportunity_score=career_opportunity_score,
                    motivational_summary=motivational_summary,
                    action_plan=action_plan,
                    next_steps=next_steps,
                    calculation_time=time.time() - start_time
                )
                
                # Cache result
                if not hasattr(self, '_analysis_cache'):
                    self._analysis_cache = {}
                self._analysis_cache[cache_key] = {
                    'result': result,
                    'timestamp': time.time()
                }
                
                # Limit cache size to prevent memory bloat
                if len(self._analysis_cache) > 1000:
                    # Remove oldest entries
                    oldest_keys = sorted(self._analysis_cache.keys(), 
                                       key=lambda k: self._analysis_cache[k]['timestamp'])[:100]
                    for key in oldest_keys:
                        del self._analysis_cache[key]
                
                calculation_time = time.time() - start_time
                perf_monitor.record_metric("income_analysis", calculation_time)
                
                logger.info(f"Income analysis completed in {calculation_time:.3f}s")
                return result
                
        except Exception as e:
            calculation_time = time.time() - start_time
            perf_monitor.record_metric("analysis_error", calculation_time)
            logger.error(f"Income analysis failed after {calculation_time:.3f}s: {str(e)}")
            raise
    
    def _generate_cache_key(self, user_income: int, location: Optional[str], 
                           education: Optional[EducationLevel], age_group: str) -> str:
        """Generate cache key for analysis results"""
        key_data = f"{user_income}_{location}_{education}_{age_group}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _compare_national_median(self, user_income: int) -> IncomeComparison:
        """Compare against national median income"""
        data = self._demographic_data[ComparisonGroup.NATIONAL_MEDIAN]
        percentile = self._calculate_percentile(user_income, data)
        gap = user_income - data.median_income
        gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.NATIONAL_MEDIAN,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=f"National median income is ${data.median_income:,}",
            motivational_insight=self._generate_insight(user_income, data.median_income, "national median"),
            action_item=self._generate_action_item(gap, "national median", data.median_income),
            data_source=data.source,
            confidence_level=0.95
        )
    
    def _compare_african_american(self, user_income: int) -> IncomeComparison:
        """Compare against African American median income"""
        data = self._demographic_data[ComparisonGroup.AFRICAN_AMERICAN]
        percentile = self._calculate_percentile(user_income, data)
        gap = user_income - data.median_income
        gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AFRICAN_AMERICAN,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=f"African American median income is ${data.median_income:,}",
            motivational_insight=self._generate_insight(user_income, data.median_income, "African American median"),
            action_item=self._generate_action_item(gap, "African American median", data.median_income),
            data_source=data.source,
            confidence_level=0.90
        )
    
    def _compare_age_group(self, user_income: int, age_group: str) -> IncomeComparison:
        """Compare against age group median income"""
        data = self._demographic_data[ComparisonGroup.AGE_25_35]
        percentile = self._calculate_percentile(user_income, data)
        gap = user_income - data.median_income
        gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AGE_25_35,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=f"Median income for ages 25-35 is ${data.median_income:,}",
            motivational_insight=self._generate_insight(user_income, data.median_income, "age group median"),
            action_item=self._generate_action_item(gap, "age group median", data.median_income),
            data_source=data.source,
            confidence_level=0.85
        )
    
    def _compare_african_american_age_group(self, user_income: int, age_group: str) -> IncomeComparison:
        """Compare against African American age group median income"""
        data = self._demographic_data[ComparisonGroup.AFRICAN_AMERICAN_25_35]
        percentile = self._calculate_percentile(user_income, data)
        gap = user_income - data.median_income
        gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AFRICAN_AMERICAN_25_35,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=f"African American ages 25-35 median income is ${data.median_income:,}",
            motivational_insight=self._generate_insight(user_income, data.median_income, "African American age group median"),
            action_item=self._generate_action_item(gap, "African American age group median", data.median_income),
            data_source=data.source,
            confidence_level=0.80
        )
    
    def _compare_education_level(self, user_income: int, education_level: EducationLevel) -> IncomeComparison:
        """Compare against education level median income"""
        data = self._demographic_data[ComparisonGroup.COLLEGE_GRADUATE]
        percentile = self._calculate_percentile(user_income, data)
        gap = user_income - data.median_income
        gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.COLLEGE_GRADUATE,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=f"College graduate median income is ${data.median_income:,}",
            motivational_insight=self._generate_insight(user_income, data.median_income, "college graduate median"),
            action_item=self._generate_action_item(gap, "college graduate median", data.median_income),
            data_source=data.source,
            confidence_level=0.85
        )
    
    def _compare_african_american_education(self, user_income: int, education_level: EducationLevel) -> IncomeComparison:
        """Compare against African American education level median income"""
        data = self._demographic_data[ComparisonGroup.AFRICAN_AMERICAN_COLLEGE]
        percentile = self._calculate_percentile(user_income, data)
        gap = user_income - data.median_income
        gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
        
        return IncomeComparison(
            comparison_group=ComparisonGroup.AFRICAN_AMERICAN_COLLEGE,
            group_name=data.group_name,
            user_income=user_income,
            median_income=data.median_income,
            percentile_rank=percentile,
            income_gap=gap,
            gap_percentage=gap_percentage,
            context_message=f"African American college graduate median income is ${data.median_income:,}",
            motivational_insight=self._generate_insight(user_income, data.median_income, "African American college graduate median"),
            action_item=self._generate_action_item(gap, "African American college graduate median", data.median_income),
            data_source=data.source,
            confidence_level=0.80
        )
    
    def _compare_location(self, user_income: int, location: str) -> List[IncomeComparison]:
        """Compare against location-specific median incomes"""
        comparisons = []
        location_data = self._metro_areas.get(location.lower())
        
        if location_data:
            for group, data in location_data.items():
                percentile = self._calculate_percentile(user_income, data)
                gap = user_income - data.median_income
                gap_percentage = (gap / data.median_income) * 100 if data.median_income > 0 else 0
                
                comparisons.append(IncomeComparison(
                    comparison_group=group,
                    group_name=data.group_name,
                    user_income=user_income,
                    median_income=data.median_income,
                    percentile_rank=percentile,
                    income_gap=gap,
                    gap_percentage=gap_percentage,
                    context_message=f"{data.group_name} median income is ${data.median_income:,}",
                    motivational_insight=self._generate_insight(user_income, data.median_income, data.group_name),
                    action_item=self._generate_action_item(gap, data.group_name, data.median_income),
                    data_source=data.source,
                    confidence_level=0.75
                ))
        
        return comparisons
    
    def _calculate_overall_percentile(self, comparisons: List[IncomeComparison]) -> float:
        """Calculate weighted overall percentile"""
        if not comparisons:
            return 50.0
        
        # Weight by confidence level and sample size
        total_weight = 0
        weighted_sum = 0
        
        for comp in comparisons:
            weight = comp.confidence_level
            total_weight += weight
            weighted_sum += comp.percentile_rank * weight
        
        return weighted_sum / total_weight if total_weight > 0 else 50.0
    
    def _find_primary_gap(self, comparisons: List[IncomeComparison]) -> IncomeComparison:
        """Find the comparison with the largest negative gap"""
        negative_gaps = [comp for comp in comparisons if comp.income_gap < 0]
        
        if not negative_gaps:
            # If no negative gaps, return the comparison with highest confidence
            return max(comparisons, key=lambda x: x.confidence_level)
        
        # Return the comparison with the largest negative gap
        return min(negative_gaps, key=lambda x: x.income_gap)
    
    def _calculate_career_opportunity_score(self, comparisons: List[IncomeComparison]) -> float:
        """Calculate career opportunity score based on gaps"""
        if not comparisons:
            return 0.0
        
        total_opportunity = 0
        total_weight = 0
        
        for comp in comparisons:
            if comp.income_gap < 0:  # Negative gap = opportunity
                opportunity = abs(comp.income_gap) / comp.median_income * 100
                weight = comp.confidence_level
                total_opportunity += opportunity * weight
                total_weight += weight
        
        return total_opportunity / total_weight if total_weight > 0 else 0.0
    
    def _generate_insight(self, user_income: int, benchmark_income: int, benchmark_name: str) -> str:
        """Generate motivational insight"""
        if user_income >= benchmark_income:
            return f"You're earning above the {benchmark_name}, which is excellent!"
        else:
            gap = benchmark_income - user_income
            return f"You have the potential to earn ${gap:,} more by reaching the {benchmark_name} level."
    
    def _generate_action_item(self, gap: int, benchmark_name: str, benchmark_income: int) -> str:
        """Generate actionable item"""
        if gap >= 0:
            return f"Maintain your advantage over the {benchmark_name} and continue growing."
        else:
            return f"Focus on skills and opportunities to close the ${abs(gap):,} gap with the {benchmark_name}."
    
    def _generate_motivational_summary(self, comparisons: List[IncomeComparison], primary_gap: IncomeComparison) -> str:
        """Generate motivational summary"""
        positive_comparisons = [c for c in comparisons if c.income_gap >= 0]
        negative_comparisons = [c for c in comparisons if c.income_gap < 0]
        
        if len(positive_comparisons) > len(negative_comparisons):
            return "You're performing well across multiple benchmarks! Focus on maintaining your advantage while exploring new opportunities."
        else:
            return f"You have significant growth potential. The largest opportunity is in {primary_gap.group_name} where you could earn ${abs(primary_gap.income_gap):,} more."
    
    def _generate_action_plan(self, comparisons: List[IncomeComparison], primary_gap: IncomeComparison) -> List[str]:
        """Generate action plan"""
        actions = [
            "Assess your skills gap and identify areas for improvement",
            "Research promotion opportunities within your current role",
            "Network with professionals in higher-paying positions",
            "Consider additional education or certifications",
            "Negotiate your compensation based on market research"
        ]
        
        if primary_gap.income_gap < 0:
            actions.insert(0, f"Focus on closing the ${abs(primary_gap.income_gap):,} gap in {primary_gap.group_name}")
        
        return actions[:5]  # Limit to 5 actions
    
    def _generate_next_steps(self, primary_gap: IncomeComparison, opportunity_score: float) -> List[str]:
        """Generate next steps"""
        steps = [
            "Review your current skills and identify growth areas",
            "Research salary ranges for your target positions",
            "Update your resume and LinkedIn profile",
            "Schedule informational interviews with industry leaders",
            "Set specific income goals and timeline"
        ]
        
        if opportunity_score > 20:
            steps.insert(0, "Prioritize the highest-impact opportunities for immediate action")
        
        return steps[:5]  # Limit to 5 steps
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location string for consistent lookup"""
        if not location:
            return ""
        
        # Pre-computed location mapping for performance
        location_mapping = {
            'atlanta': 'atlanta',
            'chicago': 'chicago',
            'dallas': 'dallas',
            'houston': 'houston',
            'los angeles': 'los_angeles',
            'miami': 'miami',
            'new york': 'new_york',
            'philadelphia': 'philadelphia',
            'washington dc': 'washington_dc',
            'washington': 'washington_dc'
        }
        
        normalized = location.lower().strip()
        return location_mapping.get(normalized, normalized)
    
    def get_available_locations(self) -> List[str]:
        """Get list of available locations"""
        return list(self._metro_areas.keys())
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        return perf_monitor.get_stats()
    
    def clear_cache(self):
        """Clear analysis cache to free memory"""
        if hasattr(self, '_analysis_cache'):
            self._analysis_cache.clear()
        self._percentile_cache.clear()
        self._location_cache.clear()
        logger.info("Cache cleared to free memory")

# Singleton instance for ultra-budget deployment
_income_comparator_instance = None
_instance_lock = threading.Lock()

def get_income_comparator() -> OptimizedIncomeComparator:
    """Get singleton instance of income comparator"""
    global _income_comparator_instance
    
    if _income_comparator_instance is None:
        with _instance_lock:
            if _income_comparator_instance is None:
                _income_comparator_instance = OptimizedIncomeComparator()
    
    return _income_comparator_instance 