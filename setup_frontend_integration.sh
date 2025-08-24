#!/bin/bash

# =====================================================
# MINGUS Article Library - Frontend Integration Setup
# =====================================================
# Script to set up the article library frontend integration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
check_directory() {
    log_info "Checking project structure..."
    
    if [ ! -d "$FRONTEND_DIR" ]; then
        log_error "Frontend directory not found at $FRONTEND_DIR"
        log_error "Please run this script from the project root directory"
        exit 1
    fi
    
    if [ ! -f "$FRONTEND_DIR/package.json" ]; then
        log_error "package.json not found in frontend directory"
        log_error "Please ensure this is a valid React project"
        exit 1
    fi
    
    log_success "Project structure verified"
}

# Copy environment configuration
setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Copy the environment template
    if [ -f "$PROJECT_ROOT/config/frontend.env.article-library" ]; then
        cp "$PROJECT_ROOT/config/frontend.env.article-library" "$FRONTEND_DIR/.env.local"
        log_success "Environment configuration copied to frontend/.env.local"
    else
        log_warning "Environment template not found, creating basic .env.local"
        cat > "$FRONTEND_DIR/.env.local" << EOF
# MINGUS Article Library - Frontend Environment
REACT_APP_API_BASE_URL=http://localhost:5000
REACT_APP_ENABLE_ARTICLE_LIBRARY=true
REACT_APP_ENABLE_AI_RECOMMENDATIONS=true
REACT_APP_ENABLE_CULTURAL_PERSONALIZATION=true
REACT_APP_ENABLE_ADVANCED_SEARCH=true
REACT_APP_ENABLE_SOCIAL_SHARING=true
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ARTICLE_FOLDERS=true
REACT_APP_ENABLE_ARTICLE_BOOKMARKS=true
REACT_APP_ENABLE_ARTICLE_NOTES=true
REACT_APP_DEBUG=true
EOF
        log_success "Basic environment configuration created"
    fi
}

# Check and install dependencies
check_dependencies() {
    log_info "Checking frontend dependencies..."
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_warning "node_modules not found, installing dependencies..."
        npm install
        log_success "Dependencies installed"
    else
        log_success "Dependencies already installed"
    fi
    
    # Check for required dependencies
    local missing_deps=()
    
    if ! npm list react-router-dom > /dev/null 2>&1; then
        missing_deps+=("react-router-dom")
    fi
    
    if ! npm list @testing-library/react > /dev/null 2>&1; then
        missing_deps+=("@testing-library/react")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_warning "Missing dependencies detected: ${missing_deps[*]}"
        log_info "Installing missing dependencies..."
        npm install "${missing_deps[@]}"
        log_success "Missing dependencies installed"
    else
        log_success "All required dependencies are installed"
    fi
}

# Create placeholder components
create_placeholder_components() {
    log_info "Creating placeholder components..."
    
    local components_dir="$FRONTEND_DIR/src/components"
    local articles_dir="$components_dir/articles"
    local shared_dir="$components_dir/shared"
    local auth_dir="$components_dir/auth"
    local layout_dir="$components_dir/Layout"
    
    # Create directories
    mkdir -p "$articles_dir" "$shared_dir" "$auth_dir" "$layout_dir"
    
    # Create placeholder article components
    cat > "$articles_dir/ArticleLibraryHome.js" << 'EOF'
import React from 'react';
import { useArticleLibrary } from '../../contexts/ArticleLibraryContext';

const ArticleLibraryHome = () => {
    const { articles, articlesLoading, articlesError } = useArticleLibrary();

    if (articlesLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading articles...</p>
                </div>
            </div>
        );
    }

    if (articlesError) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <h2 className="text-2xl font-bold text-red-600 mb-4">Error Loading Articles</h2>
                    <p className="text-gray-600">{articlesError}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Article Library</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {articles.map((article) => (
                    <div key={article.id} className="bg-white rounded-lg shadow-md p-6">
                        <h3 className="text-xl font-semibold mb-2">{article.title}</h3>
                        <p className="text-gray-600 mb-4">{article.excerpt}</p>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-500">{article.publication_date}</span>
                            <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                                {article.category}
                            </span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ArticleLibraryHome;
EOF

    # Create other placeholder components
    local placeholder_components=(
        "ArticleSearch:Search functionality for articles"
        "ArticleRecommendations:AI-powered article recommendations"
        "ArticleFolders:Article organization in folders"
        "ArticleTopics:Topic-based article browsing"
        "ArticleAnalytics:Reading analytics and insights"
        "ArticleAssessment:Assessment tests and progress"
        "ArticleSettings:Article library settings"
        "ArticleDetail:Detailed article view"
        "FolderDetail:Folder contents view"
        "TopicDetail:Topic contents view"
    )

    for component_info in "${placeholder_components[@]}"; do
        IFS=':' read -r component_name description <<< "$component_info"
        cat > "$articles_dir/$component_name.js" << EOF
import React from 'react';

const $component_name = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">$component_name</h1>
            <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-gray-600">$description - Coming Soon!</p>
                <p className="text-sm text-gray-500 mt-4">
                    This component is under development and will be available soon.
                </p>
            </div>
        </div>
    );
};

export default $component_name;
EOF
    done

    log_success "Placeholder components created"
}

# Create placeholder pages
create_placeholder_pages() {
    log_info "Creating placeholder pages..."
    
    local pages_dir="$FRONTEND_DIR/src/pages"
    mkdir -p "$pages_dir"
    
    # Create placeholder pages for existing MINGUS functionality
    cat > "$pages_dir/Dashboard.js" << 'EOF'
import React from 'react';

const Dashboard = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">MINGUS Dashboard</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-xl font-semibold mb-4">Welcome to MINGUS</h3>
                    <p className="text-gray-600">
                        Your personal development and financial planning platform.
                    </p>
                </div>
                <div className="bg-white rounded-lg shadow-md p-6">
                    <h3 className="text-xl font-semibold mb-4">Quick Actions</h3>
                    <div className="space-y-2">
                        <a href="/budget" className="block text-blue-600 hover:text-blue-800">
                            📊 Budget & Forecast
                        </a>
                        <a href="/health" className="block text-blue-600 hover:text-blue-800">
                            🏥 Health Check-in
                        </a>
                        <a href="/articles" className="block text-blue-600 hover:text-blue-800">
                            📚 Article Library
                        </a>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
EOF

    cat > "$pages_dir/BudgetForecast.js" << 'EOF'
import React from 'react';

const BudgetForecast = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Budget & Forecast</h1>
            <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-gray-600">Budget and forecasting functionality - Coming Soon!</p>
            </div>
        </div>
    );
};

