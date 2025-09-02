#!/usr/bin/env node

/**
 * Performance Test Runner for Readability Improvements
 * 
 * This script automates performance testing across different scenarios
 * and generates comprehensive reports for readability improvements.
 */

const puppeteer = require('puppeteer');
const fs = require('fs').promises;
const path = require('path');

class PerformanceTestRunner {
    constructor() {
        this.results = [];
        this.browser = null;
        this.page = null;
    }

    async init() {
        console.log('🚀 Initializing Performance Test Runner...');
        
        this.browser = await puppeteer.launch({
            headless: false, // Set to true for CI/CD
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        });

        this.page = await this.browser.newPage();
        
        // Set viewport for mobile testing
        await this.page.setViewport({
            width: 375,
            height: 667,
            deviceScaleFactor: 2,
            isMobile: true,
            hasTouch: true
        });

        console.log('✅ Test runner initialized');
    }

    async runTests() {
        console.log('📊 Starting Performance Tests...');

        const testScenarios = [
            {
                name: 'Baseline Performance',
                description: 'Testing current performance baseline',
                url: 'file://' + path.resolve('./mobile_readability_test.html')
            },
            {
                name: 'Network Simulation - Fast 4G',
                description: 'Testing on fast 4G network',
                network: { type: 'fast4g', speed: 50, latency: 50 }
            },
            {
                name: 'Network Simulation - Slow 3G',
                description: 'Testing on slow 3G network',
                network: { type: 'slow3g', speed: 0.75, latency: 200 }
            },
            {
                name: 'Font Loading Test',
                description: 'Testing font loading performance',
                focus: 'fonts'
            },
            {
                name: 'Layout Stability Test',
                description: 'Testing cumulative layout shift',
                focus: 'cls'
            }
        ];

        for (const scenario of testScenarios) {
            console.log(`\n🧪 Running: ${scenario.name}`);
            await this.runScenario(scenario);
        }

        await this.generateReport();
    }

    async runScenario(scenario) {
        try {
            // Navigate to test page
            if (scenario.url) {
                await this.page.goto(scenario.url, { waitUntil: 'networkidle0' });
            } else {
                await this.page.goto('file://' + path.resolve('./mobile_readability_test.html'), { 
                    waitUntil: 'networkidle0' 
                });
            }

            // Wait for performance monitor to initialize
            await this.page.waitForTimeout(2000);

            // Simulate network conditions if specified
            if (scenario.network) {
                await this.simulateNetwork(scenario.network);
            }

            // Run specific tests based on focus
            let metrics = {};
            if (scenario.focus === 'fonts') {
                metrics = await this.testFontLoading();
            } else if (scenario.focus === 'cls') {
                metrics = await this.testLayoutStability();
            } else {
                metrics = await this.collectAllMetrics();
            }

            // Store results
            this.results.push({
                scenario: scenario.name,
                description: scenario.description,
                timestamp: new Date().toISOString(),
                metrics: metrics
            });

            console.log(`✅ Completed: ${scenario.name}`);

        } catch (error) {
            console.error(`❌ Error in scenario ${scenario.name}:`, error.message);
            this.results.push({
                scenario: scenario.name,
                description: scenario.description,
                timestamp: new Date().toISOString(),
                error: error.message
            });
        }
    }

    async simulateNetwork(networkConfig) {
        console.log(`🌐 Simulating ${networkConfig.type} network...`);
        
        // Set network throttling
        await this.page.setRequestInterception(true);
        
        this.page.on('request', request => {
            // Simulate network delay
            setTimeout(() => {
                request.continue();
            }, networkConfig.latency);
        });
    }

    async collectAllMetrics() {
        console.log('📈 Collecting performance metrics...');

        // Wait for metrics to stabilize
        await this.page.waitForTimeout(3000);

        // Extract metrics from the performance monitor
        const metrics = await this.page.evaluate(() => {
            if (typeof performanceMonitor !== 'undefined') {
                return performanceMonitor.getMetrics();
            }
            return null;
        });

        if (!metrics) {
            // Fallback: collect basic performance metrics
            return await this.collectBasicMetrics();
        }

        return metrics;
    }

    async collectBasicMetrics() {
        const metrics = await this.page.evaluate(() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            const paint = performance.getEntriesByType('paint');
            
            return {
                pageLoad: {
                    domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                    totalTime: navigation.loadEventEnd - navigation.fetchStart
                },
                paint: {
                    firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0
                },
                memory: performance.memory ? {
                    usedJSHeapSize: performance.memory.usedJSHeapSize,
                    totalJSHeapSize: performance.memory.totalJSHeapSize
                } : null
            };
        });

