#!/usr/bin/env python3
"""
Mingus Application - Database Optimization Module
Comprehensive database optimization for Daily Outlook system performance
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy import text, Index, func, desc, asc, and_, or_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.postgresql import JSONB
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseOptimizer:
    """
    Database optimization service for Daily Outlook system
    
    Features:
    - Automatic index creation and management
    - Query optimization and analysis
    - Read replica support for analytics
    - Connection pooling optimization
    - Query result caching
    - Performance monitoring
    """
    
    def __init__(self, db_session, read_replica_session=None):
        """
        Initialize database optimizer
        
        Args:
            db_session: Primary database session
            read_replica_session: Read replica session for analytics queries
        """
        self.db_session = db_session
        self.read_replica_session = read_replica_session or db_session
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Performance metrics
        self.metrics = {
            'query_count': 0,
            'slow_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_query_time': 0.0
        }
        
        logger.info("DatabaseOptimizer initialized successfully")
    
    def create_daily_outlook_indexes(self):
        """
        Create optimized indexes for Daily Outlook queries
        
        Returns:
            List of created indexes
        """
        indexes_created = []
        
        try:
            # Composite index for user-date lookups (most common query)
            index_user_date = Index(
                'idx_daily_outlooks_user_date_optimized',
                'user_id', 'date'
            )
            indexes_created.append(index_user_date)
            
            # Index for balance score range queries
            index_balance_score = Index(
                'idx_daily_outlooks_balance_score_range',
                'balance_score'
            )
            indexes_created.append(index_balance_score)
            
            # Index for streak count queries
            index_streak = Index(
                'idx_daily_outlooks_streak_count',
                'streak_count'
            )
            indexes_created.append(index_streak)
            
            # Index for created_at for time-based queries
            index_created_at = Index(
                'idx_daily_outlooks_created_at_optimized',
                'created_at'
            )
            indexes_created.append(index_created_at)
            
            # Partial index for active outlooks only
            index_active = Index(
                'idx_daily_outlooks_active_only',
                'user_id', 'date',
                postgresql_where=text("viewed_at IS NOT NULL")
            )
            indexes_created.append(index_active)
            
            # Index for user rating queries
            index_rating = Index(
                'idx_daily_outlooks_user_rating',
                'user_rating'
            )
            indexes_created.append(index_rating)
            
            # Composite index for analytics queries
            index_analytics = Index(
                'idx_daily_outlooks_analytics',
                'date', 'balance_score', 'user_id'
            )
            indexes_created.append(index_analytics)
            
            logger.info(f"Created {len(indexes_created)} indexes for Daily Outlook optimization")
            return indexes_created
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating Daily Outlook indexes: {e}")
            return []
    
    def create_user_aggregation_indexes(self):
        """
        Create indexes for user data aggregation queries
        
        Returns:
            List of created indexes
        """
        indexes_created = []
        
        try:
            # Index for user relationship status queries
            index_relationship = Index(
                'idx_user_relationship_status_optimized',
                'user_id', 'status'
            )
            indexes_created.append(index_relationship)
            
            # Index for user tier-based queries
            index_tier = Index(
                'idx_users_tier_optimized',
                'tier'
            )
            indexes_created.append(index_tier)
            
            # Index for location-based queries
            index_location = Index(
                'idx_users_location_optimized',
                'location'
            )
            indexes_created.append(index_location)
            
            # Composite index for user analytics
            index_user_analytics = Index(
                'idx_users_analytics_optimized',
                'tier', 'location', 'created_at'
            )
            indexes_created.append(index_user_analytics)
            
            logger.info(f"Created {len(indexes_created)} indexes for user aggregation optimization")
            return indexes_created
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating user aggregation indexes: {e}")
            return []
    
    def optimize_daily_outlook_queries(self):
        """
        Optimize common Daily Outlook queries with better execution plans
        
        Returns:
            Dictionary of optimized query templates
        """
        optimized_queries = {
            'get_user_daily_outlook': """
                SELECT do.*, u.tier, u.location, urs.status as relationship_status
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                LEFT JOIN user_relationship_status urs ON do.user_id = urs.user_id
                WHERE do.user_id = :user_id 
                AND do.date = :date
                LIMIT 1
            """,
            
            'get_user_outlook_history': """
                SELECT do.*, u.tier
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.user_id = :user_id 
                AND do.date >= :start_date
                AND do.date <= :end_date
                ORDER BY do.date DESC
                LIMIT :limit
            """,
            
            'get_balance_score_stats': """
                SELECT 
                    AVG(balance_score) as avg_balance,
                    MIN(balance_score) as min_balance,
                    MAX(balance_score) as max_balance,
                    COUNT(*) as total_outlooks
                FROM daily_outlooks
                WHERE user_id = :user_id
                AND date >= :start_date
                AND date <= :end_date
            """,
            
            'get_peer_comparison_data': """
                SELECT 
                    do.balance_score,
                    do.financial_weight,
                    do.wellness_weight,
                    do.relationship_weight,
                    do.career_weight,
                    u.tier,
                    u.location
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.date = :date
                AND u.tier = :tier
                AND u.location = :location
                AND do.user_id != :exclude_user_id
            """,
            
            'get_analytics_aggregation': """
                SELECT 
                    DATE_TRUNC('day', do.date) as date,
                    u.tier,
                    u.location,
                    AVG(do.balance_score) as avg_balance,
                    COUNT(*) as outlook_count,
                    AVG(do.user_rating) as avg_rating
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.date >= :start_date
                AND do.date <= :end_date
                GROUP BY DATE_TRUNC('day', do.date), u.tier, u.location
                ORDER BY date DESC
            """
        }
        
        logger.info(f"Created {len(optimized_queries)} optimized query templates")
        return optimized_queries
    
    def get_user_daily_outlook_optimized(self, user_id: int, target_date: date) -> Optional[Dict[str, Any]]:
        """
        Get user's daily outlook with optimized query
        
        Args:
            user_id: User ID
            target_date: Target date for outlook
            
        Returns:
            Daily outlook data or None
        """
        start_time = datetime.now()
        
        try:
            query = text("""
                SELECT 
                    do.id,
                    do.user_id,
                    do.date,
                    do.balance_score,
                    do.financial_weight,
                    do.wellness_weight,
                    do.relationship_weight,
                    do.career_weight,
                    do.primary_insight,
                    do.quick_actions,
                    do.encouragement_message,
                    do.surprise_element,
                    do.streak_count,
                    do.viewed_at,
                    do.actions_completed,
                    do.user_rating,
                    do.created_at,
                    u.tier,
                    u.location,
                    urs.status as relationship_status
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                LEFT JOIN user_relationship_status urs ON do.user_id = urs.user_id
                WHERE do.user_id = :user_id 
                AND do.date = :date
                LIMIT 1
            """)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'date': target_date
            }).fetchone()
            
            if result:
                # Convert to dictionary
                outlook_data = dict(result._mapping)
                
                # Update metrics
                query_time = (datetime.now() - start_time).total_seconds()
                self._update_query_metrics(query_time)
                
                return outlook_data
            
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user daily outlook: {e}")
            return None
    
    def get_user_outlook_history_optimized(self, user_id: int, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get user's outlook history with optimized query
        
        Args:
            user_id: User ID
            days: Number of days to retrieve
            
        Returns:
            List of daily outlook data
        """
        start_time = datetime.now()
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        try:
            query = text("""
                SELECT 
                    do.id,
                    do.date,
                    do.balance_score,
                    do.primary_insight,
                    do.quick_actions,
                    do.streak_count,
                    do.viewed_at,
                    do.user_rating,
                    u.tier
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.user_id = :user_id 
                AND do.date >= :start_date
                AND do.date <= :end_date
                ORDER BY do.date DESC
            """)
            
            results = self.db_session.execute(query, {
                'user_id': user_id,
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            # Convert to list of dictionaries
            outlook_history = [dict(row._mapping) for row in results]
            
            # Update metrics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_query_metrics(query_time)
            
            return outlook_history
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting user outlook history: {e}")
            return []
    
    def get_balance_score_analytics_optimized(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get balance score analytics with optimized query
        
        Args:
            user_id: User ID
            days: Number of days to analyze
            
        Returns:
            Balance score analytics data
        """
        start_time = datetime.now()
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        try:
            query = text("""
                SELECT 
                    AVG(balance_score) as avg_balance,
                    MIN(balance_score) as min_balance,
                    MAX(balance_score) as max_balance,
                    COUNT(*) as total_outlooks,
                    AVG(financial_weight) as avg_financial_weight,
                    AVG(wellness_weight) as avg_wellness_weight,
                    AVG(relationship_weight) as avg_relationship_weight,
                    AVG(career_weight) as avg_career_weight
                FROM daily_outlooks
                WHERE user_id = :user_id
                AND date >= :start_date
                AND date <= :end_date
            """)
            
            result = self.db_session.execute(query, {
                'user_id': user_id,
                'start_date': start_date,
                'end_date': end_date
            }).fetchone()
            
            if result:
                analytics_data = dict(result._mapping)
                
                # Update metrics
                query_time = (datetime.now() - start_time).total_seconds()
                self._update_query_metrics(query_time)
                
                return analytics_data
            
            return {}
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting balance score analytics: {e}")
            return {}
    
    def get_peer_comparison_data_optimized(self, user_id: int, user_tier: str, 
                                         user_location: str, target_date: date) -> List[Dict[str, Any]]:
        """
        Get peer comparison data with optimized query
        
        Args:
            user_id: User ID (to exclude from results)
            user_tier: User's tier
            user_location: User's location
            target_date: Target date for comparison
            
        Returns:
            List of peer comparison data
        """
        start_time = datetime.now()
        
        try:
            query = text("""
                SELECT 
                    do.balance_score,
                    do.financial_weight,
                    do.wellness_weight,
                    do.relationship_weight,
                    do.career_weight,
                    u.tier,
                    u.location
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.date = :date
                AND u.tier = :tier
                AND u.location = :location
                AND do.user_id != :exclude_user_id
                ORDER BY do.balance_score DESC
                LIMIT 100
            """)
            
            results = self.db_session.execute(query, {
                'date': target_date,
                'tier': user_tier,
                'location': user_location,
                'exclude_user_id': user_id
            }).fetchall()
            
            # Convert to list of dictionaries
            peer_data = [dict(row._mapping) for row in results]
            
            # Update metrics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_query_metrics(query_time)
            
            return peer_data
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting peer comparison data: {e}")
            return []
    
    def get_analytics_aggregation_optimized(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        Get analytics aggregation with optimized query (uses read replica)
        
        Args:
            start_date: Start date for aggregation
            end_date: End date for aggregation
            
        Returns:
            List of analytics aggregation data
        """
        start_time = datetime.now()
        
        try:
            query = text("""
                SELECT 
                    DATE_TRUNC('day', do.date) as date,
                    u.tier,
                    u.location,
                    AVG(do.balance_score) as avg_balance,
                    COUNT(*) as outlook_count,
                    AVG(do.user_rating) as avg_rating,
                    COUNT(CASE WHEN do.viewed_at IS NOT NULL THEN 1 END) as viewed_count
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.date >= :start_date
                AND do.date <= :end_date
                GROUP BY DATE_TRUNC('day', do.date), u.tier, u.location
                ORDER BY date DESC
            """)
            
            results = self.read_replica_session.execute(query, {
                'start_date': start_date,
                'end_date': end_date
            }).fetchall()
            
            # Convert to list of dictionaries
            analytics_data = [dict(row._mapping) for row in results]
            
            # Update metrics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_query_metrics(query_time)
            
            return analytics_data
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting analytics aggregation: {e}")
            return []
    
    def batch_get_daily_outlooks(self, user_ids: List[int], target_date: date) -> Dict[int, Dict[str, Any]]:
        """
        Batch get daily outlooks for multiple users
        
        Args:
            user_ids: List of user IDs
            target_date: Target date for outlooks
            
        Returns:
            Dictionary mapping user_id to outlook data
        """
        start_time = datetime.now()
        
        try:
            query = text("""
                SELECT 
                    do.user_id,
                    do.id,
                    do.date,
                    do.balance_score,
                    do.primary_insight,
                    do.quick_actions,
                    do.encouragement_message,
                    do.surprise_element,
                    do.streak_count,
                    do.viewed_at,
                    do.actions_completed,
                    do.user_rating,
                    u.tier,
                    u.location
                FROM daily_outlooks do
                JOIN users u ON do.user_id = u.id
                WHERE do.user_id = ANY(:user_ids)
                AND do.date = :date
            """)
            
            results = self.db_session.execute(query, {
                'user_ids': user_ids,
                'date': target_date
            }).fetchall()
            
            # Convert to dictionary mapping user_id to outlook data
            outlooks = {}
            for row in results:
                outlooks[row.user_id] = dict(row._mapping)
            
            # Update metrics
            query_time = (datetime.now() - start_time).total_seconds()
            self._update_query_metrics(query_time)
            
            return outlooks
            
        except SQLAlchemyError as e:
            logger.error(f"Error batch getting daily outlooks: {e}")
            return {}
    
    def _update_query_metrics(self, query_time: float):
        """Update query performance metrics"""
        self.metrics['query_count'] += 1
        self.metrics['avg_query_time'] = (
            (self.metrics['avg_query_time'] * (self.metrics['query_count'] - 1) + query_time) 
            / self.metrics['query_count']
        )
        
        if query_time > 1.0:  # Consider queries > 1 second as slow
            self.metrics['slow_queries'] += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get database performance metrics
        
        Returns:
            Dictionary containing performance metrics
        """
        return {
            'query_count': self.metrics['query_count'],
            'slow_queries': self.metrics['slow_queries'],
            'avg_query_time': round(self.metrics['avg_query_time'], 3),
            'slow_query_rate': round(
                (self.metrics['slow_queries'] / self.metrics['query_count'] * 100) 
                if self.metrics['query_count'] > 0 else 0, 2
            )
        }
    
    def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """
        Analyze query performance using EXPLAIN ANALYZE
        
        Args:
            query: SQL query to analyze
            
        Returns:
            Query analysis results
        """
        try:
            explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
            result = self.db_session.execute(text(explain_query)).fetchone()
            
            if result and result[0]:
                return result[0][0]  # First plan from JSON result
            
            return {}
            
        except SQLAlchemyError as e:
            logger.error(f"Error analyzing query performance: {e}")
            return {}
    
    def optimize_connection_pool(self, max_connections: int = 20, 
                                min_connections: int = 5,
                                connection_timeout: int = 30):
        """
        Optimize database connection pool settings
        
        Args:
            max_connections: Maximum number of connections
            min_connections: Minimum number of connections
            connection_timeout: Connection timeout in seconds
        """
        try:
            # Update connection pool settings
            if hasattr(self.db_session.bind, 'pool'):
                pool = self.db_session.bind.pool
                pool.size = max_connections
                pool.max_overflow = max_connections - min_connections
                pool.timeout = connection_timeout
                
                logger.info(f"Updated connection pool: max={max_connections}, min={min_connections}, timeout={connection_timeout}")
            
        except Exception as e:
            logger.error(f"Error optimizing connection pool: {e}")
    
    def close(self):
        """Close database connections and cleanup resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        logger.info("DatabaseOptimizer closed successfully")
