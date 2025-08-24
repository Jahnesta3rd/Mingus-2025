"""
Meme Admin Interface Routes
Flask admin routes for managing memes in the personal finance app.
"""

import os
import uuid
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_cors import cross_origin
from functools import wraps
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from ..services.meme_service import MemeService
from ..models.meme_models import Meme

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
meme_admin_bp = Blueprint('meme_admin', __name__, url_prefix='/admin/memes')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Meme categories
MEME_CATEGORIES = [
    'faith', 'work_life', 'friendships', 'children', 'relationships', 'going_out'
]

def get_db_session() -> Session:
    """Get database session"""
    return current_app.db.session

def require_admin():
    """Decorator to require admin authentication"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # In a real app, you'd check for admin role
            # For now, we'll use a simple session check
            user_id = request.cookies.get('user_id') or request.args.get('user_id')
            if not user_id:
                flash('Admin access required', 'error')
                return redirect(url_for('meme_admin.login'))
            return f(*args, **kwargs)
        return wrapper
    return decorator

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file and return the file path"""
    if file and allowed_file(file.filename):
        # Generate secure filename
        filename = secure_filename(file.filename)
        # Add unique identifier to prevent conflicts
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create uploads directory if it doesn't exist
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'memes')
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Return relative path for web access
        return f'/static/uploads/memes/{unique_filename}'
    
    return None

# Admin Routes

