/**
 * Mingus Financial Services - Color Contrast Testing Tool
 * WCAG 2.1 AA/AAA Compliance Testing
 * 
 * Features:
 * - Automated contrast ratio calculation
 * - WCAG AA (4.5:1) and AAA (7:1) validation
 * - Support for light and dark modes
 * - Financial data specific testing
 * - Detailed reporting and recommendations
 */

class ContrastTestingTool {
    constructor() {
        this.testResults = {};
        this.wcagStandards = {
            AA: 4.5,
            AAA: 7.0,
            AA_LARGE: 3.0,
            AAA_LARGE: 4.5
        };
        this.colorCache = new Map();
        this.testHistory = [];
    }

    /**
     * Run comprehensive contrast audit
     */
    async runComprehensiveAudit() {
        console.log('🔍 Starting comprehensive color contrast audit...');
        
        this.testResults = {
            timestamp: new Date().toISOString(),
            summary: {
                totalElements: 0,
                passingAA: 0,
                passingAAA: 0,
                failing: 0,
                complianceRate: 0
            },
            results: {},
            recommendations: [],
            criticalIssues: []
        };

        // Test all text elements
        await this.testAllTextElements();
        
        // Test financial data elements specifically
        await this.testFinancialDataElements();
        
        // Test form elements
        await this.testFormElements();
        
        // Test interactive elements
        await this.testInteractiveElements();
        
        // Generate summary and recommendations
        this.generateSummary();
        this.generateRecommendations();
        
        // Log results
        this.logAuditResults();
        
        // Return results
        return this.testResults;
    }

    /**
     * Test all text elements on the page
     */
    async testAllTextElements() {
        const textSelectors = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'p', 'span', 'div', 'label', 'caption',
            'th', 'td', 'li', 'a', 'button'
        ];
        
        const textElements = document.querySelectorAll(textSelectors.join(','));
        
