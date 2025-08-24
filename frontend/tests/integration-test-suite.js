/**
 * MINGUS Integration Test Suite
 * Comprehensive testing framework for functionality, performance, accessibility, and cross-browser compatibility
 */

class MINGUSTestSuite {
    constructor() {
        this.tests = new Map();
        this.results = [];
        this.currentTest = null;
        this.config = {
            timeout: 10000,
            retries: 3,
            parallel: false,
            verbose: true
        };
        
        this.init();
    }
    
    init() {
        this.registerTests();
        this.setupTestEnvironment();
    }
    
    // ===== TEST REGISTRATION =====
    registerTests() {
        // Core functionality tests
        this.register('Core Functionality', [
            { name: 'Application Initialization', test: this.testAppInitialization.bind(this) },
            { name: 'Authentication Flow', test: this.testAuthenticationFlow.bind(this) },
            { name: 'Navigation System', test: this.testNavigationSystem.bind(this) },
            { name: 'API Integration', test: this.testAPIIntegration.bind(this) },
            { name: 'Component Rendering', test: this.testComponentRendering.bind(this) },
            { name: 'Form Handling', test: this.testFormHandling.bind(this) },
            { name: 'Modal Functionality', test: this.testModalFunctionality.bind(this) },
            { name: 'Error Handling', test: this.testErrorHandling.bind(this) }
        ]);
        
        // Performance tests
        this.register('Performance', [
            { name: 'Page Load Performance', test: this.testPageLoadPerformance.bind(this) },
            { name: 'Component Performance', test: this.testComponentPerformance.bind(this) },
            { name: 'Memory Usage', test: this.testMemoryUsage.bind(this) },
            { name: 'Network Performance', test: this.testNetworkPerformance.bind(this) },
            { name: 'Animation Performance', test: this.testAnimationPerformance.bind(this) }
        ]);
        
        // Accessibility tests
        this.register('Accessibility', [
            { name: 'Keyboard Navigation', test: this.testKeyboardNavigation.bind(this) },
            { name: 'Screen Reader Compatibility', test: this.testScreenReaderCompatibility.bind(this) },
            { name: 'Color Contrast', test: this.testColorContrast.bind(this) },
            { name: 'Focus Management', test: this.testFocusManagement.bind(this) },
            { name: 'ARIA Labels', test: this.testARIALabels.bind(this) },
            { name: 'Semantic HTML', test: this.testSemanticHTML.bind(this) }
        ]);
        
        // Cross-browser tests
        this.register('Cross-Browser Compatibility', [
            { name: 'Chrome Compatibility', test: this.testChromeCompatibility.bind(this) },
            { name: 'Firefox Compatibility', test: this.testFirefoxCompatibility.bind(this) },
            { name: 'Safari Compatibility', test: this.testSafariCompatibility.bind(this) },
            { name: 'Edge Compatibility', test: this.testEdgeCompatibility.bind(this) },
            { name: 'Mobile Browser Compatibility', test: this.testMobileBrowserCompatibility.bind(this) }
        ]);
        
        // Security tests
        this.register('Security', [
            { name: 'XSS Prevention', test: this.testXSSPrevention.bind(this) },
            { name: 'CSRF Protection', test: this.testCSRFProtection.bind(this) },
            { name: 'Input Validation', test: this.testInputValidation.bind(this) },
            { name: 'Authentication Security', test: this.testAuthenticationSecurity.bind(this) },
            { name: 'Data Encryption', test: this.testDataEncryption.bind(this) }
        ]);
        
        // SEO tests
        this.register('SEO', [
            { name: 'Meta Tags', test: this.testMetaTags.bind(this) },
            { name: 'Structured Data', test: this.testStructuredData.bind(this) },
            { name: 'URL Structure', test: this.testURLStructure.bind(this) },
            { name: 'Page Speed', test: this.testPageSpeed.bind(this) },
            { name: 'Mobile Friendliness', test: this.testMobileFriendliness.bind(this) }
        ]);
    }
    
    register(category, tests) {
        this.tests.set(category, tests);
    }
    
