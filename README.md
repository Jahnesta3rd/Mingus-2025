# Personal Finance Application

A web-based personal finance application with Python backend and vanilla JavaScript frontend.

## Project Structure
```
.
├── backend/
│   ├── src/
│   │   ├── models/      # Database models
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   ├── utils/       # Helper functions
│   │   └── config/      # Configuration files
│   └── tests/           # Backend tests
├── frontend/
│   ├── src/
│   │   ├── js/          # JavaScript files
│   │   ├── css/         # Stylesheets
│   │   └── components/  # Reusable UI components
│   └── public/
│       ├── images/      # Image assets
│       └── icons/       # Icon assets
├── requirements.txt     # Python dependencies
└── .gitignore          # Git ignore file
```

## Setup Instructions

### Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Setup
1. Open the `frontend/index.html` file in your browser
2. For development, you can use a local server:
   ```bash
   python -m http.server 8000
   ```

## Features
- Expense tracking
- Income management
- Budget planning
- Financial reports and analytics
- Category-based organization
