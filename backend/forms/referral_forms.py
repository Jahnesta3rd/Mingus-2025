#!/usr/bin/env python3
"""
Enhanced Form Classes for Referral-Gated Job Recommendation System
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, ValidationError
import re

class ReferralInviteForm(FlaskForm):
    """Form for sending referral invitations"""
    friend_email = StringField('Friend\'s Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=255, message='Email is too long')
    ])
    friend_name = StringField('Friend\'s Name (Optional)', validators=[
        Length(max=100, message='Name is too long')
    ])
    personal_message = TextAreaField('Personal Message (Optional)', validators=[
        Length(max=500, message='Message is too long')
    ])
    submit = SubmitField('Send Invitation')

class LocationPreferencesForm(FlaskForm):
    """Form for location preferences (REFERRAL-GATED)"""
    zipcode = StringField('ZIP Code', validators=[
        DataRequired(message='ZIP code is required'),
        Length(min=5, max=10, message='Please enter a valid ZIP code')
    ])
    search_radius = SelectField('Search Radius (miles)', choices=[
        (10, '10 miles'),
        (25, '25 miles'),
        (50, '50 miles'),
        (100, '100 miles'),
        (200, '200+ miles (Remote OK)')
    ], default=25, validators=[DataRequired()])
    commute_preference = SelectField('Commute Preference', choices=[
        ('flexible', 'Flexible - Open to various commute times'),
        ('short', 'Short - Prefer under 30 minutes'),
        ('medium', 'Medium - Up to 45 minutes is OK'),
        ('long', 'Long - Up to 60 minutes is OK'),
        ('remote', 'Remote Only - No commute preferred')
    ], default='flexible', validators=[DataRequired()])
    remote_ok = BooleanField('Open to Remote Work', default=True)
    submit = SubmitField('Save Location Preferences')

    def validate_zipcode(self, field):
        """Validate US ZIP code format"""
        zipcode = field.data.strip()
        # Basic US ZIP code pattern (5 digits or 5+4 format)
        if not re.match(r'^\d{5}(-\d{4})?$', zipcode):
            raise ValidationError('Please enter a valid US ZIP code (e.g., 12345 or 12345-6789)')

class CareerPreferencesForm(FlaskForm):
    """Form for career preferences (REFERRAL-GATED)"""
    current_salary = IntegerField('Current Annual Salary', validators=[
        DataRequired(message='Current salary is required'),
        NumberRange(min=20000, max=1000000, message='Please enter a realistic salary amount')
    ])
    target_salary_increase = SelectField('Target Salary Increase', choices=[
        (0.10, '10% increase'),
        (0.15, '15% increase'),
        (0.20, '20% increase'),
        (0.25, '25% increase'),
        (0.30, '30% increase'),
        (0.50, '50% increase'),
        (1.00, '100% increase (double salary)')
    ], default=0.25, validators=[DataRequired()])
    career_field = SelectField('Career Field', choices=[
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('operations', 'Operations'),
        ('consulting', 'Consulting'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    experience_level = SelectField('Experience Level', choices=[
        ('entry', 'Entry Level (0-2 years)'),
        ('mid', 'Mid Level (3-7 years)'),
        ('senior', 'Senior Level (8-15 years)'),
        ('executive', 'Executive Level (15+ years)')
    ], validators=[DataRequired()])
    industry_preference = SelectField('Industry Preference', choices=[
        ('any', 'Any Industry'),
        ('technology', 'Technology'),
        ('finance', 'Finance & Banking'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('retail', 'Retail'),
        ('manufacturing', 'Manufacturing'),
        ('consulting', 'Consulting'),
        ('nonprofit', 'Non-Profit'),
        ('government', 'Government')
    ], default='any')
    company_size_preference = SelectField('Company Size Preference', choices=[
        ('any', 'Any Size'),
        ('startup', 'Startup (1-50 employees)'),
        ('small', 'Small (51-200 employees)'),
        ('mid', 'Medium (201-1000 employees)'),
        ('large', 'Large (1000+ employees)')
    ], default='any')
    equity_required = BooleanField('Equity/Stock Options Required', default=False)
    min_company_rating = SelectField('Minimum Company Rating', choices=[
        (3.0, '3.0+ stars'),
        (3.5, '3.5+ stars'),
        (4.0, '4.0+ stars'),
        (4.5, '4.5+ stars'),
        (0.0, 'No minimum rating')
    ], default=3.0)
    submit = SubmitField('Save Career Preferences')

class EnhancedResumeUploadForm(FlaskForm):
    """Enhanced resume upload form (REFERRAL-GATED)"""
    resume_file = FileField('Upload Resume', validators=[
        FileRequired(message='Please select a resume file'),
        FileAllowed(['pdf', 'doc', 'docx'], message='Only PDF, DOC, and DOCX files are allowed')
    ])
    job_title = StringField('Current/Desired Job Title', validators=[
        DataRequired(message='Job title is required'),
        Length(max=100, message='Job title is too long')
    ])
    years_experience = IntegerField('Years of Experience', validators=[
        DataRequired(message='Years of experience is required'),
        NumberRange(min=0, max=50, message='Please enter a valid number of years')
    ])
    skills_summary = TextAreaField('Key Skills Summary (Optional)', validators=[
        Length(max=1000, message='Skills summary is too long')
    ])
    submit = SubmitField('Upload Resume')

class ApplicationTrackingForm(FlaskForm):
    """Form for tracking job applications (REFERRAL-GATED)"""
    job_title = StringField('Job Title', validators=[
        DataRequired(message='Job title is required'),
        Length(max=100, message='Job title is too long')
    ])
    company_name = StringField('Company Name', validators=[
        DataRequired(message='Company name is required'),
        Length(max=100, message='Company name is too long')
    ])
    application_date = StringField('Application Date', validators=[
        DataRequired(message='Application date is required')
    ])
    application_status = SelectField('Application Status', choices=[
        ('applied', 'Applied'),
        ('under_review', 'Under Review'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offer_received', 'Offer Received'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn')
    ], validators=[DataRequired()])
    salary_offered = IntegerField('Salary Offered (Optional)', validators=[
        Optional(),
        NumberRange(min=20000, max=1000000, message='Please enter a realistic salary amount')
    ])
    notes = TextAreaField('Notes (Optional)', validators=[
        Length(max=1000, message='Notes are too long')
    ])
    submit = SubmitField('Track Application')

class FeatureUnlockForm(FlaskForm):
    """Form for alternative unlock options"""
    unlock_method = SelectField('Unlock Method', choices=[
        ('referral', 'Complete 3 Referrals (Free)'),
        ('premium', 'Upgrade to Premium ($9.99/month)'),
        ('trial', 'Start 7-Day Free Trial')
    ], validators=[DataRequired()])
    submit = SubmitField('Unlock Feature')

class ZipcodeValidationForm(FlaskForm):
    """Form for ZIP code validation and geocoding"""
    zipcode = StringField('ZIP Code', validators=[
        DataRequired(message='ZIP code is required'),
        Length(min=5, max=10, message='Please enter a valid ZIP code')
    ])
    submit = SubmitField('Validate Location')

    def validate_zipcode(self, field):
        """Validate US ZIP code format"""
        zipcode = field.data.strip()
        # Basic US ZIP code pattern (5 digits or 5+4 format)
        if not re.match(r'^\d{5}(-\d{4})?$', zipcode):
            raise ValidationError('Please enter a valid US ZIP code (e.g., 12345 or 12345-6789)')

class ReferralProgressForm(FlaskForm):
    """Form for displaying referral progress"""
    # This form is primarily for display purposes
    current_referrals = IntegerField('Current Successful Referrals', render_kw={'readonly': True})
    referrals_needed = IntegerField('Referrals Needed', render_kw={'readonly': True})
    progress_percentage = IntegerField('Progress Percentage', render_kw={'readonly': True})
    
class JobRecommendationPreferencesForm(FlaskForm):
    """Form for job recommendation preferences (REFERRAL-GATED)"""
    # Location preferences
    zipcode = StringField('ZIP Code', validators=[
        DataRequired(message='ZIP code is required'),
        Length(min=5, max=10, message='Please enter a valid ZIP code')
    ])
    search_radius = SelectField('Search Radius', choices=[
        (10, '10 miles'),
        (25, '25 miles'),
        (50, '50 miles'),
        (100, '100 miles'),
        (200, '200+ miles')
    ], default=25)
    
    # Career preferences
    current_salary = IntegerField('Current Salary', validators=[
        DataRequired(message='Current salary is required'),
        NumberRange(min=20000, max=1000000, message='Please enter a realistic salary')
    ])
    target_increase = SelectField('Target Salary Increase', choices=[
        (0.10, '10%'),
        (0.20, '20%'),
        (0.30, '30%'),
        (0.50, '50%'),
        (1.00, '100%')
    ], default=0.25)
    
    # Job preferences
    career_field = SelectField('Career Field', choices=[
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('marketing', 'Marketing'),
        ('sales', 'Sales'),
        ('operations', 'Operations'),
        ('consulting', 'Consulting')
    ])
    
    experience_level = SelectField('Experience Level', choices=[
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive Level')
    ])
    
    # Additional preferences
    remote_ok = BooleanField('Open to Remote Work', default=True)
    equity_required = BooleanField('Equity Required', default=False)
    min_rating = SelectField('Minimum Company Rating', choices=[
        (3.0, '3.0+'),
        (3.5, '3.5+'),
        (4.0, '4.0+'),
        (4.5, '4.5+')
    ], default=3.0)
    
    submit = SubmitField('Get Job Recommendations')

    def validate_zipcode(self, field):
        """Validate US ZIP code format"""
        zipcode = field.data.strip()
        if not re.match(r'^\d{5}(-\d{4})?$', zipcode):
            raise ValidationError('Please enter a valid US ZIP code')
