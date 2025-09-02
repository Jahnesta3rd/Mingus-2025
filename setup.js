#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('🚀 Setting up Automated Readability Compliance Testing Framework...\n');

// Create necessary directories
const directories = [
  'reports',
  'logs',
  'baseline-screenshots',
  'current-screenshots',
  'diff-screenshots',
  'tests'
];

console.log('📁 Creating directories...');
directories.forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
    console.log(`  ✓ Created ${dir}/`);
  } else {
    console.log(`  ✓ ${dir}/ already exists`);
  }
});

// Create .env file if it doesn't exist
if (!fs.existsSync('.env')) {
  const envContent = `# Email notifications
EMAIL_ENABLED=false
EMAIL_TO=team@example.com
EMAIL_FROM=monitor@example.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Slack notifications
SLACK_ENABLED=false
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Test thresholds
ACCESSIBILITY_SCORE_THRESHOLD=90
PERFORMANCE_SCORE_THRESHOLD=80
CONTRAST_COMPLIANCE_THRESHOLD=95

# Core Web Vitals thresholds
LCP_THRESHOLD=2500
FID_THRESHOLD=100
CLS_THRESHOLD=0.1
`;
  
  fs.writeFileSync('.env', envContent);
  console.log('  ✓ Created .env file (update with your settings)');
} else {
  console.log('  ✓ .env file already exists');
}

// Install dependencies
console.log('\n📦 Installing dependencies...');
try {
  execSync('npm install', { stdio: 'inherit' });
  console.log('  ✓ Dependencies installed');
} catch (error) {
  console.error('  ✗ Failed to install dependencies:', error.message);
  process.exit(1);
}

// Install Playwright browsers
console.log('\n🌐 Installing Playwright browsers...');
try {
  execSync('npx playwright install', { stdio: 'inherit' });
  console.log('  ✓ Playwright browsers installed');
} catch (error) {
  console.error('  ✗ Failed to install Playwright browsers:', error.message);
  process.exit(1);
}

// Create initial baseline
console.log('\n📊 Creating initial baselines...');
try {
  execSync('npm run test:lighthouse', { stdio: 'inherit' });
  console.log('  ✓ Lighthouse baseline created');
} catch (error) {
  console.log('  ⚠ Lighthouse baseline creation failed (this is normal for first run)');
}

try {
  execSync('npm run test:contrast', { stdio: 'inherit' });
  console.log('  ✓ Contrast baseline created');
} catch (error) {
  console.log('  ⚠ Contrast baseline creation failed (this is normal for first run)');
}

console.log('\n🎉 Setup complete!');
console.log('\n📋 Next steps:');
console.log('  1. Update .env file with your notification settings');
console.log('  2. Run "npm test" to execute all tests');
console.log('  3. Run "npm run monitor" to start continuous monitoring');
console.log('  4. Check the README.md for detailed documentation');
console.log('\n🔗 Useful commands:');
console.log('  npm test                    # Run all tests');
console.log('  npm run test:lighthouse     # Run Lighthouse audit');
console.log('  npm run test:pa11y         # Run Pa11y accessibility test');
console.log('  npm run test:playwright    # Run Playwright tests');
console.log('  npm run test:contrast      # Run contrast testing');
console.log('  npm run monitor            # Start continuous monitoring');
console.log('  npm run report             # Generate comprehensive report');
