"""
Email Verification Celery Tasks for MINGUS Flask Application
Handles asynchronous email verification operations with proper error handling and retries
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from celery import Celery, current_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError

from ..database import get_db_session
from ..models.email_verification import EmailVerification
from ..models.user import User
from ..services.email_verification_service import EmailVerificationService
from ..services.resend_email_service import ResendEmailService

# Configure logging
logger = get_task_logger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Celery app
celery_app = Celery('email_verification_tasks')
celery_app.config_from_object('celeryconfig')

# Initialize services
email_verification_service = EmailVerificationService()
email_service = ResendEmailService()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_verification_email(self, user_id: int, email: str, verification_type: str = 'signup',
                           old_email: str = None) -> Dict[str, Any]:
    """
    Send verification email to user
    
    Args:
        user_id: User ID
        email: Email address to verify
        verification_type: Type of verification
        old_email: Previous email (for email change)
        
    Returns:
        Dictionary with operation result
    """
    try:
        logger.info(f"Sending verification email to user {user_id} at {email}")
        
        # Create verification record
        verification, token = email_verification_service.create_verification(
            user_id=user_id,
            email=email,
            verification_type=verification_type,
            old_email=old_email
        )
        
        # Get user details for personalization
        with get_db_session() as db:
            user = db.query(User).filter(User.id == user_id).first()
            user_name = user.full_name if user else "there"
        
        # Generate verification URL
        base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        verification_url = f"{base_url}/verify-email?token={token}&type={verification_type}"
        
        # Send email based on verification type
        if verification_type == 'email_change':
            success = email_service.send_email_change_verification(
                email, user_name, verification_url
            )
        else:
            success = email_service.send_verification_email(
                email, user_name, verification_url
            )
        
        if success:
            logger.info(f"Verification email sent successfully to user {user_id}")
            return {
                'success': True,
                'message': 'Verification email sent successfully',
                'user_id': user_id,
                'email': email,
                'verification_type': verification_type
            }
        else:
            raise Exception("Failed to send verification email")
            
    except Exception as exc:
        logger.error(f"Error sending verification email to user {user_id}: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying verification email for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for verification email to user {user_id}")
            
            # Log failure for monitoring
            try:
                with get_db_session() as db:
                    from ..models.audit import AuditLog
                    audit_log = AuditLog(
                        user_id=user_id,
                        action='verification_email_failed',
                        details={
                            'email': email,
                            'verification_type': verification_type,
                            'error': str(exc),
                            'retry_count': self.request.retries
                        },
                        success=False,
                        timestamp=datetime.utcnow()
                    )
                    db.add(audit_log)
                    db.commit()
            except Exception as audit_error:
                logger.error(f"Failed to log audit event: {audit_error}")
            
            return {
                'success': False,
                'message': 'Failed to send verification email after max retries',
                'error': str(exc),
                'user_id': user_id,
                'email': email
            }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_verification_reminder(self, user_id: int, reminder_type: str = 'first') -> Dict[str, Any]:
    """
    Send verification reminder email
    
    Args:
        user_id: User ID
        reminder_type: Type of reminder (first, second, final)
        
    Returns:
        Dictionary with operation result
    """
    try:
        logger.info(f"Sending {reminder_type} verification reminder to user {user_id}")
        
        with get_db_session() as db:
            # Get user and verification details
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise Exception("User not found")
            
            verification = db.query(EmailVerification).filter(
                EmailVerification.user_id == user_id
            ).first()
            
            if not verification or verification.is_verified:
                logger.info(f"User {user_id} already verified or no verification record")
                return {
                    'success': True,
                    'message': 'User already verified',
                    'user_id': user_id,
                    'reminder_type': reminder_type
                }
            
            # Check if reminder should be sent based on reminder type
            days_since_creation = (datetime.utcnow() - verification.created_at).days
            
            reminder_schedule = {
                'first': 3,    # 3 days
                'second': 7,   # 7 days
                'final': 14    # 14 days
            }
            
            if days_since_creation < reminder_schedule.get(reminder_type, 0):
                logger.info(f"Too early to send {reminder_type} reminder for user {user_id}")
                return {
                    'success': True,
                    'message': 'Too early for reminder',
                    'user_id': user_id,
                    'reminder_type': reminder_type
                }
            
            # Generate new verification token for reminder
            new_token = verification.generate_token()
            verification.verification_token_hash = verification.hash_token(new_token)
            verification.expires_at = datetime.utcnow() + timedelta(hours=24)
            verification.increment_resend_count()
            
            db.commit()
            
            # Generate verification URL
            base_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            verification_url = f"{base_url}/verify-email?token={new_token}&type={verification.verification_type}"
            
            # Send reminder email
            success = email_service.send_verification_reminder(
                user.email, user.full_name, verification_url, reminder_type
            )
            
            if success:
                logger.info(f"Verification reminder sent successfully to user {user_id}")
                return {
                    'success': True,
                    'message': f'{reminder_type.title()} reminder sent successfully',
                    'user_id': user_id,
                    'reminder_type': reminder_type
                }
            else:
                raise Exception("Failed to send reminder email")
                
    except Exception as exc:
        logger.error(f"Error sending verification reminder to user {user_id}: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying reminder email for user {user_id} (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        else:
            logger.error(f"Max retries exceeded for reminder email to user {user_id}")
            return {
                'success': False,
                'message': 'Failed to send reminder email after max retries',
                'error': str(exc),
                'user_id': user_id,
                'reminder_type': reminder_type
            }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def cleanup_expired_verifications(self) -> Dict[str, Any]:
    """
    Clean up expired verification records
    
    Returns:
        Dictionary with cleanup results
    """
    try:
        logger.info("Starting cleanup of expired verification records")
        
        with get_db_session() as db:
            # Find expired verifications
            expired_verifications = db.query(EmailVerification).filter(
                EmailVerification.expires_at < datetime.utcnow(),
                EmailVerification.verified_at.is_(None)
            ).all()
            
            expired_count = len(expired_verifications)
            logger.info(f"Found {expired_count} expired verification records")
            
            if expired_count > 0:
                # Delete expired records
                for verification in expired_verifications:
                    db.delete(verification)
                
                db.commit()
                logger.info(f"Successfully cleaned up {expired_count} expired verification records")
            
            return {
                'success': True,
                'message': f'Cleanup completed successfully',
                'records_cleaned': expired_count
            }
            
    except Exception as exc:
        logger.error(f"Error during verification cleanup: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying verification cleanup (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
        else:
            logger.error("Max retries exceeded for verification cleanup")
            return {
                'success': False,
                'message': 'Failed to cleanup expired verifications after max retries',
                'error': str(exc)
            }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def send_bulk_verification_reminders(self) -> Dict[str, Any]:
    """
    Send bulk verification reminders to users who haven't verified their email
    
    Returns:
        Dictionary with operation results
    """
    try:
        logger.info("Starting bulk verification reminder process")
        
        with get_db_session() as db:
            # Find users who need reminders
            current_time = datetime.utcnow()
            
            # Users who created account 3+ days ago and haven't verified
            first_reminder_users = db.query(User).join(EmailVerification).filter(
                User.email_verified == False,
                EmailVerification.verified_at.is_(None),
                EmailVerification.created_at <= current_time - timedelta(days=3),
                EmailVerification.created_at > current_time - timedelta(days=4)
            ).all()
            
            # Users who created account 7+ days ago and haven't verified
            second_reminder_users = db.query(User).join(EmailVerification).filter(
                User.email_verified == False,
                EmailVerification.verified_at.is_(None),
                EmailVerification.created_at <= current_time - timedelta(days=7),
                EmailVerification.created_at > current_time - timedelta(days=8)
            ).all()
            
            # Users who created account 14+ days ago and haven't verified
            final_reminder_users = db.query(User).join(EmailVerification).filter(
                User.email_verified == False,
                EmailVerification.verified_at.is_(None),
                EmailVerification.created_at <= current_time - timedelta(days=14),
                EmailVerification.created_at > current_time - timedelta(days=15)
            ).all()
            
            total_reminders = len(first_reminder_users) + len(second_reminder_users) + len(final_reminder_users)
            logger.info(f"Found {total_reminders} users needing reminders")
            
            # Send reminders
            success_count = 0
            error_count = 0
            
            # Send first reminders
            for user in first_reminder_users:
                try:
                    send_verification_reminder.delay(user.id, 'first')
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to queue first reminder for user {user.id}: {e}")
                    error_count += 1
            
            # Send second reminders
            for user in second_reminder_users:
                try:
                    send_verification_reminder.delay(user.id, 'second')
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to queue second reminder for user {user.id}: {e}")
                    error_count += 1
            
            # Send final reminders
            for user in final_reminder_users:
                try:
                    send_verification_reminder.delay(user.id, 'final')
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to queue final reminder for user {user.id}: {e}")
                    error_count += 1
            
            logger.info(f"Bulk reminder process completed: {success_count} queued, {error_count} errors")
            
            return {
                'success': True,
                'message': 'Bulk reminder process completed',
                'total_users': total_reminders,
                'success_count': success_count,
                'error_count': error_count
            }
            
    except Exception as exc:
        logger.error(f"Error during bulk reminder process: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying bulk reminder process (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=600 * (2 ** self.request.retries))
        else:
            logger.error("Max retries exceeded for bulk reminder process")
            return {
                'success': False,
                'message': 'Failed to process bulk reminders after max retries',
                'error': str(exc)
            }

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def process_verification_analytics(self) -> Dict[str, Any]:
    """
    Process verification analytics and metrics
    
    Returns:
        Dictionary with analytics results
    """
    try:
        logger.info("Processing verification analytics")
        
        with get_db_session() as db:
            # Get verification statistics
            total_verifications = db.query(EmailVerification).count()
            verified_count = db.query(EmailVerification).filter(
                EmailVerification.verified_at.isnot(None)
            ).count()
            pending_count = total_verifications - verified_count
            
            # Get verification rates by type
            signup_verifications = db.query(EmailVerification).filter(
                EmailVerification.verification_type == 'signup'
            ).count()
            signup_verified = db.query(EmailVerification).filter(
                EmailVerification.verification_type == 'signup',
                EmailVerification.verified_at.isnot(None)
            ).count()
            
            email_change_verifications = db.query(EmailVerification).filter(
                EmailVerification.verification_type == 'email_change'
            ).count()
            email_change_verified = db.query(EmailVerification).filter(
                EmailVerification.verification_type == 'email_change',
                EmailVerification.verified_at.isnot(None)
            ).count()
            
            # Calculate success rates
            overall_success_rate = (verified_count / total_verifications * 100) if total_verifications > 0 else 0
            signup_success_rate = (signup_verified / signup_verifications * 100) if signup_verifications > 0 else 0
            email_change_success_rate = (email_change_verified / email_change_verifications * 100) if email_change_verifications > 0 else 0
            
            analytics_data = {
                'total_verifications': total_verifications,
                'verified_count': verified_count,
                'pending_count': pending_count,
                'overall_success_rate': round(overall_success_rate, 2),
                'signup_verifications': signup_verifications,
                'signup_verified': signup_verified,
                'signup_success_rate': round(signup_success_rate, 2),
                'email_change_verifications': email_change_verifications,
                'email_change_verified': email_change_verified,
                'email_change_success_rate': round(email_change_success_rate, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Verification analytics processed: {analytics_data}")
            
            return {
                'success': True,
                'message': 'Analytics processed successfully',
                'data': analytics_data
            }
            
    except Exception as exc:
        logger.error(f"Error processing verification analytics: {exc}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying analytics processing (attempt {self.request.retries + 1})")
            raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))
        else:
            logger.error("Max retries exceeded for analytics processing")
            return {
                'success': False,
                'message': 'Failed to process analytics after max retries',
                'error': str(exc)
            }

# Task scheduling configuration
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks for email verification"""
    
    # Clean up expired verifications daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_expired_verifications.s(),
        name='cleanup-expired-verifications'
    )
    
    # Send bulk reminders daily at 10 AM
    sender.add_periodic_task(
        crontab(hour=10, minute=0),
        send_bulk_verification_reminders.s(),
        name='send-bulk-verification-reminders'
    )
    
    # Process analytics daily at 11 PM
    sender.add_periodic_task(
        crontab(hour=23, minute=0),
        process_verification_analytics.s(),
        name='process-verification-analytics'
    )

# Import crontab for scheduling
from celery.schedules import crontab
