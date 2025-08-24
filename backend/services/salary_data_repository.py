"""
Salary Data Repository
Handles database operations for salary data tables
"""

import logging
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

# Support both running within the full backend package and directly from backend/ as sys.path root
try:
    from backend.models.salary_data_models import (
        SalaryBenchmark, MarketData, ConfidenceScore,
        DataRefreshLog, CacheMetric
    )
except Exception:  # pragma: no cover - fallback for test import layout
    from models.salary_data_models import (
        SalaryBenchmark, MarketData, ConfidenceScore,
        DataRefreshLog, CacheMetric
    )
if TYPE_CHECKING:  # Avoid runtime circular import; types are for hints only
    try:
        from backend.services.salary_data_service import (
            SalaryDataPoint, CostOfLivingDataPoint, JobMarketDataPoint, ComprehensiveSalaryData
        )
    except Exception:  # pragma: no cover
        from services.salary_data_service import (
            SalaryDataPoint, CostOfLivingDataPoint, JobMarketDataPoint, ComprehensiveSalaryData
        )

logger = logging.getLogger(__name__)

class SalaryDataRepository:
    """Repository for salary data database operations"""
    
    def __init__(self, db_session: Session):
        """Initialize repository with database session"""
        self.db = db_session
    
    def save_salary_benchmark(self, salary_point: SalaryDataPoint) -> SalaryBenchmark:
        """
        Save salary benchmark data to database
        
        Args:
            salary_point: SalaryDataPoint from service
        
        Returns:
            Saved SalaryBenchmark record
        """
        try:
            # Check if record exists
            existing = self.db.query(SalaryBenchmark).filter(
                and_(
                    SalaryBenchmark.location == salary_point.location,
                    SalaryBenchmark.occupation == salary_point.occupation,
                    SalaryBenchmark.source == salary_point.source.value,
                    SalaryBenchmark.year == salary_point.year
                )
            ).first()
            
            if existing:
                # Update existing record
                existing.median_salary = Decimal(str(salary_point.median_salary))
                existing.mean_salary = Decimal(str(salary_point.mean_salary))
                existing.percentile_25 = Decimal(str(salary_point.percentile_25))
                existing.percentile_75 = Decimal(str(salary_point.percentile_75))
                existing.sample_size = salary_point.sample_size
                existing.confidence_score = Decimal(str(salary_point.confidence_score))
                existing.cache_key = salary_point.cache_key
                existing.updated_at = datetime.utcnow()
                
                if salary_point.validation_result:
                    existing.data_quality_score = Decimal(str(salary_point.validation_result.data_quality_score))
                    existing.validation_level = salary_point.validation_result.validation_level.value
                    existing.outliers_detected = len(salary_point.validation_result.outliers_detected)
                
                record = existing
            else:
                # Create new record
                record = SalaryBenchmark(
                    location=salary_point.location,
                    occupation=salary_point.occupation,
                    source=salary_point.source.value,
                    median_salary=Decimal(str(salary_point.median_salary)),
                    mean_salary=Decimal(str(salary_point.mean_salary)),
                    percentile_25=Decimal(str(salary_point.percentile_25)),
                    percentile_75=Decimal(str(salary_point.percentile_75)),
                    sample_size=salary_point.sample_size,
                    year=salary_point.year,
                    confidence_score=Decimal(str(salary_point.confidence_score)),
                    cache_key=salary_point.cache_key
                )
                
                if salary_point.validation_result:
                    record.data_quality_score = Decimal(str(salary_point.validation_result.data_quality_score))
                    record.validation_level = salary_point.validation_result.validation_level.value
                    record.outliers_detected = len(salary_point.validation_result.outliers_detected)
                
                self.db.add(record)
            
            self.db.commit()
            logger.info(f"Saved salary benchmark for {salary_point.location}, {salary_point.occupation}, {salary_point.source.value}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving salary benchmark: {e}")
            raise
    
    def save_cost_of_living_data(self, cost_data: CostOfLivingDataPoint) -> MarketData:
        """
        Save cost of living data to database
        
        Args:
            cost_data: CostOfLivingDataPoint from service
        
        Returns:
            Saved MarketData record
        """
        try:
            # Check if record exists
            existing = self.db.query(MarketData).filter(
                and_(
                    MarketData.location == cost_data.location,
                    MarketData.data_type == 'cost_of_living',
                    MarketData.year == cost_data.year
                )
            ).first()
            
            if existing:
                # Update existing record
                existing.overall_cost_index = Decimal(str(cost_data.overall_cost_index))
                existing.housing_cost_index = Decimal(str(cost_data.housing_cost_index))
                existing.transportation_cost_index = Decimal(str(cost_data.transportation_cost_index))
                existing.food_cost_index = Decimal(str(cost_data.food_cost_index))
                existing.healthcare_cost_index = Decimal(str(cost_data.healthcare_cost_index))
                existing.utilities_cost_index = Decimal(str(cost_data.utilities_cost_index))
                existing.confidence_score = Decimal(str(cost_data.confidence_score))
                existing.cache_key = cost_data.cache_key
                existing.updated_at = datetime.utcnow()
                
                if cost_data.validation_result:
                    existing.data_quality_score = Decimal(str(cost_data.validation_result.data_quality_score))
                    existing.validation_level = cost_data.validation_result.validation_level.value
                
                record = existing
            else:
                # Create new record
                record = MarketData(
                    location=cost_data.location,
                    data_type='cost_of_living',
                    overall_cost_index=Decimal(str(cost_data.overall_cost_index)),
                    housing_cost_index=Decimal(str(cost_data.housing_cost_index)),
                    transportation_cost_index=Decimal(str(cost_data.transportation_cost_index)),
                    food_cost_index=Decimal(str(cost_data.food_cost_index)),
                    healthcare_cost_index=Decimal(str(cost_data.healthcare_cost_index)),
                    utilities_cost_index=Decimal(str(cost_data.utilities_cost_index)),
                    year=cost_data.year,
                    confidence_score=Decimal(str(cost_data.confidence_score)),
                    cache_key=cost_data.cache_key
                )
                
                if cost_data.validation_result:
                    record.data_quality_score = Decimal(str(cost_data.validation_result.data_quality_score))
                    record.validation_level = cost_data.validation_result.validation_level.value
                
                self.db.add(record)
            
            self.db.commit()
            logger.info(f"Saved cost of living data for {cost_data.location}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving cost of living data: {e}")
            raise
    
    def save_job_market_data(self, job_data: JobMarketDataPoint) -> MarketData:
        """
        Save job market data to database
        
        Args:
            job_data: JobMarketDataPoint from service
        
        Returns:
            Saved MarketData record
        """
        try:
            # Check if record exists
            existing = self.db.query(MarketData).filter(
                and_(
                    MarketData.location == job_data.location,
                    MarketData.occupation == job_data.occupation,
                    MarketData.data_type == 'job_market'
                )
            ).first()
            
            if existing:
                # Update existing record
                existing.job_count = job_data.job_count
                existing.average_salary = Decimal(str(job_data.average_salary))
                existing.salary_range_min = Decimal(str(job_data.salary_range_min))
                existing.salary_range_max = Decimal(str(job_data.salary_range_max))
                existing.demand_score = Decimal(str(job_data.demand_score))
                existing.year = job_data.year
                existing.confidence_score = Decimal(str(job_data.confidence_score))
                existing.cache_key = job_data.cache_key
                existing.updated_at = datetime.utcnow()
                
                if job_data.validation_result:
                    existing.data_quality_score = Decimal(str(job_data.validation_result.data_quality_score))
                    existing.validation_level = job_data.validation_result.validation_level.value
                
                record = existing
            else:
                # Create new record
                record = MarketData(
                    location=job_data.location,
                    occupation=job_data.occupation,
                    data_type='job_market',
                    job_count=job_data.job_count,
                    average_salary=Decimal(str(job_data.average_salary)),
                    salary_range_min=Decimal(str(job_data.salary_range_min)),
                    salary_range_max=Decimal(str(job_data.salary_range_max)),
                    demand_score=Decimal(str(job_data.demand_score)),
                    year=job_data.year,
                    confidence_score=Decimal(str(job_data.confidence_score)),
                    cache_key=job_data.cache_key
                )
                
                if job_data.validation_result:
                    record.data_quality_score = Decimal(str(job_data.validation_result.data_quality_score))
                    record.validation_level = job_data.validation_result.validation_level.value
                
                self.db.add(record)
            
            self.db.commit()
            logger.info(f"Saved job market data for {job_data.location}, {job_data.occupation}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving job market data: {e}")
            raise
    
    def save_confidence_score(self, comprehensive_data: ComprehensiveSalaryData) -> ConfidenceScore:
        """
        Save confidence score data to database
        
        Args:
            comprehensive_data: ComprehensiveSalaryData from service
        
        Returns:
            Saved ConfidenceScore record
        """
        try:
            # Check if record exists
            existing = self.db.query(ConfidenceScore).filter(
                and_(
                    ConfidenceScore.location == comprehensive_data.location,
                    ConfidenceScore.occupation == comprehensive_data.occupation
                )
            ).first()
            
            # Calculate validation metrics
            validation_issues_count = 0
            validation_warnings_count = 0
            outliers_count = 0
            
            for salary_point in comprehensive_data.salary_data:
                if salary_point.validation_result:
                    validation_issues_count += len(salary_point.validation_result.issues)
                    validation_warnings_count += len(salary_point.validation_result.warnings)
                    outliers_count += len(salary_point.validation_result.outliers_detected)
            
            if comprehensive_data.cost_of_living_data and comprehensive_data.cost_of_living_data.validation_result:
                validation_issues_count += len(comprehensive_data.cost_of_living_data.validation_result.issues)
                validation_warnings_count += len(comprehensive_data.cost_of_living_data.validation_result.warnings)
            
            if comprehensive_data.job_market_data and comprehensive_data.job_market_data.validation_result:
                validation_issues_count += len(comprehensive_data.job_market_data.validation_result.issues)
                validation_warnings_count += len(comprehensive_data.job_market_data.validation_result.warnings)
            
            if existing:
                # Update existing record
                existing.overall_confidence_score = Decimal(str(comprehensive_data.overall_confidence_score))
                existing.data_quality_score = Decimal(str(comprehensive_data.data_quality_score))
                existing.validation_issues_count = validation_issues_count
                existing.validation_warnings_count = validation_warnings_count
                existing.outliers_count = outliers_count
                existing.data_sources_count = len(comprehensive_data.salary_data)
                existing.last_validation_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                
                record = existing
            else:
                # Create new record
                record = ConfidenceScore(
                    location=comprehensive_data.location,
                    occupation=comprehensive_data.occupation,
                    overall_confidence_score=Decimal(str(comprehensive_data.overall_confidence_score)),
                    data_quality_score=Decimal(str(comprehensive_data.data_quality_score)),
                    validation_issues_count=validation_issues_count,
                    validation_warnings_count=validation_warnings_count,
                    outliers_count=outliers_count,
                    data_sources_count=len(comprehensive_data.salary_data),
                    last_validation_at=datetime.utcnow()
                )
                
                self.db.add(record)
            
            self.db.commit()
            logger.info(f"Saved confidence score for {comprehensive_data.location}, {comprehensive_data.occupation}")
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving confidence score: {e}")
            raise
    
    def get_salary_benchmarks(self, location: str, occupation: str = None, year: int = None) -> List[SalaryBenchmark]:
        """
        Get salary benchmarks from database
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
            year: Target year (optional)
        
        Returns:
            List of SalaryBenchmark records
        """
        query = self.db.query(SalaryBenchmark).filter(
            SalaryBenchmark.location == location
        )
        
        if occupation:
            query = query.filter(SalaryBenchmark.occupation == occupation)
        
        if year:
            query = query.filter(SalaryBenchmark.year == year)
        
        return query.order_by(desc(SalaryBenchmark.confidence_score)).all()
    
    def get_market_data(self, location: str, data_type: str, occupation: str = None) -> List[MarketData]:
        """
        Get market data from database
        
        Args:
            location: Target location
            data_type: Type of market data (cost_of_living, job_market)
            occupation: Target occupation (optional)
        
        Returns:
            List of MarketData records
        """
        query = self.db.query(MarketData).filter(
            and_(
                MarketData.location == location,
                MarketData.data_type == data_type
            )
        )
        
        if occupation:
            query = query.filter(MarketData.occupation == occupation)
        
        return query.order_by(desc(MarketData.confidence_score)).all()
    
    def get_confidence_score(self, location: str, occupation: str = None) -> Optional[ConfidenceScore]:
        """
        Get confidence score from database
        
        Args:
            location: Target location
            occupation: Target occupation (optional)
        
        Returns:
            ConfidenceScore record or None
        """
        query = self.db.query(ConfidenceScore).filter(
            ConfidenceScore.location == location
        )
        
        if occupation:
            query = query.filter(ConfidenceScore.occupation == occupation)
        
        return query.first()
    
    def log_data_refresh(self, task_type: str, location: str = None, occupation: str = None, 
                        celery_task_id: str = None) -> DataRefreshLog:
        """
        Log data refresh task start
        
        Args:
            task_type: Type of task
            location: Target location (optional)
            occupation: Target occupation (optional)
            celery_task_id: Celery task ID (optional)
        
        Returns:
            DataRefreshLog record
        """
        log = DataRefreshLog(
            task_type=task_type,
            location=location,
            occupation=occupation,
            status='started',
            started_at=datetime.utcnow(),
            celery_task_id=celery_task_id
        )
        
        self.db.add(log)
        self.db.commit()
        return log
    
    def update_data_refresh_log(self, log_id: int, status: str, duration_seconds: int = None,
                              records_processed: int = None, records_updated: int = None,
                              errors_count: int = None, error_message: str = None) -> DataRefreshLog:
        """
        Update data refresh log with completion details
        
        Args:
            log_id: Log record ID
            status: Task status
            duration_seconds: Task duration
            records_processed: Number of records processed
            records_updated: Number of records updated
            errors_count: Number of errors
            error_message: Error message
        
        Returns:
            Updated DataRefreshLog record
        """
        log = self.db.query(DataRefreshLog).filter(DataRefreshLog.id == log_id).first()
        if log:
            log.status = status
            log.completed_at = datetime.utcnow()
            log.duration_seconds = duration_seconds
            log.records_processed = records_processed
            log.records_updated = records_updated
            log.errors_count = errors_count
            log.error_message = error_message
            
            self.db.commit()
        
        return log
    
    def save_cache_metric(self, cache_key_pattern: str, hits: int, misses: int, 
                         hit_rate: float, avg_response_time_ms: float = None,
                         total_size_bytes: int = None, entries_count: int = None) -> CacheMetric:
        """
        Save cache metric to database
        
        Args:
            cache_key_pattern: Cache key pattern
            hits: Number of cache hits
            misses: Number of cache misses
            hit_rate: Cache hit rate
            avg_response_time_ms: Average response time
            total_size_bytes: Total cache size
            entries_count: Number of cache entries
        
        Returns:
            Saved CacheMetric record
        """
        try:
            # Check if record exists
            existing = self.db.query(CacheMetric).filter(
                CacheMetric.cache_key_pattern == cache_key_pattern
            ).first()
            
            if existing:
                # Update existing record
                existing.hits = hits
                existing.misses = misses
                existing.hit_rate = Decimal(str(hit_rate))
                existing.avg_response_time_ms = Decimal(str(avg_response_time_ms)) if avg_response_time_ms else None
                existing.total_size_bytes = total_size_bytes
                existing.entries_count = entries_count
                existing.last_accessed_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
                
                record = existing
            else:
                # Create new record
                record = CacheMetric(
                    cache_key_pattern=cache_key_pattern,
                    hits=hits,
                    misses=misses,
                    hit_rate=Decimal(str(hit_rate)),
                    avg_response_time_ms=Decimal(str(avg_response_time_ms)) if avg_response_time_ms else None,
                    total_size_bytes=total_size_bytes,
                    entries_count=entries_count,
                    last_accessed_at=datetime.utcnow()
                )
                
                self.db.add(record)
            
            self.db.commit()
            return record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving cache metric: {e}")
            raise
    
    def get_recent_data_refresh_logs(self, limit: int = 50) -> List[DataRefreshLog]:
        """
        Get recent data refresh logs
        
        Args:
            limit: Number of logs to return
        
        Returns:
            List of recent DataRefreshLog records
        """
        return self.db.query(DataRefreshLog).order_by(
            desc(DataRefreshLog.started_at)
        ).limit(limit).all()
    
    def get_cache_metrics_summary(self) -> Dict[str, Any]:
        """
        Get cache metrics summary
        
        Returns:
            Dictionary with cache metrics summary
        """
        try:
            # Get overall cache statistics
            total_hits = self.db.query(func.sum(CacheMetric.hits)).scalar() or 0
            total_misses = self.db.query(func.sum(CacheMetric.misses)).scalar() or 0
            total_requests = total_hits + total_misses
            overall_hit_rate = total_hits / total_requests if total_requests > 0 else 0
            
            # Get average response time
            avg_response_time = self.db.query(func.avg(CacheMetric.avg_response_time_ms)).scalar()
            
            # Get total cache size
            total_size = self.db.query(func.sum(CacheMetric.total_size_bytes)).scalar() or 0
            
            # Get total entries
            total_entries = self.db.query(func.sum(CacheMetric.entries_count)).scalar() or 0
            
            return {
                'total_hits': total_hits,
                'total_misses': total_misses,
                'total_requests': total_requests,
                'overall_hit_rate': float(overall_hit_rate),
                'avg_response_time_ms': float(avg_response_time) if avg_response_time else None,
                'total_size_bytes': total_size,
                'total_entries': total_entries
            }
            
        except Exception as e:
            logger.error(f"Error getting cache metrics summary: {e}")
            return {}
    
    def cleanup_old_records(self, days_to_keep: int = 90) -> int:
        """
        Clean up old records from database
        
        Args:
            days_to_keep: Number of days to keep records
        
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # Delete old salary benchmarks
            salary_deleted = self.db.query(SalaryBenchmark).filter(
                SalaryBenchmark.created_at < cutoff_date
            ).delete()
            
            # Delete old market data
            market_deleted = self.db.query(MarketData).filter(
                MarketData.created_at < cutoff_date
            ).delete()
            
            # Delete old confidence scores
            confidence_deleted = self.db.query(ConfidenceScore).filter(
                ConfidenceScore.created_at < cutoff_date
            ).delete()
            
            # Delete old data refresh logs (keep more recent ones)
            logs_cutoff = datetime.utcnow() - timedelta(days=30)
            logs_deleted = self.db.query(DataRefreshLog).filter(
                DataRefreshLog.created_at < logs_cutoff
            ).delete()
            
            self.db.commit()
            
            total_deleted = salary_deleted + market_deleted + confidence_deleted + logs_deleted
            logger.info(f"Cleaned up {total_deleted} old records from database")
            return total_deleted
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error cleaning up old records: {e}")
            raise 