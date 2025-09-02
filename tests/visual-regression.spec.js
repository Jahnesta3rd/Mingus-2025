const { test, expect } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

test.describe('Visual Regression Testing for Typography', () => {
  const baselineDir = './baseline-screenshots';
  const currentDir = './current-screenshots';
  const diffDir = './diff-screenshots';

  // Ensure directories exist
  test.beforeAll(async () => {
    [baselineDir, currentDir, diffDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });
  });

  const viewports = [
    { width: 375, height: 667, name: 'mobile' },
    { width: 768, height: 1024, name: 'tablet' },
    { width: 1280, height: 720, name: 'desktop' },
    { width: 1920, height: 1080, name: 'large' }
  ];

  for (const viewport of viewports) {
    test(`typography visual regression - ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/mobile_readability_test.html');
      await page.waitForLoadState('networkidle');

      // Wait for any animations to complete
      await page.waitForTimeout(2000);

      const screenshotName = `typography-${viewport.name}.png`;
      const baselinePath = path.join(baselineDir, screenshotName);
      const currentPath = path.join(currentDir, screenshotName);

      // Take current screenshot
      await page.screenshot({ 
        path: currentPath,
        fullPage: true 
      });

      // Compare with baseline if it exists
      if (fs.existsSync(baselinePath)) {
        const currentImage = fs.readFileSync(currentPath);
        const baselineImage = fs.readFileSync(baselinePath);

        // Simple pixel comparison (in production, use more sophisticated tools)
        expect(currentImage.length).toBe(baselineImage.length);
        
        // For more detailed comparison, you might want to use pixelmatch or similar
        const pixelDifference = await compareImages(baselinePath, currentPath);
        expect(pixelDifference).toBeLessThan(0.01); // Less than 1% difference
      } else {
        // First run - create baseline
        fs.copyFileSync(currentPath, baselinePath);
        console.log(`Created baseline for ${viewport.name}`);
      }
    });
  }

  test('typography element-specific visual tests', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    // Test specific typography elements
    const typographyElements = [
      { selector: 'h1', name: 'headings-h1' },
      { selector: 'h2', name: 'headings-h2' },
      { selector: 'h3', name: 'headings-h3' },
      { selector: 'p', name: 'paragraphs' },
      { selector: '.test-card', name: 'test-cards' },
      { selector: 'button', name: 'buttons' },
      { selector: 'input', name: 'inputs' }
    ];

    for (const element of typographyElements) {
      const elements = await page.locator(element.selector).all();
      if (elements.length > 0) {
        const firstElement = elements[0];
        const isVisible = await firstElement.isVisible();
        
        if (isVisible) {
          const screenshotName = `element-${element.name}.png`;
          const baselinePath = path.join(baselineDir, screenshotName);
          const currentPath = path.join(currentDir, screenshotName);

          await firstElement.screenshot({ path: currentPath });

          if (fs.existsSync(baselinePath)) {
            const pixelDifference = await compareImages(baselinePath, currentPath);
            expect(pixelDifference).toBeLessThan(0.05); // 5% tolerance for element-specific tests
          } else {
            fs.copyFileSync(currentPath, baselinePath);
            console.log(`Created baseline for ${element.name}`);
          }
        }
      }
    }
  });

  test('font rendering consistency across browsers', async ({ browser }) => {
    const browsers = [
      { name: 'chromium', browser: await browser.chromium.launch() },
      { name: 'firefox', browser: await browser.firefox.launch() },
      { name: 'webkit', browser: await browser.webkit.launch() }
    ];

    for (const browserInfo of browsers) {
      const page = await browserInfo.browser.newPage();
      await page.setViewportSize({ width: 1280, height: 720 });
      await page.goto('/mobile_readability_test.html');
      await page.waitForLoadState('networkidle');

      const screenshotName = `font-rendering-${browserInfo.name}.png`;
      const currentPath = path.join(currentDir, screenshotName);

      await page.screenshot({ path: currentPath, fullPage: true });
      await browserInfo.browser.close();
    }
  });

  test('dark mode typography visual regression', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    
    // Enable dark mode
    await page.addInitScript(() => {
      Object.defineProperty(window.matchMedia, 'matches', {
        writable: true,
        value: true
      });
      window.matchMedia = (query) => ({
        matches: query.includes('prefers-color-scheme: dark'),
        addListener: () => {},
        removeListener: () => {}
      });
    });

    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const screenshotName = 'dark-mode-typography.png';
    const baselinePath = path.join(baselineDir, screenshotName);
    const currentPath = path.join(currentDir, screenshotName);

    await page.screenshot({ path: currentPath, fullPage: true });

    if (fs.existsSync(baselinePath)) {
      const pixelDifference = await compareImages(baselinePath, currentPath);
      expect(pixelDifference).toBeLessThan(0.01);
    } else {
      fs.copyFileSync(currentPath, baselinePath);
      console.log('Created dark mode baseline');
    }
  });

  test('typography scaling visual regression', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    const zoomLevels = [0.8, 1, 1.2, 1.5, 2];

    for (const zoom of zoomLevels) {
      await page.evaluate((zoomLevel) => {
        document.body.style.zoom = zoomLevel;
      });

      await page.waitForTimeout(500);

      const screenshotName = `typography-zoom-${zoom}.png`;
      const baselinePath = path.join(baselineDir, screenshotName);
      const currentPath = path.join(currentDir, screenshotName);

      await page.screenshot({ path: currentPath, fullPage: true });

      if (fs.existsSync(baselinePath)) {
        const pixelDifference = await compareImages(baselinePath, currentPath);
        expect(pixelDifference).toBeLessThan(0.02); // Higher tolerance for zoom changes
      } else {
        fs.copyFileSync(currentPath, baselinePath);
        console.log(`Created zoom baseline for ${zoom}`);
      }
    }
  });

  test('typography animation visual regression', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    // Capture initial state
    const initialScreenshot = await page.screenshot({ fullPage: true });

    // Trigger any animations
    await page.evaluate(() => {
      // Simulate user interaction that might trigger animations
      document.querySelector('button')?.click();
    });

    await page.waitForTimeout(1000);

    // Capture after animation
    const afterScreenshot = await page.screenshot({ fullPage: true });

    // Compare screenshots (they should be similar after animation completes)
    expect(afterScreenshot.length).toBe(initialScreenshot.length);
  });

  test('typography responsive breakpoint visual regression', async ({ page }) => {
    const breakpoints = [
      { width: 320, name: 'xs' },
      { width: 576, name: 'sm' },
      { width: 768, name: 'md' },
      { width: 992, name: 'lg' },
      { width: 1200, name: 'xl' },
      { width: 1400, name: 'xxl' }
    ];

    for (const breakpoint of breakpoints) {
      await page.setViewportSize({ width: breakpoint.width, height: 800 });
      await page.goto('/mobile_readability_test.html');
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000); // Allow responsive adjustments

      const screenshotName = `typography-breakpoint-${breakpoint.name}.png`;
      const baselinePath = path.join(baselineDir, screenshotName);
      const currentPath = path.join(currentDir, screenshotName);

      await page.screenshot({ path: currentPath, fullPage: true });

      if (fs.existsSync(baselinePath)) {
        const pixelDifference = await compareImages(baselinePath, currentPath);
        expect(pixelDifference).toBeLessThan(0.01);
      } else {
        fs.copyFileSync(currentPath, baselinePath);
        console.log(`Created breakpoint baseline for ${breakpoint.name}`);
      }
    }
  });
});

// Helper function to compare images (simplified version)
async function compareImages(baselinePath, currentPath) {
  // In a real implementation, you would use a library like pixelmatch
  // For now, we'll do a simple file size comparison
  const baselineStats = fs.statSync(baselinePath);
  const currentStats = fs.statSync(currentPath);
  
  const sizeDifference = Math.abs(baselineStats.size - currentStats.size);
  const averageSize = (baselineStats.size + currentStats.size) / 2;
  
  return sizeDifference / averageSize;
}
