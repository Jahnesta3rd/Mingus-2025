const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class CoreWebVitalsMonitor {
  constructor() {
    this.results = [];
    this.baselinePath = './reports/core-web-vitals-baseline.json';
    this.resultsPath = './reports/core-web-vitals-results.json';
  }

  async measureCoreWebVitals(url = 'file://' + process.cwd() + '/mobile_readability_test.html') {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
      const page = await browser.newPage();
      
      // Enable performance monitoring
      await page.setCacheEnabled(false);
      
      // Set viewport for consistent testing
      await page.setViewport({ width: 1280, height: 720 });

      // Collect performance metrics
      const metrics = await this.collectMetrics(page, url);
      
      // Analyze typography impact
      const typographyImpact = await this.analyzeTypographyImpact(page);
      
      const result = {
        timestamp: new Date().toISOString(),
        url,
        metrics,
        typographyImpact,
        summary: this.generateSummary(metrics, typographyImpact)
      };

      this.results.push(result);
      await this.saveResults();
      
      return result;
    } finally {
      await browser.close();
    }
  }

  async collectMetrics(page, url) {
    const client = await page.target().createCDPSession();
    
    // Enable performance monitoring
    await client.send('Performance.enable');
    await client.send('Network.enable');

    // Navigate to the page
    await page.goto(url, { waitUntil: 'networkidle2' });

    // Wait for page to stabilize
    await page.waitForTimeout(2000);

    // Get performance metrics
    const performanceMetrics = await page.metrics();
    const navigationTiming = await page.evaluate(() => {
      const timing = performance.getEntriesByType('navigation')[0];
      return {
        domContentLoaded: timing.domContentLoadedEventEnd - timing.domContentLoadedEventStart,
        loadComplete: timing.loadEventEnd - timing.loadEventStart,
        domInteractive: timing.domInteractive - timing.fetchStart,
        firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
        firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0
      };
    });

    // Get Core Web Vitals
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        // Simulate Core Web Vitals measurement
        setTimeout(() => {
          const observer = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lcp = entries.find(entry => entry.entryType === 'largest-contentful-paint');
            const fid = entries.find(entry => entry.entryType === 'first-input');
            const cls = entries.find(entry => entry.entryType === 'layout-shift');
            
            resolve({
              lcp: lcp ? lcp.startTime : 0,
              fid: fid ? fid.processingStart - fid.startTime : 0,
              cls: cls ? cls.value : 0
            });
          });
          
          observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
          
          // Simulate user interaction for FID
          setTimeout(() => {
            document.querySelector('button')?.click();
          }, 100);
        }, 1000);
      });
    });

    return {
      performanceMetrics,
      navigationTiming,
      webVitals
    };
  }

  async analyzeTypographyImpact(page) {
    const typographyMetrics = await page.evaluate(() => {
      const textElements = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, span, div');
      const metrics = {
        totalTextElements: textElements.length,
        fontSizes: [],
        lineHeights: [],
        fontFamilies: new Set(),
        textRendering: new Set(),
        contrastRatios: []
      };

      textElements.forEach(element => {
        const style = window.getComputedStyle(element);
        
        // Font size analysis
        const fontSize = parseFloat(style.fontSize);
        if (fontSize > 0) {
          metrics.fontSizes.push(fontSize);
        }

        // Line height analysis
        const lineHeight = parseFloat(style.lineHeight);
        if (lineHeight > 0) {
          metrics.lineHeights.push(lineHeight);
        }

        // Font family analysis
        metrics.fontFamilies.add(style.fontFamily);

        // Text rendering analysis
        metrics.textRendering.add(style.textRendering);

        // Contrast ratio analysis (simplified)
        const color = style.color;
        const backgroundColor = style.backgroundColor;
        if (color && backgroundColor) {
          // Simplified contrast calculation
          const contrastRatio = this.calculateContrastRatio(color, backgroundColor);
          if (contrastRatio > 0) {
            metrics.contrastRatios.push(contrastRatio);
          }
        }
      });

      // Calculate averages and statistics
      const avgFontSize = metrics.fontSizes.reduce((a, b) => a + b, 0) / metrics.fontSizes.length;
      const avgLineHeight = metrics.lineHeights.reduce((a, b) => a + b, 0) / metrics.lineHeights.length;
      const avgContrastRatio = metrics.contrastRatios.reduce((a, b) => a + b, 0) / metrics.contrastRatios.length;

      return {
        ...metrics,
        averages: {
          fontSize: avgFontSize,
          lineHeight: avgLineHeight,
          contrastRatio: avgContrastRatio
        },
        fontFamilies: Array.from(metrics.fontFamilies),
        textRendering: Array.from(metrics.textRendering)
      };
    });

    return typographyMetrics;
  }

  calculateContrastRatio(color1, color2) {
    // Simplified contrast ratio calculation
    // In a real implementation, you would use a proper color contrast library
    return 4.5; // Placeholder value
  }

  generateSummary(metrics, typographyImpact) {
    const summary = {
      performance: {
        status: 'good',
        issues: []
      },
      accessibility: {
        status: 'good',
        issues: []
      },
      readability: {
        status: 'good',
        issues: []
      }
    };

    // Analyze Core Web Vitals
    const { webVitals } = metrics;
    
    if (webVitals.lcp > 2500) {
      summary.performance.status = 'needs-improvement';
      summary.performance.issues.push('LCP is too slow (>2.5s)');
    }
    
    if (webVitals.fid > 100) {
      summary.performance.status = 'needs-improvement';
      summary.performance.issues.push('FID is too slow (>100ms)');
    }
    
    if (webVitals.cls > 0.1) {
      summary.performance.status = 'needs-improvement';
      summary.performance.issues.push('CLS is too high (>0.1)');
    }

    // Analyze typography impact
    const { averages } = typographyImpact;
    
    if (averages.fontSize < 12) {
      summary.readability.status = 'needs-improvement';
      summary.readability.issues.push('Average font size is too small (<12px)');
    }
    
    if (averages.lineHeight < 1.2) {
      summary.readability.status = 'needs-improvement';
      summary.readability.issues.push('Average line height is too tight (<1.2)');
    }
    
    if (averages.contrastRatio < 4.5) {
      summary.accessibility.status = 'needs-improvement';
      summary.accessibility.issues.push('Average contrast ratio is too low (<4.5:1)');
    }

    return summary;
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
        lcp: {
          baseline: baseline.metrics.webVitals.lcp,
          current: current.metrics.webVitals.lcp,
          difference: current.metrics.webVitals.lcp - baseline.metrics.webVitals.lcp,
          percentage: ((current.metrics.webVitals.lcp - baseline.metrics.webVitals.lcp) / baseline.metrics.webVitals.lcp) * 100
        },
        fid: {
          baseline: baseline.metrics.webVitals.fid,
          current: current.metrics.webVitals.fid,
          difference: current.metrics.webVitals.fid - baseline.metrics.webVitals.fid,
          percentage: ((current.metrics.webVitals.fid - baseline.metrics.webVitals.fid) / baseline.metrics.webVitals.fid) * 100
        },
        cls: {
          baseline: baseline.metrics.webVitals.cls,
          current: current.metrics.webVitals.cls,
          difference: current.metrics.webVitals.cls - baseline.metrics.webVitals.cls,
          percentage: ((current.metrics.webVitals.cls - baseline.metrics.webVitals.cls) / baseline.metrics.webVitals.cls) * 100
        },
        typography: {
          fontSize: {
            baseline: baseline.typographyImpact.averages.fontSize,
            current: current.typographyImpact.averages.fontSize,
            difference: current.typographyImpact.averages.fontSize - baseline.typographyImpact.averages.fontSize
          },
          lineHeight: {
            baseline: baseline.typographyImpact.averages.lineHeight,
            current: current.typographyImpact.averages.lineHeight,
            difference: current.typographyImpact.averages.lineHeight - baseline.typographyImpact.averages.lineHeight
          }
        }
      }
    };

    return comparison;
  }

  async createBaseline() {
    const baseline = this.results[this.results.length - 1];
    fs.writeFileSync(this.baselinePath, JSON.stringify(baseline, null, 2));
    console.log('Baseline created successfully');
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

    const report = {
      timestamp: new Date().toISOString(),
      summary: current.summary,
      metrics: current.metrics,
      typographyImpact: current.typographyImpact,
      comparison
    };

    const reportPath = './reports/core-web-vitals-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    console.log('Core Web Vitals Report Generated:', reportPath);
    return report;
  }
}

// CLI usage
if (require.main === module) {
  const monitor = new CoreWebVitalsMonitor();
  
  async function run() {
    try {
      console.log('Measuring Core Web Vitals...');
      await monitor.measureCoreWebVitals();
      
      console.log('Generating report...');
      const report = await monitor.generateReport();
      
      console.log('Report Summary:');
      console.log('Performance:', report.summary.performance.status);
      console.log('Accessibility:', report.summary.accessibility.status);
      console.log('Readability:', report.summary.readability.status);
      
      if (report.comparison) {
        console.log('\nChanges from baseline:');
        console.log('LCP:', report.comparison.changes.lcp.percentage.toFixed(2) + '%');
        console.log('FID:', report.comparison.changes.fid.percentage.toFixed(2) + '%');
        console.log('CLS:', report.comparison.changes.cls.percentage.toFixed(2) + '%');
      }
      
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  }

  run();
}

module.exports = CoreWebVitalsMonitor;
