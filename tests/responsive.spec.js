const { test, expect } = require('@playwright/test');

test.describe('Responsive Design Testing', () => {
  const viewports = [
    { width: 320, height: 568, name: 'Small Mobile' },
    { width: 375, height: 667, name: 'iPhone SE' },
    { width: 414, height: 896, name: 'iPhone 11 Pro Max' },
    { width: 768, height: 1024, name: 'iPad' },
    { width: 1024, height: 768, name: 'iPad Landscape' },
    { width: 1280, height: 720, name: 'Desktop HD' },
    { width: 1920, height: 1080, name: 'Full HD' },
    { width: 2560, height: 1440, name: '2K' },
  ];

  for (const viewport of viewports) {
    test(`should render correctly on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto('/mobile_readability_test.html');
      await page.waitForLoadState('networkidle');

      // Check that page loads without horizontal scroll
      const hasHorizontalScroll = await page.evaluate(() => {
        return document.documentElement.scrollWidth > document.documentElement.clientWidth;
      });
      expect(hasHorizontalScroll).toBeFalsy();

      // Check that text remains readable
      const textElements = await page.locator('p, h1, h2, h3, h4, h5, h6').all();
      for (const element of textElements) {
        const isVisible = await element.isVisible();
        if (!isVisible) continue;

        const fontSize = await element.evaluate(el => {
          const style = window.getComputedStyle(el);
          return parseFloat(style.fontSize);
        });

        // Minimum font size for readability
        expect(fontSize).toBeGreaterThanOrEqual(12);
      }

      // Check that interactive elements are properly sized for touch
      if (viewport.width < 768) {
        const touchTargets = await page.locator('button, a, input, select, textarea').all();
        for (const target of touchTargets) {
          const isVisible = await target.isVisible();
          if (!isVisible) continue;

          const size = await target.boundingBox();
          if (size) {
            // Minimum touch target size (44px x 44px)
            expect(size.width).toBeGreaterThanOrEqual(44);
            expect(size.height).toBeGreaterThanOrEqual(44);
          }
        }
      }
    });
  }

  test('should handle orientation changes', async ({ page }) => {
    // Test portrait orientation
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    const portraitScreenshot = await page.screenshot();
    expect(portraitScreenshot).toBeTruthy();

    // Test landscape orientation
    await page.setViewportSize({ width: 667, height: 375 });
    await page.waitForTimeout(1000); // Allow layout to adjust

    const landscapeScreenshot = await page.screenshot();
    expect(landscapeScreenshot).toBeTruthy();

    // Verify content is still accessible in both orientations
    const headings = await page.locator('h1, h2, h3').all();
    expect(headings.length).toBeGreaterThan(0);
  });

  test('should maintain proper spacing across breakpoints', async ({ page }) => {
    const breakpoints = [
      { width: 320, name: 'mobile' },
      { width: 768, name: 'tablet' },
      { width: 1024, name: 'desktop' },
      { width: 1920, name: 'large' }
    ];

    for (const breakpoint of breakpoints) {
      await page.setViewportSize({ width: breakpoint.width, height: 800 });
      await page.goto('/mobile_readability_test.html');
      await page.waitForLoadState('networkidle');

      // Check that spacing is proportional
      const containers = await page.locator('.test-card, .test-section').all();
      for (const container of containers) {
        const padding = await container.evaluate(el => {
          const style = window.getComputedStyle(el);
          return {
            top: parseFloat(style.paddingTop),
            bottom: parseFloat(style.paddingBottom),
            left: parseFloat(style.paddingLeft),
            right: parseFloat(style.paddingRight)
          };
        });

        // Ensure reasonable padding values
        expect(padding.top).toBeGreaterThanOrEqual(8);
        expect(padding.bottom).toBeGreaterThanOrEqual(8);
        expect(padding.left).toBeGreaterThanOrEqual(8);
        expect(padding.right).toBeGreaterThanOrEqual(8);
      }
    }
  });

  test('should handle zoom levels appropriately', async ({ page }) => {
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    // Test different zoom levels
    const zoomLevels = [0.5, 1, 1.5, 2, 3];

    for (const zoom of zoomLevels) {
      await page.evaluate((zoomLevel) => {
        document.body.style.zoom = zoomLevel;
      });

      await page.waitForTimeout(500);

      // Check that text remains readable
      const textElements = await page.locator('p, h1, h2, h3').all();
      for (const element of textElements) {
        const isVisible = await element.isVisible();
        if (!isVisible) continue;

        const fontSize = await element.evaluate(el => {
          const style = window.getComputedStyle(el);
          return parseFloat(style.fontSize);
        });

        // Adjusted minimum for zoom
        const minSize = 12 * zoom;
        expect(fontSize).toBeGreaterThanOrEqual(minSize);
      }
    }
  });

  test('should maintain proper line lengths for readability', async ({ page }) => {
    const viewports = [
      { width: 320, maxChars: 50 },
      { width: 768, maxChars: 75 },
      { width: 1024, maxChars: 85 },
      { width: 1920, maxChars: 100 }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize({ width: viewport.width, height: 800 });
      await page.goto('/mobile_readability_test.html');
      await page.waitForLoadState('networkidle');

      const textElements = await page.locator('p').all();
      for (const element of textElements) {
        const isVisible = await element.isVisible();
        if (!isVisible) continue;

        const text = await element.textContent();
        const lines = text.split('\n');
        
        for (const line of lines) {
          if (line.trim()) {
            // Check that line length doesn't exceed recommended maximum
            expect(line.length).toBeLessThanOrEqual(viewport.maxChars);
          }
        }
      }
    }
  });

  test('should handle high DPI displays', async ({ page }) => {
    // Simulate high DPI display
    await page.addInitScript(() => {
      Object.defineProperty(window, 'devicePixelRatio', {
        get: () => 2
      });
    });

    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    // Check that text remains crisp
    const textElements = await page.locator('p, h1, h2, h3').all();
    for (const element of textElements) {
      const isVisible = await element.isVisible();
      if (!isVisible) continue;

      const textRendering = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.textRendering;
      });

      // Should use optimized text rendering
      expect(['optimizeLegibility', 'geometricPrecision']).toContain(textRendering);
    }
  });

  test('should maintain proper touch targets on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    const touchTargets = await page.locator('button, a, input, select, textarea, [role="button"]').all();
    
    for (const target of touchTargets) {
      const isVisible = await target.isVisible();
      if (!isVisible) continue;

      const boundingBox = await target.boundingBox();
      if (boundingBox) {
        // Minimum touch target size (44px x 44px) per WCAG guidelines
        expect(boundingBox.width).toBeGreaterThanOrEqual(44);
        expect(boundingBox.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('should handle dynamic content resizing', async ({ page }) => {
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');

    // Simulate dynamic content loading
    await page.evaluate(() => {
      const newContent = document.createElement('div');
      newContent.innerHTML = `
        <h2>Dynamically Added Content</h2>
        <p>This is some dynamically added content to test how the layout handles changes in content size and structure.</p>
        <button>Dynamic Button</button>
      `;
      newContent.className = 'dynamic-content';
      document.body.appendChild(newContent);
    });

    await page.waitForTimeout(1000);

    // Check that layout remains stable
    const hasHorizontalScroll = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    expect(hasHorizontalScroll).toBeFalsy();

    // Check that new content is properly styled
    const dynamicContent = await page.locator('.dynamic-content');
    expect(await dynamicContent.isVisible()).toBeTruthy();

    const fontSize = await dynamicContent.locator('p').evaluate(el => {
      const style = window.getComputedStyle(el);
      return parseFloat(style.fontSize);
    });
    expect(fontSize).toBeGreaterThanOrEqual(12);
  });
});
