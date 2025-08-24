"""
Resume Parsing Service

This module provides resume parsing functionality for the MINGUS application,
with tier-based limits (1 per month for Budget tier).
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import re

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import SQLAlchemyError

from backend.models.user_models import User
from backend.services.subscription_tier_service import SubscriptionTierService
from backend.utils.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)


class ParsingStatus(Enum):
    """Resume parsing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    LIMIT_EXCEEDED = "limit_exceeded"


@dataclass
class ParsedResume:
    """Parsed resume data structure"""
    id: str
    user_id: str
    original_filename: str
    parsing_status: ParsingStatus
    parsed_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    file_size: int
    file_type: str


@dataclass
class ResumeInsight:
    """Resume insight data structure"""
    insight_id: str
    resume_id: str
    insight_type: str
    title: str
    description: str
    severity: str  # 'high', 'medium', 'low'
    actionable: bool
    recommendation: str
    generated_at: datetime


class ResumeParsingService:
    """Service for resume parsing with tier-based limits"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
        self.tier_service = SubscriptionTierService(db_session)
        
        # Mock data storage (in production, this would be database tables)
        self.parsed_resumes: Dict[str, List[ParsedResume]] = {}
        self.parsing_usage: Dict[str, Dict[str, Any]] = {}
    
    def parse_resume(self, user_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a resume for a user
        
        Args:
            user_id: User ID
            file_data: File data including filename, content, size, type
            
        Returns:
            Parsing result with status and data
        """
        try:
            # Check parsing limits
            limit_check = self._check_parsing_limits(user_id)
            if not limit_check['can_parse']:
                return {
                    'success': False,
                    'error': 'limit_exceeded',
                    'message': limit_check['message'],
                    'upgrade_required': limit_check['upgrade_required']
                }
            
            # Validate file data
            if not self._validate_file_data(file_data):
                return {
                    'success': False,
                    'error': 'invalid_file',
                    'message': 'Invalid file data provided'
                }
            
            # Create parsing record
            resume_id = f"resume_{int(datetime.utcnow().timestamp())}"
            parsed_resume = ParsedResume(
                id=resume_id,
                user_id=user_id,
                original_filename=file_data['filename'],
                parsing_status=ParsingStatus.PROCESSING,
                parsed_data={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                file_size=file_data.get('size', 0),
                file_type=file_data.get('type', 'unknown')
            )
            
            # Store parsing record
            if user_id not in self.parsed_resumes:
                self.parsed_resumes[user_id] = []
            self.parsed_resumes[user_id].append(parsed_resume)
            
            # Update usage tracking
            self._update_parsing_usage(user_id)
            
            # Parse the resume content
            parsed_data = self._parse_resume_content(file_data['content'])
            
            # Update parsing record with results
            parsed_resume.parsing_status = ParsingStatus.COMPLETED
            parsed_resume.parsed_data = parsed_data
            parsed_resume.updated_at = datetime.utcnow()
            
            # Generate insights
            insights = self._generate_resume_insights(resume_id, parsed_data)
            
            return {
                'success': True,
                'resume_id': resume_id,
                'parsed_data': parsed_data,
                'insights': insights,
                'parsing_usage': self._get_parsing_usage(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error parsing resume for user {user_id}: {e}")
            return {
                'success': False,
                'error': 'parsing_failed',
                'message': 'Failed to parse resume'
            }
    
    def _check_parsing_limits(self, user_id: str) -> Dict[str, Any]:
        """Check if user can parse a resume based on their tier limits"""
        try:
            # Get user's tier
            user_tier = self.tier_service.get_user_tier(user_id)
            
            # Get current usage
            usage = self._get_parsing_usage(user_id)
            
            # Define limits by tier
            tier_limits = {
                'budget': 1,
                'mid_tier': 5,
                'professional': -1  # Unlimited
            }
            
            monthly_limit = tier_limits.get(user_tier.value, 1)
            
            if monthly_limit == -1:  # Unlimited
                return {
                    'can_parse': True,
                    'message': 'Unlimited parsing available',
                    'upgrade_required': False
                }
            
            # Check if limit exceeded
            if usage['parsing_used_this_month']:
                return {
                    'can_parse': False,
                    'message': f'Monthly parsing limit ({monthly_limit}) reached. Upgrade to parse more resumes.',
                    'upgrade_required': True,
                    'current_tier': user_tier.value,
                    'upgrade_tier': 'mid_tier' if user_tier.value == 'budget' else 'professional'
                }
            
            return {
                'can_parse': True,
                'message': f'Parsing available ({monthly_limit} per month)',
                'upgrade_required': False
            }
            
        except Exception as e:
            self.logger.error(f"Error checking parsing limits for user {user_id}: {e}")
            return {
                'can_parse': False,
                'message': 'Error checking parsing limits',
                'upgrade_required': False
            }
    
    def _validate_file_data(self, file_data: Dict[str, Any]) -> bool:
        """Validate resume file data"""
        required_fields = ['filename', 'content']
        
        for field in required_fields:
            if field not in file_data:
                return False
        
        # Check file size (max 10MB)
        if file_data.get('size', 0) > 10 * 1024 * 1024:
            return False
        
        # Check file type
        allowed_types = ['pdf', 'doc', 'docx', 'txt']
        file_type = file_data.get('type', '').lower()
        if file_type not in allowed_types:
            return False
        
        return True
    
    def _parse_resume_content(self, content: str) -> Dict[str, Any]:
        """Parse resume content and extract information"""
        try:
            # This is a simplified parsing implementation
            # In production, this would use more sophisticated NLP and parsing libraries
            
            parsed_data = {
                'personal_info': self._extract_personal_info(content),
                'education': self._extract_education(content),
                'experience': self._extract_experience(content),
                'skills': self._extract_skills(content),
                'summary': self._extract_summary(content),
                'parsing_confidence': 0.85
            }
            
            return parsed_data
            
        except Exception as e:
            self.logger.error(f"Error parsing resume content: {e}")
            return {}
    
    def _extract_personal_info(self, content: str) -> Dict[str, Any]:
        """Extract personal information from resume"""
        try:
            # Extract email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, content)
            email = email_match.group() if email_match else None
            
            # Extract phone
            phone_pattern = r'\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})'
            phone_match = re.search(phone_pattern, content)
            phone = phone_match.group() if phone_match else None
            
            # Extract name (simplified)
            lines = content.split('\n')
            name = lines[0].strip() if lines else None
            
            return {
                'name': name,
                'email': email,
                'phone': phone
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting personal info: {e}")
            return {}
    
    def _extract_education(self, content: str) -> List[Dict[str, Any]]:
        """Extract education information from resume"""
        try:
            education = []
            
            # Look for education keywords
            education_keywords = ['education', 'academic', 'degree', 'university', 'college', 'school']
            
            lines = content.lower().split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in education_keywords):
                    # Extract education entry
                    if i + 1 < len(lines):
                        education_entry = {
                            'institution': lines[i + 1].strip() if i + 1 < len(lines) else '',
                            'degree': line.strip(),
                            'year': self._extract_year(lines[i + 2]) if i + 2 < len(lines) else None
                        }
                        education.append(education_entry)
            
            return education
            
        except Exception as e:
            self.logger.error(f"Error extracting education: {e}")
            return []
    
    def _extract_experience(self, content: str) -> List[Dict[str, Any]]:
        """Extract work experience from resume"""
        try:
            experience = []
            
            # Look for experience keywords
            experience_keywords = ['experience', 'work history', 'employment', 'job']
            
            lines = content.lower().split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line for keyword in experience_keywords):
                    # Extract experience entry
                    if i + 1 < len(lines):
                        experience_entry = {
                            'title': lines[i + 1].strip() if i + 1 < len(lines) else '',
                            'company': lines[i + 2].strip() if i + 2 < len(lines) else '',
                            'duration': self._extract_duration(lines[i + 3]) if i + 3 < len(lines) else None
                        }
                        experience.append(experience_entry)
            
            return experience
            
        except Exception as e:
            self.logger.error(f"Error extracting experience: {e}")
            return []
    
    def _extract_skills(self, content: str) -> List[str]:
        """Extract skills from resume"""
        try:
            skills = []
            
            # Common skill keywords
            skill_keywords = [
                'python', 'java', 'javascript', 'react', 'angular', 'node.js', 'sql', 'mongodb',
                'aws', 'docker', 'kubernetes', 'git', 'agile', 'scrum', 'project management',
                'data analysis', 'machine learning', 'ai', 'excel', 'powerpoint', 'word'
            ]
            
            content_lower = content.lower()
            for skill in skill_keywords:
                if skill in content_lower:
                    skills.append(skill.title())
            
            return skills
            
        except Exception as e:
            self.logger.error(f"Error extracting skills: {e}")
            return []
    
    def _extract_summary(self, content: str) -> str:
        """Extract summary or objective from resume"""
        try:
            # Look for summary keywords
            summary_keywords = ['summary', 'objective', 'profile']
            
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in summary_keywords):
                    if i + 1 < len(lines):
                        return lines[i + 1].strip()
            
            return ""
            
        except Exception as e:
            self.logger.error(f"Error extracting summary: {e}")
            return ""
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text"""
        try:
            year_pattern = r'\b(19|20)\d{2}\b'
            year_match = re.search(year_pattern, text)
            return int(year_match.group()) if year_match else None
        except:
            return None
    
    def _extract_duration(self, text: str) -> Optional[str]:
        """Extract duration from text"""
        try:
            duration_pattern = r'\b\d{4}\s*[-–]\s*\d{4}|\b\d{4}\s*[-–]\s*present\b'
            duration_match = re.search(duration_pattern, text, re.IGNORECASE)
            return duration_match.group() if duration_match else None
        except:
            return None
    
    def _generate_resume_insights(self, resume_id: str, parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate insights from parsed resume data"""
        try:
            insights = []
            
            # Insight 1: Skills analysis
            skills = parsed_data.get('skills', [])
            if len(skills) < 5:
                insights.append({
                    'insight_id': f'{resume_id}_skills',
                    'insight_type': 'skills',
                    'title': 'Skills Enhancement Opportunity',
                    'description': f'Your resume shows {len(skills)} technical skills. Consider adding more relevant skills.',
                    'severity': 'medium',
                    'actionable': True,
                    'recommendation': 'Research job requirements in your field and add relevant technical skills'
                })
            
            # Insight 2: Experience analysis
            experience = parsed_data.get('experience', [])
            if len(experience) < 2:
                insights.append({
                    'insight_id': f'{resume_id}_experience',
                    'insight_type': 'experience',
                    'title': 'Experience Level',
                    'description': f'Your resume shows {len(experience)} work experience entries.',
                    'severity': 'low',
                    'actionable': True,
                    'recommendation': 'Consider adding internships, projects, or volunteer work to strengthen your experience'
                })
            
            # Insight 3: Education analysis
            education = parsed_data.get('education', [])
            if not education:
                insights.append({
                    'insight_id': f'{resume_id}_education',
                    'insight_type': 'education',
                    'title': 'Education Section Missing',
                    'description': 'No education information found in your resume.',
                    'severity': 'high',
                    'actionable': True,
                    'recommendation': 'Add your educational background, including degrees, institutions, and graduation dates'
                })
            
            # Insight 4: Contact information
            personal_info = parsed_data.get('personal_info', {})
            if not personal_info.get('email') or not personal_info.get('phone'):
                insights.append({
                    'insight_id': f'{resume_id}_contact',
                    'insight_type': 'contact',
                    'title': 'Contact Information Incomplete',
                    'description': 'Missing email or phone number in your resume.',
                    'severity': 'high',
                    'actionable': True,
                    'recommendation': 'Ensure your resume includes a professional email and phone number'
                })
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating resume insights: {e}")
            return []
    
    def _update_parsing_usage(self, user_id: str):
        """Update parsing usage tracking for a user"""
        try:
            current_month = date.today().replace(day=1)
            
            if user_id not in self.parsing_usage:
                self.parsing_usage[user_id] = {
                    'parsing_used_this_month': False,
                    'last_parsed_date': None,
                    'parsed_resume_count': 0,
                    'monthly_reset_date': current_month
                }
            
            usage = self.parsing_usage[user_id]
            
            # Check if we need to reset monthly usage
            if usage['monthly_reset_date'] < current_month:
                usage['parsing_used_this_month'] = False
                usage['monthly_reset_date'] = current_month
            
            # Update usage
            usage['parsing_used_this_month'] = True
            usage['last_parsed_date'] = date.today()
            usage['parsed_resume_count'] += 1
            
        except Exception as e:
            self.logger.error(f"Error updating parsing usage for user {user_id}: {e}")
    
    def get_parsing_status(self, user_id: str) -> Dict[str, Any]:
        """Get parsing status and usage for a user"""
        try:
            usage = self._get_parsing_usage(user_id)
            
            # Get user's tier
            user_tier = self.tier_service.get_user_tier(user_id)
            
            # Get recent parsed resumes
            recent_resumes = self._get_recent_parsed_resumes(user_id, limit=5)
            
            return {
                'parsing_used_this_month': usage['parsing_used_this_month'],
                'last_parsed_date': usage['last_parsed_date'],
                'parsed_resume_count': usage['parsed_resume_count'],
                'current_tier': user_tier.value,
                'recent_resumes': recent_resumes
            }
            
        except Exception as e:
            self.logger.error(f"Error getting parsing status for user {user_id}: {e}")
            return {}
    
    def _get_parsing_usage(self, user_id: str) -> Dict[str, Any]:
        """Get parsing usage for a user"""
        try:
            if user_id not in self.parsing_usage:
                current_month = date.today().replace(day=1)
                self.parsing_usage[user_id] = {
                    'parsing_used_this_month': False,
                    'last_parsed_date': None,
                    'parsed_resume_count': 0,
                    'monthly_reset_date': current_month
                }
            
            return self.parsing_usage[user_id]
            
        except Exception as e:
            self.logger.error(f"Error getting parsing usage for user {user_id}: {e}")
            return {}
    
    def _get_recent_parsed_resumes(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent parsed resumes for a user"""
        try:
            resumes = self.parsed_resumes.get(user_id, [])
            
            # Sort by creation date (most recent first)
            resumes.sort(key=lambda x: x.created_at, reverse=True)
            
            # Convert to dictionary format
            resume_data = []
            for resume in resumes[:limit]:
                resume_dict = {
                    'id': resume.id,
                    'filename': resume.original_filename,
                    'status': resume.parsing_status.value,
                    'created_at': resume.created_at.isoformat(),
                    'file_size': resume.file_size,
                    'file_type': resume.file_type
                }
                resume_data.append(resume_dict)
            
            return resume_data
            
        except Exception as e:
            self.logger.error(f"Error getting recent parsed resumes for user {user_id}: {e}")
            return []
    
    def get_resume_insights(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get insights for a specific resume"""
        try:
            # Find the resume
            for user_resumes in self.parsed_resumes.values():
                for resume in user_resumes:
                    if resume.id == resume_id:
                        return self._generate_resume_insights(resume_id, resume.parsed_data)
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting resume insights for resume {resume_id}: {e}")
            return []
    
    def delete_resume(self, user_id: str, resume_id: str) -> bool:
        """Delete a parsed resume"""
        try:
            if user_id in self.parsed_resumes:
                self.parsed_resumes[user_id] = [
                    r for r in self.parsed_resumes[user_id] if r.id != resume_id
                ]
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting resume {resume_id} for user {user_id}: {e}")
            return False 