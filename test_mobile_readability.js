/**
 * Mobile Readability Test Runner
 * Automated testing for the Mingus Mobile-First Spacing System
 */

class MobileReadabilityTester {
    constructor() {
        this.devices = [
            { name: 'iPhone SE', width: 375, height: 667, score: 85 },
            { name: 'iPhone 13/14', width: 390, height: 844, score: 92 },
            { name: 'iPhone 14 Plus', width: 428, height: 926, score: 95 },
            { name: 'Samsung Galaxy S21', width: 360, height: 800, score: 88 },
            { name: 'Samsung Galaxy A series', width: 412, height: 915, score: 90 },
            { name: 'Tablet', width: 768, height: 1024, score: 98 },
            { name: 'Large Tablet', width: 1024, height: 1366, score: 100 }
        ];
        
        this.testResults = [];
        this.currentDevice = null;
    }

    /**
     * Initialize the test runner
     */
    init() {
        console.log('🚀 Mobile Readability Test Runner Initialized');
        console.log(`📱 Testing ${this.devices.length} device configurations`);
        
        // Add test controls to the page
        this.addTestControls();
        
        // Start with first device
        this.testDevice(this.devices[0]);
    }

    /**
     * Add test controls to the page
     */
    addTestControls() {
        const controls = document.createElement('div');
        controls.id = 'test-controls';
        controls.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1001;
            max-width: 300px;
        `;
        
        controls.innerHTML = `
            <h3>🧪 Test Controls</h3>
            <div style="margin-bottom: 15px;">
                <label>Device:</label>
                <select id="testDeviceSelect" style="width: 100%; margin-top: 5px;">
                    ${this.devices.map(device => 
                        `<option value="${device.width}">${device.name} (${device.width}px)</option>`
                    ).join('')}
                </select>
            </div>
            <div style="margin-bottom: 15px;">
                <button id="runTestBtn" style="width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Run Test
                </button>
            </div>
            <div style="margin-bottom: 15px;">
                <button id="runAllTestsBtn" style="width: 100%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Run All Tests
                </button>
            </div>
            <div style="margin-bottom: 15px;">
                <button id="exportReportBtn" style="width: 100%; padding: 10px; background: #ffc107; color: black; border: none; border-radius: 4px; cursor: pointer;">
                    Export Report
                </button>
            </div>
            <div id="testStatus" style="font-size: 12px; color: #666;"></div>
        `;
        
        document.body.appendChild(controls);
        
        // Add event listeners
        document.getElementById('testDeviceSelect').addEventListener('change', (e) => {
            const device = this.devices.find(d => d.width == e.target.value);
            if (device) {
                this.testDevice(device);
            }
        });
        
        document.getElementById('runTestBtn').addEventListener('click', () => {
            const device = this.devices.find(d => d.width == document.getElementById('testDeviceSelect').value);
            if (device) {
                this.runComprehensiveTest(device);
            }
        });
        
        document.getElementById('runAllTestsBtn').addEventListener('click', () => {
            this.runAllTests();
        });
        
        document.getElementById('exportReportBtn').addEventListener('click', () => {
            this.exportReport();
        });
    }

    /**
     * Test a specific device configuration
     */
    testDevice(device) {
        this.currentDevice = device;
        
        // Simulate device viewport
        this.simulateViewport(device);
        
        // Update status
        this.updateStatus(`Testing ${device.name} (${device.width}px)`);
        
        console.log(`📱 Testing device: ${device.name} (${device.width}x${device.height})`);
    }

    /**
     * Simulate device viewport
     */
    simulateViewport(device) {
        // Update body styles to simulate device
        document.body.style.maxWidth = device.width + 'px';
        document.body.style.margin = '0 auto';
        document.body.style.border = '2px solid #007bff';
        document.body.style.borderRadius = '8px';
        document.body.style.overflow = 'hidden';
        document.body.style.minHeight = device.height + 'px';
        
        // Update viewport meta tag
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', `width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no`);
        }
    }

    /**
     * Run comprehensive test for a device
     */
    async runComprehensiveTest(device) {
        this.updateStatus(`Running comprehensive test for ${device.name}...`);
        
        const results = {
            device: device,
            timestamp: new Date().toISOString(),
            tests: []
        };

        // Test 1: Typography Readability
        results.tests.push(await this.testTypography(device));
        
        // Test 2: Touch Target Accessibility
        results.tests.push(await this.testTouchTargets(device));
        
        // Test 3: Spacing Consistency
        results.tests.push(await this.testSpacing(device));
        
        // Test 4: Layout Responsiveness
        results.tests.push(await this.testLayout(device));
        
        // Test 5: Performance
        results.tests.push(await this.testPerformance(device));

        // Calculate overall score
        const totalScore = results.tests.reduce((sum, test) => sum + test.score, 0);
        results.overallScore = Math.round(totalScore / results.tests.length);
        
        // Store results
        this.testResults.push(results);
        
        this.updateStatus(`✅ Test completed for ${device.name}: ${results.overallScore}/100`);
        
        // Display results
        this.displayResults(results);
        
        return results;
    }

    /**
     * Test typography readability
     */
    async testTypography(device) {
        const test = {
            name: 'Typography Readability',
            score: 0,
            issues: [],
            recommendations: []
        };

        // Check font sizes
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const paragraphs = document.querySelectorAll('p');
        
        let fontSizeScore = 0;
        let lineHeightScore = 0;
        
        // Test heading sizes
        headings.forEach(heading => {
            const fontSize = parseFloat(window.getComputedStyle(heading).fontSize);
            if (device.width <= 375 && fontSize < 20) {
                test.issues.push(`Heading too small on ${device.name}: ${fontSize}px`);
            } else if (fontSize >= 20) {
                fontSizeScore += 20;
            }
        });
        
        // Test paragraph readability
        paragraphs.forEach(p => {
            const fontSize = parseFloat(window.getComputedStyle(p).fontSize);
            const lineHeight = parseFloat(window.getComputedStyle(p).lineHeight);
            
            if (fontSize >= 16) fontSizeScore += 20;
            if (lineHeight >= 1.4) lineHeightScore += 20;
        });
        
        test.score = Math.round((fontSizeScore + lineHeightScore) / 2);
        
        if (test.score < 80) {
            test.recommendations.push('Increase font sizes for better readability');
            test.recommendations.push('Improve line height for better text flow');
        }
        
        return test;
    }

    /**
     * Test touch target accessibility
     */
    async testTouchTargets(device) {
        const test = {
            name: 'Touch Target Accessibility',
            score: 0,
            issues: [],
            recommendations: []
        };

        const touchTargets = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
        let compliantTargets = 0;
        let totalTargets = touchTargets.length;
        
        touchTargets.forEach(target => {
            const rect = target.getBoundingClientRect();
            const minSize = Math.min(rect.width, rect.height);
            
            if (minSize >= 44) {
                compliantTargets++;
            } else {
                test.issues.push(`Touch target too small: ${minSize}px (${target.tagName})`);
            }
        });
        
        test.score = totalTargets > 0 ? Math.round((compliantTargets / totalTargets) * 100) : 100;
        
        if (test.score < 100) {
            test.recommendations.push('Ensure all interactive elements meet 44px minimum size');
            test.recommendations.push('Add padding to small touch targets');
        }
        
        return test;
    }

    /**
     * Test spacing consistency
     */
    async testSpacing(device) {
        const test = {
            name: 'Spacing Consistency',
            score: 0,
            issues: [],
            recommendations: []
        };

        const cards = document.querySelectorAll('.card');
        const sections = document.querySelectorAll('.section');
        
        let spacingScore = 0;
        let totalElements = cards.length + sections.length;
        
        // Test card spacing
        cards.forEach(card => {
            const padding = parseFloat(window.getComputedStyle(card).padding);
            if (padding >= 16) spacingScore += 20;
        });
        
        // Test section spacing
        sections.forEach(section => {
            const margin = parseFloat(window.getComputedStyle(section).marginTop);
            if (margin >= 24) spacingScore += 20;
        });
        
        test.score = totalElements > 0 ? Math.round(spacingScore / totalElements) : 100;
        
        if (test.score < 80) {
            test.recommendations.push('Increase spacing between elements');
            test.recommendations.push('Ensure consistent spacing throughout');
        }
        
        return test;
    }

    /**
     * Test layout responsiveness
     */
    async testLayout(device) {
        const test = {
            name: 'Layout Responsiveness',
            score: 0,
            issues: [],
            recommendations: []
        };

        const container = document.querySelector('.container');
        const body = document.body;
        
        if (container && body) {
            const containerWidth = container.offsetWidth;
            const bodyWidth = body.offsetWidth;
            
            // Check if layout fits within viewport
            if (containerWidth <= bodyWidth) {
                test.score = 100;
            } else {
                test.score = 60;
                test.issues.push('Layout exceeds viewport width');
                test.recommendations.push('Implement responsive breakpoints');
            }
        } else {
            test.score = 100;
        }
        
        return test;
    }

    /**
     * Test performance
     */
    async testPerformance(device) {
        const test = {
            name: 'Performance',
            score: 0,
            issues: [],
            recommendations: []
        };

        // Simple performance test
        const startTime = performance.now();
        
        // Simulate some DOM operations
        for (let i = 0; i < 100; i++) {
            document.querySelectorAll('.card');
        }
        
        const endTime = performance.now();
        const duration = endTime - startTime;
        
        if (duration < 50) {
            test.score = 100;
        } else if (duration < 100) {
            test.score = 80;
        } else {
            test.score = 60;
            test.issues.push(`Performance slow: ${duration.toFixed(2)}ms`);
            test.recommendations.push('Optimize DOM queries and rendering');
        }
        
        return test;
    }

    /**
     * Run tests for all devices
     */
    async runAllTests() {
        this.updateStatus('Running tests for all devices...');
        
        const allResults = [];
        
        for (const device of this.devices) {
            this.testDevice(device);
            const results = await this.runComprehensiveTest(device);
            allResults.push(results);
            
            // Small delay between tests
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        this.updateStatus(`✅ All tests completed. Overall average: ${this.calculateOverallAverage(allResults)}/100`);
        
        return allResults;
    }

    /**
     * Calculate overall average score
     */
    calculateOverallAverage(results) {
        if (results.length === 0) return 0;
        
        const totalScore = results.reduce((sum, result) => sum + result.overallScore, 0);
        return Math.round(totalScore / results.length);
    }

    /**
     * Display test results
     */
    displayResults(results) {
        // Remove existing results display
        const existingDisplay = document.getElementById('test-results-display');
        if (existingDisplay) {
            existingDisplay.remove();
        }
        
        const display = document.createElement('div');
        display.id = 'test-results-display';
        display.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 400px;
            max-height: 80vh;
            overflow-y: auto;
        `;
        
        display.innerHTML = `
            <h3>📊 Test Results: ${results.device.name}</h3>
            <div style="font-size: 24px; font-weight: bold; text-align: center; padding: 10px; background: #d4edda; color: #155724; border-radius: 4px; margin: 10px 0;">
                ${results.overallScore}/100
            </div>
            <div style="margin: 10px 0;">
                ${results.tests.map(test => `
                    <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                        <strong>${test.name}:</strong> ${test.score}/100
                        ${test.issues.length > 0 ? `
                            <div style="margin-top: 5px; font-size: 12px; color: #dc3545;">
                                Issues: ${test.issues.length}
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
            <button onclick="this.parentElement.remove()" style="width: 100%; padding: 8px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Close
            </button>
        `;
        
        document.body.appendChild(display);
    }

    /**
     * Update test status
     */
    updateStatus(message) {
        const status = document.getElementById('testStatus');
        if (status) {
            status.textContent = message;
        }
        console.log(`📊 ${message}`);
    }

    /**
     * Export test report
     */
    exportReport() {
        if (this.testResults.length === 0) {
            alert('No test results to export. Please run tests first.');
            return;
        }
        
        const report = {
            timestamp: new Date().toISOString(),
            overallScore: this.calculateOverallAverage(this.testResults),
            devices: this.testResults,
            summary: this.generateSummary()
        };
        
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `mobile-readability-test-report-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
        
        this.updateStatus('📄 Test report exported successfully');
    }

    /**
     * Generate test summary
     */
    generateSummary() {
        const summary = {
            totalDevices: this.testResults.length,
            averageScore: this.calculateOverallAverage(this.testResults),
            bestPerformingDevice: null,
            worstPerformingDevice: null,
            commonIssues: []
        };
        
        if (this.testResults.length > 0) {
            const sorted = [...this.testResults].sort((a, b) => b.overallScore - a.overallScore);
            summary.bestPerformingDevice = sorted[0].device.name;
            summary.worstPerformingDevice = sorted[sorted.length - 1].device.name;
            
            // Collect common issues
            const allIssues = [];
            this.testResults.forEach(result => {
                result.tests.forEach(test => {
                    allIssues.push(...test.issues);
                });
            });
            
            // Count issue frequency
            const issueCount = {};
            allIssues.forEach(issue => {
                issueCount[issue] = (issueCount[issue] || 0) + 1;
            });
            
            summary.commonIssues = Object.entries(issueCount)
                .sort(([,a], [,b]) => b - a)
                .slice(0, 5)
                .map(([issue, count]) => ({ issue, count }));
        }
        
        return summary;
    }
}

// Initialize test runner when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const tester = new MobileReadabilityTester();
    tester.init();
    
    // Make tester globally available
    window.mobileReadabilityTester = tester;
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileReadabilityTester;
}
