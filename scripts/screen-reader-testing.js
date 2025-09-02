const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

class ScreenReaderTester {
  constructor() {
    this.results = [];
    this.baselinePath = './reports/screen-reader-baseline.json';
    this.resultsPath = './reports/screen-reader-results.json';
  }

  async testScreenReaderAccessibility(url = 'file://' + process.cwd() + '/mobile_readability_test.html') {
    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
      const page = await browser.newPage();
      await page.setViewport({ width: 1280, height: 720 });
      await page.goto(url, { waitUntil: 'networkidle2' });

      const results = {
        timestamp: new Date().toISOString(),
        url,
        tests: {}
      };

      // Run various screen reader tests
      results.tests.headingStructure = await this.testHeadingStructure(page);
      results.tests.landmarkNavigation = await this.testLandmarkNavigation(page);
      results.tests.formAccessibility = await this.testFormAccessibility(page);
      results.tests.linkDescriptions = await this.testLinkDescriptions(page);
      results.tests.imageAccessibility = await this.testImageAccessibility(page);
      results.tests.keyboardNavigation = await this.testKeyboardNavigation(page);
      results.tests.focusManagement = await this.testFocusManagement(page);
      results.tests.semanticHTML = await this.testSemanticHTML(page);
      results.tests.ariaAttributes = await this.testARIAAttributes(page);
      results.tests.textAlternatives = await this.testTextAlternatives(page);

      // Generate summary
      results.summary = this.generateScreenReaderSummary(results.tests);

      this.results.push(results);
      await this.saveResults();
      
      return results;
    } finally {
      await browser.close();
    }
  }

  async testHeadingStructure(page) {
    const headingStructure = await page.evaluate(() => {
      const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
      const structure = headings.map(heading => ({
        level: parseInt(heading.tagName.charAt(1)),
        text: heading.textContent.trim(),
        id: heading.id || null,
        hasAriaLabel: !!heading.getAttribute('aria-label')
      }));

      // Check for proper heading hierarchy
      let previousLevel = 0;
      const hierarchyIssues = [];
      
      for (let i = 0; i < structure.length; i++) {
        const currentLevel = structure[i].level;
        if (currentLevel - previousLevel > 1) {
          hierarchyIssues.push({
            position: i,
            skippedLevel: previousLevel + 1,
            currentLevel
          });
        }
        previousLevel = currentLevel;
      }

      return {
        headings: structure,
        totalHeadings: structure.length,
        hierarchyIssues,
        hasMainHeading: structure.some(h => h.level === 1),
        headingLevels: structure.map(h => h.level)
      };
    });

    return headingStructure;
  }

  async testLandmarkNavigation(page) {
    const landmarks = await page.evaluate(() => {
      const landmarkSelectors = [
        '[role="banner"]',
        '[role="main"]',
        '[role="navigation"]',
        '[role="contentinfo"]',
        '[role="complementary"]',
        '[role="search"]',
        'main',
        'nav',
        'header',
        'footer',
        'aside'
      ];

      const foundLandmarks = [];
      
      landmarkSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          foundLandmarks.push({
            type: selector,
            role: element.getAttribute('role') || element.tagName.toLowerCase(),
            text: element.textContent.trim().substring(0, 100),
            hasLabel: !!(element.getAttribute('aria-label') || element.getAttribute('aria-labelledby')),
            isVisible: element.offsetParent !== null
          });
        });
      });

      return {
        landmarks: foundLandmarks,
        totalLandmarks: foundLandmarks.length,
        hasMain: foundLandmarks.some(l => l.role === 'main'),
        hasNavigation: foundLandmarks.some(l => l.role === 'navigation'),
        hasBanner: foundLandmarks.some(l => l.role === 'banner'),
        hasContentInfo: foundLandmarks.some(l => l.role === 'contentinfo')
      };
    });

    return landmarks;
  }

  async testFormAccessibility(page) {
    const formAccessibility = await page.evaluate(() => {
      const forms = document.querySelectorAll('form');
      const formResults = [];

      forms.forEach((form, index) => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const inputResults = [];

        inputs.forEach(input => {
          const label = input.labels?.[0] || 
                       document.querySelector(`label[for="${input.id}"]`) ||
                       input.closest('label');
          
          inputResults.push({
            type: input.type || input.tagName.toLowerCase(),
            id: input.id || null,
            name: input.name || null,
            hasLabel: !!label,
            labelText: label?.textContent?.trim() || null,
            hasAriaLabel: !!input.getAttribute('aria-label'),
            hasAriaLabelledBy: !!input.getAttribute('aria-labelledby'),
            hasAriaDescribedBy: !!input.getAttribute('aria-describedby'),
            isRequired: input.required || input.getAttribute('aria-required') === 'true',
            hasError: !!input.getAttribute('aria-invalid'),
            placeholder: input.placeholder || null
          });
        });

        formResults.push({
          formIndex: index,
          action: form.action || null,
          method: form.method || 'get',
          inputs: inputResults,
          totalInputs: inputResults.length,
          labeledInputs: inputResults.filter(i => i.hasLabel || i.hasAriaLabel).length,
          requiredInputs: inputResults.filter(i => i.isRequired).length
        });
      });

      return {
        forms: formResults,
        totalForms: formResults.length,
        totalInputs: formResults.reduce((sum, form) => sum + form.totalInputs, 0),
        labeledInputs: formResults.reduce((sum, form) => sum + form.labeledInputs, 0),
        requiredInputs: formResults.reduce((sum, form) => sum + form.requiredInputs, 0)
      };
    });

    return formAccessibility;
  }

  async testLinkDescriptions(page) {
    const linkDescriptions = await page.evaluate(() => {
      const links = document.querySelectorAll('a');
      const linkResults = [];

      links.forEach(link => {
        const text = link.textContent.trim();
        const href = link.href;
        const title = link.title;
        const ariaLabel = link.getAttribute('aria-label');
        const ariaLabelledBy = link.getAttribute('aria-labelledby');
        const hasImage = !!link.querySelector('img');

        linkResults.push({
          text: text || null,
          href: href || null,
          title: title || null,
          ariaLabel: ariaLabel || null,
          ariaLabelledBy: ariaLabelledBy || null,
          hasImage: hasImage,
          isDescriptive: text && text.length > 0 && text !== href,
          hasAccessibleName: !!(text || ariaLabel || ariaLabelledBy || title),
          isGeneric: text === 'Click here' || text === 'Read more' || text === 'Learn more'
        });
      });

      return {
        links: linkResults,
        totalLinks: linkResults.length,
        descriptiveLinks: linkResults.filter(l => l.isDescriptive).length,
        accessibleLinks: linkResults.filter(l => l.hasAccessibleName).length,
        genericLinks: linkResults.filter(l => l.isGeneric).length,
        linksWithImages: linkResults.filter(l => l.hasImage).length
      };
    });

    return linkDescriptions;
  }

  async testImageAccessibility(page) {
    const imageAccessibility = await page.evaluate(() => {
      const images = document.querySelectorAll('img');
      const imageResults = [];

      images.forEach(img => {
        const alt = img.alt;
        const src = img.src;
        const title = img.title;
        const role = img.getAttribute('role');
        const ariaLabel = img.getAttribute('aria-label');
        const ariaLabelledBy = img.getAttribute('aria-labelledby');

        imageResults.push({
          src: src || null,
          alt: alt || null,
          title: title || null,
          role: role || null,
          ariaLabel: ariaLabel || null,
          ariaLabelledBy: ariaLabelledBy || null,
          isDecorative: role === 'presentation' || role === 'none' || alt === '',
          hasAltText: !!(alt && alt.trim()),
          hasAccessibleName: !!(alt || ariaLabel || ariaLabelledBy || title),
          isFunctional: img.closest('a') || img.closest('button')
        });
      });

      return {
        images: imageResults,
        totalImages: imageResults.length,
        imagesWithAlt: imageResults.filter(img => img.hasAltText).length,
        decorativeImages: imageResults.filter(img => img.isDecorative).length,
        functionalImages: imageResults.filter(img => img.isFunctional).length,
        accessibleImages: imageResults.filter(img => img.hasAccessibleName).length
      };
    });

    return imageAccessibility;
  }

  async testKeyboardNavigation(page) {
    const keyboardNavigation = await page.evaluate(() => {
      const focusableElements = document.querySelectorAll(
        'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
      );
      
      const elementResults = [];

      focusableElements.forEach(element => {
        const tagName = element.tagName.toLowerCase();
        const tabIndex = element.tabIndex;
        const isVisible = element.offsetParent !== null;
        const hasFocusIndicator = element.style.outline !== 'none' || 
                                 element.style.boxShadow !== 'none' ||
                                 element.classList.contains('focus-visible');

        elementResults.push({
          tagName,
          tabIndex,
          isVisible,
          hasFocusIndicator,
          text: element.textContent?.trim() || element.value || null,
          isKeyboardAccessible: isVisible && (tabIndex >= 0 || tagName === 'a' || tagName === 'button' || tagName === 'input' || tagName === 'textarea' || tagName === 'select')
        });
      });

      return {
        elements: elementResults,
        totalElements: elementResults.length,
        keyboardAccessible: elementResults.filter(el => el.isKeyboardAccessible).length,
        visibleElements: elementResults.filter(el => el.isVisible).length,
        elementsWithFocusIndicator: elementResults.filter(el => el.hasFocusIndicator).length
      };
    });

    return keyboardNavigation;
  }

  async testFocusManagement(page) {
    const focusManagement = await page.evaluate(() => {
      const focusableElements = document.querySelectorAll(
        'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
      );

      // Test tab order
      const tabOrder = [];
      focusableElements.forEach(element => {
        if (element.offsetParent !== null) { // Only visible elements
          tabOrder.push({
            tagName: element.tagName.toLowerCase(),
            text: element.textContent?.trim() || element.value || null,
            tabIndex: element.tabIndex
          });
        }
      });

      // Check for logical tab order
      const logicalOrder = tabOrder.every((element, index) => {
        if (index === 0) return true;
        return element.tabIndex >= tabOrder[index - 1].tabIndex;
      });

      return {
        tabOrder,
        logicalOrder,
        totalFocusableElements: tabOrder.length,
        hasLogicalTabOrder: logicalOrder
      };
    });

    return focusManagement;
  }

  async testSemanticHTML(page) {
    const semanticHTML = await page.evaluate(() => {
      const semanticElements = [
        'main', 'nav', 'header', 'footer', 'aside', 'article', 'section',
        'figure', 'figcaption', 'time', 'mark', 'cite', 'blockquote',
        'address', 'details', 'summary', 'dialog'
      ];

      const foundElements = [];

      semanticElements.forEach(tagName => {
        const elements = document.querySelectorAll(tagName);
        elements.forEach(element => {
          foundElements.push({
            tagName,
            text: element.textContent.trim().substring(0, 100),
            hasAriaLabel: !!element.getAttribute('aria-label'),
            hasAriaLabelledBy: !!element.getAttribute('aria-labelledby')
          });
        });
      });

      return {
        elements: foundElements,
        totalSemanticElements: foundElements.length,
        elementsWithAria: foundElements.filter(el => el.hasAriaLabel || el.hasAriaLabelledBy).length
      };
    });

    return semanticHTML;
  }

  async testARIAAttributes(page) {
    const ariaAttributes = await page.evaluate(() => {
      const elementsWithAria = document.querySelectorAll('[aria-*]');
      const ariaResults = [];

      elementsWithAria.forEach(element => {
        const ariaAttrs = {};
        for (let attr of element.attributes) {
          if (attr.name.startsWith('aria-')) {
            ariaAttrs[attr.name] = attr.value;
          }
        }

        ariaResults.push({
          tagName: element.tagName.toLowerCase(),
          ariaAttributes: ariaAttrs,
          text: element.textContent.trim().substring(0, 100)
        });
      });

      return {
        elements: ariaResults,
        totalElementsWithAria: ariaResults.length,
        ariaAttributesUsed: [...new Set(ariaResults.flatMap(el => Object.keys(el.ariaAttributes)))]
      };
    });

    return ariaAttributes;
  }

  async testTextAlternatives(page) {
    const textAlternatives = await page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const alternativeResults = [];

      elements.forEach(element => {
        const ariaLabel = element.getAttribute('aria-label');
        const ariaLabelledBy = element.getAttribute('aria-labelledby');
        const ariaDescribedBy = element.getAttribute('aria-describedby');
        const title = element.title;

        if (ariaLabel || ariaLabelledBy || ariaDescribedBy || title) {
          alternativeResults.push({
            tagName: element.tagName.toLowerCase(),
            ariaLabel,
            ariaLabelledBy,
            ariaDescribedBy,
            title,
            text: element.textContent.trim().substring(0, 100)
          });
        }
      });

      return {
        elements: alternativeResults,
        totalElementsWithAlternatives: alternativeResults.length,
        elementsWithAriaLabel: alternativeResults.filter(el => el.ariaLabel).length,
        elementsWithAriaLabelledBy: alternativeResults.filter(el => el.ariaLabelledBy).length,
        elementsWithAriaDescribedBy: alternativeResults.filter(el => el.ariaDescribedBy).length,
        elementsWithTitle: alternativeResults.filter(el => el.title).length
      };
    });

    return textAlternatives;
  }

  generateScreenReaderSummary(tests) {
    const summary = {
      overall: 'pass',
      issues: [],
      recommendations: []
    };

    // Check heading structure
    if (tests.headingStructure.hierarchyIssues.length > 0) {
      summary.overall = 'fail';
      summary.issues.push(`${tests.headingStructure.hierarchyIssues.length} heading hierarchy issues found`);
    }

    if (!tests.headingStructure.hasMainHeading) {
      summary.overall = 'fail';
      summary.issues.push('No main heading (h1) found');
    }

    // Check landmarks
    if (!tests.landmarkNavigation.hasMain) {
      summary.overall = 'fail';
      summary.issues.push('No main landmark found');
    }

    // Check form accessibility
    const formLabelRate = tests.formAccessibility.labeledInputs / tests.formAccessibility.totalInputs;
    if (formLabelRate < 0.9) {
      summary.overall = 'fail';
      summary.issues.push(`Form labeling rate too low: ${(formLabelRate * 100).toFixed(1)}%`);
    }

    // Check link descriptions
    const linkDescriptionRate = tests.linkDescriptions.descriptiveLinks / tests.linkDescriptions.totalLinks;
    if (linkDescriptionRate < 0.8) {
      summary.overall = 'fail';
      summary.issues.push(`Link description rate too low: ${(linkDescriptionRate * 100).toFixed(1)}%`);
    }

    // Check image accessibility
    const imageAccessibilityRate = tests.imageAccessibility.accessibleImages / tests.imageAccessibility.totalImages;
    if (imageAccessibilityRate < 0.9) {
      summary.overall = 'fail';
      summary.issues.push(`Image accessibility rate too low: ${(imageAccessibilityRate * 100).toFixed(1)}%`);
    }

    // Check keyboard navigation
    const keyboardAccessibilityRate = tests.keyboardNavigation.keyboardAccessible / tests.keyboardNavigation.totalElements;
    if (keyboardAccessibilityRate < 0.9) {
      summary.overall = 'fail';
      summary.issues.push(`Keyboard accessibility rate too low: ${(keyboardAccessibilityRate * 100).toFixed(1)}%`);
    }

    // Generate recommendations
    if (summary.issues.length > 0) {
      summary.recommendations = this.generateScreenReaderRecommendations(tests);
    }

    return summary;
  }

  generateScreenReaderRecommendations(tests) {
    const recommendations = [];

    if (tests.headingStructure.hierarchyIssues.length > 0) {
      recommendations.push('Fix heading hierarchy by ensuring no levels are skipped');
    }

    if (!tests.headingStructure.hasMainHeading) {
      recommendations.push('Add a main heading (h1) to the page');
    }

    if (!tests.landmarkNavigation.hasMain) {
      recommendations.push('Add a main landmark to the page');
    }

    if (tests.formAccessibility.labeledInputs / tests.formAccessibility.totalInputs < 0.9) {
      recommendations.push('Ensure all form inputs have proper labels');
    }

    if (tests.linkDescriptions.descriptiveLinks / tests.linkDescriptions.totalLinks < 0.8) {
      recommendations.push('Make link text more descriptive and avoid generic text like "Click here"');
    }

    if (tests.imageAccessibility.accessibleImages / tests.imageAccessibility.totalImages < 0.9) {
      recommendations.push('Add alt text to images or mark them as decorative');
    }

    if (tests.keyboardNavigation.keyboardAccessible / tests.keyboardNavigation.totalElements < 0.9) {
      recommendations.push('Ensure all interactive elements are keyboard accessible');
    }

    return recommendations;
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
        headingStructure: {
          baseline: baseline.tests.headingStructure.totalHeadings,
          current: current.tests.headingStructure.totalHeadings,
          difference: current.tests.headingStructure.totalHeadings - baseline.tests.headingStructure.totalHeadings
        },
        formAccessibility: {
          baseline: baseline.tests.formAccessibility.labeledInputs / baseline.tests.formAccessibility.totalInputs,
          current: current.tests.formAccessibility.labeledInputs / current.tests.formAccessibility.totalInputs,
          difference: (current.tests.formAccessibility.labeledInputs / current.tests.formAccessibility.totalInputs) - 
                     (baseline.tests.formAccessibility.labeledInputs / baseline.tests.formAccessibility.totalInputs)
        },
        linkDescriptions: {
          baseline: baseline.tests.linkDescriptions.descriptiveLinks / baseline.tests.linkDescriptions.totalLinks,
          current: current.tests.linkDescriptions.descriptiveLinks / current.tests.linkDescriptions.totalLinks,
          difference: (current.tests.linkDescriptions.descriptiveLinks / current.tests.linkDescriptions.totalLinks) - 
                     (baseline.tests.linkDescriptions.descriptiveLinks / baseline.tests.linkDescriptions.totalLinks)
        }
      }
    };

    return comparison;
  }

  async createBaseline() {
    const baseline = this.results[this.results.length - 1];
    fs.writeFileSync(this.baselinePath, JSON.stringify(baseline, null, 2));
    console.log('Screen reader baseline created successfully');
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
      tests: current.tests,
      comparison
    };

    const reportPath = './reports/screen-reader-report.json';
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    console.log('Screen Reader Report Generated:', reportPath);
    return report;
  }
}

