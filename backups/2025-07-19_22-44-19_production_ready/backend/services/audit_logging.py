"""
Audit Service
Provides comprehensive audit logging for financial data access and modifications
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import request, g, current_app
from loguru import logger
from sqlalchemy.orm import Session
from backend.models.encrypted_financial_models import FinancialAuditLog

class AuditService:
    """Service for handling audit logging of financial data access"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    @property
    def sensitive_fields(self):
        return current_app.config.get('AUDIT_LOG_SENSITIVE_FIELDS', [])
    
    def log_financial_access(self, 
                           action: str, 
                           table_name: str, 
                           record_id: Optional[str] = None,
                           field_name: Optional[str] = None,
                           old_value: Any = None,
                           new_value: Any = None) -> None:
        """
        Log financial data access for audit purposes
        
        Args:
            action: CREATE, READ, UPDATE, DELETE
            table_name: Name of the table being accessed
            record_id: ID of the record being accessed
            field_name: Name of the field being accessed (if applicable)
            old_value: Previous value (for updates)
            new_value: New value (for updates)
        """
        try:
            # Create audit log entry
            audit_entry = FinancialAuditLog(
                id=str(uuid.uuid4()),
                user_id=getattr(g, 'user_id', None),
                action=action,
                table_name=table_name,
                record_id=record_id,
                field_name=field_name,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                session_id=request.cookies.get('session'),
                created_at=datetime.now()
            )
            
            # Add to database
            self.db_session.add(audit_entry)
            self.db_session.commit()
            
            # Log to file system as well
            self._log_to_file(audit_entry, old_value, new_value)
            
            logger.info(f"Audit log created: {action} on {table_name} by user {getattr(g, 'user_id', 'anonymous')}")
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")
            self.db_session.rollback()
    
    def log_financial_profile_access(self, profile_id: str, action: str) -> None:
        """Log access to financial profile"""
        self.log_financial_access(
            action=action,
            table_name='encrypted_financial_profiles',
            record_id=profile_id
        )
    
    def log_income_source_access(self, source_id: str, action: str) -> None:
        """Log access to income source"""
        self.log_financial_access(
            action=action,
            table_name='encrypted_income_sources',
            record_id=source_id
        )
    
    def log_debt_account_access(self, account_id: str, action: str) -> None:
        """Log access to debt account"""
        self.log_financial_access(
            action=action,
            table_name='encrypted_debt_accounts',
            record_id=account_id
        )
    
    def log_field_update(self, 
                        table_name: str, 
                        record_id: str, 
                        field_name: str, 
                        old_value: Any, 
                        new_value: Any) -> None:
        """Log field-level updates for sensitive data"""
        # Only log if field is sensitive
        if field_name in self.sensitive_fields:
            self.log_financial_access(
                action='UPDATE',
                table_name=table_name,
                record_id=record_id,
                field_name=field_name,
                old_value=old_value,
                new_value=new_value
            )
    
    def get_user_audit_logs(self, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get audit logs for a specific user"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            logs = self.db_session.query(FinancialAuditLog).filter(
                FinancialAuditLog.user_id == user_id,
                FinancialAuditLog.created_at >= cutoff_date
            ).order_by(FinancialAuditLog.created_at.desc()).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {str(e)}")
            return []
    
    def get_financial_audit_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get summary of financial data access for a user"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get all logs for user
            logs = self.db_session.query(FinancialAuditLog).filter(
                FinancialAuditLog.user_id == user_id,
                FinancialAuditLog.created_at >= cutoff_date
            ).all()
            
            # Calculate summary statistics
            total_accesses = len(logs)
            read_accesses = len([log for log in logs if log.action == 'READ'])
            write_accesses = len([log for log in logs if log.action in ['CREATE', 'UPDATE', 'DELETE']])
            
            # Group by table
            table_accesses = {}
            for log in logs:
                table = log.table_name
                if table not in table_accesses:
                    table_accesses[table] = {'reads': 0, 'writes': 0}
                
                if log.action == 'READ':
                    table_accesses[table]['reads'] += 1
                else:
                    table_accesses[table]['writes'] += 1
            
            # Get recent activity
            recent_activity = [
                {
                    'timestamp': log.created_at.isoformat(),
                    'action': log.action,
                    'table': log.table_name,
                    'field': log.field_name
                }
                for log in logs[:10]  # Last 10 activities
            ]
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_accesses': total_accesses,
                'read_accesses': read_accesses,
                'write_accesses': write_accesses,
                'table_accesses': table_accesses,
                'recent_activity': recent_activity
            }
            
        except Exception as e:
            logger.error(f"Failed to generate audit summary: {str(e)}")
            return {}
    
    def cleanup_old_audit_logs(self, days: int = 90) -> int:
        """Clean up audit logs older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Count logs to be deleted
            count = self.db_session.query(FinancialAuditLog).filter(
                FinancialAuditLog.created_at < cutoff_date
            ).count()
            
            # Delete old logs
            self.db_session.query(FinancialAuditLog).filter(
                FinancialAuditLog.created_at < cutoff_date
            ).delete()
            
            self.db_session.commit()
            
            logger.info(f"Cleaned up {count} old audit logs")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup audit logs: {str(e)}")
            self.db_session.rollback()
            return 0
    
    def _log_to_file(self, audit_entry: FinancialAuditLog, old_value: Any = None, new_value: Any = None) -> None:
        """Log audit entry to file system for backup"""
        try:
            log_data = {
                'audit_id': audit_entry.id,
                'timestamp': audit_entry.created_at.isoformat(),
                'user_id': audit_entry.user_id,
                'action': audit_entry.action,
                'table_name': audit_entry.table_name,
                'record_id': audit_entry.record_id,
                'field_name': audit_entry.field_name,
                'ip_address': audit_entry.ip_address,
                'user_agent': audit_entry.user_agent,
                'session_id': audit_entry.session_id,
                'request_id': getattr(g, 'request_id', None)
            }
            
            # Add values if provided (for updates)
            if old_value is not None:
                log_data['old_value'] = str(old_value)
            if new_value is not None:
                log_data['new_value'] = str(new_value)
            
            # Write to audit log file
            with open('logs/financial_audit.log', 'a') as f:
                f.write(json.dumps(log_data) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write audit log to file: {str(e)}")
    
    def export_audit_logs(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Export audit logs for a user within a date range"""
        try:
            logs = self.db_session.query(FinancialAuditLog).filter(
                FinancialAuditLog.user_id == user_id,
                FinancialAuditLog.created_at >= start_date,
                FinancialAuditLog.created_at <= end_date
            ).order_by(FinancialAuditLog.created_at.desc()).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"Failed to export audit logs: {str(e)}")
            return []
    
    def detect_suspicious_activity(self, user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect potentially suspicious activity patterns"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Get recent logs for user
            logs = self.db_session.query(FinancialAuditLog).filter(
                FinancialAuditLog.user_id == user_id,
                FinancialAuditLog.created_at >= cutoff_time
            ).all()
            
            suspicious_activities = []
            
            # Check for high frequency access
            if len(logs) > 50:  # More than 50 accesses in 24 hours
                suspicious_activities.append({
                    'type': 'high_frequency_access',
                    'description': f'User accessed financial data {len(logs)} times in {hours} hours',
                    'severity': 'medium'
                })
            
            # Check for unusual access patterns
            ip_addresses = set(log.ip_address for log in logs if log.ip_address)
            if len(ip_addresses) > 3:  # Access from more than 3 IP addresses
                suspicious_activities.append({
                    'type': 'multiple_ip_access',
                    'description': f'User accessed from {len(ip_addresses)} different IP addresses',
                    'severity': 'high'
                })
            
            # Check for rapid field updates
            update_logs = [log for log in logs if log.action == 'UPDATE']
            if len(update_logs) > 10:  # More than 10 updates in 24 hours
                suspicious_activities.append({
                    'type': 'rapid_updates',
                    'description': f'User made {len(update_logs)} updates in {hours} hours',
                    'severity': 'medium'
                })
            
            return suspicious_activities
            
        except Exception as e:
            logger.error(f"Failed to detect suspicious activity: {str(e)}")
            return [] 