        for (const element of textElements) {
            if (this.isVisibleElement(element) && this.hasTextContent(element)) {
                await this.testElementContrast(element, 'text');
            }
        }
    }

    /**
     * Test financial data elements specifically
     */
    async testFinancialDataElements() {
        const financialSelectors = [
            '[data-financial-status]',
            '[data-amount]',
            '[data-currency]',
            '.financial-data',
            '.profit-loss',
            '.balance',
            '.transaction',
            '.investment',
            '.portfolio'
        ];
        
        const financialElements = document.querySelectorAll(financialSelectors.join(','));
        
        for (const element of financialElements) {
            if (this.isVisibleElement(element)) {
                await this.testElementContrast(element, 'financial');
            }
        }
    }

    /**
     * Test form elements
     */
    async testFormElements() {
        const formSelectors = [
            'input', 'select', 'textarea', 'button',
            '.form-input', '.form-label', '.form-error',
            '.form-success', '.form-warning'
        ];
        
        const formElements = document.querySelectorAll(formSelectors.join(','));
        
        for (const element of formElements) {
            if (this.isVisibleElement(element)) {
                await this.testElementContrast(element, 'form');
            }
        }
    }

    /**
     * Test interactive elements
     */
    async testInteractiveElements() {
        const interactiveSelectors = [
            'button', 'a', '[role="button"]', '[role="link"]',
            '[role="tab"]', '[role="menuitem"]', '[tabindex]'
        ];
        
        const interactiveElements = document.querySelectorAll(interactiveSelectors.join(','));
        
        for (const element of interactiveElements) {
            if (this.isVisibleElement(element)) {
                await this.testElementContrast(element, 'interactive');
            }
        }
    }

    /**
     * Test contrast for a specific element
     */
    async testElementContrast(element, elementType) {
        try {
            const elementPath = this.getElementPath(element);
            const styles = window.getComputedStyle(element);
            
            // Get text and background colors
            const textColor = this.parseColor(styles.color);
            const backgroundColor = this.getEffectiveBackgroundColor(element);
            
            if (!textColor || !backgroundColor) {
                this.recordTestResult(element, elementType, {
                    status: 'error',
                    message: 'Could not parse colors',
                    elementPath,
                    elementType
                });
                return;
            }
            
            // Calculate contrast ratio
            const contrastRatio = this.calculateContrastRatio(textColor, backgroundColor);
            
            // Determine font size for WCAG level
            const fontSize = parseFloat(styles.fontSize);
            const isLargeText = fontSize >= 18 || (fontSize >= 14 && this.isBoldFont(styles.fontWeight));
            
            // Determine WCAG compliance
            const wcagLevel = this.determineWCAGLevel(contrastRatio, isLargeText);
            
            // Record test result
            const result = {
                status: wcagLevel.passes ? 'pass' : 'fail',
                contrastRatio: contrastRatio,
                textColor: textColor,
                backgroundColor: backgroundColor,
                fontSize: fontSize,
                isLargeText: isLargeText,
                wcagLevel: wcagLevel,
                elementPath: elementPath,
                elementType: elementType,
                element: element,
                timestamp: new Date().toISOString()
            };
            
            this.recordTestResult(element, elementType, result);
            
            // Add to critical issues if failing
            if (!wcagLevel.passes) {
                this.addCriticalIssue(result);
            }
            
        } catch (error) {
            console.error('Error testing element contrast:', error);
            this.recordTestResult(element, elementType, {
                status: 'error',
                message: error.message,
                elementPath: this.getElementPath(element),
                elementType
            });
        }
    }

    /**
     * Get effective background color (handles transparent backgrounds)
     */
    getEffectiveBackgroundColor(element) {
        const styles = window.getComputedStyle(element);
        let backgroundColor = this.parseColor(styles.backgroundColor);
        
        // If background is transparent, check parent elements
        if (this.isTransparent(backgroundColor)) {
            let parent = element.parentElement;
            while (parent && parent !== document.body) {
                const parentStyles = window.getComputedStyle(parent);
                const parentBg = this.parseColor(parentStyles.backgroundColor);
                
                if (!this.isTransparent(parentBg)) {
                    backgroundColor = parentBg;
                    break;
                }
                
                parent = parent.parentElement;
            }
            
            // If still transparent, use document body background
            if (this.isTransparent(backgroundColor)) {
                const bodyStyles = window.getComputedStyle(document.body);
                backgroundColor = this.parseColor(bodyStyles.backgroundColor);
            }
        }
        
        return backgroundColor;
    }

    /**
     * Check if color is transparent
     */
    isTransparent(color) {
        if (!color) return true;
        return color[3] !== undefined && color[3] === 0;
    }

    /**
     * Check if font is bold
     */
    isBoldFont(fontWeight) {
        const weight = parseInt(fontWeight);
        return weight >= 700;
    }

    /**
     * Determine WCAG compliance level
     */
    determineWCAGLevel(contrastRatio, isLargeText) {
        const standards = isLargeText ? {
            AA: this.wcagStandards.AA_LARGE,
            AAA: this.wcagStandards.AAA_LARGE
        } : {
            AA: this.wcagStandards.AA,
            AAA: this.wcagStandards.AAA
        };
        
        return {
            passes: contrastRatio >= standards.AA,
            passesAA: contrastRatio >= standards.AA,
            passesAAA: contrastRatio >= standards.AAA,
            AA: standards.AA,
            AAA: standards.AAA,
            level: contrastRatio >= standards.AAA ? 'AAA' : 
                   contrastRatio >= standards.AA ? 'AA' : 'Fail'
        };
    }

    /**
     * Calculate contrast ratio between two colors
     */
    calculateContrastRatio(color1, color2) {
        const luminance1 = this.calculateLuminance(color1);
        const luminance2 = this.calculateLuminance(color2);
        
        const lighter = Math.max(luminance1, luminance2);
        const darker = Math.min(luminance1, luminance2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * Calculate luminance of a color
     */
    calculateLuminance(color) {
        if (!color || color.length < 3) return 0;
        
        const [r, g, b] = color.slice(0, 3).map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }

    /**
     * Parse color string to RGBA values
     */
    parseColor(colorString) {
        if (!colorString) return null;
        
        // Check cache first
        if (this.colorCache.has(colorString)) {
            return this.colorCache.get(colorString);
        }
        
        let parsedColor = null;
        
        // Handle named colors
        const namedColors = {
            'black': [0, 0, 0, 1],
            'white': [255, 255, 255, 1],
            'red': [255, 0, 0, 1],
            'green': [0, 128, 0, 1],
            'blue': [0, 0, 255, 1],
            'yellow': [255, 255, 0, 1],
            'cyan': [0, 255, 255, 1],
            'magenta': [255, 0, 255, 1],
            'gray': [128, 128, 128, 1],
            'grey': [128, 128, 128, 1],
            'transparent': [0, 0, 0, 0]
        };
        
        if (namedColors[colorString.toLowerCase()]) {
            parsedColor = namedColors[colorString.toLowerCase()];
        }
        // Handle hex colors
        else if (colorString.startsWith('#')) {
            parsedColor = this.parseHexColor(colorString);
        }
        // Handle rgb/rgba colors
        else if (colorString.startsWith('rgb')) {
            parsedColor = this.parseRGBColor(colorString);
        }
        // Handle hsl/hsla colors
        else if (colorString.startsWith('hsl')) {
            parsedColor = this.parseHSLColor(colorString);
        }
        
        // Cache the result
        if (parsedColor) {
            this.colorCache.set(colorString, parsedColor);
        }
        
        return parsedColor;
    }

    /**
     * Parse hex color
     */
    parseHexColor(hex) {
        const cleanHex = hex.replace('#', '');
        let r, g, b, a = 1;
        
        if (cleanHex.length === 3) {
            r = parseInt(cleanHex[0] + cleanHex[0], 16);
            g = parseInt(cleanHex[1] + cleanHex[1], 16);
            b = parseInt(cleanHex[2] + cleanHex[2], 16);
        } else if (cleanHex.length === 6) {
            r = parseInt(cleanHex.slice(0, 2), 16);
            g = parseInt(cleanHex.slice(2, 4), 16);
            b = parseInt(cleanHex.slice(4, 6), 16);
        } else if (cleanHex.length === 8) {
            r = parseInt(cleanHex.slice(0, 2), 16);
            g = parseInt(cleanHex.slice(2, 4), 16);
            b = parseInt(cleanHex.slice(4, 6), 16);
            a = parseInt(cleanHex.slice(6, 8), 16) / 255;
        } else {
            return null;
        }
        
        return [r, g, b, a];
    }

    /**
     * Parse RGB color
     */
    parseRGBColor(rgb) {
        const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
        if (!match) return null;
        
        const r = parseInt(match[1]);
        const g = parseInt(match[2]);
        const b = parseInt(match[3]);
        const a = match[4] ? parseFloat(match[4]) : 1;
        
        return [r, g, b, a];
    }

    /**
     * Parse HSL color
     */
    parseHSLColor(hsl) {
        const match = hsl.match(/hsla?\((\d+),\s*(\d+)%,\s*(\d+)%(?:,\s*([\d.]+))?\)/);
        if (!match) return null;
        
        const h = parseInt(match[1]);
        const s = parseInt(match[2]) / 100;
        const l = parseInt(match[3]) / 100;
        const a = match[4] ? parseFloat(match[4]) : 1;
        
        // Convert HSL to RGB
        const rgb = this.hslToRgb(h, s, l);
        return [...rgb, a];
    }

    /**
     * Convert HSL to RGB
     */
    hslToRgb(h, s, l) {
        h = h / 360;
        
        const hue2rgb = (p, q, t) => {
            if (t < 0) t += 1;
            if (t > 1) t -= 1;
            if (t < 1/6) return p + (q - p) * 6 * t;
            if (t < 1/2) return q;
            if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        };
        
        let r, g, b;
        
        if (s === 0) {
            r = g = b = l;
        } else {
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
        
        return [
            Math.round(r * 255),
            Math.round(g * 255),
            Math.round(b * 255)
        ];
    }

    /**
     * Record test result
     */
    recordTestResult(element, elementType, result) {
        const elementPath = result.elementPath || this.getElementPath(element);
        
        this.testResults.results[elementPath] = result;
        this.testHistory.push(result);
        
        // Update summary counts
        if (result.status === 'pass') {
            if (result.wcagLevel && result.wcagLevel.passesAAA) {
                this.testResults.summary.passingAAA++;
            } else if (result.wcagLevel && result.wcagLevel.passesAA) {
                this.testResults.summary.passingAA++;
            }
        } else if (result.status === 'fail') {
            this.testResults.summary.failing++;
        }
        
        this.testResults.summary.totalElements++;
    }

    /**
     * Add critical issue
     */
    addCriticalIssue(result) {
        const issue = {
            severity: 'high',
            elementPath: result.elementPath,
            elementType: result.elementType,
            contrastRatio: result.contrastRatio,
            requiredRatio: result.wcagLevel ? result.wcagLevel.AA : 4.5,
            description: `Contrast ratio ${result.contrastRatio.toFixed(2)}:1 fails WCAG ${result.wcagLevel ? result.wcagLevel.AA : 'AA'} requirement`,
            recommendation: this.generateContrastRecommendation(result)
        };
        
        this.testResults.criticalIssues.push(issue);
    }

    /**
     * Generate contrast recommendation
     */
    generateContrastRecommendation(result) {
        const currentRatio = result.contrastRatio;
        const requiredRatio = result.wcagLevel ? result.wcagLevel.AA : 4.5;
        
        if (currentRatio < requiredRatio) {
            const improvement = requiredRatio - currentRatio;
            return `Increase contrast ratio by ${improvement.toFixed(2)} to meet WCAG AA requirements. Consider using darker text or lighter background.`;
        }
        
        return 'Contrast ratio meets WCAG AA requirements.';
    }

    /**
     * Generate summary
     */
    generateSummary() {
        const summary = this.testResults.summary;
        summary.complianceRate = ((summary.passingAA + summary.passingAAA) / summary.totalElements * 100);
        
        // Add WCAG level breakdown
        summary.wcagBreakdown = {
            AAA: summary.passingAAA,
            AA: summary.passingAA - summary.passingAAA,
            Fail: summary.failing
        };
    }

    /**
     * Generate recommendations
     */
    generateRecommendations() {
        const recommendations = [];
        
        // Group issues by type
        const issuesByType = {};
        this.testResults.criticalIssues.forEach(issue => {
            if (!issuesByType[issue.elementType]) {
                issuesByType[issue.elementType] = [];
            }
            issuesByType[issue.elementType].push(issue);
        });
        
        // Generate type-specific recommendations
        Object.entries(issuesByType).forEach(([type, issues]) => {
            const avgContrast = issues.reduce((sum, issue) => sum + issue.contrastRatio, 0) / issues.length;
            const minRequired = Math.max(...issues.map(issue => issue.requiredRatio));
            
            recommendations.push({
                type: type,
                count: issues.length,
                averageContrast: avgContrast,
                requiredContrast: minRequired,
                priority: avgContrast < minRequired * 0.8 ? 'high' : 'medium',
                description: `${issues.length} ${type} elements have insufficient contrast`,
                action: `Review and update ${type} element colors to achieve minimum ${minRequired}:1 contrast ratio`
            });
        });
        
        // Add general recommendations
        if (this.testResults.summary.failing > 0) {
            recommendations.push({
                type: 'general',
                priority: 'high',
                description: 'Implement systematic color contrast improvements',
                action: 'Establish design system with WCAG-compliant color palette and enforce usage across all components'
            });
        }
        
        this.testResults.recommendations = recommendations;
    }

    /**
     * Log audit results
     */
    logAuditResults() {
        console.log('\n🎯 === COLOR CONTRAST AUDIT RESULTS ===');
        console.log(`📊 Total Elements Tested: ${this.testResults.summary.totalElements}`);
        console.log(`✅ Passing WCAG AAA (7:1): ${this.testResults.summary.passingAAA}`);
        console.log(`✅ Passing WCAG AA (4.5:1): ${this.testResults.summary.passingAA}`);
        console.log(`❌ Failing WCAG AA: ${this.testResults.summary.failing}`);
        console.log(`📈 Compliance Rate: ${this.testResults.summary.complianceRate.toFixed(1)}%`);
        
        if (this.testResults.criticalIssues.length > 0) {
            console.log('\n🚨 Critical Issues Found:');
            this.testResults.criticalIssues.forEach((issue, index) => {
                console.log(`${index + 1}. ${issue.elementPath}`);
                console.log(`   Contrast: ${issue.contrastRatio.toFixed(2)}:1 (Required: ${issue.requiredRatio}:1)`);
                console.log(`   Recommendation: ${issue.recommendation}`);
            });
        }
        
        if (this.testResults.recommendations.length > 0) {
            console.log('\n💡 Recommendations:');
            this.testResults.recommendations.forEach((rec, index) => {
                console.log(`${index + 1}. [${rec.priority.toUpperCase()}] ${rec.description}`);
                console.log(`   Action: ${rec.action}`);
            });
        }
    }

    /**
     * Get element path for identification
     */
    getElementPath(element) {
        if (!element) return 'unknown';
        
        const path = [];
        let current = element;
        
        while (current && current !== document.body) {
            let selector = current.tagName.toLowerCase();
            
            if (current.id) {
                selector += `#${current.id}`;
            } else if (current.className) {
                const classes = Array.from(current.classList).slice(0, 3).join('.');
                if (classes) {
                    selector += `.${classes}`;
                }
            }
            
            path.unshift(selector);
            current = current.parentElement;
        }
        
        return path.join(' > ');
    }

    /**
     * Check if element is visible
     */
    isVisibleElement(element) {
        if (!element) return false;
        
        const styles = window.getComputedStyle(element);
        return styles.display !== 'none' && 
               styles.visibility !== 'hidden' && 
               styles.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
    }

    /**
     * Check if element has text content
     */
    hasTextContent(element) {
        if (!element) return false;
        
        const text = element.textContent || element.innerText || '';
        return text.trim().length > 0;
    }

    /**
     * Export results to JSON
     */
    exportResults() {
        return JSON.stringify(this.testResults, null, 2);
    }

    /**
     * Generate HTML report
     */
    generateHTMLReport() {
        const report = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Color Contrast Audit Report - Mingus Financial</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .issue { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .critical { background: #f8d7da; border-color: #f5c6cb; }
        .recommendation { background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat { background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .stat-label { color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🎯 Color Contrast Audit Report</h1>
    <p><strong>Generated:</strong> ${new Date(this.testResults.timestamp).toLocaleString()}</p>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="stats">
            <div class="stat">
                <div class="stat-number">${this.testResults.summary.totalElements}</div>
                <div class="stat-label">Total Elements</div>
            </div>
            <div class="stat">
                <div class="stat-number">${this.testResults.summary.passingAA + this.testResults.summary.passingAAA}</div>
                <div class="stat-label">Passing WCAG AA</div>
            </div>
            <div class="stat">
                <div class="stat-number">${this.testResults.summary.passingAAA}</div>
                <div class="stat-label">Passing WCAG AAA</div>
            </div>
            <div class="stat">
                <div class="stat-number">${this.testResults.summary.complianceRate.toFixed(1)}%</div>
                <div class="stat-label">Compliance Rate</div>
            </div>
        </div>
    </div>
    
    ${this.testResults.criticalIssues.length > 0 ? `
    <h2>🚨 Critical Issues (${this.testResults.criticalIssues.length})</h2>
    ${this.testResults.criticalIssues.map(issue => `
        <div class="issue critical">
            <h3>${issue.elementPath}</h3>
            <p><strong>Type:</strong> ${issue.elementType}</p>
            <p><strong>Contrast:</strong> ${issue.contrastRatio.toFixed(2)}:1 (Required: ${issue.requiredRatio}:1)</p>
            <p><strong>Description:</strong> ${issue.description}</p>
            <p><strong>Recommendation:</strong> ${issue.recommendation}</p>
        </div>
    `).join('')}
    ` : ''}
    
    ${this.testResults.recommendations.length > 0 ? `
    <h2>💡 Recommendations</h2>
    ${this.testResults.recommendations.map(rec => `
        <div class="recommendation">
            <h3>[${rec.priority.toUpperCase()}] ${rec.type}</h3>
            <p><strong>Description:</strong> ${rec.description}</p>
            <p><strong>Action:</strong> ${rec.action}</p>
            ${rec.count ? `<p><strong>Affected Elements:</strong> ${rec.count}</p>` : ''}
        </div>
    `).join('')}
    ` : ''}
    
    <h2>📋 Detailed Results</h2>
    <p>Total elements tested: ${this.testResults.summary.totalElements}</p>
    <p>Elements passing WCAG AA: ${this.testResults.summary.passingAA + this.testResults.summary.passingAAA}</p>
    <p>Elements passing WCAG AAA: ${this.testResults.summary.passingAAA}</p>
    <p>Elements failing: ${this.testResults.summary.failing}</p>
</body>
</html>`;
        
        return report;
    }

    /**
     * Test specific color combination
     */
    testColorCombination(textColor, backgroundColor) {
        const parsedTextColor = this.parseColor(textColor);
        const parsedBackgroundColor = this.parseColor(backgroundColor);
        
        if (!parsedTextColor || !parsedBackgroundColor) {
            return {
                status: 'error',
                message: 'Could not parse one or both colors'
            };
        }
        
        const contrastRatio = this.calculateContrastRatio(parsedTextColor, parsedBackgroundColor);
        const wcagLevel = this.determineWCAGLevel(contrastRatio, false);
        
        return {
            textColor: parsedTextColor,
            backgroundColor: parsedBackgroundColor,
            contrastRatio: contrastRatio,
            wcagLevel: wcagLevel,
            passes: wcagLevel.passes,
            status: wcagLevel.passes ? 'pass' : 'fail'
        };
    }

    /**
     * Get accessibility status
     */
    getAccessibilityStatus() {
        return {
            contrastCompliance: this.testResults.summary.complianceRate >= 95 ? 'Excellent' :
                                this.testResults.summary.complianceRate >= 80 ? 'Good' :
                                this.testResults.summary.complianceRate >= 60 ? 'Fair' : 'Poor',
            wcagLevel: this.testResults.summary.passingAAA > 0 ? 'AAA' : 
                      this.testResults.summary.passingAA > 0 ? 'AA' : 'Fail',
            criticalIssues: this.testResults.criticalIssues.length,
            recommendations: this.testResults.recommendations.length,
            lastTested: this.testResults.timestamp
        };
    }
}

// Initialize and export
if (typeof window !== 'undefined') {
    window.MingusContrastTester = ContrastTestingTool;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContrastTestingTool;
}

// Auto-run if in browser
if (typeof window !== 'undefined' && document.readyState === 'complete') {
    const tester = new ContrastTestingTool();
    tester.runComprehensiveAudit().then(results => {
        console.log('Contrast testing completed:', results);
    });
}
