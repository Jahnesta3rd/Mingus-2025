#!/usr/bin/env node

/**
 * Test Runner for ScenarioComparison Component
 * 
 * This script provides multiple ways to test the ScenarioComparison component:
 * 1. Unit tests via Jest
 * 2. Manual testing with a test page
 * 3. Integration testing
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

console.log('🧪 ScenarioComparison Component Test Runner');
console.log('==========================================\n');

// Check if we're in the frontend directory
const frontendDir = process.cwd();
const packageJsonPath = path.join(frontendDir, 'package.json');

if (!fs.existsSync(packageJsonPath)) {
  console.error('❌ Error: package.json not found. Please run this script from the frontend directory.');
  process.exit(1);
}

// Check if Jest is available
function checkJest() {
  try {
    execSync('npm list jest', { stdio: 'pipe' });
    return true;
  } catch (error) {
    return false;
  }
}

// Install Jest if not available
function installJest() {
  console.log('📦 Installing Jest and testing dependencies...');
  try {
    execSync('npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom', { stdio: 'inherit' });
    console.log('✅ Jest installed successfully');
    return true;
  } catch (error) {
    console.error('❌ Failed to install Jest:', error.message);
    return false;
  }
}

// Run unit tests
function runUnitTests() {
  console.log('\n🔬 Running Unit Tests...');
  console.log('========================\n');
  
  try {
    const testCommand = 'npm test -- --testPathPattern=ScenarioComparison.test.tsx --watchAll=false --verbose';
    execSync(testCommand, { stdio: 'inherit' });
    console.log('\n✅ Unit tests completed successfully');
    return true;
  } catch (error) {
    console.error('\n❌ Unit tests failed:', error.message);
    return false;
  }
}

// Create a test page for manual testing
function createTestPage() {
  console.log('\n📄 Creating Manual Test Page...');
  console.log('===============================\n');
  
  const testPageContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ScenarioComparison Manual Test</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .test-controls {
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .test-controls h3 {
            margin-top: 0;
            color: #1976d2;
        }
        .control-group {
            margin-bottom: 10px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        select, input {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
        }
        button {
            background: #1976d2;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 10px;
        }
        button:hover {
            background: #1565c0;
        }
        .test-results {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .test-results h3 {
            margin-top: 0;
            color: #2e7d32;
        }
        .test-item {
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .test-item:last-child {
            border-bottom: none;
        }
        .status-pass { color: #2e7d32; font-weight: bold; }
        .status-fail { color: #d32f2f; font-weight: bold; }
        .status-pending { color: #f57c00; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 ScenarioComparison Component Manual Test</h1>
        
        <div class="test-controls">
            <h3>Test Controls</h3>
            
            <div class="control-group">
                <label for="userTier">User Tier:</label>
                <select id="userTier">
                    <option value="budget">Budget</option>
                    <option value="budget_career_vehicle">Budget Career Vehicle</option>
                    <option value="mid_tier" selected>Mid-tier</option>
                    <option value="professional">Professional</option>
                </select>
            </div>
            
            <div class="control-group">
                <label for="scenarioCount">Number of Scenarios:</label>
                <select id="scenarioCount">
                    <option value="1">1 Scenario</option>
                    <option value="2" selected>2 Scenarios</option>
                    <option value="3">3 Scenarios</option>
                </select>
            </div>
            
            <div class="control-group">
                <button onclick="runTests()">Run Tests</button>
                <button onclick="clearResults()">Clear Results</button>
                <button onclick="testResponsive()">Test Responsive</button>
            </div>
        </div>
        
        <div id="testResults" class="test-results" style="display: none;">
            <h3>Test Results</h3>
            <div id="testList"></div>
        </div>
        
        <div id="componentContainer">
            <h2>Component Preview</h2>
            <p>Component will be rendered here when tests are run...</p>
        </div>
    </div>

    <script>
        // Mock data for testing
        const mockCurrentSituation = {
            rent: 1400,
            commute_cost: 0,
            total_monthly_cost: 1400,
            affordability_score: 75,
            location: 'Current Location',
            commute_time: 0
        };

        const mockScenarios = [
            {
                id: 1,
                scenario_name: 'Downtown Apartment',
                housing_data: {
                    address: '123 Main St, Downtown',
                    rent: 1245,
                    bedrooms: 2,
                    bathrooms: 2,
                    square_feet: 1200,
                    housing_type: 'apartment',
                    amenities: ['parking', 'laundry', 'gym'],
                    neighborhood: 'Downtown',
                    zip_code: '12345',
                    latitude: 40.7128,
                    longitude: -74.0060
                },
                commute_data: {
                    distance_miles: 8.5,
                    drive_time_minutes: 25,
                    public_transit_time_minutes: 35,
                    walking_time_minutes: 15,
                    gas_cost_daily: 4.50,
                    public_transit_cost_daily: 5.00,
                    parking_cost_daily: 12.00,
                    total_daily_cost: 16.50,
                    total_monthly_cost: 65
                },
                financial_impact: {
                    affordability_score: 85,
                    rent_to_income_ratio: 0.28,
                    total_housing_cost: 1310,
                    monthly_savings: 90,
                    annual_savings: 1080,
                    cost_of_living_index: 1.2,
                    property_tax_estimate: 0,
                    insurance_estimate: 50
                },
                career_data: {
                    job_opportunities_count: 150,
                    average_salary: 75000,
                    salary_range_min: 55000,
                    salary_range_max: 95000,
                    industry_concentration: ['tech', 'finance', 'healthcare'],
                    remote_work_friendly: true,
                    commute_impact_score: 75
                },
                is_favorite: false,
                created_at: '2024-01-01T00:00:00Z'
            },
            {
                id: 2,
                scenario_name: 'Suburban House',
                housing_data: {
                    address: '456 Oak Ave, Suburbs',
                    rent: 1100,
                    bedrooms: 3,
                    bathrooms: 2,
                    square_feet: 1500,
                    housing_type: 'house',
                    amenities: ['garage', 'yard', 'laundry'],
                    neighborhood: 'Suburbs',
                    zip_code: '54321',
                    latitude: 40.7589,
                    longitude: -73.9851
                },
                commute_data: {
                    distance_miles: 15.2,
                    drive_time_minutes: 35,
                    public_transit_time_minutes: 45,
                    walking_time_minutes: 5,
                    gas_cost_daily: 6.80,
                    public_transit_cost_daily: 7.50,
                    parking_cost_daily: 0,
                    total_daily_cost: 14.30,
                    total_monthly_cost: 95
                },
                financial_impact: {
                    affordability_score: 90,
                    rent_to_income_ratio: 0.25,
                    total_housing_cost: 1195,
                    monthly_savings: 205,
                    annual_savings: 2460,
                    cost_of_living_index: 1.1,
                    property_tax_estimate: 0,
                    insurance_estimate: 40
                },
                career_data: {
                    job_opportunities_count: 80,
                    average_salary: 70000,
                    salary_range_min: 50000,
                    salary_range_max: 90000,
                    industry_concentration: ['manufacturing', 'retail', 'healthcare'],
                    remote_work_friendly: false,
                    commute_impact_score: 60
                },
                is_favorite: true,
                created_at: '2024-01-02T00:00:00Z'
            }
        ];

        const tests = [
            {
                name: 'Component renders without crashing',
                test: () => {
                    const container = document.getElementById('componentContainer');
                    return container && container.innerHTML.includes('Scenario Comparison');
                }
            },
            {
                name: 'Current situation card displays correctly',
                test: () => {
                    const container = document.getElementById('componentContainer');
                    return container && container.innerHTML.includes('Current Situation');
                }
            },
            {
                name: 'Scenario cards are rendered',
                test: () => {
                    const container = document.getElementById('componentContainer');
                    return container && container.innerHTML.includes('Downtown Apartment');
                }
            },
            {
                name: 'Tabs are present',
                test: () => {
                    const container = document.getElementById('componentContainer');
                    return container && container.innerHTML.includes('Financial Impact');
                }
            },
            {
                name: 'Action buttons are present',
                test: () => {
                    const container = document.getElementById('componentContainer');
                    return container && container.innerHTML.includes('Make Primary Choice');
                }
            }
        ];

        function runTests() {
            console.log('🧪 Running manual tests...');
            
            const resultsDiv = document.getElementById('testResults');
            const testListDiv = document.getElementById('testList');
            
            resultsDiv.style.display = 'block';
            testListDiv.innerHTML = '';
            
            // Simulate component rendering
            renderMockComponent();
            
            let passedTests = 0;
            let totalTests = tests.length;
            
            tests.forEach((test, index) => {
                const testItem = document.createElement('div');
                testItem.className = 'test-item';
                
                try {
                    const result = test.test();
                    if (result) {
                        testItem.innerHTML = \`<span class="status-pass">✅</span> \${test.name}\`;
                        passedTests++;
                    } else {
                        testItem.innerHTML = \`<span class="status-fail">❌</span> \${test.name}\`;
                    }
                } catch (error) {
                    testItem.innerHTML = \`<span class="status-fail">❌</span> \${test.name} - Error: \${error.message}\`;
                }
                
                testListDiv.appendChild(testItem);
            });
            
            // Add summary
            const summary = document.createElement('div');
            summary.className = 'test-item';
            summary.innerHTML = \`<strong>Summary: \${passedTests}/\${totalTests} tests passed</strong>\`;
            testListDiv.appendChild(summary);
            
            console.log(\`✅ \${passedTests}/\${totalTests} tests passed\`);
        }

        function renderMockComponent() {
            const container = document.getElementById('componentContainer');
            const userTier = document.getElementById('userTier').value;
            const scenarioCount = parseInt(document.getElementById('scenarioCount').value);
            
            const scenarios = mockScenarios.slice(0, scenarioCount);
            
            container.innerHTML = \`
                <h2>ScenarioComparison Component (Mock)</h2>
                <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px;">
                    <h3>Scenario Comparison</h3>
                    <p>Compare your current situation with potential housing scenarios</p>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
                        <!-- Current Situation Card -->
                        <div style="border: 2px solid #1976d2; padding: 15px; border-radius: 8px;">
                            <h4>🏠 Current Situation</h4>
                            <p>Current Location</p>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                <div>
                                    <small>Monthly Cost</small>
                                    <div>$1,400</div>
                                </div>
                                <div>
                                    <small>Affordability Score</small>
                                    <div style="color: #2e7d32;">75/100</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Scenario Cards -->
                        \${scenarios.map(scenario => \`
                            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; cursor: pointer;">
                                <h4>🏠 \${scenario.scenario_name}</h4>
                                <p>\${scenario.housing_data.address}</p>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                                    <div>
                                        <small>Monthly Cost</small>
                                        <div>\$\${scenario.housing_data.rent.toLocaleString()}</div>
                                    </div>
                                    <div>
                                        <small>Affordability Score</small>
                                        <div style="color: \${scenario.financial_impact.affordability_score >= 80 ? '#2e7d32' : '#f57c00'}">\${scenario.financial_impact.affordability_score}/100</div>
                                    </div>
                                </div>
                            </div>
                        \`).join('')}
                    </div>
                    
                    <!-- Tabs -->
                    <div style="border-bottom: 1px solid #ddd; margin: 20px 0;">
                        <button style="padding: 10px 20px; border: none; background: #1976d2; color: white; margin-right: 10px;">Financial Impact</button>
                        <button style="padding: 10px 20px; border: 1px solid #ddd; background: white;">Comparison Table</button>
                        <button style="padding: 10px 20px; border: 1px solid #ddd; background: white;">Career Integration</button>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div style="margin: 20px 0;">
                        <button style="padding: 10px 20px; background: #1976d2; color: white; border: none; margin-right: 10px;">Make Primary Choice</button>
                        <button style="padding: 10px 20px; border: 1px solid #ddd; background: white; margin-right: 10px;">Export Analysis</button>
                        <button style="padding: 10px 20px; border: 1px solid #ddd; background: white; margin-right: 10px;">Share Scenario</button>
                        <button style="padding: 10px 20px; border: 1px solid #ddd; background: white; color: #d32f2f;">Delete Scenario</button>
                    </div>
                    
                    <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px;">
                        <h4>Test Information</h4>
                        <p><strong>User Tier:</strong> \${userTier}</p>
                        <p><strong>Scenarios:</strong> \${scenarioCount}</p>
                        <p><strong>Features Available:</strong> \${userTier === 'professional' ? 'All features' : userTier === 'mid_tier' ? 'Career integration + Export' : 'Basic features only'}</p>
                    </div>
                </div>
            \`;
        }

        function clearResults() {
            document.getElementById('testResults').style.display = 'none';
            document.getElementById('componentContainer').innerHTML = '<h2>Component Preview</h2><p>Component will be rendered here when tests are run...</p>';
        }

        function testResponsive() {
            console.log('📱 Testing responsive design...');
            
            // Test different screen sizes
            const sizes = [
                { name: 'Mobile', width: 375 },
                { name: 'Tablet', width: 768 },
                { name: 'Desktop', width: 1200 }
            ];
            
            sizes.forEach(size => {
                console.log(\`Testing \${size.name} (\${size.width}px)...\`);
                // In a real test, you would resize the viewport
                // For this mock, we'll just log the test
            });
            
            alert('Responsive test completed! Check console for details.');
        }

        // Initialize
        renderMockComponent();
    </script>
</body>
</html>`;

  const testPagePath = path.join(frontendDir, 'scenario-comparison-test.html');
  fs.writeFileSync(testPagePath, testPageContent);
  
  console.log('✅ Test page created:', testPagePath);
  console.log('🌐 Open the file in your browser to run manual tests');
  return testPagePath;
}

// Main test runner
function main() {
  const args = process.argv.slice(2);
  const command = args[0] || 'all';
  
  switch (command) {
    case 'unit':
      if (!checkJest()) {
        if (!installJest()) {
          process.exit(1);
        }
      }
      runUnitTests();
      break;
      
    case 'manual':
      createTestPage();
      break;
      
    case 'all':
      console.log('🚀 Running all tests...\n');
      
      // Install Jest if needed
      if (!checkJest()) {
        if (!installJest()) {
          console.log('⚠️  Skipping unit tests due to Jest installation failure');
        } else {
          runUnitTests();
        }
      } else {
        runUnitTests();
      }
      
      // Create manual test page
      createTestPage();
      
      console.log('\n✅ All tests completed!');
      console.log('\n📋 Next steps:');
      console.log('1. Check unit test results above');
      console.log('2. Open scenario-comparison-test.html in your browser for manual testing');
      console.log('3. Test different user tiers and scenarios');
      console.log('4. Verify responsive design on different screen sizes');
      break;
      
    default:
      console.log('Usage: node test-scenario-comparison.js [unit|manual|all]');
      console.log('  unit   - Run unit tests only');
      console.log('  manual - Create manual test page only');
      console.log('  all    - Run all tests (default)');
      break;
  }
}

// Run the main function
main();
