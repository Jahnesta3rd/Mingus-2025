const puppeteer = require('puppeteer');
const chroma = require('chroma-js');
const fs = require('fs');
const path = require('path');

class ContrastTester {
  constructor() {
    this.results = [];
    this.baselinePath = './reports/contrast-baseline.json';
    this.resultsPath = './reports/contrast-results.json';
  }

  async testContrast(url = 'file://' + process.cwd() + '/mobile_readability_test.html') {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
      const page = await browser.newPage();
      await page.setViewport({ width: 1280, height: 720 });
      await page.goto(url, { waitUntil: 'networkidle2' });

      const contrastResults = await this.analyzeContrast(page);
      const result = {
        timestamp: new Date().toISOString(),
        url,
        contrastResults,
        summary: this.generateContrastSummary(contrastResults)
      };

      this.results.push(result);
      await this.saveResults();
      
      return result;
    } finally {
      await browser.close();
    }
  }

  async analyzeContrast(page) {
    const contrastData = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const results = [];

      elements.forEach(element => {
        const style = window.getComputedStyle(element);
        const textColor = style.color;
        const backgroundColor = style.backgroundColor;
        const fontSize = parseFloat(style.fontSize);
        const fontWeight = parseInt(style.fontWeight) || 400;

        // Only test elements with visible text
        if (textColor && backgroundColor && 
            textColor !== 'rgba(0, 0, 0, 0)' && 
            backgroundColor !== 'rgba(0, 0, 0, 0)' &&
            element.textContent && element.textContent.trim()) {
          
          results.push({
            element: element.tagName.toLowerCase(),
            text: element.textContent.trim().substring(0, 50),
            textColor,
            backgroundColor,
            fontSize,
            fontWeight,
            isLargeText: fontSize >= 18 || (fontSize >= 14 && fontWeight >= 700)
          });
        }
      });

      return results;
    });

    // Calculate contrast ratios
    const contrastResults = contrastData.map(item => {
      const contrastRatio = this.calculateContrastRatio(item.textColor, item.backgroundColor);
      const wcagAA = this.checkWCAGCompliance(contrastRatio, item.isLargeText, 'AA');
      const wcagAAA = this.checkWCAGCompliance(contrastRatio, item.isLargeText, 'AAA');

      return {
        ...item,
        contrastRatio,
        wcagAA,
        wcagAAA,
        status: this.getContrastStatus(contrastRatio, item.isLargeText)
      };
    });

    return contrastResults;
  }

  calculateContrastRatio(color1, color2) {
    try {
      // Convert colors to chroma objects
      const c1 = chroma(color1);
      const c2 = chroma(color2);

      // Get luminance values
      const l1 = c1.luminance();
      const l2 = c2.luminance();

      // Calculate contrast ratio
      const brightest = Math.max(l1, l2);
      const darkest = Math.min(l1, l2);

      return (brightest + 0.05) / (darkest + 0.05);
    } catch (error) {
      console.warn('Error calculating contrast ratio:', error);
      return 0;
    }
  }

  checkWCAGCompliance(contrastRatio, isLargeText, level) {
    const thresholds = {
      AA: { normal: 4.5, large: 3.0 },
      AAA: { normal: 7.0, large: 4.5 }
    };

    const threshold = isLargeText ? thresholds[level].large : thresholds[level].normal;
    return contrastRatio >= threshold;
  }

  getContrastStatus(contrastRatio, isLargeText) {
    if (contrastRatio >= 7.0) return 'excellent';
    if (contrastRatio >= 4.5) return 'good';
    if (contrastRatio >= 3.0 && isLargeText) return 'acceptable';
    return 'poor';
  }

  generateContrastSummary(contrastResults) {
    const summary = {
      totalElements: contrastResults.length,
      compliant: {
        wcagAA: 0,
        wcagAAA: 0
      },
      status: {
        excellent: 0,
        good: 0,
        acceptable: 0,
        poor: 0
      },
      issues: []
    };

    contrastResults.forEach(result => {
      // Count compliance
      if (result.wcagAA) summary.compliant.wcagAA++;
      if (result.wcagAAA) summary.compliant.wcagAAA++;
      
      // Count status
      summary.status[result.status]++;

      // Identify issues
      if (result.status === 'poor') {
        summary.issues.push({
          element: result.element,
          text: result.text,
          contrastRatio: result.contrastRatio,
          fontSize: result.fontSize,
          isLargeText: result.isLargeText
        });
      }
    });

    // Calculate percentages
    summary.complianceRate = {
      wcagAA: (summary.compliant.wcagAA / summary.totalElements) * 100,
      wcagAAA: (summary.compliant.wcagAAA / summary.totalElements) * 100
    };

    return summary;
  }

  async testSpecificColorCombinations() {
    const colorCombinations = [
      { text: '#000000', background: '#FFFFFF', name: 'Black on White' },
      { text: '#FFFFFF', background: '#000000', name: 'White on Black' },
      { text: '#333333', background: '#FFFFFF', name: 'Dark Gray on White' },
      { text: '#666666', background: '#FFFFFF', name: 'Medium Gray on White' },
      { text: '#999999', background: '#FFFFFF', name: 'Light Gray on White' },
      { text: '#007BFF', background: '#FFFFFF', name: 'Blue on White' },
      { text: '#28A745', background: '#FFFFFF', name: 'Green on White' },
      { text: '#DC3545', background: '#FFFFFF', name: 'Red on White' },
      { text: '#FFC107', background: '#FFFFFF', name: 'Yellow on White' },
      { text: '#6C757D', background: '#FFFFFF', name: 'Gray on White' }
    ];

    const results = colorCombinations.map(combo => {
      const contrastRatio = this.calculateContrastRatio(combo.text, combo.background);
      const wcagAA = this.checkWCAGCompliance(contrastRatio, false, 'AA');
      const wcagAAA = this.checkWCAGCompliance(contrastRatio, false, 'AAA');

      return {
        name: combo.name,
        textColor: combo.text,
        backgroundColor: combo.background,
        contrastRatio,
        wcagAA,
        wcagAAA,
        status: this.getContrastStatus(contrastRatio, false)
      };
    });

    return results;
  }

  async testAccessibilityColorPalette() {
    const palette = {
      primary: ['#007BFF', '#0056B3', '#004085'],
      secondary: ['#6C757D', '#545B62', '#3D4449'],
      success: ['#28A745', '#1E7E34', '#155724'],
      danger: ['#DC3545', '#C82333', '#A71E2A'],
      warning: ['#FFC107', '#E0A800', '#D39E00'],
      info: ['#17A2B8', '#138496', '#0C5460'],
      light: ['#F8F9FA', '#E2E6EA', '#D6D8DB'],
      dark: ['#343A40', '#23272B', '#1D2124']
    };

    const results = {};

    for (const [category, colors] of Object.entries(palette)) {
      results[category] = [];
      
      for (let i = 0; i < colors.length; i++) {
        for (let j = 0; j < colors.length; j++) {
          if (i !== j) {
            const contrastRatio = this.calculateContrastRatio(colors[i], colors[j]);
            const wcagAA = this.checkWCAGCompliance(contrastRatio, false, 'AA');
            const wcagAAA = this.checkWCAGCompliance(contrastRatio, false, 'AAA');

            results[category].push({
              textColor: colors[i],
              backgroundColor: colors[j],
              contrastRatio,
              wcagAA,
              wcagAAA,
              status: this.getContrastStatus(contrastRatio, false)
            });
          }
        }
      }
    }

    return results;
  }

  async compareWithBaseline() {
    if (!fs.existsSync(this.baselinePath)) {
      console.log('No baseline found. Creating baseline...');
      await this.createBaseline();
      return null;
    }

    const baseline = JSON.parse(fs.readFileSync(this.baselinePath, 'utf8'));
    const current = this.results[this.results.length - 1];

    const comparison = {
      timestamp: new Date().toISOString(),
      changes: {
        totalElements: {
          baseline: baseline.contrastResults.length,
          current: current.contrastResults.length,
          difference: current.contrastResults.length - baseline.contrastResults.length
        },
        complianceRate: {
          wcagAA: {
            baseline: baseline.summary.complianceRate.wcagAA,
            current: current.summary.complianceRate.wcagAA,
            difference: current.summary.complianceRate.wcagAA - baseline.summary.complianceRate.wcagAA
          },
          wcagAAA: {
            baseline: baseline.summary.complianceRate.wcagAAA,
            current: current.summary.complianceRate.wcagAAA,
            difference: current.summary.complianceRate.wcagAAA - baseline.summary.complianceRate.wcagAAA
          }
        },
        issues: {
          baseline: baseline.summary.issues.length,
          current: current.summary.issues.length,
          difference: current.summary.issues.length - baseline.summary.issues.length
        }
      }
    };

    return comparison;
  }

  async createBaseline() {
    const baseline = this.results[this.results.length - 1];
    fs.writeFileSync(this.baselinePath, JSON.stringify(baseline, null, 2));
    console.log('Contrast baseline created successfully');
  }

  async saveResults() {
    const resultsDir = path.dirname(this.resultsPath);
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }
    
    fs.writeFileSync(this.resultsPath, JSON.stringify(this.results, null, 2));
  }

  async generateReport() {
    const comparison = await this.compareWithBaseline();
    const current = this.results[this.results.length - 1];
    const colorCombinations = await this.testSpecificColorCombinations();
    const accessibilityPalette = await this.testAccessibilityColorPalette();

    const report = {
      timestamp: new Date().toISOString(),
      summary: current.summary,
      contrastResults: current.contrastResults,
      colorCombinations,
      accessibilityPalette,
      comparison
    };

    const reportPath = './reports/contrast-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    console.log('Contrast Report Generated:', reportPath);
    return report;
  }
}

// CLI usage
if (require.main === module) {
  const tester = new ContrastTester();
  
  async function run() {
    try {
      console.log('Testing contrast ratios...');
      await tester.testContrast();
      
      console.log('Generating report...');
      const report = await tester.generateReport();
      
      console.log('Contrast Report Summary:');
      console.log('Total elements tested:', report.summary.totalElements);
      console.log('WCAG AA compliance:', report.summary.complianceRate.wcagAA.toFixed(1) + '%');
      console.log('WCAG AAA compliance:', report.summary.complianceRate.wcagAAA.toFixed(1) + '%');
      console.log('Issues found:', report.summary.issues.length);
      
      if (report.comparison) {
        console.log('\nChanges from baseline:');
        console.log('WCAG AA compliance change:', report.comparison.changes.complianceRate.wcagAA.difference.toFixed(1) + '%');
        console.log('Issues change:', report.comparison.changes.issues.difference);
      }
      
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  }

  run();
}

module.exports = ContrastTester;