// CLI usage
if (require.main === module) {
  const tester = new ScreenReaderTester();
  
  async function run() {
    try {
      console.log('Testing screen reader accessibility...');
      await tester.testScreenReaderAccessibility();
      
      console.log('Generating report...');
      const report = await tester.generateReport();
      
      console.log('Screen Reader Report Summary:');
      console.log('Overall status:', report.summary.overall);
      console.log('Issues found:', report.summary.issues.length);
      console.log('Total headings:', report.tests.headingStructure.totalHeadings);
      console.log('Form labeling rate:', (report.tests.formAccessibility.labeledInputs / report.tests.formAccessibility.totalInputs * 100).toFixed(1) + '%');
      console.log('Link description rate:', (report.tests.linkDescriptions.descriptiveLinks / report.tests.linkDescriptions.totalLinks * 100).toFixed(1) + '%');
      
      if (report.comparison) {
        console.log('\nChanges from baseline:');
        console.log('Form labeling change:', (report.comparison.changes.formAccessibility.difference * 100).toFixed(1) + '%');
        console.log('Link description change:', (report.comparison.changes.linkDescriptions.difference * 100).toFixed(1) + '%');
      }
      
    } catch (error) {
      console.error('Error:', error);
      process.exit(1);
    }
  }

  run();
}

module.exports = ScreenReaderTester;
