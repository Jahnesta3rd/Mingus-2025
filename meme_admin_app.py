#!/usr/bin/env python3
"""
Mingus Personal Finance App - Meme Admin Interface
Simple Flask admin interface for managing memes
"""

import os
import sqlite3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from PIL import Image
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
DB_PATH = 'mingus_memes.db'

# Meme categories as specified in requirements
MEME_CATEGORIES = [
    'faith',
    'work_life', 
    'friendships',
    'children',
    'relationships',
    'going_out'
]

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with meme table if it doesn't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create memes table with original 6 categories
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url TEXT NOT NULL,
            category TEXT NOT NULL CHECK (category IN (
                'faith', 
                'work_life', 
                'friendships', 
                'children', 
                'relationships', 
                'going_out'
            )),
            caption TEXT NOT NULL,
            alt_text TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memes_category ON memes(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memes_active ON memes(is_active)')
    
    # Create trigger for automatic timestamp updates
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS update_memes_timestamp 
            AFTER UPDATE ON memes
            FOR EACH ROW
        BEGIN
            UPDATE memes SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def save_uploaded_file(file):
    """Save uploaded file with secure filename"""
    if file and allowed_file(file.filename):
        # Generate secure filename
        filename = secure_filename(file.filename)
        # Add UUID to prevent conflicts
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)
        
        # Create thumbnail for better performance
        try:
            with Image.open(filepath) as img:
                # Resize if too large
                if img.width > 800 or img.height > 600:
                    img.thumbnail((800, 600), Image.Resampling.LANCZOS)
                    img.save(filepath, optimize=True, quality=85)
        except Exception as e:
            logger.warning(f"Could not optimize image: {e}")
        
        return unique_filename
    return None

