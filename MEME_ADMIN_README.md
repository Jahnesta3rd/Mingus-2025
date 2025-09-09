# Mingus Meme Admin Interface

A simple Flask admin interface for managing memes in the Mingus personal finance app. This interface provides a user-friendly way to upload, edit, and manage memes with proper file handling and security features.

## 🚀 Features

### ✅ Core Functionality
- **Web Form Upload**: Upload new memes with image, category, caption, alt text, and status
- **Meme Listing**: View all memes in a responsive table with thumbnails
- **CRUD Operations**: Create, Read, Update, Delete memes
- **File Handling**: Secure image upload with validation and optimization
- **Category Management**: Support for 6 predefined categories

### 🎨 User Interface
- **Bootstrap Styling**: Modern, responsive design
- **Image Previews**: Real-time preview of uploaded images
- **Character Counters**: Live feedback for text fields
- **Filtering & Search**: Filter by category, status, and search text
- **Pagination**: Handle large numbers of memes efficiently

### 🔒 Security Features
- **File Validation**: Check file types and sizes
- **Secure Filenames**: Generate unique, safe filenames
- **Input Sanitization**: Validate all form inputs
- **Error Handling**: Graceful error handling and user feedback

## 📋 Requirements

### System Requirements
- Python 3.7 or higher
- SQLite database support
- File system write permissions

### Python Dependencies
```
Flask==2.3.3
Werkzeug==2.3.7
Pillow==10.0.1
```

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements_meme_admin.txt
```

### 2. Run the Application
```bash
python meme_admin_app.py
```

### 3. Access the Interface
Open your browser and navigate to:
```
http://localhost:5000
```

## 📁 File Structure

```
├── meme_admin_app.py          # Main Flask application
├── templates/                 # HTML templates
│   ├── base.html             # Base template with Bootstrap
│   ├── index.html            # Dashboard page
│   ├── memes_list.html       # Meme listing page
│   ├── add_meme.html         # Add new meme form
│   ├── edit_meme.html        # Edit existing meme form
│   ├── 404.html              # 404 error page
│   └── 500.html              # 500 error page
├── static/                   # Static files
│   └── uploads/              # Uploaded meme images
├── requirements_meme_admin.txt # Python dependencies
└── MEME_ADMIN_README.md      # This documentation
```

## 🎯 Usage Guide

### Dashboard
- View meme statistics and category breakdown
- Quick access to common actions
- System information and status

### Adding Memes
1. Click "Add New Meme" button
2. Upload an image file (PNG, JPG, JPEG, GIF, WEBP)
3. Select a category from the dropdown
4. Enter caption and alt text
5. Set active/inactive status
6. Click "Add Meme"

### Managing Memes
- **View All**: Browse all memes in a table format
- **Filter**: Filter by category or status
- **Search**: Search by caption or alt text
- **Edit**: Click edit button to modify meme details
- **Delete**: Click delete button to remove memes

### Categories
The system supports 6 predefined categories:
- **Faith**: Religious/spiritual financial struggles
- **Work Life**: Work-related financial challenges
- **Friendships**: Social spending and friend expenses
- **Children**: Parenting and child-related costs
- **Relationships**: Dating, marriage, relationship expenses
- **Going Out**: Entertainment and social activities

## 🔧 Configuration

### Environment Variables
```bash
# Optional: Set a secure secret key
export SECRET_KEY="your-secret-key-here"

# Optional: Custom database path
export MINGUS_MEME_DB_PATH="/path/to/custom/database.db"
```

### File Upload Settings
- **Max File Size**: 5MB
- **Allowed Formats**: PNG, JPG, JPEG, GIF, WEBP
- **Storage Location**: `static/uploads/`
- **Image Optimization**: Automatic resizing and compression

## 🗄️ Database Schema

The application uses SQLite with the following schema:

```sql
CREATE TABLE memes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'faith', 'work_life', 'friendships', 
        'children', 'relationships', 'going_out'
    )),
    caption TEXT NOT NULL,
    alt_text TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## 🔌 API Endpoints

### REST API
- `GET /api/memes` - Get all memes (JSON)
- `GET /api/memes?category=faith` - Filter by category
- `GET /api/memes?active_only=true` - Get only active memes

### Web Interface
- `GET /` - Dashboard
- `GET /memes` - List all memes
- `GET /memes/add` - Add new meme form
- `POST /memes/add` - Submit new meme
- `GET /memes/<id>/edit` - Edit meme form
- `POST /memes/<id>/edit` - Update meme
- `POST /memes/<id>/delete` - Delete meme

## 🚀 Production Deployment

### Security Considerations
1. **Change Secret Key**: Set a strong, unique secret key
2. **File Permissions**: Ensure proper file system permissions
3. **Database Security**: Use proper database access controls
4. **HTTPS**: Use HTTPS in production
5. **Input Validation**: All inputs are validated and sanitized

### Production Setup
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 meme_admin_app:app
```

### Environment Configuration
```bash
# Production environment variables
export FLASK_ENV=production
export SECRET_KEY="your-production-secret-key"
export MINGUS_MEME_DB_PATH="/var/lib/mingus/memes.db"
```

## 🐛 Troubleshooting

### Common Issues

**File Upload Errors**
- Check file size (max 5MB)
- Verify file format (PNG, JPG, JPEG, GIF, WEBP)
- Ensure write permissions on uploads directory

**Database Errors**
- Verify SQLite database file permissions
- Check database file path configuration
- Ensure database directory exists

**Image Display Issues**
- Check file paths in uploads directory
- Verify image file integrity
- Check web server static file serving

### Debug Mode
To enable debug mode for development:
```python
app.run(debug=True)
```

## 📊 Performance Considerations

- **Image Optimization**: Automatic resizing and compression
- **Database Indexing**: Optimized queries with proper indexes
- **File Caching**: Browser caching for uploaded images
- **Pagination**: Efficient handling of large meme collections

## 🔄 Integration with Existing System

This admin interface is designed to work with the existing Mingus meme system:

1. **Database Compatibility**: Uses the same SQLite database schema
2. **Category Support**: Supports the original 6 categories
3. **API Integration**: Provides JSON API for frontend integration
4. **File Management**: Manages images in the standard uploads directory

## 📝 License

This admin interface is part of the Mingus Personal Finance Application.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the error logs
3. Verify file permissions and database access
4. Test with different file types and sizes

---

**Note**: This is a beginner-friendly interface designed for easy meme management. All operations include proper error handling and user feedback.
