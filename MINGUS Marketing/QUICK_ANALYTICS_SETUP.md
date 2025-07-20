# Quick Analytics Setup Guide

## 🚀 **Fast Implementation Steps**

### **Step 1: Get Your Google Analytics 4 Measurement ID**

1. Go to [Google Analytics](https://analytics.google.com/)
2. Create new property or use existing
3. Get your **Measurement ID** (format: G-XXXXXXXXXX)

### **Step 2: Update Landing Pages**

#### **For Ratchet Money Landing Page** (`ratchet_money_landing.html`)

Add this code right after the `<head>` tag:

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    page_title: 'Ratchet Money Landing Page',
    page_location: window.location.href
  });
</script>

<!-- Analytics Integration -->
<script src="analytics-integration.js"></script>
```

#### **For MINGUS Landing Page** (`Mingus_Landing_page_new.html`)

Add this code right after the `<head>` tag:

```html
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX', {
    page_title: 'MINGUS Landing Page',
    page_location: window.location.href
  });
</script>

<!-- Analytics Integration -->
<script src="analytics-integration.js"></script>
```

### **Step 3: Replace Placeholder IDs**

Replace `G-XXXXXXXXXX` with your actual GA4 Measurement ID in both files.

### **Step 4: Test Implementation**

1. Open both landing pages in browser
2. Check browser console for "Analytics Integration Initialized"
3. Perform some actions (click CTAs, scroll, etc.)
4. Check console for event tracking logs

## 📊 **What Gets Tracked Automatically**

### **Page Interactions**
- ✅ Page views and exits
- ✅ Scroll depth (25%, 50%, 75%, 100%)
- ✅ Time on page
- ✅ CTA clicks
- ✅ Form submissions
- ✅ Email field interactions

### **User Behavior**
- ✅ Assessment starts
- ✅ Micro-conversions
- ✅ User engagement
- ✅ Page performance metrics

### **Cross-Platform Data**
- ✅ Google Analytics 4 events
- ✅ Microsoft Clarity session recordings
- ✅ Heatmaps and user journey analysis

## 🎯 **Quick Verification**

### **Check Google Analytics**
1. Go to [Google Analytics](https://analytics.google.com/)
2. Check **Realtime** reports
3. Verify page views are tracking

### **Check Microsoft Clarity**
1. Go to [Microsoft Clarity](https://clarity.microsoft.com/)
2. Check **Projects**:
   - Ratchet Money: `seg861um4a`
   - MINGUS: `shdin8hbm3`
3. Verify session recordings are appearing

## 🔧 **Custom Events (Optional)**

Add custom tracking for specific actions:

```javascript
// Track custom conversion
window.trackEvent('custom_conversion', {
  conversion_type: 'email_signup',
  value: 1
});

// Set user segment
window.setUserSegment('high_value_visitor');
```

## 📈 **Expected Results**

### **Day 1**
- Basic page view tracking
- Initial session recordings
- Real-time data in GA4

### **Week 1**
- Sufficient data for analysis
- Heatmaps and scroll depth
- User behavior patterns

### **Month 1**
- Comprehensive insights
- Conversion optimization data
- A/B testing support

## 🚨 **Troubleshooting**

### **No Data in GA4**
- Check Measurement ID is correct
- Verify script placement in `<head>`
- Test in incognito mode

### **No Clarity Recordings**
- Check Project IDs are correct
- Verify scripts are loading
- Wait 24-48 hours for initial data

### **Events Not Tracking**
- Check browser console for errors
- Verify `analytics-integration.js` is loaded
- Test event triggers manually

## ✅ **Success Checklist**

- [ ] GA4 Measurement ID added to both pages
- [ ] Analytics integration script loaded
- [ ] Console shows "Analytics Integration Initialized"
- [ ] Page views tracking in GA4
- [ ] Session recordings appearing in Clarity
- [ ] Custom events firing correctly

## 🎉 **You're Done!**

Once completed, you'll have:
- **Complete user behavior tracking**
- **Cross-platform analytics**
- **Conversion optimization insights**
- **A/B testing support**

**Your landing pages are now fully equipped with advanced analytics! 🚀** 