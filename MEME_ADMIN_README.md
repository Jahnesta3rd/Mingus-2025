# Meme Admin Interface

A simple Flask admin interface for managing memes in the Mingus personal finance app.

## Features

### 1. Web Form for Uploading New Memes
- **File Upload**: Supports PNG, JPG, JPEG, GIF, and WEBP formats
- **Category Selection**: Dropdown with categories (faith, work_life, friendships, children, relationships, going_out)
- **Caption**: Text field for meme caption
- **Alt Text**: Text field for accessibility
- **Active/Inactive Status**: Checkbox to control visibility
- **Priority**: Dropdown (1-10) to control display frequency
- **Tags**: Optional comma-separated tags
- **Source Attribution**: Credit to original creator
- **Admin Notes**: Internal notes not visible to users

### 2. Meme Listing Page
- **Thumbnail Images**: Shows preview of each meme
- **Category Badges**: Color-coded category labels
- **Truncated Captions**: Shows first part of caption with full text on hover
- **Status Indicators**: Active/Inactive badges
- **Action Buttons**: View, Edit, Toggle Status, Delete
- **Statistics Cards**: Total memes, active/inactive counts, categories

### 3. CRUD Operations
- **Create**: Add new memes with image upload
- **Read**: View all memes in table format and individual meme details
- **Update**: Edit existing memes with optional image replacement
- **Delete**: Remove memes with confirmation

### 4. File Handling
- **File Validation**: Checks for allowed image formats
- **Secure Filenames**: Uses `secure_filename()` and adds unique identifiers
- **Upload Directory**: Saves to `backend/static/uploads/memes/`
- **Web-Friendly URLs**: Generates accessible file paths

## Security Features

- **File Type Validation**: Only allows image files
- **Secure Filenames**: Prevents path traversal attacks
- **Unique File Names**: Prevents filename conflicts
- **Admin Authentication**: Simple login system (demo credentials)
- **CSRF Protection**: Form-based security
- **Input Validation**: Server-side validation of all inputs

## Installation & Setup

1. **Access the Admin Interface**:
   ```
   http://localhost:5000/admin/memes/login
   ```

2. **Login Credentials** (Demo):
   - Username: `admin`
   - Password: `admin123`

3. **Upload Directory**:
   The system automatically creates the upload directory at:
   ```
   backend/static/uploads/memes/
   ```

## Usage

### Adding a New Meme
1. Click "Add New Meme" button
2. Upload an image file
3. Select a category from the dropdown
4. Enter caption and alt text
5. Set priority and other optional fields
6. Check "Active" to make it visible to users
7. Click "Create Meme"

### Editing a Meme
1. Click the "Edit" button on any meme
2. Modify any fields as needed
3. Optionally upload a new image (keeps existing if none selected)
4. Click "Update Meme"

### Managing Meme Status
- Use the toggle button to quickly activate/deactivate memes
- Inactive memes won't be shown to users but remain in the database

### Deleting Memes
1. Click the "Delete" button
2. Confirm the deletion
3. Meme is permanently removed from the database

## File Structure

```
backend/
├── routes/
│   └── meme_admin.py          # Admin routes and logic
├── templates/
│   └── admin/
│       └── memes/
│           ├── base.html      # Base template with navigation
│           ├── index.html     # Meme listing page
│           ├── create.html    # Add new meme form
│           ├── edit.html      # Edit meme form
│           ├── show.html      # View meme details
│           └── login.html     # Admin login page
├── static/
│   └── uploads/
│       └── memes/             # Uploaded meme images
└── models/
    └── meme_models.py         # Meme database model
```

## Categories

The system supports these meme categories:
- **faith**: Religious/spiritual content
- **work_life**: Work-life balance memes
- **friendships**: Friendship-related content
- **children**: Parenting and family memes
- **relationships**: Relationship advice and humor
- **going_out**: Social activities and entertainment

## Styling

The interface uses:
- **Bootstrap 5.3.0**: For responsive design and components
- **Font Awesome 6.0.0**: For icons
- **Custom CSS**: For admin-specific styling
- **Responsive Design**: Works on desktop and mobile devices

## Error Handling

- **File Upload Errors**: Validates file types and sizes
- **Database Errors**: Graceful handling with user-friendly messages
- **Validation Errors**: Form validation with helpful error messages
- **Flash Messages**: Success/error notifications that auto-dismiss

## Production Considerations

1. **Replace Demo Authentication**: Implement proper user authentication
2. **File Storage**: Consider using cloud storage (AWS S3, etc.) for production
3. **Image Optimization**: Add image resizing and compression
4. **Rate Limiting**: Add upload rate limiting
5. **Backup Strategy**: Implement regular database backups
6. **Monitoring**: Add logging and monitoring for admin actions

## API Endpoints

- `GET /admin/memes/` - List all memes
- `GET /admin/memes/create` - Show create form
- `POST /admin/memes/create` - Create new meme
- `GET /admin/memes/<id>` - View meme details
- `GET /admin/memes/<id>/edit` - Show edit form
- `POST /admin/memes/<id>/edit` - Update meme
- `POST /admin/memes/<id>/delete` - Delete meme
- `POST /admin/memes/<id>/toggle-status` - Toggle active status
- `GET /admin/memes/login` - Show login form
- `POST /admin/memes/login` - Process login

This admin interface provides a complete solution for managing memes in your personal finance app with a beginner-friendly interface and robust security features.
