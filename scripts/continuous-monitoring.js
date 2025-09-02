const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const nodemailer = require('nodemailer');
const winston = require('winston');

class ContinuousMonitor {
  constructor() {
    this.config = {
      checkInterval: 3600000, // 1 hour
      alertThresholds: {
        accessibilityScore: 90,
        performanceScore: 80,
        contrastCompliance: 95,
        coreWebVitals: {
          lcp: 2500,
          fid: 100,
          cls: 0.1
        }
      },
      notifications: {
        email: {
          enabled: process.env.EMAIL_ENABLED === 'true',
          to: process.env.EMAIL_TO || 'team@example.com',
          from: process.env.EMAIL_FROM || 'monitor@example.com',
          smtp: {
            host: process.env.SMTP_HOST || 'smtp.gmail.com',
            port: process.env.SMTP_PORT || 587,
            secure: false,
            auth: {
              user: process.env.SMTP_USER,
              pass: process.env.SMTP_PASS
            }
          }
        },
        slack: {
          enabled: process.env.SLACK_ENABLED === 'true',
          webhook: process.env.SLACK_WEBHOOK
        }
      }
    };

    this.setupLogging();
    this.setupEmailTransport();
  }

  setupLogging() {
    this.logger = winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      ),
      transports: [
        new winston.transports.File({ filename: './logs/monitor-error.log', level: 'error' }),
        new winston.transports.File({ filename: './logs/monitor-combined.log' }),
        new winston.transports.Console({
          format: winston.format.simple()
        })
      ]
    });
  }

  setupEmailTransport() {
    if (this.config.notifications.email.enabled) {
      this.emailTransporter = nodemailer.createTransporter(this.config.notifications.email.smtp);
    }
  }

  async runAllTests() {
    this.logger.info('Starting comprehensive readability compliance tests...');
    
    const results = {
      timestamp: new Date().toISOString(),
      tests: {}
    };

    try {
      // Run Lighthouse accessibility audit
      results.tests.lighthouse = await this.runLighthouseTest();
      
      // Run Pa11y accessibility test
      results.tests.pa11y = await this.runPa11yTest();
      
      // Run Playwright accessibility tests
      results.tests.playwright = await this.runPlaywrightTests();
      
      // Run Core Web Vitals test
      results.tests.coreWebVitals = await this.runCoreWebVitalsTest();
      
      // Run contrast testing
      results.tests.contrast = await this.runContrastTest();
      
      // Run visual regression tests
      results.tests.visual = await this.runVisualRegressionTests();
      
      // Generate summary
      results.summary = this.generateSummary(results.tests);
      
      // Save results
      await this.saveResults(results);
      
      // Check for issues and send alerts
      await this.checkForIssues(results);
      
      this.logger.info('All tests completed successfully');
      return results;
      
    } catch (error) {
      this.logger.error('Error running tests:', error);
      throw error;
    }
  }

  async runLighthouseTest() {
    return new Promise((resolve, reject) => {
      exec('npm run test:lighthouse', (error, stdout, stderr) => {
        if (error) {
          reject(error);
          return;
        }
        
        try {
          const reportPath = './reports/lighthouse-report.json';
          if (fs.existsSync(reportPath)) {
            const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            resolve({
              accessibility: report.categories.accessibility.score * 100,
              performance: report.categories.performance.score * 100,
              bestPractices: report.categories['best-practices'].score * 100,
              seo: report.categories.seo.score * 100,
              audits: report.audits
            });
          } else {
            reject(new Error('Lighthouse report not found'));
          }
        } catch (parseError) {
          reject(parseError);
        }
      });
    });
  }

  async runPa11yTest() {
    return new Promise((resolve, reject) => {
      exec('npm run test:pa11y', (error, stdout, stderr) => {
        if (error) {
          reject(error);
          return;
        }
        
        try {
          const reportPath = './reports/pa11y-report.json';
          if (fs.existsSync(reportPath)) {
            const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            resolve({
              issues: report.issues,
              documentTitle: report.documentTitle,
              pageUrl: report.pageUrl,
              issuesCount: report.issues.length
            });
          } else {
            reject(new Error('Pa11y report not found'));
          }
        } catch (parseError) {
          reject(parseError);
        }
      });
    });
  }

  async runPlaywrightTests() {
    return new Promise((resolve, reject) => {
      exec('npm run test:playwright', (error, stdout, stderr) => {
        if (error) {
          reject(error);
          return;
        }
        
        try {
          const reportPath = './reports/playwright-results.json';
          if (fs.existsSync(reportPath)) {
            const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            resolve({
              totalTests: report.suites[0]?.specs?.length || 0,
              passed: report.suites[0]?.specs?.filter(spec => spec.tests[0]?.results[0]?.status === 'passed').length || 0,
              failed: report.suites[0]?.specs?.filter(spec => spec.tests[0]?.results[0]?.status === 'failed').length || 0,
              results: report
            });
          } else {
            reject(new Error('Playwright report not found'));
          }
        } catch (parseError) {
          reject(parseError);
        }
      });
    });
  }

  async runCoreWebVitalsTest() {
    return new Promise((resolve, reject) => {
      exec('npm run test:core-web-vitals', (error, stdout, stderr) => {
        if (error) {
          reject(error);
          return;
        }
        
        try {
          const reportPath = './reports/core-web-vitals-report.json';
          if (fs.existsSync(reportPath)) {
            const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            resolve({
              lcp: report.metrics.webVitals.lcp,
              fid: report.metrics.webVitals.fid,
              cls: report.metrics.webVitals.cls,
              summary: report.summary
            });
          } else {
            reject(new Error('Core Web Vitals report not found'));
          }
        } catch (parseError) {
          reject(parseError);
        }
      });
    });
  }

  async runContrastTest() {
    return new Promise((resolve, reject) => {
      exec('npm run test:contrast', (error, stdout, stderr) => {
        if (error) {
          reject(error);
          return;
        }
        
        try {
          const reportPath = './reports/contrast-report.json';
          if (fs.existsSync(reportPath)) {
            const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
            resolve({
              complianceRate: report.summary.complianceRate,
              totalElements: report.summary.totalElements,
              issues: report.summary.issues
            });
          } else {
            reject(new Error('Contrast report not found'));
          }
        } catch (parseError) {
          reject(parseError);
        }
      });
    });
  }

  async runVisualRegressionTests() {
    return new Promise((resolve, reject) => {
      exec('npm run test:visual', (error, stdout, stderr) => {
        if (error) {
          reject(error);
          return;
        }
        
        resolve({
          status: 'completed',
          message: 'Visual regression tests completed'
        });
      });
    });
  }

  generateSummary(testResults) {
    const summary = {
      overall: 'pass',
      issues: [],
      recommendations: []
    };

    // Check Lighthouse scores
    if (testResults.lighthouse) {
      if (testResults.lighthouse.accessibility < this.config.alertThresholds.accessibilityScore) {
        summary.overall = 'fail';
        summary.issues.push(`Accessibility score too low: ${testResults.lighthouse.accessibility.toFixed(1)}%`);
      }
      
      if (testResults.lighthouse.performance < this.config.alertThresholds.performanceScore) {
        summary.overall = 'fail';
        summary.issues.push(`Performance score too low: ${testResults.lighthouse.performance.toFixed(1)}%`);
      }
    }

    // Check Pa11y issues
    if (testResults.pa11y && testResults.pa11y.issuesCount > 0) {
      summary.overall = 'fail';
      summary.issues.push(`${testResults.pa11y.issuesCount} accessibility issues found`);
    }

    // Check Core Web Vitals
    if (testResults.coreWebVitals) {
      const { lcp, fid, cls } = testResults.coreWebVitals;
      
      if (lcp > this.config.alertThresholds.coreWebVitals.lcp) {
        summary.overall = 'fail';
        summary.issues.push(`LCP too slow: ${lcp}ms`);
      }
      
      if (fid > this.config.alertThresholds.coreWebVitals.fid) {
        summary.overall = 'fail';
        summary.issues.push(`FID too slow: ${fid}ms`);
      }
      
      if (cls > this.config.alertThresholds.coreWebVitals.cls) {
        summary.overall = 'fail';
        summary.issues.push(`CLS too high: ${cls}`);
      }
    }

    // Check contrast compliance
    if (testResults.contrast) {
      if (testResults.contrast.complianceRate.wcagAA < this.config.alertThresholds.contrastCompliance) {
        summary.overall = 'fail';
        summary.issues.push(`WCAG AA contrast compliance too low: ${testResults.contrast.complianceRate.wcagAA.toFixed(1)}%`);
      }
    }

    // Generate recommendations
    if (summary.issues.length > 0) {
      summary.recommendations = this.generateRecommendations(testResults);
    }

    return summary;
  }

  generateRecommendations(testResults) {
    const recommendations = [];

    if (testResults.lighthouse && testResults.lighthouse.accessibility < 90) {
      recommendations.push('Improve accessibility by addressing Lighthouse audit failures');
    }

    if (testResults.pa11y && testResults.pa11y.issuesCount > 0) {
      recommendations.push('Fix Pa11y accessibility violations');
    }

    if (testResults.coreWebVitals) {
      const { lcp, fid, cls } = testResults.coreWebVitals;
      
      if (lcp > 2500) {
        recommendations.push('Optimize Largest Contentful Paint by improving server response times and resource loading');
      }
      
      if (fid > 100) {
        recommendations.push('Reduce First Input Delay by optimizing JavaScript execution');
      }
      
      if (cls > 0.1) {
        recommendations.push('Reduce Cumulative Layout Shift by reserving space for dynamic content');
      }
    }

    if (testResults.contrast && testResults.contrast.complianceRate.wcagAA < 95) {
      recommendations.push('Improve color contrast ratios to meet WCAG AA standards');
    }

    return recommendations;
  }

  async checkForIssues(results) {
    if (results.summary.overall === 'fail') {
      this.logger.warn('Issues detected in readability compliance tests', {
        issues: results.summary.issues,
        recommendations: results.summary.recommendations
      });

      // Send notifications
      await this.sendEmailAlert(results);
      await this.sendSlackAlert(results);
    }
  }

  async sendEmailAlert(results) {
    if (!this.config.notifications.email.enabled || !this.emailTransporter) {
      return;
    }

    const emailContent = this.generateEmailContent(results);
    
    try {
      await this.emailTransporter.sendMail({
        from: this.config.notifications.email.from,
        to: this.config.notifications.email.to,
        subject: 'Readability Compliance Alert - Issues Detected',
        html: emailContent
      });
      
      this.logger.info('Email alert sent successfully');
    } catch (error) {
      this.logger.error('Failed to send email alert:', error);
    }
  }

  async sendSlackAlert(results) {
    if (!this.config.notifications.slack.enabled || !this.config.notifications.slack.webhook) {
      return;
    }

    const slackMessage = this.generateSlackMessage(results);
    
    try {
      const response = await fetch(this.config.notifications.slack.webhook, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(slackMessage)
      });
      
      if (response.ok) {
        this.logger.info('Slack alert sent successfully');
      } else {
        this.logger.error('Failed to send Slack alert:', response.statusText);
      }
    } catch (error) {
      this.logger.error('Failed to send Slack alert:', error);
    }
  }

  generateEmailContent(results) {
    return `
      <h2>Readability Compliance Alert</h2>
      <p><strong>Status:</strong> ${results.summary.overall.toUpperCase()}</p>
      <p><strong>Timestamp:</strong> ${results.timestamp}</p>
      
      <h3>Issues Found:</h3>
      <ul>
        ${results.summary.issues.map(issue => `<li>${issue}</li>`).join('')}
      </ul>
      
      <h3>Recommendations:</h3>
      <ul>
        ${results.summary.recommendations.map(rec => `<li>${rec}</li>`).join('')}
      </ul>
      
      <h3>Test Results Summary:</h3>
      <ul>
        <li>Lighthouse Accessibility: ${results.tests.lighthouse?.accessibility?.toFixed(1)}%</li>
        <li>Lighthouse Performance: ${results.tests.lighthouse?.performance?.toFixed(1)}%</li>
        <li>Pa11y Issues: ${results.tests.pa11y?.issuesCount || 0}</li>
        <li>Core Web Vitals LCP: ${results.tests.coreWebVitals?.lcp}ms</li>
        <li>Contrast Compliance: ${results.tests.contrast?.complianceRate?.wcagAA?.toFixed(1)}%</li>
      </ul>
    `;
  }

  generateSlackMessage(results) {
    return {
      text: 'Readability Compliance Alert',
      attachments: [
        {
          color: results.summary.overall === 'fail' ? '#ff0000' : '#00ff00',
          title: 'Test Results',
          fields: [
            {
              title: 'Status',
              value: results.summary.overall.toUpperCase(),
              short: true
            },
            {
              title: 'Issues',
              value: results.summary.issues.length.toString(),
              short: true
            },
            {
              title: 'Lighthouse Accessibility',
              value: `${results.tests.lighthouse?.accessibility?.toFixed(1)}%`,
              short: true
            },
            {
              title: 'Contrast Compliance',
              value: `${results.tests.contrast?.complianceRate?.wcagAA?.toFixed(1)}%`,
              short: true
            }
          ]
        }
      ]
    };
  }

  async saveResults(results) {
    const resultsDir = './reports';
    if (!fs.existsSync(resultsDir)) {
      fs.mkdirSync(resultsDir, { recursive: true });
    }

    const filename = `monitoring-${new Date().toISOString().split('T')[0]}.json`;
    const filepath = path.join(resultsDir, filename);
    
    fs.writeFileSync(filepath, JSON.stringify(results, null, 2));
    this.logger.info(`Results saved to ${filepath}`);
  }

  async startMonitoring() {
    this.logger.info('Starting continuous monitoring...');
    
    // Run initial test
    await this.runAllTests();
    
    // Set up periodic monitoring
    setInterval(async () => {
      try {
        await this.runAllTests();
      } catch (error) {
        this.logger.error('Error in periodic monitoring:', error);
      }
    }, this.config.checkInterval);
    
    this.logger.info(`Monitoring active. Checking every ${this.config.checkInterval / 60000} minutes.`);
  }
}

// CLI usage
if (require.main === module) {
  const monitor = new ContinuousMonitor();
  
  async function run() {
    try {
      await monitor.startMonitoring();
    } catch (error) {
      console.error('Error starting monitoring:', error);
      process.exit(1);
    }
  }

  run();
}

module.exports = ContinuousMonitor;
