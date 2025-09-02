const { test, expect } = require('@playwright/test');
const { AxeBuilder } = require('@axe-core/playwright');

test.describe('Accessibility and Readability Compliance', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/mobile_readability_test.html');
    await page.waitForLoadState('networkidle');
  });

  test('should pass axe-core accessibility audit', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
    
    // Log detailed results for debugging
    if (accessibilityScanResults.violations.length > 0) {
      console.log('Accessibility violations found:', accessibilityScanResults.violations);
    }
  });

  test('should have proper heading hierarchy', async ({ page }) => {
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all();
    const headingLevels = await Promise.all(
      headings.map(async (heading) => {
        const tagName = await heading.evaluate(el => el.tagName.toLowerCase());
        const text = await heading.textContent();
        return { level: tagName, text: text.trim() };
      })
    );

    // Check for proper heading hierarchy (no skipping levels)
    let previousLevel = 0;
    for (const heading of headingLevels) {
      const currentLevel = parseInt(heading.level.charAt(1));
      expect(currentLevel - previousLevel).toBeLessThanOrEqual(1);
      previousLevel = currentLevel;
    }
  });

  test('should have sufficient color contrast ratios', async ({ page }) => {
    // Test text contrast ratios
    const textElements = await page.locator('p, span, div, h1, h2, h3, h4, h5, h6, a, button, input, label').all();
    
    for (const element of textElements) {
      const isVisible = await element.isVisible();
      if (!isVisible) continue;

      const color = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.color;
      });

      const backgroundColor = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.backgroundColor;
      });

      // Calculate contrast ratio (simplified check)
      const contrastRatio = await page.evaluate((color, bgColor) => {
        // Convert colors to RGB and calculate luminance
        const getLuminance = (r, g, b) => {
          const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
          });
          return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
        };

        // Parse color values (simplified)
        const parseColor = (colorStr) => {
          if (colorStr.startsWith('rgb')) {
            const match = colorStr.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
            return match ? [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])] : [0, 0, 0];
          }
          return [0, 0, 0]; // Default fallback
        };

        const [r1, g1, b1] = parseColor(color);
        const [r2, g2, b2] = parseColor(bgColor);

        const lum1 = getLuminance(r1, g1, b1);
        const lum2 = getLuminance(r2, g2, b2);

        const brightest = Math.max(lum1, lum2);
        const darkest = Math.min(lum1, lum2);

        return (brightest + 0.05) / (darkest + 0.05);
      }, color, backgroundColor);

      // WCAG AA requires 4.5:1 for normal text, 3:1 for large text
      expect(contrastRatio).toBeGreaterThanOrEqual(3.0);
    }
  });

  test('should have proper focus indicators', async ({ page }) => {
    const focusableElements = await page.locator('a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])').all();
    
    for (const element of focusableElements) {
      await element.focus();
      
      const hasFocusIndicator = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.outline !== 'none' || 
               style.boxShadow !== 'none' || 
               style.borderColor !== 'initial' ||
               el.classList.contains('focus-visible');
      });

      expect(hasFocusIndicator).toBeTruthy();
    }
  });

  test('should have proper alt text for images', async ({ page }) => {
    const images = await page.locator('img').all();
    
    for (const image of images) {
      const alt = await image.getAttribute('alt');
      const isDecorative = await image.getAttribute('role') === 'presentation' || 
                          await image.getAttribute('aria-hidden') === 'true';
      
      if (!isDecorative) {
        expect(alt).toBeTruthy();
        expect(alt.trim()).not.toBe('');
      }
    }
  });

  test('should have proper form labels', async ({ page }) => {
    const formControls = await page.locator('input, textarea, select').all();
    
    for (const control of formControls) {
      const id = await control.getAttribute('id');
      const ariaLabel = await control.getAttribute('aria-label');
      const ariaLabelledBy = await control.getAttribute('aria-labelledby');
      
      if (id) {
        const label = await page.locator(`label[for="${id}"]`).first();
        expect(await label.count()).toBeGreaterThan(0);
      } else if (!ariaLabel && !ariaLabelledBy) {
        // Check if it's wrapped in a label
        const parentLabel = await control.locator('xpath=ancestor::label').first();
        expect(await parentLabel.count()).toBeGreaterThan(0);
      }
    }
  });

  test('should have proper ARIA attributes', async ({ page }) => {
    // Check for proper ARIA landmarks
    const landmarks = await page.locator('[role="banner"], [role="main"], [role="navigation"], [role="contentinfo"]').all();
    expect(landmarks.length).toBeGreaterThan(0);

    // Check for proper ARIA labels on interactive elements
    const interactiveElements = await page.locator('button, a, input, textarea, select').all();
    
    for (const element of interactiveElements) {
      const ariaLabel = await element.getAttribute('aria-label');
      const ariaLabelledBy = await element.getAttribute('aria-labelledby');
      const hasText = await element.textContent();
      
      // At least one of these should be present
      const hasAccessibleName = ariaLabel || ariaLabelledBy || (hasText && hasText.trim() !== '');
      expect(hasAccessibleName).toBeTruthy();
    }
  });

  test('should be keyboard navigable', async ({ page }) => {
    // Test tab navigation
    await page.keyboard.press('Tab');
    
    const firstFocused = await page.evaluate(() => document.activeElement);
    expect(firstFocused).not.toBeNull();
    
    // Test that we can tab through all focusable elements
    const focusableElements = await page.locator('a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])').all();
    
    for (let i = 0; i < Math.min(focusableElements.length, 10); i++) {
      await page.keyboard.press('Tab');
      const focused = await page.evaluate(() => document.activeElement);
      expect(focused).not.toBeNull();
    }
  });

  test('should have proper text sizing and spacing', async ({ page }) => {
    const textElements = await page.locator('p, span, div, h1, h2, h3, h4, h5, h6').all();
    
    for (const element of textElements) {
      const isVisible = await element.isVisible();
      if (!isVisible) continue;

      const fontSize = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return parseFloat(style.fontSize);
      });

      const lineHeight = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return parseFloat(style.lineHeight);
      });

      // Check minimum font size (12px for accessibility)
      expect(fontSize).toBeGreaterThanOrEqual(12);
      
      // Check line height for readability (minimum 1.2)
      expect(lineHeight).toBeGreaterThanOrEqual(1.2);
    }
  });

  test('should handle reduced motion preferences', async ({ page }) => {
    // Test with reduced motion preference
    await page.addInitScript(() => {
      Object.defineProperty(window.matchMedia, 'matches', {
        writable: true,
        value: true
      });
      window.matchMedia = (query) => ({
        matches: query.includes('prefers-reduced-motion'),
        addListener: () => {},
        removeListener: () => {}
      });
    });

    await page.reload();
    
    // Check that animations are disabled or reduced
    const animatedElements = await page.locator('[style*="animation"], [style*="transition"]').all();
    
    for (const element of animatedElements) {
      const animationDuration = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return style.animationDuration || style.transitionDuration;
      });
      
      // Animation duration should be very short or none for reduced motion
      const duration = parseFloat(animationDuration);
      expect(duration).toBeLessThanOrEqual(0.1);
    }
  });
});