@meme_admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Simple admin login (for demo purposes)"""
    if request.method == 'POST':
        # Simple demo authentication - in production, use proper auth
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Demo credentials (replace with proper authentication)
        if username == 'admin' and password == 'admin123':
            response = redirect(url_for('meme_admin.index'))
            response.set_cookie('user_id', 'admin', max_age=3600)  # 1 hour
            return response
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/memes/login.html')

@meme_admin_bp.route('/')
@require_admin()
def index():
    """Display list of all memes"""
    try:
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        # Get all memes
        memes = meme_service.get_all_memes()
        
        return render_template('admin/memes/index.html', 
                             memes=memes, 
                             categories=MEME_CATEGORIES)
    except Exception as e:
        logger.error(f"Error loading memes: {str(e)}")
        flash('Error loading memes', 'error')
        return render_template('admin/memes/index.html', 
                             memes=[], 
                             categories=MEME_CATEGORIES)

@meme_admin_bp.route('/create', methods=['GET', 'POST'])
@require_admin()
def create():
    """Create a new meme"""
    if request.method == 'POST':
        try:
            db_session = get_db_session()
            meme_service = MemeService(db_session)
            
            # Handle file upload
            image_file = request.files.get('image')
            if not image_file:
                flash('Image file is required', 'error')
                return render_template('admin/memes/create.html', 
                                     categories=MEME_CATEGORIES)
            
            # Save uploaded file
            image_path = save_uploaded_file(image_file)
            if not image_path:
                flash('Invalid file type. Please upload a valid image.', 'error')
                return render_template('admin/memes/create.html', 
                                     categories=MEME_CATEGORIES)
            
            # Prepare meme data
            meme_data = {
                'image_url': image_path,
                'image_file_path': image_path,
                'category': request.form.get('category'),
                'caption_text': request.form.get('caption', ''),
                'alt_text': request.form.get('alt_text', ''),
                'is_active': 'is_active' in request.form,
                'priority': int(request.form.get('priority', 5)),
                'tags': request.form.get('tags', ''),
                'source_attribution': request.form.get('source_attribution', ''),
                'admin_notes': request.form.get('admin_notes', '')
            }
            
            # Validate required fields
            if not meme_data['category'] or not meme_data['caption_text']:
                flash('Category and caption are required', 'error')
                return render_template('admin/memes/create.html', 
                                     categories=MEME_CATEGORIES)
            
            # Create meme
            meme = meme_service.create_meme(meme_data)
            
            flash(f'Meme "{meme.caption_text[:50]}..." created successfully!', 'success')
            return redirect(url_for('meme_admin.index'))
            
        except Exception as e:
            logger.error(f"Error creating meme: {str(e)}")
            flash('Error creating meme', 'error')
            return render_template('admin/memes/create.html', 
                                 categories=MEME_CATEGORIES)
    
    return render_template('admin/memes/create.html', 
                         categories=MEME_CATEGORIES)

@meme_admin_bp.route('/<meme_id>')
@require_admin()
def show(meme_id):
    """Display a single meme"""
    try:
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        meme = meme_service.get_meme_by_id(meme_id)
        if not meme:
            flash('Meme not found', 'error')
            return redirect(url_for('meme_admin.index'))
        
        return render_template('admin/memes/show.html', 
                             meme=meme, 
                             categories=MEME_CATEGORIES)
    except Exception as e:
        logger.error(f"Error loading meme: {str(e)}")
        flash('Error loading meme', 'error')
        return redirect(url_for('meme_admin.index'))

@meme_admin_bp.route('/<meme_id>/edit', methods=['GET', 'POST'])
@require_admin()
def edit(meme_id):
    """Edit a meme"""
    try:
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        meme = meme_service.get_meme_by_id(meme_id)
        if not meme:
            flash('Meme not found', 'error')
            return redirect(url_for('meme_admin.index'))
        
        if request.method == 'POST':
            # Handle file upload if new image provided
            image_file = request.files.get('image')
            image_path = meme.image_url  # Keep existing image by default
            
            if image_file and image_file.filename:
                new_image_path = save_uploaded_file(image_file)
                if new_image_path:
                    image_path = new_image_path
                else:
                    flash('Invalid file type. Please upload a valid image.', 'error')
                    return render_template('admin/memes/edit.html', 
                                         meme=meme, 
                                         categories=MEME_CATEGORIES)
            
            # Update meme data
            meme.category = request.form.get('category', meme.category)
            meme.caption_text = request.form.get('caption', meme.caption_text)
            meme.alt_text = request.form.get('alt_text', meme.alt_text)
            meme.is_active = 'is_active' in request.form
            meme.priority = int(request.form.get('priority', meme.priority))
            meme.tags = request.form.get('tags', meme.tags)
            meme.source_attribution = request.form.get('source_attribution', meme.source_attribution)
            meme.admin_notes = request.form.get('admin_notes', meme.admin_notes)
            meme.image_url = image_path
            meme.image_file_path = image_path
            meme.updated_at = datetime.utcnow()
            
            # Validate required fields
            if not meme.category or not meme.caption_text:
                flash('Category and caption are required', 'error')
                return render_template('admin/memes/edit.html', 
                                     meme=meme, 
                                     categories=MEME_CATEGORIES)
            
            # Save changes
            db_session.commit()
            
            flash(f'Meme "{meme.caption_text[:50]}..." updated successfully!', 'success')
            return redirect(url_for('meme_admin.index'))
        
        return render_template('admin/memes/edit.html', 
                             meme=meme, 
                             categories=MEME_CATEGORIES)
    except Exception as e:
        logger.error(f"Error editing meme: {str(e)}")
        flash('Error editing meme', 'error')
        return redirect(url_for('meme_admin.index'))

@meme_admin_bp.route('/<meme_id>/delete', methods=['POST'])
@require_admin()
def delete(meme_id):
    """Delete a meme"""
    try:
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        meme = meme_service.get_meme_by_id(meme_id)
        if not meme:
            flash('Meme not found', 'error')
            return redirect(url_for('meme_admin.index'))
        
        # Delete the meme
        db_session.delete(meme)
        db_session.commit()
        
        flash(f'Meme "{meme.caption_text[:50]}..." deleted successfully!', 'success')
        return redirect(url_for('meme_admin.index'))
    except Exception as e:
        logger.error(f"Error deleting meme: {str(e)}")
        flash('Error deleting meme', 'error')
        return redirect(url_for('meme_admin.index'))

@meme_admin_bp.route('/<meme_id>/toggle-status', methods=['POST'])
@require_admin()
def toggle_status(meme_id):
    """Toggle meme active/inactive status"""
    try:
        db_session = get_db_session()
        meme_service = MemeService(db_session)
        
        meme = meme_service.get_meme_by_id(meme_id)
        if not meme:
            return jsonify({'error': 'Meme not found'}), 404
        
        meme.is_active = not meme.is_active
        meme.updated_at = datetime.utcnow()
        db_session.commit()
        
        status = 'active' if meme.is_active else 'inactive'
        return jsonify({
            'success': True,
            'status': status,
            'message': f'Meme is now {status}'
        })
    except Exception as e:
        logger.error(f"Error toggling meme status: {str(e)}")
        return jsonify({'error': 'Error updating status'}), 500

# Error handlers
@meme_admin_bp.errorhandler(404)
def meme_not_found(error):
    flash('Meme not found', 'error')
    return redirect(url_for('meme_admin.index'))

@meme_admin_bp.errorhandler(500)
def internal_error(error):
    db_session = get_db_session()
    db_session.rollback()
    flash('Internal server error', 'error')
    return redirect(url_for('meme_admin.index'))