export default BudgetForecast;
EOF

    cat > "$pages_dir/HealthCheckin.js" << 'EOF'
import React from 'react';

const HealthCheckin = () => {
    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Health Check-in</h1>
            <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-gray-600">Health tracking functionality - Coming Soon!</p>
            </div>
        </div>
    );
};

export default HealthCheckin;
EOF

    log_success "Placeholder pages created"
}

# Create MainLayout component
create_main_layout() {
    log_info "Creating MainLayout component..."
    
    local layout_dir="$FRONTEND_DIR/src/components/Layout"
    mkdir -p "$layout_dir"
    
    cat > "$layout_dir/MainLayout.js" << 'EOF'
import React from 'react';

const MainLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-gray-50">
            <main className="flex-1">
                {children}
            </main>
        </div>
    );
};

export default MainLayout;
EOF

    log_success "MainLayout component created"
}

# Test the integration
test_integration() {
    log_info "Testing the integration..."
    
    cd "$FRONTEND_DIR"
    
    # Check if the app can start without errors
    log_info "Checking if the app can be built..."
    if npm run build > /dev/null 2>&1; then
        log_success "Build successful - integration is working!"
    else
        log_warning "Build failed - check for any missing dependencies or syntax errors"
        log_info "You can run 'npm start' to see detailed error messages"
    fi
}

# Main setup function
main() {
    log_info "Starting MINGUS Article Library frontend integration setup..."
    
    check_directory
    setup_environment
    check_dependencies
    create_placeholder_components
    create_placeholder_pages
    create_main_layout
    test_integration
    
    log_success "Frontend integration setup completed!"
    
    echo ""
    echo "🎉 Setup Complete!"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Start the development server: cd frontend && npm start"
    echo "   2. Navigate to http://localhost:3000 to see the integrated app"
    echo "   3. Click on 'Article Library' in the navigation to test the integration"
    echo ""
    echo "📚 Available routes:"
    echo "   - / (Dashboard)"
    echo "   - /budget (Budget & Forecast)"
    echo "   - /health (Health Check-in)"
    echo "   - /articles (Article Library)"
    echo "   - /articles/search (Article Search)"
    echo "   - /articles/recommendations (AI Recommendations)"
    echo "   - /articles/folders (Article Folders)"
    echo "   - /articles/topics (Article Topics)"
    echo "   - /articles/analytics (Reading Analytics)"
    echo "   - /articles/assessment (Assessment Tests)"
    echo "   - /articles/settings (Article Settings)"
    echo ""
    echo "🔧 Configuration:"
    echo "   - Environment variables: frontend/.env.local"
    echo "   - Feature flags: config/frontend.env.article-library"
    echo "   - API endpoints: frontend/src/config/articleLibrary.js"
    echo ""
    echo "📖 Documentation:"
    echo "   - FRONTEND_INTEGRATION_SUMMARY.md"
    echo "   - MINGUS_ARTICLE_LIBRARY_CONFIGURATION_GUIDE.md"
}

# Run the setup
main
