# Screen Reader Testing Guide for MINGUS Financial Application

## Overview
This guide provides comprehensive testing procedures for ensuring screen reader compatibility with NVDA, JAWS, VoiceOver, and TalkBack. Follow these steps to validate accessibility compliance for your financial application.

## Table of Contents
1. [General Testing Principles](#general-testing-principles)
2. [NVDA Testing (Windows)](#nvda-testing-windows)
3. [JAWS Testing (Windows)](#jaws-testing-windows)
4. [VoiceOver Testing (macOS/iOS)](#voiceover-testing-macosios)
5. [TalkBack Testing (Android)](#talkback-testing-android)
6. [Financial Form Specific Tests](#financial-form-specific-tests)
7. [Common Issues and Solutions](#common-issues-and-solutions)
8. [Testing Checklist](#testing-checklist)

## General Testing Principles

### Before Testing
- Ensure your application is running and accessible
- Have the screen reader documentation ready
- Test in a quiet environment to hear announcements clearly
- Use headphones for better audio quality
- Have a notepad ready to document issues

### Testing Approach
1. **Navigation Testing**: Test all navigation methods (Tab, Arrow keys, etc.)
2. **Content Announcements**: Verify all content is properly announced
3. **Form Interactions**: Test form filling, validation, and submission
4. **Dynamic Content**: Test real-time updates and calculations
5. **Error Handling**: Test error messages and validation feedback

## NVDA Testing (Windows)

### Installation and Setup
1. Download NVDA from [nvaccess.org](https://www.nvaccess.org/)
2. Install and restart your computer
3. Press `Ctrl + Alt + N` to start/stop NVDA
4. Press `Insert + Space` to switch between browse and focus modes

### Key Commands
- **Tab**: Navigate between interactive elements
- **Arrow Keys**: Navigate within content
- **Enter/Space**: Activate buttons and links
- **H**: Navigate between headings
- **L**: Navigate between lists
- **F**: Navigate between form fields
- **Insert + Space**: Toggle browse/focus mode

### Testing Steps
1. **Page Load**
   - Navigate to your financial application
   - Verify page title is announced
   - Check if skip links are announced

2. **Navigation**
   - Use Tab to navigate through all interactive elements
   - Verify each element is properly announced
   - Test skip link functionality

3. **Forms**
   - Navigate to financial forms
   - Verify labels are announced with inputs
   - Test required field indicators
   - Check help text announcements

4. **Financial Data**
   - Navigate through financial tables
   - Verify currency amounts are properly announced
   - Check percentage values
   - Test calculation results

## JAWS Testing (Windows)

### Installation and Setup
1. Download JAWS from [freedomscientific.com](https://www.freedomscientific.com/)
2. Install and configure for your system
3. Press `Insert + J` to open JAWS settings
4. Use `Insert + F2` to access JAWS help

### Key Commands
- **Tab**: Navigate between elements
- **Arrow Keys**: Navigate within content
- **Enter**: Activate elements
- **H**: Navigate headings
- **L**: Navigate lists
- **F**: Navigate form fields
- **Insert + F5**: Forms mode

### Testing Steps
1. **Page Structure**
   - Verify landmark regions are announced
   - Check heading hierarchy
   - Test skip link functionality

2. **Form Accessibility**
   - Enter forms mode (`Insert + F5`)
   - Navigate through all form fields
   - Verify labels and help text
   - Test validation messages

3. **Financial Tables**
   - Navigate table structure
   - Verify column headers
   - Test cell navigation
   - Check data announcements

## VoiceOver Testing (macOS/iOS)

### macOS Setup
1. Go to System Preferences > Accessibility > VoiceOver
2. Enable VoiceOver (`Cmd + F5`)
3. Use `Cmd + F5` to toggle on/off

### iOS Setup
1. Go to Settings > Accessibility > VoiceOver
2. Enable VoiceOver
3. Triple-tap home button to toggle

### Key Commands (macOS)
- **Tab**: Navigate interactive elements
- **Arrow Keys**: Navigate content
- **Cmd + F5**: Toggle VoiceOver
- **Ctrl + Option + Arrow**: Navigate by element type
- **Ctrl + Option + Space**: Activate elements

### Testing Steps
1. **Page Navigation**
   - Verify page title announcement
   - Test skip link functionality
   - Navigate through headings

2. **Form Testing**
   - Navigate to form fields
   - Verify label associations
   - Test input validation
   - Check error announcements

3. **Financial Content**
   - Navigate financial tables
   - Verify currency announcements
   - Test calculation results
   - Check progress indicators

## TalkBack Testing (Android)

### Setup
1. Go to Settings > Accessibility > TalkBack
2. Enable TalkBack
3. Use volume up + down to toggle

### Gestures
- **Single tap**: Navigate to element
- **Double tap**: Activate element
- **Swipe left/right**: Navigate between elements
- **Swipe up/down**: Navigate within content

### Testing Steps
1. **App Navigation**
   - Navigate through app screens
   - Verify screen announcements
   - Test navigation menus

2. **Form Accessibility**
   - Navigate to financial forms
   - Verify field labels
   - Test input validation
   - Check error messages

3. **Financial Data**
   - Navigate financial information
   - Verify currency amounts
   - Test calculation displays
   - Check progress indicators

## Financial Form Specific Tests

### 1. Income Form Testing
```html
<!-- Test this form structure -->
<form role="form" aria-labelledby="income-form-title">
  <fieldset>
    <legend>Primary Income Sources</legend>
    
    <div class="form-group">
      <label for="annual-salary" class="form-label required">
        Annual Salary
        <span className="required-indicator" aria-label="required field">*</span>
      </label>
      <div class="currency-input">
        <input type="number" id="annual-salary" name="annual-salary" 
               class="form-input" required 
               aria-describedby="salary-help"
               aria-label="Annual salary in dollars before taxes">
      </div>
      <div id="salary-help" class="form-help">
        Enter your gross annual salary before any deductions
      </div>
    </div>
  </fieldset>
</form>
```

**Test Cases:**
- [ ] Form title is announced
- [ ] Fieldset legend is announced
- [ ] Label is properly associated with input
- [ ] Required indicator is announced
- [ ] Help text is announced
- [ ] Currency input context is clear
- [ ] Validation errors are announced

### 2. Budget Calculator Testing
```html
<!-- Test calculation results -->
<div class="financial-summary" aria-live="polite" aria-atomic="true">
  <h3>Budget Summary</h3>
  <div class="summary-item">
    <span class="summary-label">Total Monthly Income:</span>
    <span class="summary-value" id="summary-income">$5,000</span>
  </div>
</div>
```

**Test Cases:**
- [ ] Calculation start is announced
- [ ] Results are announced when complete
- [ ] Currency amounts are properly formatted
- [ ] Progress indicators are announced
- [ ] Error messages are clear

### 3. Financial Table Testing
```html
<!-- Test table accessibility -->
<table class="financial-data-table" data-type="financial" 
       summary="Monthly budget breakdown showing income, expenses, and savings">
  <caption>Monthly Budget Breakdown</caption>
  <thead>
    <tr>
      <th scope="col">Category</th>
      <th scope="col">Amount</th>
      <th scope="col">Percentage</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Income</td>
      <td>$5,000</td>
      <td>100%</td>
    </tr>
  </tbody>
</table>
```

**Test Cases:**
- [ ] Table summary is announced
- [ ] Caption is announced
- [ ] Column headers are announced
- [ ] Data cells are properly announced
- [ ] Currency and percentage context is clear
- [ ] Keyboard navigation works

## Common Issues and Solutions

### 1. Missing Labels
**Problem**: Screen reader announces "edit text" without context
**Solution**: Ensure every input has a proper label or aria-label

```html
<!-- Good -->
<label for="income">Annual Income</label>
<input id="income" name="income">

<!-- Also Good -->
<input aria-label="Annual income in dollars" name="income">
```

### 2. Unclear Financial Context
**Problem**: Screen reader announces "5000" without currency context
**Solution**: Use aria-label with financial context

```html
<input aria-label="Annual income: 5000 dollars" value="5000">
```

### 3. Missing Error Announcements
**Problem**: Validation errors are not announced to screen readers
**Solution**: Use aria-live regions and role="alert"

```html
<div role="alert" aria-live="assertive">
  Error: Annual income is required
</div>
```

### 4. Poor Table Navigation
**Problem**: Users can't navigate table data effectively
**Solution**: Proper table structure with headers and scope

```html
<th scope="col">Amount</th>
<td aria-label="Amount: 5000 dollars">$5,000</td>
```

## Testing Checklist

### Page Structure
- [ ] Page title is announced
- [ ] Skip links are functional
- [ ] Heading hierarchy is logical
- [ ] Landmark regions are defined

### Navigation
- [ ] Tab order is logical
- [ ] All interactive elements are reachable
- [ ] Focus indicators are visible
- [ ] Skip links work properly

### Forms
- [ ] All inputs have labels
- [ ] Required fields are indicated
- [ ] Help text is available
- [ ] Error messages are announced
- [ ] Validation feedback is clear

### Financial Data
- [ ] Currency amounts are properly announced
- [ ] Percentage values are clear
- [ ] Calculations are announced
- [ ] Tables are navigable
- [ ] Progress indicators work

### Dynamic Content
- [ ] Live regions are defined
- [ ] Updates are announced
- [ ] Loading states are indicated
- [ ] Error states are clear

### Mobile Accessibility
- [ ] Touch targets are adequate (44x44px minimum)
- [ ] Gestures work with screen readers
- [ ] Content is readable on small screens
- [ ] Navigation is touch-friendly

## Testing Tools and Resources

### Automated Testing
- **axe-core**: Automated accessibility testing
- **WAVE**: Web accessibility evaluation tool
- **Lighthouse**: Chrome DevTools accessibility audit

### Manual Testing
- **Screen Reader Simulators**: Test without installing full screen readers
- **Keyboard Navigation**: Test with Tab, Arrow keys, Enter, Space
- **High Contrast Mode**: Test visual accessibility

### Documentation
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [Screen Reader User Guide](https://webaim.org/articles/screenreader_guide/)

## Conclusion

Regular screen reader testing is essential for maintaining accessibility compliance. Test with multiple screen readers to ensure broad compatibility. Document all issues and track resolution progress. Remember that accessibility is an ongoing process, not a one-time task.

For questions or issues, refer to the accessibility documentation or contact the development team.
