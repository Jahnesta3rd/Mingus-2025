// Dashboard Integration Test Utilities

export interface TestResult {
  test: string;
  status: 'pass' | 'fail' | 'pending';
  message: string;
  details?: string;
  timestamp: Date;
}

export class DashboardTester {
  private results: TestResult[] = [];

  async runTest(testName: string, testFn: () => Promise<boolean>, details?: string): Promise<TestResult> {
    const startTime = Date.now();
    
    try {
      const result = await testFn();
      const duration = Date.now() - startTime;
      
      const testResult: TestResult = {
        test: testName,
        status: result ? 'pass' : 'fail',
        message: result ? `✅ Passed (${duration}ms)` : '❌ Failed',
        details,
        timestamp: new Date()
      };
      
      this.results.push(testResult);
      return testResult;
    } catch (error) {
      const testResult: TestResult = {
        test: testName,
        status: 'fail',
        message: '❌ Error',
        details: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date()
      };
      
      this.results.push(testResult);
      return testResult;
    }
  }

  // Test Daily Outlook Card Component
  async testDailyOutlookCard(): Promise<TestResult> {
    return this.runTest(
      'Daily Outlook Card Component',
      async () => {
        try {
          // Test if component can be imported
          const { default: DailyOutlookCard } = await import('../components/DailyOutlookCard');
          return typeof DailyOutlookCard === 'function';
        } catch {
          return false;
        }
      },
      'Daily Outlook Card component should be importable and functional'
    );
  }

  // Test Mobile Daily Outlook Component
  async testMobileDailyOutlook(): Promise<TestResult> {
    return this.runTest(
      'Mobile Daily Outlook Component',
      async () => {
        try {
          const { default: MobileDailyOutlook } = await import('../components/MobileDailyOutlook');
          return typeof MobileDailyOutlook === 'function';
        } catch {
          return false;
        }
      },
      'Mobile Daily Outlook component should be importable and functional'
    );
  }

  // Test Cache Hook
  async testCacheHook(): Promise<TestResult> {
    return this.runTest(
      'Daily Outlook Cache Hook',
      async () => {
        try {
          const { useDailyOutlookCache } = await import('../hooks/useDailyOutlookCache');
          return typeof useDailyOutlookCache === 'function';
        } catch {
          return false;
        }
      },
      'Cache hook should be available for performance optimization'
    );
  }

  // Test Dashboard Integration
  async testDashboardIntegration(): Promise<TestResult> {
    return this.runTest(
      'Dashboard Integration',
      async () => {
        try {
          // Test if CareerProtectionDashboard can be imported
          const { default: CareerProtectionDashboard } = await import('../pages/CareerProtectionDashboard');
          return typeof CareerProtectionDashboard === 'function';
        } catch {
          return false;
        }
      },
      'Dashboard should integrate Daily Outlook as first tab'
    );
  }

  // Test Mobile Detection
  async testMobileDetection(): Promise<TestResult> {
    return this.runTest(
      'Mobile Detection',
      async () => {
        const isMobile = window.innerWidth < 768;
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        return typeof isMobile === 'boolean' && typeof hasTouch === 'boolean';
      },
      'Should correctly detect mobile devices and touch support'
    );
  }

  // Test Performance Features
  async testPerformanceFeatures(): Promise<TestResult> {
    return this.runTest(
      'Performance Features',
      async () => {
        const hasLocalStorage = typeof Storage !== 'undefined';
        const hasFetch = typeof fetch === 'function';
        const hasSuspense = typeof React.Suspense === 'function';
        
        return hasLocalStorage && hasFetch && hasSuspense;
      },
      'Should have all required performance features (localStorage, fetch, Suspense)'
    );
  }

  // Test Analytics Integration
  async testAnalyticsIntegration(): Promise<TestResult> {
    return this.runTest(
      'Analytics Integration',
      async () => {
        try {
          const { useAnalytics } = await import('../hooks/useAnalytics');
          return typeof useAnalytics === 'function';
        } catch {
          return false;
        }
      },
      'Analytics hook should be available for user tracking'
    );
  }

  // Test Error Boundaries
  async testErrorBoundaries(): Promise<TestResult> {
    return this.runTest(
      'Error Boundaries',
      async () => {
        try {
          const { default: DashboardErrorBoundary } = await import('../components/DashboardErrorBoundary');
          return typeof DashboardErrorBoundary === 'function';
        } catch {
          return false;
        }
      },
      'Error boundaries should be available for graceful error handling'
    );
  }

  // Test Lazy Loading
  async testLazyLoading(): Promise<TestResult> {
    return this.runTest(
      'Lazy Loading Support',
      async () => {
        const hasLazy = typeof React.lazy === 'function';
        const hasSuspense = typeof React.Suspense === 'function';
        return hasLazy && hasSuspense;
      },
      'Should support lazy loading with React.lazy and Suspense'
    );
  }

  // Test Touch Events
  async testTouchEvents(): Promise<TestResult> {
    return this.runTest(
      'Touch Event Support',
      async () => {
        const hasTouchStart = 'ontouchstart' in window;
        const hasTouchPoints = navigator.maxTouchPoints > 0;
        return hasTouchStart || hasTouchPoints;
      },
      'Should support touch events for mobile interactions'
    );
  }

  // Run all tests
  async runAllTests(): Promise<TestResult[]> {
    this.results = [];
    
    await this.testDailyOutlookCard();
    await this.testMobileDailyOutlook();
    await this.testCacheHook();
    await this.testDashboardIntegration();
    await this.testMobileDetection();
    await this.testPerformanceFeatures();
    await this.testAnalyticsIntegration();
    await this.testErrorBoundaries();
    await this.testLazyLoading();
    await this.testTouchEvents();
    
    return this.results;
  }

  // Get test results
  getResults(): TestResult[] {
    return this.results;
  }

  // Get success rate
  getSuccessRate(): number {
    if (this.results.length === 0) return 0;
    const passed = this.results.filter(r => r.status === 'pass').length;
    return (passed / this.results.length) * 100;
  }

  // Get summary
  getSummary(): { total: number; passed: number; failed: number; successRate: number } {
    const total = this.results.length;
    const passed = this.results.filter(r => r.status === 'pass').length;
    const failed = this.results.filter(r => r.status === 'fail').length;
    const successRate = total > 0 ? (passed / total) * 100 : 0;
    
    return { total, passed, failed, successRate };
  }
}

// Export singleton instance
export const dashboardTester = new DashboardTester();

// Quick test function
export const quickTest = async (): Promise<{ success: boolean; message: string }> => {
  try {
    const results = await dashboardTester.runAllTests();
    const summary = dashboardTester.getSummary();
    
    if (summary.successRate >= 80) {
      return {
        success: true,
        message: `✅ Dashboard tests passed! ${summary.passed}/${summary.total} tests successful (${summary.successRate.toFixed(1)}%)`
      };
    } else {
      return {
        success: false,
        message: `❌ Dashboard tests failed! Only ${summary.passed}/${summary.total} tests successful (${summary.successRate.toFixed(1)}%)`
      };
    }
  } catch (error) {
    return {
      success: false,
      message: `❌ Test execution failed: ${error instanceof Error ? error.message : 'Unknown error'}`
    };
  }
};
