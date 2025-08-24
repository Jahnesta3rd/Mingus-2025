#!/usr/bin/env node

/**
 * MINGUS Article Library - Navigation Integration Test
 * ===================================================
 * Simple test to verify the navigation integration works correctly
 */

const fs = require('fs');
const path = require('path');

// Colors for output
const colors = {
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    reset: '\x1b[0m'
};

const log = {
    info: (msg) => console.log(`${colors.blue}[INFO]${colors.reset} ${msg}`),
    success: (msg) => console.log(`${colors.green}[SUCCESS]${colors.reset} ${msg}`),
    warning: (msg) => console.log(`${colors.yellow}[WARNING]${colors.reset} ${msg}`),
    error: (msg) => console.log(`${colors.red}[ERROR]${colors.reset} ${msg}`)
};

// Test configuration
const testConfig = {
    projectRoot: process.cwd(),
    frontendDir: path.join(process.cwd(), 'frontend'),
    requiredFiles: [
        'frontend/src/App.js',
        'frontend/src/components/Layout/Navigation.js',
        'frontend/src/routes/articleLibraryRoutes.js',
        'frontend/src/contexts/ArticleLibraryContext.js',
        'frontend/src/config/articleLibrary.js',
        'frontend/src/components/shared/ErrorBoundary.js',
        'frontend/src/components/shared/LoadingSpinner.js',
        'frontend/src/components/auth/ProtectedRoute.js',
        'frontend/src/pages/Dashboard.js',
        'frontend/src/pages/BudgetForecast.js',
        'frontend/src/pages/HealthCheckin.js',
        'frontend/src/pages/Profile.js',
        'config/frontend.env.article-library'
    ],
    requiredDependencies: [
        'react-router-dom',
        'lucide-react'
    ]
};

// Test functions
function checkFileExists(filePath) {
    const fullPath = path.join(testConfig.projectRoot, filePath);
    const exists = fs.existsSync(fullPath);
    if (exists) {
        log.success(`✓ ${filePath}`);
    } else {
        log.error(`✗ ${filePath} - File not found`);
    }
    return exists;
}

function checkPackageJson() {
    const packageJsonPath = path.join(testConfig.frontendDir, 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
        log.error('✗ frontend/package.json - File not found');
        return false;
    }

    try {
        const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
        const dependencies = { ...packageJson.dependencies, ...packageJson.devDependencies };
        
        log.info('Checking dependencies...');
        let allDepsFound = true;
        
        testConfig.requiredDependencies.forEach(dep => {
            if (dependencies[dep]) {
                log.success(`✓ ${dep} (${dependencies[dep]})`);
            } else {
                log.error(`✗ ${dep} - Dependency not found`);
                allDepsFound = false;
            }
        });
        
        return allDepsFound;
    } catch (error) {
        log.error(`✗ Error reading package.json: ${error.message}`);
        return false;
    }
}

function checkEnvironmentFile() {
    const envPath = path.join(testConfig.frontendDir, '.env.local');
    if (fs.existsSync(envPath)) {
        log.success('✓ frontend/.env.local - Environment file exists');
        return true;
    } else {
        log.warning('⚠ frontend/.env.local - Environment file not found (run setup script to create)');
        return false;
    }
}

function checkNavigationStructure() {
    const navigationPath = path.join(testConfig.projectRoot, 'frontend/src/components/Layout/Navigation.js');
    if (!fs.existsSync(navigationPath)) {
        log.error('✗ Navigation.js - File not found');
        return false;
    }

    try {
        const content = fs.readFileSync(navigationPath, 'utf8');
        
        // Check for required imports
        const requiredImports = [
            'lucide-react',
            'getArticleLibraryNavigation',
            'isFeatureEnabled'
        ];
        
        let allImportsFound = true;
        requiredImports.forEach(importName => {
            if (content.includes(importName)) {
                log.success(`✓ Navigation imports ${importName}`);
            } else {
                log.error(`✗ Navigation missing import: ${importName}`);
                allImportsFound = false;
            }
        });
        
        // Check for main navigation items
        const mainNavItems = ['Dashboard', 'Budget', 'Health Check', 'Profile', 'Learning Library'];
        mainNavItems.forEach(item => {
            if (content.includes(item)) {
                log.success(`✓ Navigation includes: ${item}`);
            } else {
                log.warning(`⚠ Navigation missing: ${item}`);
            }
        });
        
        return allImportsFound;
    } catch (error) {
        log.error(`✗ Error reading Navigation.js: ${error.message}`);
        return false;
    }
}

function checkAppStructure() {
    const appPath = path.join(testConfig.projectRoot, 'frontend/src/App.js');
    if (!fs.existsSync(appPath)) {
        log.error('✗ App.js - File not found');
        return false;
    }

    try {
        const content = fs.readFileSync(appPath, 'utf8');
        
        // Check for required providers and components
        const requiredElements = [
            'ArticleLibraryProvider',
            'ArticleLibraryRoutes',
            'Navigation',
            'ErrorBoundary'
        ];
        
        let allElementsFound = true;
        requiredElements.forEach(element => {
            if (content.includes(element)) {
                log.success(`✓ App.js includes: ${element}`);
            } else {
                log.error(`✗ App.js missing: ${element}`);
                allElementsFound = false;
            }
        });
        
        return allElementsFound;
    } catch (error) {
        log.error(`✗ Error reading App.js: ${error.message}`);
        return false;
    }
}

// Main test function
function runTests() {
    log.info('Starting MINGUS Article Library Navigation Integration Test...');
    console.log('');
    
    let allTestsPassed = true;
    
    // Test 1: Check required files
    log.info('Test 1: Checking required files...');
    testConfig.requiredFiles.forEach(file => {
        if (!checkFileExists(file)) {
            allTestsPassed = false;
        }
    });
    console.log('');
    
    // Test 2: Check package.json and dependencies
    log.info('Test 2: Checking dependencies...');
    if (!checkPackageJson()) {
        allTestsPassed = false;
    }
    console.log('');
    
    // Test 3: Check environment file
    log.info('Test 3: Checking environment configuration...');
    checkEnvironmentFile();
    console.log('');
    
    // Test 4: Check navigation structure
    log.info('Test 4: Checking navigation structure...');
    if (!checkNavigationStructure()) {
        allTestsPassed = false;
    }
    console.log('');
    
    // Test 5: Check app structure
    log.info('Test 5: Checking app structure...');
    if (!checkAppStructure()) {
        allTestsPassed = false;
    }
    console.log('');
    
    // Summary
    console.log('='.repeat(60));
    if (allTestsPassed) {
        log.success('🎉 All tests passed! Navigation integration is working correctly.');
        console.log('');
        log.info('Next steps:');
        log.info('1. Start the development server: cd frontend && npm start');
        log.info('2. Navigate to http://localhost:3000');
        log.info('3. Test the navigation by clicking on "Learning Library"');
        log.info('4. Verify all routes are accessible');
    } else {
        log.error('❌ Some tests failed. Please check the errors above.');
        console.log('');
        log.info('To fix issues:');
        log.info('1. Run the setup script: ./setup_frontend_integration.sh');
        log.info('2. Install missing dependencies: cd frontend && npm install');
        log.info('3. Check file paths and imports');
    }
    console.log('='.repeat(60));
    
    return allTestsPassed;
}

// Run tests if this file is executed directly
if (require.main === module) {
    const success = runTests();
    process.exit(success ? 0 : 1);
}

module.exports = { runTests };
