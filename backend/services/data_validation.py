"""
Data Validation Service for Salary Data
Handles outlier detection, data quality validation, and confidence scoring
"""

import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import statistics
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(str, Enum):
    """Data validation levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INVALID = "invalid"

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    confidence_score: float
    validation_level: ValidationLevel
    issues: List[str]
    warnings: List[str]
    outliers_detected: List[Dict[str, Any]]
    data_quality_score: float
    last_updated: datetime

class OutlierDetector:
    """Detect outliers in salary data using statistical methods"""
    
    def __init__(self, method: str = "iqr"):
        """
        Initialize outlier detector
        
        Args:
            method: Detection method ('iqr', 'zscore', 'modified_zscore')
        """
        self.method = method
    
    def detect_outliers(self, data: List[float], threshold: float = 1.5) -> List[Dict[str, Any]]:
        """
        Detect outliers in a dataset
        
        Args:
            data: List of numerical values
            threshold: Threshold for outlier detection
        
        Returns:
            List of outlier information
        """
        if len(data) < 3:
            return []
        
        outliers = []
        
        if self.method == "iqr":
            outliers = self._iqr_method(data, threshold)
        elif self.method == "zscore":
            outliers = self._zscore_method(data, threshold)
        elif self.method == "modified_zscore":
            outliers = self._modified_zscore_method(data, threshold)
        
        return outliers
    
    def _iqr_method(self, data: List[float], threshold: float) -> List[Dict[str, Any]]:
        """Detect outliers using Interquartile Range method"""
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - (threshold * iqr)
        upper_bound = q3 + (threshold * iqr)
        
        outliers = []
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                outliers.append({
                    'index': i,
                    'value': value,
                    'method': 'iqr',
                    'bounds': (lower_bound, upper_bound),
                    'severity': 'high' if abs(value - np.mean(data)) > 2 * np.std(data) else 'medium'
                })
        
        return outliers
    
    def _zscore_method(self, data: List[float], threshold: float) -> List[Dict[str, Any]]:
        """Detect outliers using Z-score method"""
        mean = np.mean(data)
        std = np.std(data)
        
        if std == 0:
            return []
        
        outliers = []
        for i, value in enumerate(data):
            z_score = abs((value - mean) / std)
            if z_score > threshold:
                outliers.append({
                    'index': i,
                    'value': value,
                    'method': 'zscore',
                    'z_score': z_score,
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        return outliers
    
    def _modified_zscore_method(self, data: List[float], threshold: float) -> List[Dict[str, Any]]:
        """Detect outliers using Modified Z-score method"""
        median = np.median(data)
        mad = np.median([abs(x - median) for x in data])
        
        if mad == 0:
            return []
        
        outliers = []
        for i, value in enumerate(data):
            modified_z_score = abs(0.6745 * (value - median) / mad)
            if modified_z_score > threshold:
                outliers.append({
                    'index': i,
                    'value': value,
                    'method': 'modified_zscore',
                    'modified_z_score': modified_z_score,
                    'severity': 'high' if modified_z_score > 3.5 else 'medium'
                })
        
        return outliers

class DataValidator:
    """Validate salary data quality and detect issues"""
    
    def __init__(self):
        """Initialize data validator"""
        self.outlier_detector = OutlierDetector()
        
        # Validation thresholds
        self.thresholds = {
            'min_salary': 20000,  # Minimum reasonable salary
            'max_salary': 500000,  # Maximum reasonable salary
            'min_sample_size': 10,  # Minimum sample size for statistical analysis
            'max_age_days': 365,  # Maximum age of data in days
            'min_confidence': 0.5,  # Minimum confidence score
            'outlier_threshold': 2.0  # Z-score threshold for outliers
        }
    
    def validate_salary_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate salary data quality
        
        Args:
            data: Salary data dictionary
        
        Returns:
            ValidationResult with validation information
        """
        issues = []
        warnings = []
        confidence_score = 1.0
        
        # Check required fields
        required_fields = ['median_salary', 'mean_salary', 'sample_size', 'year']
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.2
        
        if issues:
            return ValidationResult(
                is_valid=False,
                confidence_score=max(0.0, confidence_score),
                validation_level=ValidationLevel.INVALID,
                issues=issues,
                warnings=warnings,
                outliers_detected=[],
                data_quality_score=0.0,
                last_updated=datetime.now()
            )
        
        # Validate salary ranges
        median_salary = data.get('median_salary', 0)
        mean_salary = data.get('mean_salary', 0)
        
        if median_salary < self.thresholds['min_salary']:
            issues.append(f"Median salary too low: ${median_salary:,}")
            confidence_score -= 0.3
        
        if median_salary > self.thresholds['max_salary']:
            issues.append(f"Median salary too high: ${median_salary:,}")
            confidence_score -= 0.3
        
        if mean_salary < self.thresholds['min_salary']:
            issues.append(f"Mean salary too low: ${mean_salary:,}")
            confidence_score -= 0.2
        
        if mean_salary > self.thresholds['max_salary']:
            issues.append(f"Mean salary too high: ${mean_salary:,}")
            confidence_score -= 0.2
        
        # Check for logical consistency
        if mean_salary < median_salary * 0.8:
            warnings.append("Mean salary significantly lower than median (possible data skew)")
            confidence_score -= 0.1
        
        if mean_salary > median_salary * 1.5:
            warnings.append("Mean salary significantly higher than median (possible outliers)")
            confidence_score -= 0.1
        
        # Validate sample size
        sample_size = data.get('sample_size', 0)
        if sample_size < self.thresholds['min_sample_size']:
            warnings.append(f"Small sample size: {sample_size}")
            confidence_score -= 0.2
        
        # Validate data age
        year = data.get('year', 0)
        current_year = datetime.now().year
        if current_year - year > 3:
            warnings.append(f"Data is {current_year - year} years old")
            confidence_score -= 0.1
        
        # Detect outliers if percentile data is available
        outliers = []
        if 'percentile_25' in data and 'percentile_75' in data:
            percentile_data = [
                data['percentile_25'],
                data['median_salary'],
                data['percentile_75']
            ]
            outliers = self.outlier_detector.detect_outliers(
                percentile_data, 
                self.thresholds['outlier_threshold']
            )
            
            if outliers:
                warnings.append(f"Detected {len(outliers)} potential outliers")
                confidence_score -= 0.1
        
        # Calculate data quality score
        data_quality_score = self._calculate_quality_score(data, outliers)
        
        # Determine validation level
        validation_level = self._determine_validation_level(confidence_score, issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence_score=max(0.0, confidence_score),
            validation_level=validation_level,
            issues=issues,
            warnings=warnings,
            outliers_detected=outliers,
            data_quality_score=data_quality_score,
            last_updated=datetime.now()
        )
    
    def validate_cost_of_living_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate cost of living data
        
        Args:
            data: Cost of living data dictionary
        
        Returns:
            ValidationResult with validation information
        """
        issues = []
        warnings = []
        confidence_score = 1.0
        
        # Check required fields
        required_fields = ['overall_cost_index', 'housing_cost_index']
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.3
        
        if issues:
            return ValidationResult(
                is_valid=False,
                confidence_score=max(0.0, confidence_score),
                validation_level=ValidationLevel.INVALID,
                issues=issues,
                warnings=warnings,
                outliers_detected=[],
                data_quality_score=0.0,
                last_updated=datetime.now()
            )
        
        # Validate cost indices
        overall_index = data.get('overall_cost_index', 0)
        housing_index = data.get('housing_cost_index', 0)
        
        if overall_index < 50 or overall_index > 300:
            issues.append(f"Overall cost index out of reasonable range: {overall_index}")
            confidence_score -= 0.3
        
        if housing_index < 50 or housing_index > 400:
            issues.append(f"Housing cost index out of reasonable range: {housing_index}")
            confidence_score -= 0.3
        
        # Check for logical consistency
        if housing_index > overall_index * 2:
            warnings.append("Housing cost index significantly higher than overall index")
            confidence_score -= 0.1
        
        # Validate other indices if available
        for index_name in ['transportation_cost_index', 'food_cost_index', 'healthcare_cost_index', 'utilities_cost_index']:
            if index_name in data:
                index_value = data[index_name]
                if index_value < 30 or index_value > 250:
                    warnings.append(f"{index_name} out of reasonable range: {index_value}")
                    confidence_score -= 0.05
        
        # Calculate data quality score
        data_quality_score = self._calculate_cost_quality_score(data)
        
        # Determine validation level
        validation_level = self._determine_validation_level(confidence_score, issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence_score=max(0.0, confidence_score),
            validation_level=validation_level,
            issues=issues,
            warnings=warnings,
            outliers_detected=[],
            data_quality_score=data_quality_score,
            last_updated=datetime.now()
        )
    
    def validate_job_market_data(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Validate job market data
        
        Args:
            data: Job market data dictionary
        
        Returns:
            ValidationResult with validation information
        """
        issues = []
        warnings = []
        confidence_score = 1.0
        
        # Check required fields
        required_fields = ['job_count', 'average_salary']
        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")
                confidence_score -= 0.3
        
        if issues:
            return ValidationResult(
                is_valid=False,
                confidence_score=max(0.0, confidence_score),
                validation_level=ValidationLevel.INVALID,
                issues=issues,
                warnings=warnings,
                outliers_detected=[],
                data_quality_score=0.0,
                last_updated=datetime.now()
            )
        
        # Validate job count
        job_count = data.get('job_count', 0)
        if job_count < 1:
            issues.append("No jobs found")
            confidence_score -= 0.5
        
        if job_count > 10000:
            warnings.append(f"Unusually high job count: {job_count}")
            confidence_score -= 0.1
        
        # Validate salary range
        avg_salary = data.get('average_salary', 0)
        if avg_salary < self.thresholds['min_salary']:
            issues.append(f"Average salary too low: ${avg_salary:,}")
            confidence_score -= 0.3
        
        if avg_salary > self.thresholds['max_salary']:
            issues.append(f"Average salary too high: ${avg_salary:,}")
            confidence_score -= 0.3
        
        # Validate salary range if available
        if 'salary_range_min' in data and 'salary_range_max' in data:
            min_salary = data['salary_range_min']
            max_salary = data['salary_range_max']
            
            if min_salary > max_salary:
                issues.append("Salary range minimum greater than maximum")
                confidence_score -= 0.3
            
            if max_salary - min_salary > 200000:
                warnings.append("Very wide salary range (possible data quality issue)")
                confidence_score -= 0.1
        
        # Validate demand score if available
        if 'demand_score' in data:
            demand_score = data['demand_score']
            if demand_score < 0 or demand_score > 100:
                issues.append(f"Demand score out of range: {demand_score}")
                confidence_score -= 0.2
        
        # Calculate data quality score
        data_quality_score = self._calculate_job_market_quality_score(data)
        
        # Determine validation level
        validation_level = self._determine_validation_level(confidence_score, issues)
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            confidence_score=max(0.0, confidence_score),
            validation_level=validation_level,
            issues=issues,
            warnings=warnings,
            outliers_detected=[],
            data_quality_score=data_quality_score,
            last_updated=datetime.now()
        )
    
    def _calculate_quality_score(self, data: Dict[str, Any], outliers: List[Dict[str, Any]]) -> float:
        """Calculate data quality score for salary data"""
        score = 1.0
        
        # Sample size factor
        sample_size = data.get('sample_size', 0)
        if sample_size < 100:
            score -= 0.2
        elif sample_size < 1000:
            score -= 0.1
        
        # Data completeness factor
        required_fields = ['median_salary', 'mean_salary', 'percentile_25', 'percentile_75']
        missing_fields = sum(1 for field in required_fields if field not in data)
        score -= missing_fields * 0.1
        
        # Outlier factor
        if outliers:
            score -= len(outliers) * 0.05
        
        # Data age factor
        year = data.get('year', 0)
        current_year = datetime.now().year
        if current_year - year > 2:
            score -= 0.1
        
        return max(0.0, score)
    
    def _calculate_cost_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score for cost of living data"""
        score = 1.0
        
        # Index completeness factor
        required_indices = ['overall_cost_index', 'housing_cost_index']
        optional_indices = ['transportation_cost_index', 'food_cost_index', 'healthcare_cost_index', 'utilities_cost_index']
        
        missing_required = sum(1 for field in required_indices if field not in data)
        score -= missing_required * 0.3
        
        missing_optional = sum(1 for field in optional_indices if field not in data)
        score -= missing_optional * 0.05
        
        return max(0.0, score)
    
    def _calculate_job_market_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score for job market data"""
        score = 1.0
        
        # Job count factor
        job_count = data.get('job_count', 0)
        if job_count < 10:
            score -= 0.3
        elif job_count < 50:
            score -= 0.1
        
        # Data completeness factor
        required_fields = ['job_count', 'average_salary', 'salary_range_min', 'salary_range_max', 'demand_score']
        missing_fields = sum(1 for field in required_fields if field not in data)
        score -= missing_fields * 0.1
        
        return max(0.0, score)
    
    def _determine_validation_level(self, confidence_score: float, issues: List[str]) -> ValidationLevel:
        """Determine validation level based on confidence score and issues"""
        if confidence_score >= 0.8 and not issues:
            return ValidationLevel.HIGH
        elif confidence_score >= 0.6:
            return ValidationLevel.MEDIUM
        elif confidence_score >= 0.4:
            return ValidationLevel.LOW
        else:
            return ValidationLevel.INVALID
    
    def compare_datasets(self, dataset1: Dict[str, Any], dataset2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two datasets for consistency
        
        Args:
            dataset1: First dataset
            dataset2: Second dataset
        
        Returns:
            Comparison results
        """
        comparison = {
            'consistent': True,
            'differences': [],
            'similarity_score': 0.0
        }
        
        # Compare median salaries
        if 'median_salary' in dataset1 and 'median_salary' in dataset2:
            median1 = dataset1['median_salary']
            median2 = dataset2['median_salary']
            
            if median1 > 0 and median2 > 0:
                difference = abs(median1 - median2) / max(median1, median2)
                
                if difference > 0.2:  # 20% difference threshold
                    comparison['consistent'] = False
                    comparison['differences'].append({
                        'field': 'median_salary',
                        'difference_percent': difference * 100,
                        'dataset1_value': median1,
                        'dataset2_value': median2
                    })
        
        # Calculate similarity score
        if comparison['differences']:
            avg_difference = sum(d['difference_percent'] for d in comparison['differences']) / len(comparison['differences'])
            comparison['similarity_score'] = max(0.0, 100 - avg_difference)
        else:
            comparison['similarity_score'] = 100.0
        
        return comparison 