        return metrics;
    }

    async testFontLoading() {
        console.log('🔤 Testing font loading performance...');

        const fontMetrics = await this.page.evaluate(() => {
            return new Promise((resolve) => {
                const startTime = performance.now();
                
                document.fonts.ready.then(() => {
                    const loadTime = performance.now() - startTime;
                    resolve({
                        fontLoadTime: loadTime,
                        fontsLoaded: document.fonts.size,
                        fontStatus: document.fonts.status
                    });
                });
            });
        });

        return { fontLoading: fontMetrics };
    }

    async testLayoutStability() {
        console.log('📐 Testing layout stability...');

        // Trigger some layout changes to test CLS
        await this.page.evaluate(() => {
            // Simulate font loading and layout changes
            const testElement = document.createElement('div');
            testElement.textContent = 'Test content for layout stability';
            testElement.style.fontSize = '16px';
            document.body.appendChild(testElement);
            
            setTimeout(() => {
                testElement.style.fontSize = '18px';
            }, 100);
            
            setTimeout(() => {
                testElement.style.fontSize = '20px';
            }, 200);
        });

        // Wait for layout changes to complete
        await this.page.waitForTimeout(500);

        // Collect CLS metrics
        const clsMetrics = await this.page.evaluate(() => {
            return new Promise((resolve) => {
                let clsValue = 0;
                const observer = new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            clsValue += entry.value;
                        }
                    }
                });
                
                observer.observe({ entryTypes: ['layout-shift'] });
                
                setTimeout(() => {
                    observer.disconnect();
                    resolve({
                        cumulativeLayoutShift: clsValue,
                        layoutShifts: clsValue > 0 ? 'detected' : 'none'
                    });
                }, 1000);
            });
        });

        return { layoutStability: clsMetrics };
    }

    async generateReport() {
        console.log('\n📋 Generating Performance Report...');

        const report = {
            timestamp: new Date().toISOString(),
            summary: this.generateSummary(),
            scenarios: this.results,
            recommendations: this.generateRecommendations()
        };

        // Save detailed report
        const reportPath = `performance-report-${Date.now()}.json`;
        await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
        console.log(`📄 Detailed report saved: ${reportPath}`);

        // Generate HTML report
        await this.generateHTMLReport(report);

        // Print summary to console
        this.printSummary(report);
    }

    generateSummary() {
        const totalTests = this.results.length;
        const successfulTests = this.results.filter(r => !r.error).length;
        const failedTests = totalTests - successfulTests;

        const metrics = this.results
            .filter(r => r.metrics)
            .map(r => r.metrics)
            .filter(m => m);

        // Calculate averages
        const avgMetrics = this.calculateAverageMetrics(metrics);

        return {
            totalTests,
            successfulTests,
            failedTests,
            successRate: (successfulTests / totalTests * 100).toFixed(1) + '%',
            averageMetrics: avgMetrics
        };
    }

    calculateAverageMetrics(metrics) {
        if (metrics.length === 0) return {};

        const avg = {};
        
        // Calculate averages for common metrics
        const pageLoads = metrics.filter(m => m.pageLoad).map(m => m.pageLoad);
        if (pageLoads.length > 0) {
            avg.pageLoad = {
                domContentLoaded: this.average(pageLoads.map(p => p.domContentLoaded)),
                loadComplete: this.average(pageLoads.map(p => p.loadComplete)),
                totalTime: this.average(pageLoads.map(p => p.totalTime))
            };
        }

        const paints = metrics.filter(m => m.paint).map(m => m.paint);
        if (paints.length > 0) {
            avg.paint = {
                firstPaint: this.average(paints.map(p => p.firstPaint)),
                firstContentfulPaint: this.average(paints.map(p => p.firstContentfulPaint))
            };
        }

        return avg;
    }

    average(array) {
        return array.reduce((a, b) => a + b, 0) / array.length;
    }

    generateRecommendations() {
        const recommendations = [];

        // Analyze results and generate recommendations
        this.results.forEach(result => {
            if (result.metrics) {
                if (result.metrics.pageLoad?.totalTime > 3000) {
                    recommendations.push({
                        type: 'performance',
                        priority: 'high',
                        scenario: result.scenario,
                        issue: 'Page load time exceeds 3 seconds',
                        suggestion: 'Optimize critical rendering path and reduce initial payload'
                    });
                }

                if (result.metrics.layoutStability?.cumulativeLayoutShift > 0.1) {
                    recommendations.push({
                        type: 'layout',
                        priority: 'high',
                        scenario: result.scenario,
                        issue: 'High cumulative layout shift detected',
                        suggestion: 'Implement proper font loading strategies and size containers'
                    });
                }

                if (result.metrics.fontLoading?.fontLoadTime > 1000) {
                    recommendations.push({
                        type: 'fonts',
                        priority: 'medium',
                        scenario: result.scenario,
                        issue: 'Font loading time exceeds 1 second',
                        suggestion: 'Consider font preloading, subsetting, or system fonts'
                    });
                }
            }
        });

        return recommendations;
    }

    async generateHTMLReport(report) {
        const htmlTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Test Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .summary {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }
        .metric {
            display: inline-block;
            margin: 10px 20px 10px 0;
            padding: 10px 15px;
            background: #007bff;
            color: white;
            border-radius: 4px;
            font-weight: bold;
        }
        .scenario {
            border: 1px solid #ddd;
            margin: 15px 0;
            border-radius: 6px;
            overflow: hidden;
        }
        .scenario-header {
            background: #f8f9fa;
            padding: 15px;
            font-weight: bold;
            border-bottom: 1px solid #ddd;
        }
        .scenario-content {
            padding: 15px;
        }
        .recommendation {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }
        .recommendation.high {
            background: #f8d7da;
            border-color: #f5c6cb;
        }
        .timestamp {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Performance Test Report</h1>
        <div class="timestamp">Generated: ${new Date(report.timestamp).toLocaleString()}</div>
        
        <div class="summary">
            <h2>Summary</h2>
            <div class="metric">Total Tests: ${report.summary.totalTests}</div>
            <div class="metric">Success Rate: ${report.summary.successRate}</div>
            <div class="metric">Successful: ${report.summary.successfulTests}</div>
            <div class="metric">Failed: ${report.summary.failedTests}</div>
        </div>

        <h2>Test Scenarios</h2>
        ${report.scenarios.map(scenario => `
            <div class="scenario">
                <div class="scenario-header">${scenario.scenario}</div>
                <div class="scenario-content">
                    <p><strong>Description:</strong> ${scenario.description}</p>
                    <p><strong>Timestamp:</strong> ${new Date(scenario.timestamp).toLocaleString()}</p>
                    ${scenario.error ? 
                        `<p><strong>Error:</strong> <span style="color: red;">${scenario.error}</span></p>` :
                        `<pre>${JSON.stringify(scenario.metrics, null, 2)}</pre>`
                    }
                </div>
            </div>
        `).join('')}

        <h2>Recommendations</h2>
        ${report.recommendations.map(rec => `
            <div class="recommendation ${rec.priority}">
                <h3>${rec.type.toUpperCase()} - ${rec.priority.toUpperCase()} Priority</h3>
                <p><strong>Scenario:</strong> ${rec.scenario}</p>
                <p><strong>Issue:</strong> ${rec.issue}</p>
                <p><strong>Suggestion:</strong> ${rec.suggestion}</p>
            </div>
        `).join('')}
    </div>
</body>
</html>`;

        const htmlPath = `performance-report-${Date.now()}.html`;
        await fs.writeFile(htmlPath, htmlTemplate);
        console.log(`🌐 HTML report saved: ${htmlPath}`);
    }

    printSummary(report) {
        console.log('\n' + '='.repeat(60));
        console.log('📊 PERFORMANCE TEST SUMMARY');
        console.log('='.repeat(60));
        console.log(`Total Tests: ${report.summary.totalTests}`);
        console.log(`Success Rate: ${report.summary.successRate}`);
        console.log(`Successful: ${report.summary.successfulTests}`);
        console.log(`Failed: ${report.summary.failedTests}`);
        
        if (report.recommendations.length > 0) {
            console.log('\n🚨 RECOMMENDATIONS:');
            report.recommendations.forEach(rec => {
                console.log(`- ${rec.type.toUpperCase()} (${rec.priority}): ${rec.issue}`);
            });
        }
        
        console.log('\n' + '='.repeat(60));
    }

    async cleanup() {
        if (this.browser) {
            await this.browser.close();
        }
        console.log('🧹 Cleanup completed');
    }
}

// CLI interface
async function main() {
    const runner = new PerformanceTestRunner();
    
    try {
        await runner.init();
        await runner.runTests();
    } catch (error) {
        console.error('❌ Test runner failed:', error);
        process.exit(1);
    } finally {
        await runner.cleanup();
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = PerformanceTestRunner;
