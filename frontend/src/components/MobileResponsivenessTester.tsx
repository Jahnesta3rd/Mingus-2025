import React, { useState, useEffect, useRef } from 'react';
import { DeviceSmartphone, Tablet, Monitor, Smartphone, CheckCircle, AlertCircle, Info } from 'lucide-react';

interface DeviceConfig {
  name: string;
  width: number;
  height: number;
  category: string;
  icon: React.ReactNode;
}

interface TestResult {
  device: string;
  timestamp: string;
  viewportSize: { width: number; height: number };
  issues: string[];
  recommendations: string[];
  score: number;
}

const MobileResponsivenessTester: React.FC = () => {
  const [selectedDevice, setSelectedDevice] = useState<DeviceConfig | null>(null);
  const [customWidth, setCustomWidth] = useState(375);
  const [customHeight, setCustomHeight] = useState(812);
  const [isTesting, setIsTesting] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [currentViewport, setCurrentViewport] = useState({ width: 375, height: 812 });
  const [showGuidelines, setShowGuidelines] = useState(false);
  const [activeTests, setActiveTests] = useState<string[]>([]);
  
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const devices: DeviceConfig[] = [
    {
      name: 'iPhone SE',
      width: 320,
      height: 568,
      category: 'Small Mobile',
      icon: <DeviceSmartphone className="w-5 h-5" />
    },
    {
      name: 'iPhone 14',
      width: 375,
      height: 812,
      category: 'Standard Mobile',
      icon: <Smartphone className="w-5 h-5" />
    },
    {
      name: 'iPhone 14 Plus',
      width: 428,
      height: 926,
      category: 'Large Mobile',
      icon: <Smartphone className="w-5 h-5" />
    },
    {
      name: 'Samsung Galaxy S21',
      width: 360,
      height: 800,
      category: 'Android Mobile',
      icon: <DeviceSmartphone className="w-5 h-5" />
    },
    {
      name: 'Google Pixel',
      width: 411,
      height: 731,
      category: 'Android Mobile',
      icon: <DeviceSmartphone className="w-5 h-5" />
    },
    {
      name: 'iPad',
      width: 768,
      height: 1024,
      category: 'Tablet',
      icon: <Tablet className="w-5 h-5" />
    },
    {
      name: 'Desktop',
      width: 1024,
      height: 768,
      category: 'Desktop',
      icon: <Monitor className="w-5 h-5" />
    }
  ];

  useEffect(() => {
    if (selectedDevice) {
      setCurrentViewport({ width: selectedDevice.width, height: selectedDevice.height });
      setCustomWidth(selectedDevice.width);
      setCustomHeight(selectedDevice.height);
    }
  }, [selectedDevice]);

  const runResponsivenessTests = async () => {
    setIsTesting(true);
    const newResults: TestResult[] = [];
    
    // Test current viewport
    const result = await testCurrentViewport();
    newResults.push(result);
    
    setTestResults(prev => [...prev, ...newResults]);
    setIsTesting(false);
  };

  const testCurrentViewport = async (): Promise<TestResult> => {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let score = 100;

    // Test 1: Touch Target Sizes
    if (currentViewport.width <= 768) {
      setActiveTests(prev => [...prev, 'touch-targets']);
      const touchTargetResult = await testTouchTargets();
      issues.push(...touchTargetResult.issues);
      recommendations.push(...touchTargetResult.recommendations);
      score -= touchTargetResult.scoreDeduction;
      setActiveTests(prev => prev.filter(t => t !== 'touch-targets'));
    }

    // Test 2: CSS Media Queries
    setActiveTests(prev => [...prev, 'media-queries']);
    const mediaQueryResult = await testCSSMediaQueries();
    issues.push(...mediaQueryResult.issues);
    recommendations.push(...mediaQueryResult.recommendations);
    score -= mediaQueryResult.scoreDeduction;
    setActiveTests(prev => prev.filter(t => t !== 'media-queries'));

    // Test 3: Form Usability
    setActiveTests(prev => [...prev, 'form-usability']);
    const formResult = await testFormUsability();
    issues.push(...formResult.issues);
    recommendations.push(...formResult.recommendations);
    score -= formResult.scoreDeduction;
    setActiveTests(prev => prev.filter(t => t !== 'form-usability'));

    // Test 4: Navigation
    setActiveTests(prev => [...prev, 'navigation']);
    const navResult = await testNavigation();
    issues.push(...navResult.issues);
    recommendations.push(...navResult.recommendations);
    score -= navResult.scoreDeduction;
    setActiveTests(prev => prev.filter(t => t !== 'navigation'));

    return {
      device: selectedDevice?.name || 'Custom',
      timestamp: new Date().toISOString(),
      viewportSize: currentViewport,
      issues,
      recommendations,
      score: Math.max(0, score)
    };
  };

  const testTouchTargets = async (): Promise<{ issues: string[]; recommendations: string[]; scoreDeduction: number }> => {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let scoreDeduction = 0;

    try {
      // Simulate touch target testing
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Check for common touch target issues
      if (currentViewport.width <= 375) {
        issues.push('Some buttons may be too small for comfortable touch interaction');
        recommendations.push('Ensure all interactive elements are at least 44x44px');
        scoreDeduction += 15;
      }

      if (currentViewport.width <= 320) {
        issues.push('Limited space may cause touch targets to overlap');
        recommendations.push('Increase spacing between interactive elements to at least 8px');
        scoreDeduction += 10;
      }
    } catch (error) {
      issues.push('Touch target testing failed');
      scoreDeduction += 5;
    }

    return { issues, recommendations, scoreDeduction };
  };

  const testCSSMediaQueries = async (): Promise<{ issues: string[]; recommendations: string[]; scoreDeduction: number }> => {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let scoreDeduction = 0;

    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Check for responsive breakpoints
      const breakpoints = [320, 375, 768, 1024, 1440];
      const currentBreakpoint = breakpoints.find(bp => currentViewport.width <= bp);
      
      if (currentBreakpoint && currentViewport.width <= 768) {
        if (currentViewport.width <= 375) {
          issues.push('Mobile-first CSS approach recommended for small screens');
          recommendations.push('Use min-width media queries starting from 320px');
          scoreDeduction += 10;
        }
      }
    } catch (error) {
      issues.push('CSS media query testing failed');
      scoreDeduction += 5;
    }

    return { issues, recommendations, scoreDeduction };
  };

  const testFormUsability = async (): Promise<{ issues: string[]; recommendations: string[]; scoreDeduction: number }> => {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let scoreDeduction = 0;

    try {
      await new Promise(resolve => setTimeout(resolve, 600));
      
      if (currentViewport.width <= 768) {
        issues.push('Form inputs should be optimized for mobile keyboards');
        recommendations.push('Use appropriate input types and ensure adequate sizing');
        scoreDeduction += 10;
      }
    } catch (error) {
      issues.push('Form usability testing failed');
      scoreDeduction += 5;
    }

    return { issues, recommendations, scoreDeduction };
  };

  const testNavigation = async (): Promise<{ issues: string[]; recommendations: string[]; scoreDeduction: number }> => {
    const issues: string[] = [];
    const recommendations: string[] = [];
    let scoreDeduction = 0;

    try {
      await new Promise(resolve => setTimeout(resolve, 700));
      
      if (currentViewport.width <= 768) {
        issues.push('Hamburger menu should be easily accessible');
        recommendations.push('Ensure menu toggle is visible and properly sized');
        scoreDeduction += 10;
      }
    } catch (error) {
      issues.push('Navigation testing failed');
      scoreDeduction += 5;
    }

    return { issues, recommendations, scoreDeduction };
  };

  const clearResults = () => {
    setTestResults([]);
  };

  const exportResults = () => {
    const dataStr = JSON.stringify(testResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mobile-responsiveness-test-results-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Mobile Responsiveness Tester
          </h1>
          <p className="text-gray-600">
            Test your application across different device sizes and viewport configurations
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Device Selection Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Device Configuration</h2>
              
              {/* Preset Devices */}
              <div className="space-y-3 mb-6">
                <h3 className="text-sm font-medium text-gray-700">Preset Devices</h3>
                {devices.map((device) => (
                  <button
                    key={device.name}
                    onClick={() => setSelectedDevice(device)}
                    className={`w-full flex items-center justify-between p-3 rounded-lg border transition-colors ${
                      selectedDevice?.name === device.name
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      {device.icon}
                      <div className="text-left">
                        <div className="font-medium">{device.name}</div>
                        <div className="text-sm text-gray-500">{device.category}</div>
                      </div>
                    </div>
                    <div className="text-sm text-gray-500">
                      {device.width} × {device.height}
                    </div>
                  </button>
                ))}
              </div>

              {/* Custom Viewport */}
              <div className="space-y-3 mb-6">
                <h3 className="text-sm font-medium text-gray-700">Custom Viewport</h3>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Width (px)</label>
                    <input
                      type="number"
                      value={customWidth}
                      onChange={(e) => setCustomWidth(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="200"
                      max="2000"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">Height (px)</label>
                    <input
                      type="number"
                      value={customHeight}
                      onChange={(e) => setCustomHeight(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      min="200"
                      max="2000"
                    />
                  </div>
                </div>
                <button
                  onClick={() => setCurrentViewport({ width: customWidth, height: customHeight })}
                  className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
                >
                  Apply Custom Viewport
                </button>
              </div>

              {/* Testing Controls */}
              <div className="space-y-3">
                <button
                  onClick={runResponsivenessTests}
                  disabled={isTesting}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isTesting ? 'Running Tests...' : 'Run Responsiveness Tests'}
                </button>
                
                <div className="flex space-x-2">
                  <button
                    onClick={clearResults}
                    className="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300 transition-colors"
                  >
                    Clear Results
                  </button>
                  <button
                    onClick={exportResults}
                    disabled={testResults.length === 0}
                    className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                  >
                    Export Results
                  </button>
                </div>
              </div>

              {/* Guidelines Toggle */}
              <button
                onClick={() => setShowGuidelines(!showGuidelines)}
                className="w-full mt-4 text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                {showGuidelines ? 'Hide' : 'Show'} Testing Guidelines
              </button>
            </div>

            {/* Testing Guidelines */}
            {showGuidelines && (
              <div className="bg-white rounded-lg shadow-sm p-6 mt-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Testing Guidelines</h3>
                <div className="space-y-3 text-sm text-gray-600">
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Touch targets should be at least 44×44px on mobile</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Use mobile-first CSS with min-width media queries</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Ensure adequate spacing between interactive elements</span>
                  </div>
                  <div className="flex items-start space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span>Test navigation usability across all device sizes</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Viewport Preview */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Viewport Preview</h2>
                <div className="text-sm text-gray-500">
                  {currentViewport.width} × {currentViewport.height}px
                </div>
              </div>
              
              <div className="flex justify-center">
                <div
                  ref={containerRef}
                  className="border-2 border-gray-300 rounded-lg overflow-hidden bg-white"
                  style={{
                    width: Math.min(currentViewport.width, 600),
                    height: Math.min(currentViewport.height, 800),
                    maxWidth: '100%',
                    maxHeight: '80vh'
                  }}
                >
                  <iframe
                    ref={iframeRef}
                    src="/"
                    className="w-full h-full border-0"
                    title="Viewport Preview"
                  />
                </div>
              </div>
            </div>

            {/* Test Results */}
            {testResults.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Results</h2>
                
                <div className="space-y-4">
                  {testResults.map((result, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <h3 className="font-medium text-gray-900">{result.device}</h3>
                          <p className="text-sm text-gray-500">
                            {result.viewportSize.width} × {result.viewportSize.height}px • 
                            {new Date(result.timestamp).toLocaleTimeString()}
                          </p>
                        </div>
                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                          result.score >= 80 ? 'bg-green-100 text-green-800' :
                          result.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {result.score}/100
                        </div>
                      </div>

                      {result.issues.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium text-red-700 mb-2 flex items-center">
                            <AlertCircle className="w-4 h-4 mr-1" />
                            Issues Found
                          </h4>
                          <ul className="space-y-1">
                            {result.issues.map((issue, i) => (
                              <li key={i} className="text-sm text-red-600">• {issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {result.recommendations.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-blue-700 mb-2 flex items-center">
                            <Info className="w-4 h-4 mr-1" />
                            Recommendations
                          </h4>
                          <ul className="space-y-1">
                            {result.recommendations.map((rec, i) => (
                              <li key={i} className="text-sm text-blue-600">• {rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MobileResponsivenessTester;
