#!/usr/bin/env node

const { execSync } = require('child_process');

console.log('🧪 Running OptimalLocationRouter Tests...\n');

try {
  // Run the tests with a simple configuration
  execSync('npx jest src/components/OptimalLocation/__tests__/OptimalLocationRouter.test.tsx --testEnvironment=jsdom --no-coverage --verbose', {
    stdio: 'inherit',
    cwd: process.cwd()
  });
  
  console.log('\n✅ Tests completed successfully!');
} catch (error) {
  console.error('\n❌ Tests failed:', error.message);
  process.exit(1);
}
