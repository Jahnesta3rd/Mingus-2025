// MINGUS Button Analyzer - Chrome DevTools Console Script
// Run this in Chrome DevTools Console while on mobile emulation

console.log('🔍 MINGUS Button Analysis Starting...');
console.log('=' .repeat(50));

// Find all interactive elements
const interactiveElements = document.querySelectorAll(`
  button, 
  a[role="button"], 
  a[href^="#"], 
  [tabindex="0"],
  input[type="button"],
  input[type="submit"],
  input[type="reset"]
`);

console.log(`Found ${interactiveElements.length} interactive elements`);

// Analyze each element
const analysis = [];
let criticalIssues = 0;
let mediumIssues = 0;
let passedElements = 0;

interactiveElements.forEach((element, index) => {
  const rect = element.getBoundingClientRect();
  const computed = window.getComputedStyle(element);
  const isVisible = rect.width > 0 && rect.height > 0 && 
                   computed.display !== 'none' && 
                   computed.visibility !== 'hidden' && 
                   computed.opacity !== '0';
  
  const width = Math.round(rect.width);
  const height = Math.round(rect.height);
  const minSize = 44;
  
  const widthPass = width >= minSize;
  const heightPass = height >= minSize;
  const overallPass = widthPass && heightPass && isVisible;
  
  const elementInfo = {
    index,
    tagName: element.tagName,
    text: element.textContent?.trim().substring(0, 40) + (element.textContent?.length > 40 ? '...' : ''),
    dimensions: `${width}x${height}`,
    isVisible,
    widthPass,
    heightPass,
    overallPass,
    minHeight: computed.minHeight,
    minWidth: computed.minWidth,
    padding: computed.padding,
    display: computed.display,
    visibility: computed.visibility,
    opacity: computed.opacity,
    className: element.className,
    id: element.id
  };
  
  analysis.push(elementInfo);
  
  // Categorize issues
  if (!isVisible) {
    criticalIssues++;
    console.log(`❌ CRITICAL - Button ${index}: INVISIBLE (${width}x${height})`);
  } else if (!overallPass) {
    if (width < minSize || height < minSize) {
      criticalIssues++;
      console.log(`❌ CRITICAL - Button ${index}: TOO SMALL (${width}x${height}) - "${elementInfo.text}"`);
    } else {
      mediumIssues++;
      console.log(`⚠️  MEDIUM - Button ${index}: ISSUES (${width}x${height}) - "${elementInfo.text}"`);
    }
  } else {
    passedElements++;
    console.log(`✅ PASS - Button ${index}: GOOD (${width}x${height}) - "${elementInfo.text}"`);
  }
});

// Summary
console.log('\n📊 ANALYSIS SUMMARY');
console.log('=' .repeat(30));
console.log(`Total Elements: ${interactiveElements.length}`);
console.log(`✅ Passed: ${passedElements}`);
console.log(`❌ Critical Issues: ${criticalIssues}`);
console.log(`⚠️  Medium Issues: ${mediumIssues}`);
console.log(`Success Rate: ${Math.round((passedElements / interactiveElements.length) * 100)}%`);

// Critical issues breakdown
if (criticalIssues > 0) {
  console.log('\n🚨 CRITICAL ISSUES BREAKDOWN');
  console.log('=' .repeat(35));
  
  const criticalElements = analysis.filter(el => !el.isVisible || (!el.widthPass || !el.heightPass));
  criticalElements.forEach(el => {
    console.log(`Button ${el.index}:`);
    console.log(`  Text: "${el.text}"`);
    console.log(`  Dimensions: ${el.dimensions}`);
    console.log(`  Visible: ${el.isVisible}`);
    console.log(`  Min Height: ${el.minHeight}`);
    console.log(`  Min Width: ${el.minWidth}`);
    console.log(`  Display: ${el.display}`);
    console.log(`  Class: ${el.className}`);
    console.log(`  ID: ${el.id}`);
    console.log('---');
  });
}

// Quick fix suggestion
console.log('\n🔧 QUICK FIX SUGGESTION');
console.log('=' .repeat(30));
console.log('Add this CSS to fix critical issues:');
console.log(`
button, a, input, select {
  min-height: 44px !important;
  min-width: 44px !important;
  padding: 12px 16px !important;
}
`);

// Export data for further analysis
window.mingusButtonAnalysis = analysis;
console.log('\n💾 Data exported to window.mingusButtonAnalysis for further analysis');

// Highlight problematic buttons
console.log('\n🎯 Highlighting problematic buttons...');
criticalElements.forEach(el => {
  const element = interactiveElements[el.index];
  if (element) {
    element.style.outline = '3px solid red';
    element.style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
  }
});

console.log('✅ Analysis complete! Check highlighted elements on page.');
