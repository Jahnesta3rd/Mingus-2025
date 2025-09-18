# MINGUS Button Inspection Guide
**Step-by-Step Chrome DevTools Analysis**

## Prerequisites
- Chrome browser open at http://localhost:3000
- DevTools open (F12 or right-click → Inspect)

## Step 1: Enable Mobile Device Emulation

1. **Open Chrome DevTools** (F12)
2. **Click Device Toggle** (📱 icon) or press `Ctrl+Shift+M` (Windows) / `Cmd+Shift+M` (Mac)
3. **Select iPhone 12** from device dropdown
4. **Set dimensions to 375x812px**
5. **Refresh page** to ensure mobile view loads

## Step 2: Identify All Buttons on Page

### Method 1: Console Command
Open Console tab and run:
```javascript
// Find all buttons and their dimensions
const buttons = document.querySelectorAll('button, a[role="button"], [tabindex="0"]');
console.log('=== BUTTON ANALYSIS ===');
buttons.forEach((btn, index) => {
  const rect = btn.getBoundingClientRect();
  const computed = window.getComputedStyle(btn);
  console.log(`Button ${index}:`, {
    element: btn.tagName,
    text: btn.textContent?.trim().substring(0, 30) + '...',
    dimensions: `${rect.width}x${rect.height}`,
    minHeight: computed.minHeight,
    minWidth: computed.minWidth,
    padding: computed.padding,
    display: computed.display,
    visibility: computed.visibility,
    opacity: computed.opacity
  });
});
```

### Method 2: Manual Inspection
Right-click each button and inspect individually.

## Step 3: Critical Buttons to Check

### 🔴 **HIGH PRIORITY - Known Issues**

#### **Buttons 0-3 (Invisible Buttons)**
- **Location:** Likely in hero section
- **Expected Issue:** 0x0px dimensions
- **Inspection Steps:**
  1. Right-click in hero section
  2. Select "Inspect"
  3. Look for buttons with `display: none` or `visibility: hidden`
  4. Check computed styles for width/height

#### **Button 4 (40x40px)**
- **Expected Issue:** 4px too small
- **Target:** 44x44px minimum
- **Inspection Steps:**
  1. Find button with 40x40px dimensions
  2. Check padding, min-height, min-width
  3. Look for CSS overrides

#### **Button 13 (232x32px)**
- **Expected Issue:** Height 12px too small
- **Target:** 44px minimum height
- **Inspection Steps:**
  1. Find button with 232x32px dimensions
  2. Check if it's a navigation or CTA button
  3. Verify height constraints

### 🟡 **MEDIUM PRIORITY - Assessment Buttons**

#### **AI Risk Assessment Button**
- **Text:** "Determine Your Replacement Risk Due To AI"
- **Location:** Hero section, top row
- **Check:** Touch target size, clickability

#### **Income Comparison Button**
- **Text:** "Determine How Your Income Compares"
- **Location:** Hero section, top row
- **Check:** Touch target size, clickability

#### **Cuffing Season Button**
- **Text:** "Determine Your 'Cuffing Season' Score"
- **Location:** Hero section, bottom row
- **Check:** Touch target size, clickability

#### **Layoff Risk Button**
- **Text:** "Determine Your Layoff Risk"
- **Location:** Hero section, bottom row
- **Check:** Touch target size, clickability

### 🟢 **LOW PRIORITY - Other Buttons**

#### **Navigation Buttons**
- **Location:** Top navigation bar
- **Check:** Menu items, hamburger menu

#### **CTA Buttons**
- **Location:** Call-to-action sections
- **Check:** "Start Your Wealth Journey", "Join Our Community"

#### **FAQ Accordion Buttons**
- **Location:** FAQ section
- **Check:** Expand/collapse functionality

#### **Pricing Buttons**
- **Location:** Pricing section
- **Check:** "Get Started", "Start Free Trial", "Go Professional"

## Step 4: Record Findings

### **Button Analysis Template**
```
Button #: [Number]
Location: [Section/Description]
Text: [Button text]
Current Dimensions: [Width x Height]
Required Minimum: 44x44px
Status: [PASS/FAIL]
Issues Found:
- [Issue 1]
- [Issue 2]
CSS Properties:
- min-height: [value]
- min-width: [value]
- padding: [value]
- display: [value]
```

## Step 5: Common Issues to Look For

### **CSS Issues**
- `min-height: 0` or `min-height: auto`
- `min-width: 0` or `min-width: auto`
- `display: none` or `visibility: hidden`
- `opacity: 0`
- `height: 0` or `width: 0`
- `padding: 0` or very small padding

### **Layout Issues**
- Buttons inside containers with `overflow: hidden`
- Flexbox or grid constraints
- Responsive breakpoints hiding elements
- JavaScript dynamically setting dimensions

### **Accessibility Issues**
- Buttons not keyboard accessible
- Missing ARIA labels
- Poor contrast ratios
- Text too small to read

## Step 6: Quick Fix Verification

After identifying issues, test this CSS fix:
```css
/* Add to browser console or DevTools */
document.head.insertAdjacentHTML('beforeend', `
<style>
button, a, input, select {
  min-height: 44px !important;
  min-width: 44px !important;
  padding: 12px 16px !important;
}
</style>
`);
```

## Step 7: Document Results

Record all findings in the format above and note:
1. **Total buttons found**
2. **Buttons failing 44px rule**
3. **Most common issues**
4. **Sections with most problems**
5. **Priority order for fixes**

---

**Next Steps:** After completing this inspection, we'll create targeted CSS fixes for each problematic button.
