#!/usr/bin/env node
/**
 * Test Runner for Mingus Application
 * Runs different test suites to verify application functionality
 */

const { exec } = require('child_process');
const path = require('path');

const testSuites = [
  {
    name: 'Application Health Check',
    file: 'application-health-check.cy.js',
    description: 'Basic connectivity and core functionality tests'
  },
  {
    name: 'Authentication Flow',
    file: 'auth-flow-detailed.cy.js', 
    description: 'Detailed login/registration testing'
  },
  {
    name: 'Health & Onboarding Features',
    file: 'health-onboarding-features.cy.js',
    description: 'Health check-in and onboarding system tests'
  },
  {
    name: 'Basic Auth Flow (Legacy)',
    file: 'basic-auth-flow.cy.js',
    description: 'Original basic authentication tests'
  }
];

function runTestSuite(suite) {
  return new Promise((resolve, reject) => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`Running: ${suite.name}`);
    console.log(`Description: ${suite.description}`);
    console.log(`${'='.repeat(60)}\n`);

    const command = `npx cypress run --spec "cypress/e2e/${suite.file}" --reporter spec`;
    
    const child = exec(command, { cwd: __dirname }, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error running ${suite.name}:`, error.message);
        resolve({ suite, success: false, error: error.message, output: stderr });
        return;
      }
      
      console.log(stdout);
      resolve({ suite, success: true, output: stdout });
    });

    child.stdout.on('data', (data) => {
      process.stdout.write(data);
    });

    child.stderr.on('data', (data) => {
      process.stderr.write(data);
    });
  });
}

async function runAllTests() {
  console.log('🚀 Starting Mingus Application Test Suite');
  console.log(`📁 Test directory: ${__dirname}`);
  console.log(`⏰ Started at: ${new Date().toISOString()}\n`);

  const results = [];
  
  for (const suite of testSuites) {
    try {
      const result = await runTestSuite(suite);
      results.push(result);
      
      if (result.success) {
        console.log(`✅ ${suite.name} completed successfully`);
      } else {
        console.log(`❌ ${suite.name} failed: ${result.error}`);
      }
    } catch (error) {
      console.error(`💥 Error running ${suite.name}:`, error);
      results.push({ suite, success: false, error: error.message });
    }
  }

  // Summary
  console.log(`\n${'='.repeat(60)}`);
  console.log('📊 TEST SUMMARY');
  console.log(`${'='.repeat(60)}`);
  
  const successful = results.filter(r => r.success).length;
  const failed = results.filter(r => !r.success).length;
  
  console.log(`✅ Successful: ${successful}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${((successful / results.length) * 100).toFixed(1)}%`);
  
  if (failed > 0) {
    console.log('\n❌ Failed Tests:');
    results.filter(r => !r.success).forEach(result => {
      console.log(`   - ${result.suite.name}: ${result.error}`);
    });
  }
  
  console.log(`\n⏰ Completed at: ${new Date().toISOString()}`);
  
  return results;
}

function runSpecificTest(testName) {
  const suite = testSuites.find(s => 
    s.name.toLowerCase().includes(testName.toLowerCase()) ||
    s.file.toLowerCase().includes(testName.toLowerCase())
  );
  
  if (!suite) {
    console.error(`❌ Test suite not found: ${testName}`);
    console.log('Available test suites:');
    testSuites.forEach(s => console.log(`   - ${s.name} (${s.file})`));
    return;
  }
  
  return runTestSuite(suite);
}

// CLI handling
const args = process.argv.slice(2);

if (args.length === 0) {
  // Run all tests
  runAllTests().then(results => {
    const exitCode = results.some(r => !r.success) ? 1 : 0;
    process.exit(exitCode);
  });
} else if (args[0] === '--help' || args[0] === '-h') {
  console.log('Mingus Application Test Runner');
  console.log('\nUsage:');
  console.log('  node run-tests.js                    # Run all tests');
  console.log('  node run-tests.js <test-name>        # Run specific test');
  console.log('  node run-tests.js --help             # Show this help');
  console.log('\nAvailable test suites:');
  testSuites.forEach(suite => {
    console.log(`  - ${suite.name}: ${suite.description}`);
  });
} else {
  // Run specific test
  runSpecificTest(args[0]).then(result => {
    if (result) {
      const exitCode = result.success ? 0 : 1;
      process.exit(exitCode);
    } else {
      process.exit(1);
    }
  });
} 