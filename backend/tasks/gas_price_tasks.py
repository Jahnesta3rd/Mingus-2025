#!/usr/bin/env python3
"""
Mingus Gas Price Celery Tasks

Background tasks for updating gas prices daily and managing gas price data.
Compatible with the existing Celery setup in the Mingus application.

Features:
- Daily gas price updates
- Error handling and retry logic
- Integration with existing Celery configuration
- Comprehensive logging
- Health monitoring
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add backend modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Celery imports
from celery import Celery
from celery.exceptions import Retry
from celery.utils.log import get_task_logger

# Import our gas price service
from services.gas_price_service import GasPriceService

# Configure logging
logger = logging.getLogger(__name__)
celery_logger = get_task_logger(__name__)

# Initialize Celery app
def make_celery(app=None):
    """Create and configure Celery app"""
    celery = Celery(
        app.import_name if app else 'mingus_gas_price_tasks',
        broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
        backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
        include=['backend.tasks.gas_price_tasks']
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,  # 5 minutes
        task_soft_time_limit=240,  # 4 minutes
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        worker_disable_rate_limits=False,
        task_compression='gzip',
        result_compression='gzip',
        task_routes={
            'backend.tasks.gas_price_tasks.*': {'queue': 'gas_price_queue'},
        },
        task_default_queue='gas_price_queue',
        task_default_exchange='gas_price_exchange',
        task_default_exchange_type='direct',
        task_default_routing_key='gas_price_task',
    )
    
    return celery

# Create Celery app
celery_app = make_celery()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def update_daily_gas_prices(self, force_update: bool = False):
    """
    Daily task to update gas prices for all MSAs.
    
    Args:
        force_update: If True, force update even if recently updated
        
    Returns:
        Dict containing update results and statistics
    """
    task_id = self.request.id
    celery_logger.info(f"Starting daily gas price update task {task_id}")
    
    try:
        # Initialize gas price service
        gas_service = GasPriceService()
        
        # Check if update is needed (unless forced)
        if not force_update:
            last_update = _get_last_update_time()
            if last_update and last_update > datetime.utcnow() - timedelta(hours=6):
                celery_logger.info("Gas prices updated recently, skipping update")
                return {
                    'success': True,
                    'skipped': True,
                    'reason': 'Recently updated',
                    'last_update': last_update.isoformat(),
                    'task_id': task_id
                }
        
        # Update gas prices
        celery_logger.info("Updating gas prices for all MSAs")
        update_results = gas_service.update_all_gas_prices()
        
        # Add task metadata
        update_results.update({
            'task_id': task_id,
            'task_start_time': datetime.utcnow().isoformat(),
            'force_update': force_update
        })
        
        # Log results
        if update_results['success']:
            celery_logger.info(f"Gas price update completed successfully: {update_results['total_updated']} MSAs updated")
        else:
            celery_logger.error(f"Gas price update failed: {update_results.get('error', 'Unknown error')}")
        
        return update_results
        
    except Exception as exc:
        celery_logger.error(f"Gas price update task failed: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            celery_logger.info(f"Retrying gas price update task (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))  # Exponential backoff
        
        # Final failure
        return {
            'success': False,
            'error': str(exc),
            'task_id': task_id,
            'retries_exhausted': True,
            'task_start_time': datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def update_specific_msa_price(self, msa_name: str, price: float, data_source: str = 'Manual'):
    """
    Update gas price for a specific MSA.
    
    Args:
        msa_name: Name of the MSA to update
        price: New gas price
        data_source: Source of the price data
        
    Returns:
        Dict containing update results
    """
    task_id = self.request.id
    celery_logger.info(f"Updating gas price for MSA {msa_name} to ${price}")
    
    try:
        from models.database import db
        from models.vehicle_models import MSAGasPrice
        from decimal import Decimal
        
        # Get existing record
        existing_price = MSAGasPrice.query.filter_by(msa_name=msa_name).first()
        
        if existing_price:
            # Update existing record
            existing_price.previous_price = existing_price.current_price
            existing_price.current_price = Decimal(str(price))
            existing_price.data_source = data_source
            existing_price.confidence_score = 0.9  # Manual updates have high confidence
            existing_price.calculate_price_change()
        else:
            # Create new record
            new_price = MSAGasPrice(
                msa_name=msa_name,
                current_price=Decimal(str(price)),
                data_source=data_source,
                confidence_score=0.9
            )
            db.session.add(new_price)
        
        db.session.commit()
        
        celery_logger.info(f"Successfully updated gas price for MSA {msa_name}")
        
        return {
            'success': True,
            'msa_name': msa_name,
            'new_price': price,
            'data_source': data_source,
            'task_id': task_id,
            'updated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        celery_logger.error(f"Failed to update gas price for MSA {msa_name}: {exc}")
        
        if self.request.retries < self.max_retries:
            celery_logger.info(f"Retrying MSA price update for {msa_name}")
            raise self.retry(countdown=30)
        
        return {
            'success': False,
            'msa_name': msa_name,
            'error': str(exc),
            'task_id': task_id,
            'retries_exhausted': True
        }

@celery_app.task(bind=True)
def cleanup_old_gas_price_data(self, days_to_keep: int = 30):
    """
    Clean up old gas price data to prevent database bloat.
    
    Args:
        days_to_keep: Number of days of data to keep
        
    Returns:
        Dict containing cleanup results
    """
    task_id = self.request.id
    celery_logger.info(f"Starting gas price data cleanup (keeping {days_to_keep} days)")
    
    try:
        from models.database import db
        from models.vehicle_models import MSAGasPrice
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Count records to be deleted
        old_records = MSAGasPrice.query.filter(
            MSAGasPrice.last_updated < cutoff_date
        ).count()
        
        if old_records == 0:
            celery_logger.info("No old gas price data found to clean up")
            return {
                'success': True,
                'records_deleted': 0,
                'cutoff_date': cutoff_date.isoformat(),
                'task_id': task_id
            }
        
        # Delete old records
        MSAGasPrice.query.filter(
            MSAGasPrice.last_updated < cutoff_date
        ).delete()
        
        db.session.commit()
        
        celery_logger.info(f"Cleaned up {old_records} old gas price records")
        
        return {
            'success': True,
            'records_deleted': old_records,
            'cutoff_date': cutoff_date.isoformat(),
            'task_id': task_id
        }
        
    except Exception as exc:
        celery_logger.error(f"Gas price data cleanup failed: {exc}")
        return {
            'success': False,
            'error': str(exc),
            'task_id': task_id
        }

@celery_app.task(bind=True)
def health_check_gas_price_service(self):
    """
    Health check task for the gas price service.
    
    Returns:
        Dict containing health status information
    """
    task_id = self.request.id
    celery_logger.info("Running gas price service health check")
    
    try:
        gas_service = GasPriceService()
        health_status = gas_service.get_service_status()
        
        # Add task metadata
        health_status.update({
            'task_id': task_id,
            'check_time': datetime.utcnow().isoformat(),
            'task_type': 'health_check'
        })
        
        # Determine overall health
        if health_status['service_status'] == 'healthy':
            celery_logger.info("Gas price service health check passed")
        else:
            celery_logger.warning(f"Gas price service health check failed: {health_status.get('error', 'Unknown error')}")
        
        return health_status
        
    except Exception as exc:
        celery_logger.error(f"Gas price service health check failed: {exc}")
        return {
            'service_status': 'error',
            'error': str(exc),
            'task_id': task_id,
            'check_time': datetime.utcnow().isoformat(),
            'task_type': 'health_check'
        }

@celery_app.task(bind=True)
def get_gas_price_by_zipcode_task(self, zipcode: str):
    """
    Task to get gas price for a specific zipcode.
    
    Args:
        zipcode: 5-digit US zipcode string
        
    Returns:
        Dict containing gas price information
    """
    task_id = self.request.id
    celery_logger.info(f"Getting gas price for zipcode {zipcode}")
    
    try:
        gas_service = GasPriceService()
        result = gas_service.get_gas_price_by_zipcode(zipcode)
        
        # Add task metadata
        result.update({
            'task_id': task_id,
            'requested_at': datetime.utcnow().isoformat()
        })
        
        celery_logger.info(f"Retrieved gas price for zipcode {zipcode}: ${result.get('gas_price', 'N/A')}")
        
        return result
        
    except Exception as exc:
        celery_logger.error(f"Failed to get gas price for zipcode {zipcode}: {exc}")
        return {
            'success': False,
            'zipcode': zipcode,
            'error': str(exc),
            'task_id': task_id,
            'requested_at': datetime.utcnow().isoformat()
        }

def _get_last_update_time() -> Optional[datetime]:
    """Get the time of the last gas price update"""
    try:
        from models.database import db
        from models.vehicle_models import MSAGasPrice
        
        latest_update = db.session.query(
            db.func.max(MSAGasPrice.last_updated)
        ).scalar()
        
        return latest_update
        
    except Exception as e:
        celery_logger.error(f"Error getting last update time: {e}")
        return None

# Periodic task configuration (to be set up in Celery Beat)
@celery_app.task
def schedule_daily_gas_price_updates():
    """
    Schedule daily gas price updates.
    This should be called by Celery Beat scheduler.
    """
    celery_logger.info("Scheduling daily gas price update")
    
    # Schedule the update task
    result = update_daily_gas_prices.delay()
    
    return {
        'success': True,
        'scheduled_task_id': result.id,
        'scheduled_at': datetime.utcnow().isoformat()
    }

# Error handling and monitoring
@celery_app.task(bind=True)
def monitor_gas_price_tasks(self):
    """
    Monitor gas price tasks and send alerts if needed.
    """
    task_id = self.request.id
    celery_logger.info("Monitoring gas price tasks")
    
    try:
        # Check for failed tasks
        # In a real implementation, you would query Celery's result backend
        # to check for failed tasks and send alerts
        
        return {
            'success': True,
            'monitoring_active': True,
            'task_id': task_id,
            'checked_at': datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        celery_logger.error(f"Gas price task monitoring failed: {exc}")
        return {
            'success': False,
            'error': str(exc),
            'task_id': task_id
        }
