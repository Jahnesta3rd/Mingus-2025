# Federal Worker Crisis Landing Page

A mobile-first landing page designed to help federal workers affected by government layoffs access crisis recovery resources and guidance.

## 🎯 Project Overview

This landing page serves as a crisis recovery resource hub for federal workers who have been laid off or are anticipating layoffs. It provides expert guidance on benefits transition, COBRA alternatives, TSP strategies, and career transition planning.

### Key Features
- **Mobile-first responsive design** (414px optimized)
- **Email capture system** with agency and status selection
- **Interactive timeline** showing 60-day recovery process
- **Social proof elements** with testimonials and statistics
- **FAQ section** addressing common concerns
- **Animated elements** for enhanced user engagement

## 📁 File Structure

```
Federal Worker Crisis Site/
├── index.html          # Main HTML structure
├── styles.css          # All CSS styling and animations
├── script.js           # JavaScript functionality
└── README.md           # Project documentation
```

## 🚀 Quick Start

1. **Clone or download** the project files
2. **Open `index.html`** in any modern web browser
3. **No build process required** - pure HTML, CSS, and JavaScript

## 🛠️ Technical Stack

- **HTML5** - Semantic markup and structure
- **CSS3** - Custom properties, Flexbox, animations
- **Vanilla JavaScript** - No frameworks or dependencies
- **Google Fonts** - Inter, Open Sans, and Lato typography

## 🎨 Design System

### Color Palette
- **Primary Red**: `#dc2626` (Crisis urgency)
- **Primary Orange**: `#f97316` (Action items)
- **Primary Green**: `#10b981` (Success/positive elements)
- **Background**: `#FFFFFF` (Primary), `#F5F5F5` (Secondary)
- **Text**: `#000000` (Primary), `#333333` (Secondary)

### Typography
- **Inter** - Headlines and UI elements
- **Open Sans** - Body text and descriptions
- **Lato** - Social proof elements

## 📱 Responsive Design

The landing page is optimized for mobile devices with a maximum width of 414px, following mobile-first design principles. Key responsive features:

- **Flexible container** with max-width constraints
- **Scalable typography** using relative units
- **Touch-friendly** buttons and interactive elements
- **Optimized spacing** for mobile viewing

## ⚡ Performance Features

- **Minimal dependencies** - No external libraries
- **Optimized animations** - CSS transitions and transforms
- **Lazy loading** - Intersection Observer for scroll animations
- **Efficient selectors** - CSS custom properties for consistency

## 🔧 Customization

### Modifying Content
- **Hero section**: Update headline and subtext in `index.html`
- **Statistics**: Modify numbers and labels in the stats section
- **Timeline**: Adjust recovery timeline steps and descriptions
- **Testimonials**: Replace with real federal worker testimonials
- **FAQ**: Update questions and add answers as needed

### Styling Changes
- **Colors**: Update CSS custom properties in `:root`
- **Typography**: Modify font-family declarations
- **Layout**: Adjust container max-widths and spacing
- **Animations**: Customize keyframes and transition timing

### Functionality Updates
- **Email capture**: Integrate with your email service provider
- **Form validation**: Add additional validation rules
- **Analytics**: Include tracking codes for conversion monitoring
- **A/B testing**: Create variations for optimization

## 📊 Analytics Integration

To track conversions and user behavior, consider adding:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>

<!-- Facebook Pixel -->
<script>
  !function(f,b,e,v,n,t,s)
  {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', 'YOUR_PIXEL_ID');
  fbq('track', 'PageView');
</script>
```

## 📧 Email Service Integration

The current form submits to console.log. To integrate with email services:

### Mailchimp
```javascript
// Replace submitEmail function
function submitEmail(event) {
    event.preventDefault();
    
    const email = document.getElementById('emailInput').value;
    const agency = document.getElementById('agencyInput').value;
    const status = document.getElementById('statusInput').value;
    
    // Mailchimp integration
    fetch('YOUR_MAILCHIMP_ENDPOINT', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            email_address: email,
            status: 'subscribed',
            merge_fields: {
                AGENCY: agency,
                STATUS: status
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        alert('Thank you! Your guide is being sent to your email.');
        closeModal();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('There was an error. Please try again.');
    });
}
```

### ConvertKit
```javascript
// ConvertKit integration
function submitEmail(event) {
    event.preventDefault();
    
    const formData = new FormData();
    formData.append('email', document.getElementById('emailInput').value);
    formData.append('agency', document.getElementById('agencyInput').value);
    formData.append('status', document.getElementById('statusInput').value);
    
    fetch('YOUR_CONVERTKIT_ENDPOINT', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        alert('Thank you! Your guide is being sent to your email.');
        closeModal();
    })
    .catch(error => {
        console.error('Error:', error);
        alert('There was an error. Please try again.');
    });
}
```

## 🔒 Privacy & Compliance

- **GDPR compliant** - Clear data collection purpose
- **Privacy policy** - Include link in footer
- **Cookie consent** - Add if using analytics
- **Data retention** - Define clear policies

## 🚀 Deployment

### Static Hosting
- **Netlify** - Drag and drop deployment
- **Vercel** - Git-based deployment
- **GitHub Pages** - Free hosting for public repos
- **AWS S3** - Scalable static hosting

### Domain Setup
1. **Purchase domain** (e.g., federalworkercrisis.com)
2. **Configure DNS** to point to hosting provider
3. **Set up SSL certificate** for HTTPS
4. **Test all functionality** on live domain

## 📈 Conversion Optimization

### A/B Testing Ideas
- **Headline variations** - Test different value propositions
- **CTA button text** - "Get Guide" vs "Download Now"
- **Social proof placement** - Above vs below fold
- **Form fields** - Required vs optional agency selection
- **Urgency elements** - Countdown timers, limited availability

### Performance Metrics
- **Conversion rate** - Email captures / page visitors
- **Bounce rate** - Single-page sessions
- **Time on page** - Engagement depth
- **Scroll depth** - Content consumption
- **Mobile vs desktop** - Device performance

## 🤝 Contributing

To contribute to this project:

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test thoroughly**
5. **Submit a pull request**

## 📄 License

This project is created for educational and commercial use. Please ensure compliance with all applicable laws and regulations when using this landing page.

## 📞 Support

For questions or support:
- **Email**: [your-email@domain.com]
- **Documentation**: [link-to-docs]
- **Issues**: [GitHub issues page]

---

**Created with ❤️ for federal workers by federal workers**

*Last updated: January 2025* 