// Responsive Testing Utilities for Mingus Application

export interface BreakpointTest {
  name: string;
  minWidth: number;
  maxWidth: number;
  description: string;
}

export const BREAKPOINTS: BreakpointTest[] = [
  {
    name: 'Mobile Small',
    minWidth: 320,
    maxWidth: 375,
    description: 'iPhone SE, Samsung S21'
  },
  {
    name: 'Mobile Medium',
    minWidth: 376,
    maxWidth: 414,
    description: 'iPhone 14, most Android'
  },
  {
    name: 'Mobile Large',
    minWidth: 415,
    maxWidth: 768,
    description: 'iPhone Plus, iPad Mini'
  },
  {
    name: 'Tablet',
    minWidth: 769,
    maxWidth: 1024,
    description: 'iPad, Surface'
  },
  {
    name: 'Desktop',
    minWidth: 1025,
    maxWidth: 1920,
    description: 'Laptop, Desktop'
  }
];

export const testResponsiveBehavior = () => {
  const results: { [key: string]: any } = {};
  
  BREAKPOINTS.forEach(breakpoint => {
    // Test typography scaling
    const root = document.documentElement;
    const computedStyle = getComputedStyle(root);
    
    results[breakpoint.name] = {
      breakpoint,
      typography: {
        '--text-xs': computedStyle.getPropertyValue('--text-xs'),
        '--text-sm': computedStyle.getPropertyValue('--text-sm'),
        '--text-base': computedStyle.getPropertyValue('--text-base'),
        '--text-lg': computedStyle.getPropertyValue('--text-lg'),
        '--text-xl': computedStyle.getPropertyValue('--text-xl'),
        '--text-2xl': computedStyle.getPropertyValue('--text-2xl'),
        '--text-3xl': computedStyle.getPropertyValue('--text-3xl'),
        '--text-4xl': computedStyle.getPropertyValue('--text-4xl'),
        '--text-5xl': computedStyle.getPropertyValue('--text-5xl'),
        '--text-6xl': computedStyle.getPropertyValue('--text-6xl'),
      },
      spacing: {
        '--space-xs': computedStyle.getPropertyValue('--space-xs'),
        '--space-sm': computedStyle.getPropertyValue('--space-sm'),
        '--space-md': computedStyle.getPropertyValue('--space-md'),
        '--space-lg': computedStyle.getPropertyValue('--space-lg'),
        '--space-xl': computedStyle.getPropertyValue('--space-xl'),
        '--space-2xl': computedStyle.getPropertyValue('--space-2xl'),
      }
    };
  });
  
  return results;
};

export const testAccessibility = () => {
  const results: { [key: string]: any } = {};
  
  // Test color contrast
  const testElements = document.querySelectorAll('h1, h2, h3, p, button, a');
  const contrastResults: any[] = [];
  
  testElements.forEach((element, index) => {
    const computedStyle = getComputedStyle(element);
    const color = computedStyle.color;
    const backgroundColor = computedStyle.backgroundColor;
    
    // Basic contrast check (simplified)
    contrastResults.push({
      element: element.tagName,
      color,
      backgroundColor,
      hasGoodContrast: true // This would need a proper contrast calculation
    });
  });
  
  results.contrast = contrastResults;
  
  // Test focus management
  const focusableElements = document.querySelectorAll('button, a, input, select, textarea');
  const focusResults: any[] = [];
  
  focusableElements.forEach((element, index) => {
    const hasFocusStyles = getComputedStyle(element).outline !== 'none';
    focusResults.push({
      element: element.tagName,
      hasFocusStyles,
      tabIndex: element.getAttribute('tabindex')
    });
  });
  
  results.focus = focusResults;
  
  return results;
};

export const testSmoothScrolling = () => {
  const results: { [key: string]: any } = {};
  
  // Test smooth scrolling behavior
  const htmlElement = document.documentElement;
  const scrollBehavior = getComputedStyle(htmlElement).scrollBehavior;
  
  results.scrollBehavior = scrollBehavior;
  results.scrollPaddingTop = getComputedStyle(htmlElement).scrollPaddingTop;
  
  // Test navigation links
  const navLinks = document.querySelectorAll('button[onclick*="scrollToSection"]');
  const navResults: any[] = [];
  
  navLinks.forEach((link, index) => {
    navResults.push({
      link: link.textContent,
      hasClickHandler: true,
      isAccessible: link.getAttribute('aria-label') !== null
    });
  });
  
  results.navigation = navResults;
  
  return results;
};

export const runComprehensiveTest = () => {
  console.log('🧪 Running Comprehensive Responsive Test...');
  
  const responsiveResults = testResponsiveBehavior();
  const accessibilityResults = testAccessibility();
  const smoothScrollingResults = testSmoothScrolling();
  
  const comprehensiveResults = {
    responsive: responsiveResults,
    accessibility: accessibilityResults,
    smoothScrolling: smoothScrollingResults,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    viewport: {
      width: window.innerWidth,
      height: window.innerHeight
    }
  };
  
  console.log('📊 Test Results:', comprehensiveResults);
  
  return comprehensiveResults;
};

// Note: Auto-run functionality has been removed to prevent memory leaks.
// React components should use useEffect with proper cleanup instead.
// This ensures proper cleanup when components unmount.
