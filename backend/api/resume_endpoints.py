"""
Resume Parsing API endpoints for extracting and analyzing resume data
"""

import os
import sqlite3
import json
import logging
import re
import hashlib
import hmac
import secrets
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest, InternalServerError
from ..utils.validation import APIValidator

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
resume_api = Blueprint('resume_api', __name__, url_prefix='/api')

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('resume_parsing.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_resume_database():
    """Initialize resume parsing database with tables"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create resume parsing results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_parsing_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                file_name TEXT,
                file_hash TEXT UNIQUE,
                raw_content TEXT,
                parsed_data TEXT,
                extraction_errors TEXT,
                confidence_score REAL,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create resume analytics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resume_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id INTEGER,
                action TEXT NOT NULL,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resume_id) REFERENCES resume_parsing_results (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Resume parsing database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing resume parsing database: {e}")
        raise

def validate_csrf_token(token):
    """Validate CSRF token"""
    if not token:
        return False
    
    # In development, accept test token
    if token == 'test-token':
        return True
    
    # In production, implement proper CSRF validation
    return True

def check_rate_limit(client_ip):
    """Check rate limiting"""
    # Simple rate limiting - in production, use Redis or similar
    return True

class ResumeParser:
    """Resume parsing service with comprehensive error handling"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.confidence_score = 0.0
        
    def parse_resume(self, content: str, file_name: str = None) -> Dict[str, Any]:
        """
        Parse resume content and extract structured data
        
        Args:
            content: Raw resume text content
            file_name: Original file name (optional)
            
        Returns:
            Dictionary containing parsed resume data and metadata
        """
        self.errors = []
        self.warnings = []
        self.confidence_score = 0.0
        
        try:
            logger.debug("ResumeParser.parse_resume: start file_name=%s content_len=%d", file_name, len(content) if content else 0)
            # Basic validation
            if not content or len(content.strip()) < 50:
                self.errors.append("Resume content is too short or empty")
                return self._create_error_response()
            
            # Extract sections
            sections = self._extract_sections(content)
            logger.debug("Sections detected: %s", list(sections.keys()))
            
            # Parse each section
            parsed_data = {
                'personal_info': self._parse_personal_info(content, sections),
                'contact_info': self._parse_contact_info(content, sections),
                'experience': self._parse_experience(content, sections),
                'education': self._parse_education(content, sections),
                'skills': self._parse_skills(content, sections),
                'certifications': self._parse_certifications(content, sections),
                'projects': self._parse_projects(content, sections),
                'languages': self._parse_languages(content, sections),
                'summary': self._parse_summary(content, sections)
            }
            
            # Calculate confidence score
            self.confidence_score = self._calculate_confidence_score(parsed_data)
            logger.debug("Confidence score computed: %.2f", self.confidence_score)
            
            # Generate metadata
            metadata = {
                'file_name': file_name,
                'content_length': len(content),
                'word_count': len(content.split()),
                'sections_found': list(sections.keys()),
                'confidence_score': self.confidence_score,
                'parsing_errors': self.errors,
                'parsing_warnings': self.warnings,
                'processing_timestamp': datetime.utcnow().isoformat()
            }
            
            return {
                'success': True,
                'parsed_data': parsed_data,
                'metadata': metadata,
                'errors': self.errors,
                'warnings': self.warnings
            }
            
        except Exception as e:
            error_msg = f"Critical error during resume parsing: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            return self._create_error_response()
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract different sections from resume content with enhanced detection"""
        try:
            # Use improved section detection
            return self._improve_section_detection(content)
        except Exception as e:
            self.errors.append(f"Error extracting sections: {str(e)}")
            return {}
    
    def _improve_section_detection(self, text: str) -> Dict[str, str]:
        """Enhanced section detection with proper boundaries"""
        sections = {}
        
        try:
            logger.debug("Section detection: start")
            # Improved section header patterns
            section_patterns = {
                'contact': r'(?:CONTACT|PERSONAL|PROFILE)(?:\s+INFO(?:RMATION)?)?',
                'experience': r'(?:EXPERIENCE|WORK\s+HISTORY|EMPLOYMENT|PROFESSIONAL\s+EXPERIENCE)',
                'education': r'(?:EDUCATION|ACADEMIC|QUALIFICATIONS)',
                'skills': r'(?:SKILLS|TECHNICAL\s+SKILLS|COMPETENCIES|EXPERTISE)',
                'certifications': r'(?:CERTIFICATIONS?|LICENSES?|CREDENTIALS)',
                'projects': r'(?:PROJECTS|PORTFOLIO|KEY\s+PROJECTS)',
                'languages': r'(?:LANGUAGES|LANGUAGE\s+PROFICIENCY)',
                'summary': r'(?:SUMMARY|OBJECTIVE|PROFESSIONAL\s+SUMMARY|CAREER\s+OBJECTIVE)',
                'personal_info': r'(?:PERSONAL\s+INFORMATION|ABOUT\s+ME|PROFILE)'
            }
            
            # Find section boundaries
            section_boundaries = self._find_section_boundaries(text, section_patterns)
            
            # Extract content for each section with proper boundaries
            for section_name, (start, end) in section_boundaries.items():
                section_content = text[start:end].strip()
                sections[section_name] = self._clean_section_content(section_content)
            logger.debug("Section detection: found=%s", list(sections.keys()))
            
            return sections
            
        except Exception as e:
            self.errors.append(f"Error in improved section detection: {str(e)}")
            return {}
    
    def _find_section_boundaries(self, text: str, patterns: Dict[str, str]) -> Dict[str, tuple]:
        """Find proper start/end positions for each section"""
        try:
            boundaries = {}
            matches = []
            
            # Find all section headers
            for section, pattern in patterns.items():
                for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                    matches.append({
                        'section': section,
                        'start': match.start(),
                        'header_end': match.end()
                    })
            
            # Sort by position and assign boundaries
            matches.sort(key=lambda x: x['start'])
            
            for i, match in enumerate(matches):
                section_start = match['header_end']
                section_end = matches[i + 1]['start'] if i + 1 < len(matches) else len(text)
                boundaries[match['section']] = (section_start, section_end)
            
            return boundaries
            
        except Exception as e:
            self.errors.append(f"Error finding section boundaries: {str(e)}")
            return {}
    
    def _clean_section_content(self, content: str) -> str:
        """Clean and normalize section content"""
        try:
            # Remove excessive whitespace
            content = re.sub(r'\s+', ' ', content)
            
            # Remove common artifacts
            content = re.sub(r'^[•\-\*]\s*', '', content, flags=re.MULTILINE)  # Remove bullet points
            content = re.sub(r'^\d+\.\s*', '', content, flags=re.MULTILINE)  # Remove numbered lists
            
            # Clean up line breaks
            content = re.sub(r'\n\s*\n', '\n', content)  # Remove empty lines
            content = content.strip()
            
            return content
            
        except Exception as e:
            self.errors.append(f"Error cleaning section content: {str(e)}")
            return content
    
    def _parse_personal_info(self, content: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """Parse personal information from resume"""
        personal_info = {}
        
        try:
            # Extract name with improved validation
            extracted_name = self._extract_name_improved(content, sections)
            if extracted_name:
                personal_info['full_name'] = extracted_name
                logger.debug("Personal info: name=%s", extracted_name)
            
            # Extract location
            location_patterns = [
                r'(?i)(?:location|address):\s*([^,\n]+(?:,\s*[^,\n]+)*)',
                r'([A-Z][a-z]+,\s*[A-Z]{2}(?:\s+\d{5})?)',
                r'([A-Z][a-z]+,\s*[A-Z][a-z]+)'
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, content)
                if match:
                    personal_info['location'] = match.group(1).strip()
                    break
            
            # Extract LinkedIn profile
            linkedin_pattern = r'(?:linkedin|linkedin\.com)[:\s]*([^\s\n]+)'
            match = re.search(linkedin_pattern, content, re.IGNORECASE)
            if match:
                personal_info['linkedin'] = match.group(1).strip()
            
            # Extract GitHub profile
            github_pattern = r'(?:github|github\.com)[:\s]*([^\s\n]+)'
            match = re.search(github_pattern, content, re.IGNORECASE)
            if match:
                personal_info['github'] = match.group(1).strip()
            
        except Exception as e:
            self.errors.append(f"Error parsing personal info: {str(e)}")
        
        return personal_info
    
    def _extract_name_improved(self, content: str, sections: Dict[str, str]) -> Optional[str]:
        """Improved name extraction with validation and confidence scoring"""
        try:
            # Split content into lines for processing
            lines = content.split('\n')
            
            # Common job title exclusions to avoid false positives
            job_title_exclusions = [
                r'engineer', r'developer', r'manager', r'analyst', r'specialist', 
                r'coordinator', r'director', r'senior', r'junior', r'lead', r'principal',
                r'architect', r'consultant', r'designer', r'programmer', r'technician',
                r'administrator', r'supervisor', r'executive', r'officer', r'agent',
                r'consultant', r'advisor', r'coordinator', r'facilitator', r'operator'
            ]
            
            # Pattern 1: Look for names at document start (first 3 lines)
            first_lines = lines[:3]
            for i, line in enumerate(first_lines):
                line = line.strip()
                if not line:
                    continue
                
                # Check for ALL CAPS names (common in resumes) - prioritize first line
                # Updated to handle accented characters
                all_caps_match = re.match(r'^([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ][A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ\s]+)$', line)
                if all_caps_match:
                    potential_name = all_caps_match.group(1).strip()
                    if self._validate_name(potential_name, job_title_exclusions):
                        return potential_name.title()
                
                # Check for proper case names (First Last) - prioritize first line
                proper_case_match = re.match(r'^([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', line)
                if proper_case_match:
                    potential_name = proper_case_match.group(1).strip()
                    if self._validate_name(potential_name, job_title_exclusions):
                        return potential_name
                
                # For the first line only, also try a more flexible pattern
                if i == 0:
                    # Try to match names that might have some formatting issues
                    # Updated to handle accented characters
                    flexible_match = re.match(r'^([A-ZÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞ][A-Za-zÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþ\s]+)$', line)
                    if flexible_match:
                        potential_name = flexible_match.group(1).strip()
                        if self._validate_name(potential_name, job_title_exclusions):
                            return potential_name.title()
            
            # Pattern 2: Look for explicit name fields
            explicit_name_patterns = [
                r'Name:\s*([A-Za-z\s]+)',
                r'Full Name:\s*([A-Za-z\s]+)',
                r'Candidate:\s*([A-Za-z\s]+)',
                r'Applicant:\s*([A-Za-z\s]+)'
            ]
            
            for pattern in explicit_name_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    potential_name = match.group(1).strip()
                    if self._validate_name(potential_name, job_title_exclusions):
                        return potential_name.title()
            
            # Pattern 3: Look for names in personal info section
            personal_section = sections.get('personal_info', '')
            if personal_section:
                # First line of personal section is often the name
                personal_lines = personal_section.split('\n')
                for line in personal_lines[:2]:  # Check first 2 lines
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for proper case names
                    proper_case_match = re.match(r'^([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)$', line)
                    if proper_case_match:
                        potential_name = proper_case_match.group(1).strip()
                        if self._validate_name(potential_name, job_title_exclusions):
                            return potential_name
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error in improved name extraction: {str(e)}")
            return None
    
    def _validate_name(self, name: str, job_title_exclusions: List[str]) -> bool:
        """Validate that extracted text is likely a name, not a job title"""
        try:
            if not name or len(name.strip()) < 2:
                return False
            
            name_lower = name.lower()
            
            # Check against job title exclusions
            for exclusion in job_title_exclusions:
                if re.search(exclusion, name_lower):
                    return False
            
            # Check for common non-name patterns
            non_name_patterns = [
                r'\d+',  # Contains numbers
                r'[^\w\s]',  # Contains special characters (except spaces)
                r'^(mr|mrs|ms|dr|prof)\.?\s',  # Titles
                r'(inc|llc|corp|company|ltd|group|systems|technologies|solutions)$',  # Company suffixes
                r'^(university|college|institute|school|academy)',  # Institution names
                r'^(software|web|mobile|frontend|backend|fullstack)',  # Tech prefixes
            ]
            
            for pattern in non_name_patterns:
                if re.search(pattern, name_lower):
                    return False
            
            # Must contain at least one space (first and last name)
            if ' ' not in name:
                return False
            
            # Check that each word starts with capital letter
            words = name.split()
            if len(words) < 2:
                return False
            
            for word in words:
                # Allow ALL CAPS names (like "JOHN SMITH") or proper case (like "John Smith")
                if not (word.isupper() or (word[0].isupper() and word[1:].islower())):
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error validating name: {str(e)}")
            return False
    
    def _parse_contact_info(self, content: str, sections: Dict[str, str]) -> Dict[str, Any]:
        """Parse contact information"""
        contact_info = {}
        
        try:
            # Extract email
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            email_match = re.search(email_pattern, content)
            if email_match:
                contact_info['email'] = email_match.group(0)
            
            # Extract phone number
            phone_patterns = [
                r'\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})',
                r'(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})',
                r'\+?1[-.\s]?\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})'
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, content)
                if match:
                    contact_info['phone'] = ''.join(match.groups())
                    break
            
            # Extract website/portfolio
            website_patterns = [
                r'(?:website|portfolio|url)[:\s]*([^\s\n]+)',
                r'(https?://[^\s\n]+)',
                r'(www\.[^\s\n]+)'
            ]
            
            for pattern in website_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    contact_info['website'] = match.group(1).strip()
                    break
            
        except Exception as e:
            self.errors.append(f"Error parsing contact info: {str(e)}")
        
        return contact_info
    
    def _parse_experience(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse work experience with improved field mapping"""
        try:
            # Use improved experience parsing
            return self._parse_experience_improved(content, sections)
        except Exception as e:
            self.errors.append(f"Error parsing experience: {str(e)}")
            return []
    
    def _parse_experience_improved(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Improved experience parsing with proper field mapping"""
        experience_blocks = []
        
        try:
            # Look for experience section
            exp_content = sections.get('experience', content)
            
            # Step 1: Identify experience sections
            experience_patterns = [
                r'EXPERIENCE|WORK HISTORY|EMPLOYMENT|PROFESSIONAL EXPERIENCE',
                r'(?:Job|Position|Role):\s*(.+)',
                r'(?:Company|Employer):\s*(.+)',
            ]
            
            # Step 2: Parse each experience block
            for block in self._extract_experience_blocks(exp_content):
                experience = {
                    'job_title': self._extract_job_title(block),
                    'company': self._extract_company_name(block),
                    'start_date': self._extract_start_date(block),
                    'end_date': self._extract_end_date(block),
                    'description': self._extract_job_description(block)
                }
                
                # Validation: Ensure fields are correctly assigned
                if self._validate_experience_entry(experience):
                    experience_blocks.append(experience)
            logger.debug("Experience parsed entries=%d", len(experience_blocks))
            
        except Exception as e:
            self.errors.append(f"Error in improved experience parsing: {str(e)}")
        
        return experience_blocks
    
    def _extract_experience_blocks(self, content: str) -> List[str]:
        """Extract individual experience blocks from content"""
        try:
            # Split by common delimiters and patterns
            exp_entries = re.split(r'\n\s*\n|\n(?=[A-Z][^,\n]*[,\s]*[A-Z][a-z]+)', content)
            
            # Filter out very short entries
            return [entry.strip() for entry in exp_entries if len(entry.strip()) >= 20]
            
        except Exception as e:
            self.errors.append(f"Error extracting experience blocks: {str(e)}")
            return []
    
    def _extract_job_title(self, block: str) -> Optional[str]:
        """Extract job title with validation"""
        try:
            # Look for title patterns excluding dates and companies
            title_patterns = [
                r'(?:Title|Position|Role):\s*(.+)',
                r'^([A-Z][a-z\s]+(?:Engineer|Developer|Manager|Analyst|Specialist|Coordinator|Director|Senior|Junior|Lead|Principal|Architect|Consultant|Designer|Programmer|Technician|Administrator|Supervisor|Executive|Officer|Agent|Advisor|Facilitator|Operator))',
                r'([A-Z][a-z\s]+)\s*(?:\n|$)',  # Line before company
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, block, re.MULTILINE)
                if match:
                    potential_title = match.group(1).strip()
                    if self._validate_job_title(potential_title):
                        return potential_title
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting job title: {str(e)}")
            return None
    
    def _extract_company_name(self, block: str) -> Optional[str]:
        """Extract company name excluding dates"""
        try:
            # Company patterns excluding date formats
            company_patterns = [
                r'(?:Company|Employer):\s*(.+)',
                r'(?:at\s+)([A-Z][a-z\s]+(?:Inc|Corp|LLC|Ltd|Group|Systems|Technologies|Solutions)?)',
                r'([A-Z][a-z\s]+(?:Inc|Corp|LLC|Ltd|Group|Systems|Technologies|Solutions))',
            ]
            
            for pattern in company_patterns:
                match = re.search(pattern, block, re.IGNORECASE)
                if match:
                    potential_company = match.group(1).strip()
                    if self._validate_company_name(potential_company):
                        return potential_company
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting company name: {str(e)}")
            return None
    
    def _extract_start_date(self, block: str) -> Optional[str]:
        """Extract start date from experience block"""
        try:
            date_patterns = [
                r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)',
                r'([A-Za-z]+ \d{4})\s*[-–]\s*([A-Za-z]+ \d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current)'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, block)
                if match:
                    return match.group(1).strip()
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting start date: {str(e)}")
            return None
    
    def _extract_end_date(self, block: str) -> Optional[str]:
        """Extract end date from experience block"""
        try:
            date_patterns = [
                r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)',
                r'([A-Za-z]+ \d{4})\s*[-–]\s*([A-Za-z]+ \d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current)'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, block)
                if match:
                    return match.group(2).strip()
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting end date: {str(e)}")
            return None
    
    def _extract_job_description(self, block: str) -> Optional[str]:
        """Extract job description from experience block"""
        try:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            # Skip first line (usually title/company) and look for description
            description_lines = []
            for line in lines[1:]:
                # Skip lines that look like dates or locations
                if not re.search(r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)', line) and \
                   not re.search(r'([A-Z][a-z]+,\s*[A-Z]{2})', line):
                    description_lines.append(line)
            
            return ' '.join(description_lines) if description_lines else None
            
        except Exception as e:
            self.errors.append(f"Error extracting job description: {str(e)}")
            return None
    
    def _validate_experience_entry(self, experience: Dict[str, Any]) -> bool:
        """Validate that experience entry has required fields"""
        try:
            # Must have at least job title or company
            return bool(experience.get('job_title') or experience.get('company'))
            
        except Exception as e:
            self.errors.append(f"Error validating experience entry: {str(e)}")
            return False
    
    def _validate_job_title(self, title: str) -> bool:
        """Validate that extracted text is likely a job title"""
        try:
            if not title or len(title.strip()) < 3:
                return False
            
            # Exclude common non-title patterns
            non_title_patterns = [
                r'^\d+',  # Starts with number
                r'[^\w\s]',  # Contains special characters
                r'^(university|college|institute|school|academy)',  # Institution names
            ]
            
            for pattern in non_title_patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error validating job title: {str(e)}")
            return False
    
    def _validate_company_name(self, company: str) -> bool:
        """Validate that extracted text is likely a company name"""
        try:
            if not company or len(company.strip()) < 2:
                return False
            
            # Exclude common non-company patterns
            non_company_patterns = [
                r'^\d+',  # Starts with number
                r'^(january|february|march|april|may|june|july|august|september|october|november|december)',  # Month names
                r'^(present|current|ongoing)',  # Status words
            ]
            
            for pattern in non_company_patterns:
                if re.search(pattern, company, re.IGNORECASE):
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error validating company name: {str(e)}")
            return False
    
    def _parse_single_experience(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single experience entry"""
        try:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if len(lines) < 2:
                return None
            
            exp_data = {}
            
            # First line usually contains company and title
            first_line = lines[0]
            
            # Try to extract company and title
            company_title_patterns = [
                r'([^,\n]+),\s*([^,\n]+)',
                r'([A-Z][^,\n]+(?:Inc|LLC|Corp|Company|Ltd|Group|Systems|Technologies|Solutions)?)[,\s]*([^,\n]+)',
                r'([A-Z][^,\n]+)[,\s]*([A-Z][a-z]+ [A-Z][a-z]+)'
            ]
            
            for pattern in company_title_patterns:
                match = re.search(pattern, first_line)
                if match:
                    exp_data['company'] = match.group(1).strip()
                    exp_data['title'] = match.group(2).strip()
                    break
            
            # Extract dates
            date_patterns = [
                r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)',
                r'([A-Za-z]+ \d{4})\s*[-–]\s*([A-Za-z]+ \d{4}|Present|Current)',
                r'(\d{1,2}/\d{4})\s*[-–]\s*(\d{1,2}/\d{4}|Present|Current)'
            ]
            
            for line in lines:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        exp_data['start_date'] = match.group(1).strip()
                        exp_data['end_date'] = match.group(2).strip()
                        break
                if 'start_date' in exp_data:
                    break
            
            # Extract location
            location_pattern = r'([A-Z][a-z]+,\s*[A-Z]{2}(?:\s+\d{5})?)'
            for line in lines:
                match = re.search(location_pattern, line)
                if match:
                    exp_data['location'] = match.group(1).strip()
                    break
            
            # Extract description (remaining lines)
            description_lines = []
            for line in lines[1:]:
                if not re.search(r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)', line):
                    description_lines.append(line)
            
            if description_lines:
                exp_data['description'] = ' '.join(description_lines)
            
            return exp_data if exp_data else None
            
        except Exception as e:
            self.errors.append(f"Error parsing single experience entry: {str(e)}")
            return None
    
    def _parse_education(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse education information with improved parsing"""
        try:
            # Use improved education parsing
            return self._parse_education_improved(content, sections)
        except Exception as e:
            self.errors.append(f"Error parsing education: {str(e)}")
            return []
    
    def _parse_education_improved(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fixed education parsing without truncation"""
        education_entries = []
        
        try:
            # Find education section
            education_section = self._extract_education_section(content, sections)
            
            # Improved degree extraction patterns
            degree_patterns = [
                r'(?:Bachelor|Master|PhD|Doctorate|Associate)(?:\s+of\s+)?(?:Science|Arts|Engineering|Business)(?:\s+in\s+[\w\s]+)?',
                r'(?:BS|BA|MS|MA|PhD|MBA)(?:\s+in\s+[\w\s]+)?',
                r'Degree:\s*(.+?)(?:\n|$)',
            ]
            
            for entry in self._split_education_entries(education_section):
                education = {
                    'degree': self._extract_complete_degree(entry, degree_patterns),
                    'university': self._extract_university(entry),
                    'graduation_date': self._extract_graduation_date(entry),
                    'gpa': self._extract_gpa(entry)
                }
                
                if self._validate_education_entry(education):
                    education_entries.append(education)
            logger.debug("Education parsed entries=%d", len(education_entries))
            
        except Exception as e:
            self.errors.append(f"Error in improved education parsing: {str(e)}")
        
        return education_entries
    
    def _extract_education_section(self, content: str, sections: Dict[str, str]) -> str:
        """Extract education section from content"""
        try:
            # First try to get from sections
            if 'education' in sections:
                return sections['education']
            
            # Look for education section in content
            education_patterns = [
                r'(?i)(?:education|academic\s+background|qualifications|educational\s+background)',
                r'(?i)(?:degree|university|college|institute|school)'
            ]
            
            lines = content.split('\n')
            education_lines = []
            in_education_section = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line starts an education section
                for pattern in education_patterns:
                    if re.search(pattern, line):
                        in_education_section = True
                        break
                
                if in_education_section:
                    education_lines.append(line)
                    # Stop if we hit another major section
                    if re.search(r'(?i)(?:experience|work|skills|certifications|projects)', line):
                        break
            
            return '\n'.join(education_lines)
            
        except Exception as e:
            self.errors.append(f"Error extracting education section: {str(e)}")
            return content
    
    def _split_education_entries(self, education_section: str) -> List[str]:
        """Split education section into individual entries"""
        try:
            # Split by common delimiters
            edu_entries = re.split(r'\n\s*\n|\n(?=[A-Z][^,\n]*(?:University|College|Institute|School|Academy))', education_section)
            
            # Filter out very short entries
            return [entry.strip() for entry in edu_entries if len(entry.strip()) >= 15]
            
        except Exception as e:
            self.errors.append(f"Error splitting education entries: {str(e)}")
            return []
    
    def _extract_complete_degree(self, text: str, degree_patterns: List[str]) -> Optional[str]:
        """Extract complete degree without truncation"""
        try:
            # Fix the truncation bug - ensure full string capture
            for pattern in degree_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Return full match, not truncated substring
                    degree = match.group(0).strip()
                    # Clean up the degree name
                    degree = re.sub(r'\s+', ' ', degree)  # Normalize whitespace
                    return degree
            
            # Enhanced fallback patterns for common degree formats
            fallback_patterns = [
                r'(Bachelor of Science in [^,\n]+)',
                r'(Master of Science in [^,\n]+)',
                r'(Bachelor of Arts in [^,\n]+)',
                r'(Master of Arts in [^,\n]+)',
                r'(PhD in [^,\n]+)',
                r'(MBA in [^,\n]+)',
                r'(Bachelor of [^,\n]+)',
                r'(Master of [^,\n]+)',
                r'(Associate of [^,\n]+)',
                r'(Doctorate in [^,\n]+)',
                r'(BS [^,\n]+)',
                r'(BA [^,\n]+)',
                r'(MS [^,\n]+)',
                r'(MA [^,\n]+)',
                r'(MBA [^,\n]+)',
                r'(PhD [^,\n]+)',
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:University|College|Institute|School|Academy)?)',
                r'([A-Z][^,\n]+(?:University|College|Institute|School|Academy)?)',
                r'([A-Z][a-z]+ [A-Z][a-z]+)'
            ]
            
            for pattern in fallback_patterns:
                match = re.search(pattern, text)
                if match:
                    degree = match.group(1).strip()
                    # Clean up the degree name
                    degree = re.sub(r'\s+', ' ', degree)  # Normalize whitespace
                    return degree
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting complete degree: {str(e)}")
            return None
    
    def _extract_university(self, text: str) -> Optional[str]:
        """Extract university/institution name"""
        try:
            university_patterns = [
                r'([A-Z][^,\n]+(?:University|College|Institute|School|Academy))',
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:University|College|Institute|School|Academy))',
                r'([A-Z][a-z]+(?:University|College|Institute|School|Academy))',
                r'(?:University|College|Institute|School|Academy) of ([^,\n]+)',
                r'([A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+(?:University|College|Institute|School|Academy))'  # For names like "Harvard Business School"
            ]
            
            for pattern in university_patterns:
                match = re.search(pattern, text)
                if match:
                    university = match.group(1).strip()
                    # Clean up common artifacts
                    university = re.sub(r'\s+', ' ', university)  # Normalize whitespace
                    return university
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting university: {str(e)}")
            return None
    
    def _extract_graduation_date(self, text: str) -> Optional[str]:
        """Extract graduation date"""
        try:
            date_patterns = [
                r'(?:Graduated|Graduation|Completed):\s*([^,\n]+)',
                r'(\d{4})',
                r'([A-Za-z]+ \d{4})',
                r'(Expected \d{4})'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1).strip()
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting graduation date: {str(e)}")
            return None
    
    def _extract_gpa(self, text: str) -> Optional[str]:
        """Extract GPA information"""
        try:
            gpa_patterns = [
                r'GPA[:\s]*(\d+\.?\d*)',
                r'Grade Point Average[:\s]*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*/\s*\d+\.?\d*',  # Format like 3.8/4.0
                r'(\d+\.?\d*)\s*out\s*of\s*\d+\.?\d*'  # Format like 3.8 out of 4.0
            ]
            
            for pattern in gpa_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return None
            
        except Exception as e:
            self.errors.append(f"Error extracting GPA: {str(e)}")
            return None
    
    def _validate_education_entry(self, education: Dict[str, Any]) -> bool:
        """Validate that education entry has required fields"""
        try:
            # Must have at least degree or university
            return bool(education.get('degree') or education.get('university'))
            
        except Exception as e:
            self.errors.append(f"Error validating education entry: {str(e)}")
            return False
    
    def _parse_single_education(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single education entry"""
        try:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if len(lines) < 1:
                return None
            
            edu_data = {}
            
            # First line usually contains institution and degree
            first_line = lines[0]
            
            # Extract degree and institution
            degree_patterns = [
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:University|College|Institute|School|Academy)?)[,\s]*([^,\n]+)',
                r'([A-Z][a-z]+(?:University|College|Institute|School|Academy)?)[,\s]*([^,\n]+)',
                r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s]*([A-Z][a-z]+(?:University|College|Institute|School|Academy)?)'
            ]
            
            for pattern in degree_patterns:
                match = re.search(pattern, first_line)
                if match:
                    edu_data['institution'] = match.group(1).strip()
                    edu_data['degree'] = match.group(2).strip()
                    break
            
            # Extract graduation date
            date_patterns = [
                r'(\d{4})',
                r'([A-Za-z]+ \d{4})',
                r'(Expected \d{4})'
            ]
            
            for line in lines:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        edu_data['graduation_date'] = match.group(1).strip()
                        break
                if 'graduation_date' in edu_data:
                    break
            
            # Extract GPA
            gpa_pattern = r'GPA[:\s]*(\d+\.?\d*)'
            for line in lines:
                match = re.search(gpa_pattern, line, re.IGNORECASE)
                if match:
                    edu_data['gpa'] = match.group(1).strip()
                    break
            
            return edu_data if edu_data else None
            
        except Exception as e:
            self.errors.append(f"Error parsing single education entry: {str(e)}")
            return None
    
    def _parse_skills(self, content: str, sections: Dict[str, str]) -> List[str]:
        """Parse skills section with improved quality control"""
        try:
            # Use improved skills parsing
            return self._parse_skills_improved(content, sections)
        except Exception as e:
            self.errors.append(f"Error parsing skills: {str(e)}")
            return []
    
    def _parse_skills_improved(self, content: str, sections: Dict[str, str]) -> List[str]:
        """Improved skills parsing with quality control"""
        try:
            # Extract skills section
            skills_section = self._extract_skills_section(content, sections)
            
            # Extract individual skills
            raw_skills = self._extract_raw_skills(skills_section)
            
            # Filter and validate skills
            filtered_skills = []
            for skill in raw_skills:
                if self._is_valid_skill(skill):
                    relevance_score = self._calculate_skill_relevance(skill)
                    if relevance_score > 0.5:  # Threshold for relevance
                        filtered_skills.append({
                            'skill': skill.strip(),
                            'relevance': relevance_score
                        })
            
            # Sort by relevance and limit to top 15
            filtered_skills.sort(key=lambda x: x['relevance'], reverse=True)
            skills = [skill['skill'] for skill in filtered_skills[:15]]
            logger.debug("Skills parsed count=%d", len(skills))
            return skills
            
        except Exception as e:
            self.errors.append(f"Error in improved skills parsing: {str(e)}")
            return []
    
    def _extract_skills_section(self, content: str, sections: Dict[str, str]) -> str:
        """Extract skills section from content"""
        try:
            # First try to get from sections
            if 'skills' in sections:
                return sections['skills']
            
            # Look for skills section in content
            skills_patterns = [
                r'(?i)(?:skills|technical\s+skills|core\s+competencies|proficiencies)',
                r'(?i)(?:programming\s+languages|technologies|tools)'
            ]
            
            lines = content.split('\n')
            skills_lines = []
            in_skills_section = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this line starts a skills section
                for pattern in skills_patterns:
                    if re.search(pattern, line):
                        in_skills_section = True
                        break
                
                if in_skills_section:
                    skills_lines.append(line)
                    # Stop if we hit another major section
                    if re.search(r'(?i)(?:experience|work|education|certifications|projects)', line):
                        break
            
            return '\n'.join(skills_lines)
            
        except Exception as e:
            self.errors.append(f"Error extracting skills section: {str(e)}")
            return content
    
    def _extract_raw_skills(self, skills_section: str) -> List[str]:
        """Extract raw skills from skills section"""
        try:
            skills = []
            
            # Common skill delimiters
            skill_delimiters = [',', ';', '|', '\n', '\t']
            
            for delimiter in skill_delimiters:
                if delimiter in skills_section:
                    skill_list = [skill.strip() for skill in skills_section.split(delimiter) if skill.strip()]
                    if len(skill_list) > 1:
                        skills.extend(skill_list)
                        break
            
            # If no delimiters found, try to extract individual skills
            if not skills:
                # Look for bullet points or numbered lists
                bullet_pattern = r'[•\-\*]\s*([^\n]+)'
                matches = re.findall(bullet_pattern, skills_section)
                if matches:
                    skills.extend([match.strip() for match in matches])
            
            # Clean up skills
            skills = [skill.strip() for skill in skills if len(skill.strip()) > 1]
            
            return skills
            
        except Exception as e:
            self.errors.append(f"Error extracting raw skills: {str(e)}")
            return []
    
    def _is_valid_skill(self, skill: str) -> bool:
        """Validate individual skills"""
        try:
            # Remove invalid entries
            if len(skill) < 2 or len(skill) > 50:
                return False
            if any(char in skill for char in ['\n', '\t', '  ']):
                return False
            if skill.lower() in ['and', 'or', 'with', 'including', 'skills', 'technologies', 'tools', 'languages']:
                return False
            
            # Check for common non-skill patterns
            non_skill_patterns = [
                r'^\d+$',  # Just numbers
                r'^[A-Z\s]+$',  # All caps (likely headers)
                r'^[a-z\s]+:$',  # Colon endings (likely headers)
                r'^\s*$',  # Empty or whitespace only
            ]
            
            for pattern in non_skill_patterns:
                if re.match(pattern, skill):
                    return False
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error validating skill: {str(e)}")
            return False
    
    def _calculate_skill_relevance(self, skill: str) -> float:
        """Score skill relevance for career advancement"""
        try:
            # Technical skills database for scoring
            high_value_skills = [
                'python', 'javascript', 'java', 'sql', 'aws', 'azure', 'react', 'angular', 'vue',
                'node.js', 'django', 'flask', 'spring', 'docker', 'kubernetes', 'git', 'github',
                'leadership', 'project management', 'data analysis', 'machine learning', 'ai',
                'cloud computing', 'devops', 'agile', 'scrum', 'api', 'rest', 'graphql',
                'typescript', 'html', 'css', 'bootstrap', 'jquery', 'mongodb', 'postgresql',
                'mysql', 'redis', 'elasticsearch', 'kafka', 'rabbitmq', 'jenkins', 'ci/cd',
                'terraform', 'ansible', 'linux', 'unix', 'bash', 'powershell', 'tcp/ip',
                'networking', 'security', 'encryption', 'oauth', 'jwt', 'microservices',
                'serverless', 'lambda', 'ec2', 's3', 'rds', 'dynamodb', 'cloudformation'
            ]
            
            medium_value_skills = [
                'excel', 'powerpoint', 'word', 'outlook', 'photoshop', 'illustrator',
                'communication', 'teamwork', 'problem solving', 'analytical', 'creative',
                'detail oriented', 'time management', 'customer service', 'sales',
                'marketing', 'finance', 'accounting', 'human resources', 'operations'
            ]
            
            skill_lower = skill.lower()
            
            # Check for high-value skills
            for hvs in high_value_skills:
                if hvs in skill_lower:
                    return 0.9
            
            # Check for medium-value skills
            for mvs in medium_value_skills:
                if mvs in skill_lower:
                    return 0.7
            
            # Check for technical indicators
            technical_indicators = [
                r'\b(?:programming|development|coding|software|web|mobile|database|server|cloud|api|framework|library|tool|platform|system|application|software|hardware|network|security|data|analytics|machine|learning|artificial|intelligence|blockchain|cryptocurrency|devops|automation|testing|deployment|integration|architecture|design|ui|ux|frontend|backend|fullstack|full-stack)\b'
            ]
            
            for pattern in technical_indicators:
                if re.search(pattern, skill_lower):
                    return 0.8
            
            # Check for length and complexity
            if len(skill) > 20:  # Longer skills are often more specific
                return 0.6
            elif len(skill) > 10:
                return 0.5
            else:
                return 0.4  # Default relevance for short skills
                
        except Exception as e:
            self.errors.append(f"Error calculating skill relevance: {str(e)}")
            return 0.5
    
    def _parse_certifications(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse certifications"""
        certifications = []
        
        try:
            cert_content = sections.get('certifications', content)
            
            # Split by common delimiters
            cert_entries = re.split(r'\n\s*\n|\n(?=[A-Z])', cert_content)
            
            for entry in cert_entries:
                if len(entry.strip()) < 10:
                    continue
                
                cert_data = self._parse_single_certification(entry)
                if cert_data:
                    certifications.append(cert_data)
            
        except Exception as e:
            self.errors.append(f"Error parsing certifications: {str(e)}")
        
        return certifications
    
    def _parse_single_certification(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single certification entry"""
        try:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if len(lines) < 1:
                return None
            
            cert_data = {}
            
            # First line usually contains certification name
            cert_data['name'] = lines[0]
            
            # Extract issuing organization
            org_patterns = [
                r'([A-Z][^,\n]+(?:Institute|Association|Board|Council|Society|Foundation)?)',
                r'([A-Z][a-z]+ [A-Z][a-z]+(?:Institute|Association|Board|Council|Society|Foundation)?)'
            ]
            
            for line in lines:
                for pattern in org_patterns:
                    match = re.search(pattern, line)
                    if match and match.group(1) != cert_data['name']:
                        cert_data['issuing_organization'] = match.group(1).strip()
                        break
                if 'issuing_organization' in cert_data:
                    break
            
            # Extract date
            date_patterns = [
                r'(\d{4})',
                r'([A-Za-z]+ \d{4})',
                r'(Issued \d{4})'
            ]
            
            for line in lines:
                for pattern in date_patterns:
                    match = re.search(pattern, line)
                    if match:
                        cert_data['date'] = match.group(1).strip()
                        break
                if 'date' in cert_data:
                    break
            
            return cert_data if cert_data else None
            
        except Exception as e:
            self.errors.append(f"Error parsing single certification: {str(e)}")
            return None
    
    def _parse_projects(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse projects section"""
        projects = []
        
        try:
            projects_content = sections.get('projects', content)
            
            # Split by common delimiters
            project_entries = re.split(r'\n\s*\n|\n(?=[A-Z])', projects_content)
            
            for entry in project_entries:
                if len(entry.strip()) < 15:
                    continue
                
                project_data = self._parse_single_project(entry)
                if project_data:
                    projects.append(project_data)
            
        except Exception as e:
            self.errors.append(f"Error parsing projects: {str(e)}")
        
        return projects
    
    def _parse_single_project(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single project entry"""
        try:
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if len(lines) < 1:
                return None
            
            project_data = {}
            
            # First line usually contains project name
            project_data['name'] = lines[0]
            
            # Extract description (remaining lines)
            if len(lines) > 1:
                project_data['description'] = ' '.join(lines[1:])
            
            # Extract technologies used
            tech_patterns = [
                r'(?:Technologies?|Tech|Tools?)[:\s]*([^\n]+)',
                r'(?:Built with|Using)[:\s]*([^\n]+)'
            ]
            
            for line in lines:
                for pattern in tech_patterns:
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        project_data['technologies'] = match.group(1).strip()
                        break
                if 'technologies' in project_data:
                    break
            
            return project_data if project_data else None
            
        except Exception as e:
            self.errors.append(f"Error parsing single project: {str(e)}")
            return None
    
    def _parse_languages(self, content: str, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse languages section"""
        languages = []
        
        try:
            languages_content = sections.get('languages', content)
            
            # Common language patterns
            language_patterns = [
                r'([A-Z][a-z]+)[,\s]*([A-Z][a-z]+(?:Native|Fluent|Intermediate|Basic|Beginner)?)',
                r'([A-Z][a-z]+)[,\s]*([A-Z][a-z]+)'
            ]
            
            # Split by common delimiters
            lang_entries = re.split(r'[,\n]', languages_content)
            
            for entry in lang_entries:
                entry = entry.strip()
                if len(entry) < 3:
                    continue
                
                lang_data = self._parse_single_language(entry)
                if lang_data:
                    languages.append(lang_data)
            
        except Exception as e:
            self.errors.append(f"Error parsing languages: {str(e)}")
        
        return languages
    
    def _parse_single_language(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single language entry"""
        try:
            # Extract language and proficiency level
            proficiency_patterns = [
                r'([A-Z][a-z]+)[,\s]*([A-Z][a-z]+(?:Native|Fluent|Intermediate|Basic|Beginner)?)',
                r'([A-Z][a-z]+)[,\s]*([A-Z][a-z]+)'
            ]
            
            for pattern in proficiency_patterns:
                match = re.search(pattern, entry)
                if match:
                    return {
                        'language': match.group(1).strip(),
                        'proficiency': match.group(2).strip()
                    }
            
            # If no pattern matches, just return the language
            return {'language': entry.strip()}
            
        except Exception as e:
            self.errors.append(f"Error parsing single language: {str(e)}")
            return None
    
    def _parse_summary(self, content: str, sections: Dict[str, str]) -> str:
        """Parse professional summary/objective"""
        try:
            summary_content = sections.get('summary', '')
            
            if summary_content:
                # Clean up the summary
                summary = re.sub(r'\s+', ' ', summary_content).strip()
                return summary
            
            return ""
            
        except Exception as e:
            self.errors.append(f"Error parsing summary: {str(e)}")
            return ""
    
    def _calculate_confidence_score(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data quality"""
        try:
            score = 0.0
            max_score = 100.0

            personal = parsed_data.get('personal_info', {})
            contact = parsed_data.get('contact_info', {})
            experience = parsed_data.get('experience', [])
            education = parsed_data.get('education', [])
            skills = parsed_data.get('skills', [])

            # Personal info (name is critical)
            if personal.get('full_name'):
                score += 20  # previously 10
            if personal.get('location'):
                score += 5
            if personal.get('linkedin'):
                score += 5

            # Contact info
            if contact.get('email'):
                score += 10
            if contact.get('phone'):
                score += 10

            # Section coverage bonus (up to 20)
            present_sections = 0
            for key in ['experience', 'education', 'skills', 'certifications', 'projects', 'summary']:
                if parsed_data.get(key):
                    present_sections += 1
            score += min(20, present_sections * 4)

            # Experience quality: points for entries and completeness
            if experience:
                base = min(20, len(experience) * 5)
                completeness = 0
                for exp in experience[:5]:
                    has_company = bool(exp.get('company'))
                    has_title = bool(exp.get('job_title')) or bool(exp.get('title'))
                    if has_company and has_title:
                        completeness += 2
                    elif has_company or has_title:
                        completeness += 1
                score += base + min(10, completeness)

            # Education quality
            if education:
                base_edu = min(10, len(education) * 5)
                degree_bonus = 0
                for edu in education[:3]:
                    if edu.get('degree'):
                        degree_bonus += 3
                    if edu.get('university') or edu.get('institution'):
                        degree_bonus += 2
                score += min(15, base_edu + degree_bonus)

            # Skills (prefer 10-15 items)
            if skills:
                count = len(skills)
                if 10 <= count <= 15:
                    score += 10
                else:
                    score += 6  # present but not ideal range

            # Other sections
            if parsed_data.get('certifications'):
                score += 2
            if parsed_data.get('projects'):
                score += 2
            if parsed_data.get('summary'):
                score += 1

            return min(score, max_score)
            
        except Exception as e:
            self.errors.append(f"Error calculating confidence score: {str(e)}")
            return 0.0
    
    def _create_error_response(self) -> Dict[str, Any]:
        """Create error response when parsing fails"""
        return {
            'success': False,
            'parsed_data': {},
            'metadata': {
                'confidence_score': 0.0,
                'parsing_errors': self.errors,
                'parsing_warnings': self.warnings,
                'processing_timestamp': datetime.utcnow().isoformat()
            },
            'errors': self.errors,
            'warnings': self.warnings
        }

@resume_api.route('/resume/parse', methods=['POST'])
def parse_resume():
    """
    Parse resume content and extract structured data
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in resume parsing")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        # Rate limiting check
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({'success': False, 'error': 'Rate limit exceeded'}), 429
        
        data = request.get_json()
        
        if not data:
            raise BadRequest("No data provided")
        
        # Validate required fields
        if 'content' not in data:
            raise BadRequest("Missing required field: content")
        
        content = data['content']
        file_name = data.get('file_name', 'Unknown')
        user_id = data.get('user_id', 'anonymous')
        
        # Validate content
        if not content or len(content.strip()) < 50:
            raise BadRequest("Resume content is too short or empty")
        
        # Generate file hash for deduplication
        file_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        # Check if resume was already parsed
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM resume_parsing_results WHERE file_hash = ?', (file_hash,))
        existing_result = cursor.fetchone()
        
        if existing_result:
            conn.close()
            return jsonify({
                'success': True,
                'parsed_data': json.loads(existing_result['parsed_data']),
                'metadata': {
                    'file_name': existing_result['file_name'],
                    'confidence_score': existing_result['confidence_score'],
                    'processing_timestamp': existing_result['created_at'],
                    'cached': True
                },
                'message': 'Resume already parsed (cached result)'
            })
        
        # Parse resume
        start_time = datetime.utcnow()
        parser = ResumeParser()
        result = parser.parse_resume(content, file_name)
        end_time = datetime.utcnow()
        
        processing_time = (end_time - start_time).total_seconds()
        
        # Store result in database
        cursor.execute('''
            INSERT INTO resume_parsing_results 
            (user_id, file_name, file_hash, raw_content, parsed_data, extraction_errors, confidence_score, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            file_name,
            file_hash,
            content,
            json.dumps(result.get('parsed_data', {})),
            json.dumps(result.get('errors', [])),
            result.get('metadata', {}).get('confidence_score', 0.0),
            processing_time
        ))
        
        resume_id = cursor.lastrowid
        
        # Track analytics
        cursor.execute('''
            INSERT INTO resume_analytics (resume_id, action, data)
            VALUES (?, ?, ?)
        ''', (resume_id, 'resume_parsed', json.dumps({
            'file_name': file_name,
            'content_length': len(content),
            'confidence_score': result.get('metadata', {}).get('confidence_score', 0.0),
            'processing_time': processing_time,
            'error_count': len(result.get('errors', [])),
            'warning_count': len(result.get('warnings', []))
        })))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Resume parsed successfully: {resume_id}")
        
        return jsonify({
            'success': True,
            'resume_id': resume_id,
            'parsed_data': result.get('parsed_data', {}),
            'metadata': result.get('metadata', {}),
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'message': 'Resume parsed successfully'
        })
        
    except BadRequest as e:
        logger.warning(f"Bad request in parse_resume: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in parse_resume: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@resume_api.route('/resume/<resume_id>', methods=['GET'])
def get_resume_result(resume_id):
    """
    Get parsed resume result by ID
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in resume retrieval")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM resume_parsing_results WHERE id = ?
        ''', (resume_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'error': 'Resume not found'}), 404
        
        return jsonify({
            'success': True,
            'resume_id': result['id'],
            'parsed_data': json.loads(result['parsed_data']),
            'metadata': {
                'file_name': result['file_name'],
                'confidence_score': result['confidence_score'],
                'processing_time': result['processing_time'],
                'created_at': result['created_at']
            },
            'errors': json.loads(result['extraction_errors'])
        })
        
    except Exception as e:
        logger.error(f"Error in get_resume_result: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@resume_api.route('/resume/analytics', methods=['GET'])
def get_resume_analytics():
    """
    Get resume parsing analytics
    """
    try:
        # Validate CSRF token
        csrf_token = request.headers.get('X-CSRF-Token')
        if not validate_csrf_token(csrf_token):
            logger.warning("Invalid CSRF token in resume analytics")
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get basic statistics
        cursor.execute('SELECT COUNT(*) as total_resumes FROM resume_parsing_results')
        total_resumes = cursor.fetchone()['total_resumes']
        
        cursor.execute('SELECT AVG(confidence_score) as avg_confidence FROM resume_parsing_results')
        avg_confidence = cursor.fetchone()['avg_confidence'] or 0
        
        cursor.execute('SELECT AVG(processing_time) as avg_processing_time FROM resume_parsing_results')
        avg_processing_time = cursor.fetchone()['avg_processing_time'] or 0
        
        # Get recent activity
        cursor.execute('''
            SELECT action, COUNT(*) as count 
            FROM resume_analytics 
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY action
        ''')
        recent_activity = {row['action']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_resumes': total_resumes,
                'average_confidence_score': round(avg_confidence, 2),
                'average_processing_time': round(avg_processing_time, 2),
                'recent_activity': recent_activity
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_resume_analytics: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

# Initialize database when module is imported
init_resume_database()