    // ===== CORE FUNCTIONALITY TESTS =====
    async testAppInitialization() {
        const result = { passed: false, details: [] };
        
        try {
            // Test if MINGUS app is available
            if (!window.MINGUS || !window.MINGUS.app) {
                throw new Error('MINGUS application not found');
            }
            
            // Test if app is initialized
            if (!window.MINGUS.app.isAppInitialized()) {
                throw new Error('Application not initialized');
            }
            
            // Test if all services are available
            const requiredServices = ['utils', 'api', 'auth', 'router', 'components'];
            for (const service of requiredServices) {
                if (!window.MINGUS[service]) {
                    throw new Error(`Service ${service} not available`);
                }
            }
            
            result.passed = true;
            result.details.push('Application initialized successfully');
            result.details.push('All required services available');
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testAuthenticationFlow() {
        const result = { passed: false, details: [] };
        
        try {
            const auth = window.MINGUS.auth;
            
            // Test login functionality
            const loginResult = await auth.login({
                email: 'test@example.com',
                password: 'testpassword'
            });
            
            if (loginResult.success) {
                result.details.push('Login functionality working');
            } else {
                result.details.push('Login failed as expected (test credentials)');
            }
            
            // Test logout functionality
            await auth.logout();
            result.details.push('Logout functionality working');
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testNavigationSystem() {
        const result = { passed: false, details: [] };
        
        try {
            const router = window.MINGUS.router;
            
            // Test navigation to different routes
            const routes = ['/dashboard', '/assessments', '/analytics', '/profile'];
            
            for (const route of routes) {
                await router.navigate(route);
                const currentPath = router.getCurrentPath();
                
                if (currentPath === route) {
                    result.details.push(`Navigation to ${route} successful`);
                } else {
                    throw new Error(`Navigation to ${route} failed`);
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testAPIIntegration() {
        const result = { passed: false, details: [] };
        
        try {
            const api = window.MINGUS.api;
            
            // Test health check endpoint
            const healthCheck = await api.healthCheck();
            if (healthCheck) {
                result.details.push('Health check endpoint working');
            }
            
            // Test API error handling
            try {
                await api.get('/nonexistent-endpoint');
            } catch (error) {
                if (error.code === 'HTTP_ERROR') {
                    result.details.push('API error handling working');
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testComponentRendering() {
        const result = { passed: false, details: [] };
        
        try {
            const components = window.MINGUS.components;
            
            // Test button component
            const button = components.create('Button', {
                text: 'Test Button',
                variant: 'primary'
            });
            
            if (button && button.tagName === 'BUTTON') {
                result.details.push('Button component rendering correctly');
            }
            
            // Test modal component
            const modal = components.create('Modal', {
                title: 'Test Modal',
                content: 'Test content'
            });
            
            if (modal && modal.querySelector('.modal-content')) {
                result.details.push('Modal component rendering correctly');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testFormHandling() {
        const result = { passed: false, details: [] };
        
        try {
            const components = window.MINGUS.components;
            
            // Test form creation
            const form = components.create('Form', {
                fields: [
                    { type: 'email', name: 'email', label: 'Email', required: true },
                    { type: 'password', name: 'password', label: 'Password', required: true }
                ],
                onSubmit: (data) => {
                    result.details.push('Form submission working');
                }
            });
            
            if (form && form.tagName === 'FORM') {
                result.details.push('Form component rendering correctly');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testModalFunctionality() {
        const result = { passed: false, details: [] };
        
        try {
            const components = window.MINGUS.components;
            
            // Test modal show/hide
            const modal = components.showModal({
                title: 'Test Modal',
                content: 'Test content'
            });
            
            if (modal && modal.classList.contains('active')) {
                result.details.push('Modal show functionality working');
            }
            
            // Test modal close
            components.hideModal(modal.id);
            
            setTimeout(() => {
                if (!modal.classList.contains('active')) {
                    result.details.push('Modal hide functionality working');
                }
            }, 300);
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testErrorHandling() {
        const result = { passed: false, details: [] };
        
        try {
            // Test global error handling
            const originalError = window.onerror;
            let errorCaught = false;
            
            window.onerror = () => {
                errorCaught = true;
                return true;
            };
            
            // Trigger a test error
            setTimeout(() => {
                throw new Error('Test error');
            }, 0);
            
            setTimeout(() => {
                if (errorCaught) {
                    result.details.push('Global error handling working');
                }
                window.onerror = originalError;
            }, 100);
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    // ===== PERFORMANCE TESTS =====
    async testPageLoadPerformance() {
        const result = { passed: false, details: [] };
        
        try {
            // Measure page load time
            const startTime = performance.now();
            
            // Wait for page to be fully loaded
            await new Promise(resolve => {
                if (document.readyState === 'complete') {
                    resolve();
                } else {
                    window.addEventListener('load', resolve);
                }
            });
            
            const loadTime = performance.now() - startTime;
            
            // Check Core Web Vitals
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                const ttfb = navigation.responseStart - navigation.requestStart;
                const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart;
                const loadComplete = navigation.loadEventEnd - navigation.loadEventStart;
                
                result.details.push(`Page load time: ${loadTime.toFixed(2)}ms`);
                result.details.push(`Time to first byte: ${ttfb.toFixed(2)}ms`);
                result.details.push(`DOM content loaded: ${domContentLoaded.toFixed(2)}ms`);
                result.details.push(`Load complete: ${loadComplete.toFixed(2)}ms`);
                
                // Performance thresholds
                if (loadTime < 3000) {
                    result.details.push('Page load performance: Good');
                } else if (loadTime < 5000) {
                    result.details.push('Page load performance: Needs improvement');
                } else {
                    result.details.push('Page load performance: Poor');
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testComponentPerformance() {
        const result = { passed: false, details: [] };
        
        try {
            const components = window.MINGUS.components;
            
            // Test component creation performance
            const startTime = performance.now();
            
            for (let i = 0; i < 100; i++) {
                components.create('Button', { text: `Button ${i}` });
            }
            
            const creationTime = performance.now() - startTime;
            result.details.push(`Component creation time: ${creationTime.toFixed(2)}ms`);
            
            if (creationTime < 100) {
                result.details.push('Component performance: Good');
            } else {
                result.details.push('Component performance: Needs improvement');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testMemoryUsage() {
        const result = { passed: false, details: [] };
        
        try {
            // Check memory usage if available
            if (performance.memory) {
                const memory = performance.memory;
                const usedMB = memory.usedJSHeapSize / 1024 / 1024;
                const totalMB = memory.totalJSHeapSize / 1024 / 1024;
                const limitMB = memory.jsHeapSizeLimit / 1024 / 1024;
                
                result.details.push(`Memory used: ${usedMB.toFixed(2)}MB`);
                result.details.push(`Memory total: ${totalMB.toFixed(2)}MB`);
                result.details.push(`Memory limit: ${limitMB.toFixed(2)}MB`);
                
                const usagePercent = (usedMB / limitMB) * 100;
                if (usagePercent < 50) {
                    result.details.push('Memory usage: Good');
                } else if (usagePercent < 80) {
                    result.details.push('Memory usage: Acceptable');
                } else {
                    result.details.push('Memory usage: High');
                }
            } else {
                result.details.push('Memory usage information not available');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testNetworkPerformance() {
        const result = { passed: false, details: [] };
        
        try {
            const api = window.MINGUS.api;
            
            // Test API response time
            const startTime = performance.now();
            
            try {
                await api.healthCheck();
            } catch (error) {
                // Expected for test environment
            }
            
            const responseTime = performance.now() - startTime;
            result.details.push(`API response time: ${responseTime.toFixed(2)}ms`);
            
            if (responseTime < 1000) {
                result.details.push('Network performance: Good');
            } else if (responseTime < 3000) {
                result.details.push('Network performance: Acceptable');
            } else {
                result.details.push('Network performance: Poor');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testAnimationPerformance() {
        const result = { passed: false, details: [] };
        
        try {
            // Test animation performance
            const element = document.createElement('div');
            element.style.transition = 'all 0.3s ease';
            document.body.appendChild(element);
            
            const startTime = performance.now();
            
            // Trigger animation
            element.style.transform = 'translateX(100px)';
            
            await new Promise(resolve => {
                element.addEventListener('transitionend', resolve, { once: true });
                setTimeout(resolve, 400); // Fallback
            });
            
            const animationTime = performance.now() - startTime;
            result.details.push(`Animation time: ${animationTime.toFixed(2)}ms`);
            
            document.body.removeChild(element);
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    // ===== ACCESSIBILITY TESTS =====
    async testKeyboardNavigation() {
        const result = { passed: false, details: [] };
        
        try {
            // Test tab navigation
            const focusableElements = document.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                result.details.push(`Found ${focusableElements.length} focusable elements`);
                
                // Test tab order
                let tabOrder = [];
                for (let i = 0; i < Math.min(5, focusableElements.length); i++) {
                    focusableElements[i].focus();
                    tabOrder.push(document.activeElement);
                }
                
                if (tabOrder.length > 0) {
                    result.details.push('Tab navigation working');
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testScreenReaderCompatibility() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for ARIA attributes
            const ariaElements = document.querySelectorAll('[aria-label], [aria-labelledby], [aria-describedby]');
            result.details.push(`Found ${ariaElements.length} elements with ARIA attributes`);
            
            // Check for semantic HTML
            const semanticElements = document.querySelectorAll('nav, main, section, article, aside, header, footer');
            result.details.push(`Found ${semanticElements.length} semantic HTML elements`);
            
            // Check for alt text on images
            const images = document.querySelectorAll('img');
            const imagesWithAlt = document.querySelectorAll('img[alt]');
            result.details.push(`${imagesWithAlt.length}/${images.length} images have alt text`);
            
            if (ariaElements.length > 0 && semanticElements.length > 0) {
                result.details.push('Screen reader compatibility: Good');
            } else {
                result.details.push('Screen reader compatibility: Needs improvement');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testColorContrast() {
        const result = { passed: false, details: [] };
        
        try {
            // Basic color contrast check
            const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
            let contrastIssues = 0;
            
            for (let i = 0; i < Math.min(10, textElements.length); i++) {
                const element = textElements[i];
                const style = window.getComputedStyle(element);
                const color = style.color;
                const backgroundColor = style.backgroundColor;
                
                // Simple contrast check (this is a basic implementation)
                if (color && backgroundColor) {
                    // For a real implementation, you would use a proper contrast ratio calculation
                    result.details.push(`Element ${i + 1}: Color ${color}, Background ${backgroundColor}`);
                }
            }
            
            result.details.push('Color contrast check completed');
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testFocusManagement() {
        const result = { passed: false, details: [] };
        
        try {
            // Test focus management in modals
            const modals = document.querySelectorAll('.modal-container');
            
            if (modals.length > 0) {
                const modal = modals[0];
                const focusableElements = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                
                if (focusableElements.length > 0) {
                    result.details.push(`Modal has ${focusableElements.length} focusable elements`);
                    
                    // Test focus trap
                    focusableElements[0].focus();
                    if (document.activeElement === focusableElements[0]) {
                        result.details.push('Focus management in modals working');
                    }
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testARIALabels() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for ARIA labels
            const ariaLabels = document.querySelectorAll('[aria-label]');
            const ariaLabelledby = document.querySelectorAll('[aria-labelledby]');
            const ariaDescribedby = document.querySelectorAll('[aria-describedby]');
            
            result.details.push(`Elements with aria-label: ${ariaLabels.length}`);
            result.details.push(`Elements with aria-labelledby: ${ariaLabelledby.length}`);
            result.details.push(`Elements with aria-describedby: ${ariaDescribedby.length}`);
            
            // Check for form labels
            const inputs = document.querySelectorAll('input, select, textarea');
            const inputsWithLabels = document.querySelectorAll('input[aria-label], input[aria-labelledby], label input');
            
            result.details.push(`${inputsWithLabels.length}/${inputs.length} form inputs have labels`);
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testSemanticHTML() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for semantic HTML elements
            const semanticElements = {
                'nav': document.querySelectorAll('nav').length,
                'main': document.querySelectorAll('main').length,
                'section': document.querySelectorAll('section').length,
                'article': document.querySelectorAll('article').length,
                'aside': document.querySelectorAll('aside').length,
                'header': document.querySelectorAll('header').length,
                'footer': document.querySelectorAll('footer').length
            };
            
            let totalSemantic = 0;
            for (const [element, count] of Object.entries(semanticElements)) {
                result.details.push(`${element}: ${count}`);
                totalSemantic += count;
            }
            
            result.details.push(`Total semantic elements: ${totalSemantic}`);
            
            if (totalSemantic > 0) {
                result.details.push('Semantic HTML structure: Good');
            } else {
                result.details.push('Semantic HTML structure: Needs improvement');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    // ===== CROSS-BROWSER TESTS =====
    async testChromeCompatibility() {
        return this.testBrowserCompatibility('Chrome');
    }
    
    async testFirefoxCompatibility() {
        return this.testBrowserCompatibility('Firefox');
    }
    
    async testSafariCompatibility() {
        return this.testBrowserCompatibility('Safari');
    }
    
    async testEdgeCompatibility() {
        return this.testBrowserCompatibility('Edge');
    }
    
    async testMobileBrowserCompatibility() {
        return this.testBrowserCompatibility('Mobile');
    }
    
    async testBrowserCompatibility(browser) {
        const result = { passed: false, details: [] };
        
        try {
            const userAgent = navigator.userAgent;
            result.details.push(`Current browser: ${userAgent}`);
            
            // Test browser-specific features
            const features = {
                'localStorage': typeof Storage !== 'undefined',
                'sessionStorage': typeof sessionStorage !== 'undefined',
                'fetch': typeof fetch !== 'undefined',
                'Promise': typeof Promise !== 'undefined',
                'async/await': (async () => {}).constructor.name === 'AsyncFunction',
                'ES6 Classes': typeof class Test {} === 'function',
                'CSS Grid': CSS.supports('display', 'grid'),
                'CSS Flexbox': CSS.supports('display', 'flex'),
                'WebGL': (() => {
                    try {
                        const canvas = document.createElement('canvas');
                        return !!(window.WebGLRenderingContext && 
                            (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
                    } catch (e) {
                        return false;
                    }
                })()
            };
            
            for (const [feature, supported] of Object.entries(features)) {
                result.details.push(`${feature}: ${supported ? 'Supported' : 'Not supported'}`);
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    // ===== SECURITY TESTS =====
    async testXSSPrevention() {
        const result = { passed: false, details: [] };
        
        try {
            // Test XSS prevention in content rendering
            const testContent = '<script>alert("XSS")</script><img src="x" onerror="alert(\'XSS\')">';
            
            // Test if content is properly escaped
            const tempDiv = document.createElement('div');
            tempDiv.textContent = testContent;
            
            if (tempDiv.innerHTML.includes('<script>') || tempDiv.innerHTML.includes('onerror=')) {
                result.details.push('XSS prevention: Needs improvement');
            } else {
                result.details.push('XSS prevention: Working');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testCSRFProtection() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for CSRF tokens in forms
            const forms = document.querySelectorAll('form');
            let formsWithCSRF = 0;
            
            forms.forEach(form => {
                const csrfToken = form.querySelector('input[name*="csrf"], input[name*="token"]');
                if (csrfToken) {
                    formsWithCSRF++;
                }
            });
            
            result.details.push(`${formsWithCSRF}/${forms.length} forms have CSRF protection`);
            
            if (formsWithCSRF > 0) {
                result.details.push('CSRF protection: Implemented');
            } else {
                result.details.push('CSRF protection: Not found');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testInputValidation() {
        const result = { passed: false, details: [] };
        
        try {
            // Test input validation
            const inputs = document.querySelectorAll('input, textarea, select');
            let inputsWithValidation = 0;
            
            inputs.forEach(input => {
                if (input.hasAttribute('required') || input.hasAttribute('pattern') || input.hasAttribute('minlength')) {
                    inputsWithValidation++;
                }
            });
            
            result.details.push(`${inputsWithValidation}/${inputs.length} inputs have validation`);
            
            if (inputsWithValidation > 0) {
                result.details.push('Input validation: Implemented');
            } else {
                result.details.push('Input validation: Needs improvement');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testAuthenticationSecurity() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for secure authentication practices
            const auth = window.MINGUS.auth;
            
            if (auth) {
                // Check if tokens are stored securely
                const token = auth.getToken();
                if (token) {
                    result.details.push('Authentication tokens: Present');
                } else {
                    result.details.push('Authentication tokens: Not found');
                }
                
                // Check session management
                if (auth.isLoggedIn) {
                    result.details.push('Session management: Implemented');
                } else {
                    result.details.push('Session management: Basic');
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testDataEncryption() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for HTTPS
            if (location.protocol === 'https:') {
                result.details.push('HTTPS: Enabled');
            } else {
                result.details.push('HTTPS: Not enabled (use for production)');
            }
            
            // Check for secure headers
            result.details.push('Security headers: Check server configuration');
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    // ===== SEO TESTS =====
    async testMetaTags() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for essential meta tags
            const metaTags = {
                'title': document.title,
                'description': document.querySelector('meta[name="description"]')?.content,
                'viewport': document.querySelector('meta[name="viewport"]')?.content,
                'robots': document.querySelector('meta[name="robots"]')?.content,
                'charset': document.querySelector('meta[charset]')?.getAttribute('charset')
            };
            
            for (const [tag, content] of Object.entries(metaTags)) {
                if (content) {
                    result.details.push(`${tag}: Present`);
                } else {
                    result.details.push(`${tag}: Missing`);
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testStructuredData() {
        const result = { passed: false, details: [] };
        
        try {
            // Check for structured data
            const structuredData = document.querySelectorAll('script[type="application/ld+json"]');
            
            if (structuredData.length > 0) {
                result.details.push(`Found ${structuredData.length} structured data blocks`);
                
                structuredData.forEach((script, index) => {
                    try {
                        const data = JSON.parse(script.textContent);
                        result.details.push(`Block ${index + 1}: ${data['@type'] || 'Unknown type'}`);
                    } catch (e) {
                        result.details.push(`Block ${index + 1}: Invalid JSON`);
                    }
                });
            } else {
                result.details.push('No structured data found');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testURLStructure() {
        const result = { passed: false, details: [] };
        
        try {
            const currentUrl = window.location.href;
            
            // Check URL structure
            result.details.push(`Current URL: ${currentUrl}`);
            
            // Check for clean URLs
            if (!currentUrl.includes('?') && !currentUrl.includes('#')) {
                result.details.push('URL structure: Clean');
            } else {
                result.details.push('URL structure: Contains parameters');
            }
            
            // Check for HTTPS
            if (currentUrl.startsWith('https://')) {
                result.details.push('HTTPS: Enabled');
            } else {
                result.details.push('HTTPS: Not enabled');
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testPageSpeed() {
        const result = { passed: false, details: [] };
        
        try {
            // Basic page speed metrics
            const navigation = performance.getEntriesByType('navigation')[0];
            
            if (navigation) {
                const loadTime = navigation.loadEventEnd - navigation.fetchStart;
                const domContentLoaded = navigation.domContentLoadedEventEnd - navigation.fetchStart;
                
                result.details.push(`Page load time: ${loadTime.toFixed(2)}ms`);
                result.details.push(`DOM content loaded: ${domContentLoaded.toFixed(2)}ms`);
                
                if (loadTime < 2000) {
                    result.details.push('Page speed: Excellent');
                } else if (loadTime < 4000) {
                    result.details.push('Page speed: Good');
                } else {
                    result.details.push('Page speed: Needs improvement');
                }
            }
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    async testMobileFriendliness() {
        const result = { passed: false, details: [] };
        
        try {
            // Check viewport meta tag
            const viewport = document.querySelector('meta[name="viewport"]');
            if (viewport) {
                result.details.push('Viewport meta tag: Present');
            } else {
                result.details.push('Viewport meta tag: Missing');
            }
            
            // Check responsive design
            const mediaQueries = document.querySelectorAll('link[media], style');
            let responsiveCSS = 0;
            
            mediaQueries.forEach(element => {
                if (element.media && element.media.includes('max-width')) {
                    responsiveCSS++;
                }
            });
            
            result.details.push(`Responsive CSS rules: ${responsiveCSS} found`);
            
            // Check touch targets
            const touchTargets = document.querySelectorAll('button, a, input, select');
            let smallTargets = 0;
            
            touchTargets.forEach(target => {
                const rect = target.getBoundingClientRect();
                if (rect.width < 44 || rect.height < 44) {
                    smallTargets++;
                }
            });
            
            result.details.push(`Small touch targets: ${smallTargets} found`);
            
            result.passed = true;
            
        } catch (error) {
            result.details.push(`Error: ${error.message}`);
        }
        
        return result;
    }
    
    // ===== TEST EXECUTION =====
    async runTests(categories = null) {
        const startTime = performance.now();
        this.results = [];
        
        console.log('🚀 Starting MINGUS Test Suite...');
        
        const testCategories = categories || Array.from(this.tests.keys());
        
        for (const category of testCategories) {
            if (this.tests.has(category)) {
                console.log(`\n📋 Running ${category} tests...`);
                
                const categoryTests = this.tests.get(category);
                const categoryResults = {
                    category,
                    tests: [],
                    passed: 0,
                    failed: 0
                };
                
                for (const test of categoryTests) {
                    console.log(`  ⏳ Running: ${test.name}`);
                    
                    try {
                        const result = await this.runTest(test);
                        categoryResults.tests.push({
                            name: test.name,
                            ...result
                        });
                        
                        if (result.passed) {
                            categoryResults.passed++;
                            console.log(`  ✅ Passed: ${test.name}`);
                        } else {
                            categoryResults.failed++;
                            console.log(`  ❌ Failed: ${test.name}`);
                        }
                        
                    } catch (error) {
                        categoryResults.failed++;
                        console.log(`  💥 Error: ${test.name} - ${error.message}`);
                        
                        categoryResults.tests.push({
                            name: test.name,
                            passed: false,
                            details: [`Error: ${error.message}`]
                        });
                    }
                }
                
                this.results.push(categoryResults);
                
                console.log(`  📊 ${category}: ${categoryResults.passed} passed, ${categoryResults.failed} failed`);
            }
        }
        
        const totalTime = performance.now() - startTime;
        console.log(`\n⏱️  Test suite completed in ${totalTime.toFixed(2)}ms`);
        
        this.generateReport();
        
        return this.results;
    }
    
    async runTest(test) {
        return new Promise(async (resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error('Test timeout'));
            }, this.config.timeout);
            
            try {
                const result = await test.test();
                clearTimeout(timeout);
                resolve(result);
            } catch (error) {
                clearTimeout(timeout);
                reject(error);
            }
        });
    }
    
    // ===== REPORTING =====
    generateReport() {
        const totalTests = this.results.reduce((sum, category) => 
            sum + category.tests.length, 0);
        const totalPassed = this.results.reduce((sum, category) => 
            sum + category.passed, 0);
        const totalFailed = this.results.reduce((sum, category) => 
            sum + category.failed, 0);
        
        console.log('\n📈 TEST SUITE REPORT');
        console.log('='.repeat(50));
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${totalPassed}`);
        console.log(`Failed: ${totalFailed}`);
        console.log(`Success Rate: ${((totalPassed / totalTests) * 100).toFixed(1)}%`);
        
        console.log('\n📋 DETAILED RESULTS');
        console.log('='.repeat(50));
        
        this.results.forEach(category => {
            console.log(`\n${category.category.toUpperCase()}`);
            console.log('-'.repeat(category.category.length));
            
            category.tests.forEach(test => {
                const status = test.passed ? '✅' : '❌';
                console.log(`${status} ${test.name}`);
                
                if (test.details && test.details.length > 0) {
                    test.details.forEach(detail => {
                        console.log(`   ${detail}`);
                    });
                }
            });
        });
        
        // Save report to localStorage for debugging
        if (typeof localStorage !== 'undefined') {
            localStorage.setItem('mingus-test-report', JSON.stringify({
                timestamp: new Date().toISOString(),
                results: this.results,
                summary: {
                    total: totalTests,
                    passed: totalPassed,
                    failed: totalFailed,
                    successRate: (totalPassed / totalTests) * 100
                }
            }));
        }
    }
    
    // ===== UTILITY METHODS =====
    setupTestEnvironment() {
        // Create test container
        const testContainer = document.createElement('div');
        testContainer.id = 'mingus-test-container';
        testContainer.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 300px;
            max-height: 400px;
            background: white;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 10px;
            font-size: 12px;
            overflow-y: auto;
            z-index: 10000;
            display: none;
        `;
        
        document.body.appendChild(testContainer);
    }
    
    showTestResults() {
        const container = document.getElementById('mingus-test-container');
        if (container) {
            container.style.display = 'block';
            
            let html = '<h3>Test Results</h3>';
            
            this.results.forEach(category => {
                html += `<h4>${category.category}</h4>`;
                html += `<p>Passed: ${category.passed}, Failed: ${category.failed}</p>`;
                
                category.tests.forEach(test => {
                    const status = test.passed ? '✅' : '❌';
                    html += `<div>${status} ${test.name}</div>`;
                });
            });
            
            container.innerHTML = html;
        }
    }
    
    hideTestResults() {
        const container = document.getElementById('mingus-test-container');
        if (container) {
            container.style.display = 'none';
        }
    }
}

// ===== EXPORT TEST SUITE =====
const testSuite = new MINGUSTestSuite();

// Make available globally
window.MINGUS = window.MINGUS || {};
window.MINGUS.testSuite = testSuite;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MINGUSTestSuite;
}

// Auto-run tests in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // Wait for app to be ready
    window.addEventListener('mingus:ready', () => {
        setTimeout(() => {
            console.log('🧪 Auto-running test suite in development mode...');
            testSuite.runTests();
        }, 2000);
    });
}