@app.route('/')
def index():
    """Main admin dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get meme statistics
    cursor.execute('SELECT COUNT(*) as total FROM memes')
    total_memes = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as active FROM memes WHERE is_active = 1')
    active_memes = cursor.fetchone()['active']
    
    cursor.execute('SELECT category, COUNT(*) as count FROM memes GROUP BY category')
    category_stats = dict(cursor.fetchall())
    
    conn.close()
    
    return render_template('index.html', 
                         total_memes=total_memes,
                         active_memes=active_memes,
                         category_stats=category_stats,
                         categories=MEME_CATEGORIES)

@app.route('/memes')
def list_memes():
    """List all memes in a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all memes with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    cursor.execute('''
        SELECT * FROM memes 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    
    memes = cursor.fetchall()
    
    # Get total count for pagination
    cursor.execute('SELECT COUNT(*) as total FROM memes')
    total = cursor.fetchone()['total']
    
    conn.close()
    
    return render_template('memes_list.html', 
                         memes=memes, 
                         page=page,
                         per_page=per_page,
                         total=total,
                         categories=MEME_CATEGORIES)

@app.route('/memes/add', methods=['GET', 'POST'])
def add_meme():
    """Add new meme"""
    if request.method == 'POST':
        try:
            # Validate form data
            category = request.form.get('category')
            caption = request.form.get('caption', '').strip()
            alt_text = request.form.get('alt_text', '').strip()
            is_active = 'is_active' in request.form
            
            # Validate required fields
            if not category or not caption or not alt_text:
                flash('All fields are required!', 'error')
                return render_template('add_meme.html', categories=MEME_CATEGORIES)
            
            if category not in MEME_CATEGORIES:
                flash('Invalid category selected!', 'error')
                return render_template('add_meme.html', categories=MEME_CATEGORIES)
            
            # Handle file upload
            if 'image' not in request.files:
                flash('No image file selected!', 'error')
                return render_template('add_meme.html', categories=MEME_CATEGORIES)
            
            file = request.files['image']
            if file.filename == '':
                flash('No image file selected!', 'error')
                return render_template('add_meme.html', categories=MEME_CATEGORIES)
            
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > MAX_FILE_SIZE:
                flash(f'File too large! Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB', 'error')
                return render_template('add_meme.html', categories=MEME_CATEGORIES)
            
            # Save file
            filename = save_uploaded_file(file)
            if not filename:
                flash('Invalid file type! Allowed types: PNG, JPG, JPEG, GIF, WEBP', 'error')
                return render_template('add_meme.html', categories=MEME_CATEGORIES)
            
            # Save to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO memes (image_url, category, caption, alt_text, is_active)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, category, caption, alt_text, is_active))
            
            conn.commit()
            conn.close()
            
            flash('Meme added successfully!', 'success')
            return redirect(url_for('list_memes'))
            
        except Exception as e:
            logger.error(f"Error adding meme: {e}")
            flash('Error adding meme. Please try again.', 'error')
            return render_template('add_meme.html', categories=MEME_CATEGORIES)
    
    return render_template('add_meme.html', categories=MEME_CATEGORIES)

@app.route('/memes/<int:meme_id>/edit', methods=['GET', 'POST'])
def edit_meme(meme_id):
    """Edit existing meme"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        try:
            # Validate form data
            category = request.form.get('category')
            caption = request.form.get('caption', '').strip()
            alt_text = request.form.get('alt_text', '').strip()
            is_active = 'is_active' in request.form
            
            # Validate required fields
            if not category or not caption or not alt_text:
                flash('All fields are required!', 'error')
                return redirect(url_for('edit_meme', meme_id=meme_id))
            
            if category not in MEME_CATEGORIES:
                flash('Invalid category selected!', 'error')
                return redirect(url_for('edit_meme', meme_id=meme_id))
            
            # Handle file upload if new file provided
            filename = None
            if 'image' in request.files:
                file = request.files['image']
                if file.filename != '':
                    # Check file size
                    file.seek(0, 2)
                    file_size = file.tell()
                    file.seek(0)
                    
                    if file_size > MAX_FILE_SIZE:
                        flash(f'File too large! Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB', 'error')
                        return redirect(url_for('edit_meme', meme_id=meme_id))
                    
                    filename = save_uploaded_file(file)
                    if not filename:
                        flash('Invalid file type! Allowed types: PNG, JPG, JPEG, GIF, WEBP', 'error')
                        return redirect(url_for('edit_meme', meme_id=meme_id))
            
            # Update database
            if filename:
                # Get old filename to delete
                cursor.execute('SELECT image_url FROM memes WHERE id = ?', (meme_id,))
                old_filename = cursor.fetchone()['image_url']
                
                cursor.execute('''
                    UPDATE memes 
                    SET image_url = ?, category = ?, caption = ?, alt_text = ?, is_active = ?
                    WHERE id = ?
                ''', (filename, category, caption, alt_text, is_active, meme_id))
                
                # Delete old file
                try:
                    old_filepath = os.path.join(UPLOAD_FOLDER, old_filename)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                except Exception as e:
                    logger.warning(f"Could not delete old file: {e}")
            else:
                cursor.execute('''
                    UPDATE memes 
                    SET category = ?, caption = ?, alt_text = ?, is_active = ?
                    WHERE id = ?
                ''', (category, caption, alt_text, is_active, meme_id))
            
            conn.commit()
            conn.close()
            
            flash('Meme updated successfully!', 'success')
            return redirect(url_for('list_memes'))
            
        except Exception as e:
            logger.error(f"Error updating meme: {e}")
            flash('Error updating meme. Please try again.', 'error')
            return redirect(url_for('edit_meme', meme_id=meme_id))
    
    # GET request - show edit form
    cursor.execute('SELECT * FROM memes WHERE id = ?', (meme_id,))
    meme = cursor.fetchone()
    conn.close()
    
    if not meme:
        flash('Meme not found!', 'error')
        return redirect(url_for('list_memes'))
    
    return render_template('edit_meme.html', meme=meme, categories=MEME_CATEGORIES)

@app.route('/memes/<int:meme_id>/delete', methods=['POST'])
def delete_meme(meme_id):
    """Delete meme"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get filename to delete
        cursor.execute('SELECT image_url FROM memes WHERE id = ?', (meme_id,))
        result = cursor.fetchone()
        
        if not result:
            flash('Meme not found!', 'error')
            return redirect(url_for('list_memes'))
        
        filename = result['image_url']
        
        # Delete from database
        cursor.execute('DELETE FROM memes WHERE id = ?', (meme_id,))
        conn.commit()
        conn.close()
        
        # Delete file
        try:
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.warning(f"Could not delete file: {e}")
        
        flash('Meme deleted successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting meme: {e}")
        flash('Error deleting meme. Please try again.', 'error')
    
    return redirect(url_for('list_memes'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/memes')
def api_memes():
    """API endpoint to get memes (for potential frontend integration)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    category = request.args.get('category')
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    
    query = 'SELECT * FROM memes WHERE 1=1'
    params = []
    
    if category and category in MEME_CATEGORIES:
        query += ' AND category = ?'
        params.append(category)
    
    if active_only:
        query += ' AND is_active = 1'
    
    query += ' ORDER BY created_at DESC'
    
    cursor.execute(query, params)
    memes = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify(memes)

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    flash('File too large! Maximum size is 5MB', 'error')
    return redirect(url_for('add_meme'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {e}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Run app
    app.run(debug=True, host='0.0.0.0', port=5001)
