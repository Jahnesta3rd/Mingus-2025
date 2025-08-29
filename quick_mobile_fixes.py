#!/usr/bin/env python3
"""
Quick Mobile Fixes for Landing Page
Applies immediate mobile optimizations to the landing page
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filename):
    """Create a backup of the original file"""
    if os.path.exists(filename):
        backup_name = f"{filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filename, backup_name)
        print(f"✅ Backed up {filename} to {backup_name}")
        return backup_name
    return None

def apply_mobile_optimizations():
    """Apply mobile optimizations to the landing page"""
    print("🚀 Applying Quick Mobile Optimizations")
    print("=" * 50)
    
    # 1. Optimize responsive.css
    print("\n📱 Optimizing responsive.css...")
    responsive_css = "static/styles/responsive.css"
    
    if os.path.exists(responsive_css):
        backup_file(responsive_css)
        
        with open(responsive_css, 'r') as f:
            content = f.read()
        
        # Add mobile-specific optimizations
        mobile_optimizations = """
/* ==========================================================================
   Mobile-Specific Optimizations
   ========================================================================== */

/* Mobile Touch Targets */
@media (max-width: 768px) {
  /* Ensure minimum touch target size for all interactive elements */
  .hero-cta-primary,
  .hero-cta-secondary,
  .landing-nav-cta,
  .landing-nav-links a,
  button,
  input[type="submit"],
  input[type="button"] {
    min-height: 44px !important;
    min-width: 44px !important;
    padding: 12px 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
  }
  
  /* Touch feedback for buttons */
  .hero-cta-primary:active,
  .hero-cta-secondary:active,
  .landing-nav-cta:active {
    transform: scale(0.95) !important;
    transition: transform 0.1s ease !important;
  }
  
  /* Mobile typography improvements */
  .hero-title {
    font-size: 2rem !important;
    line-height: 1.2 !important;
    margin-bottom: 1rem !important;
  }
  
  .hero-subtitle {
    font-size: 1.1rem !important;
    line-height: 1.5 !important;
    margin-bottom: 2rem !important;
  }
  
  /* Improve paragraph readability */
  p {
    font-size: 16px !important;
    line-height: 1.6 !important;
    margin-bottom: 1rem !important;
  }
  
  /* Better heading hierarchy */
  h1 { font-size: 2rem !important; }
  h2 { font-size: 1.5rem !important; }
  h3 { font-size: 1.25rem !important; }
  
  /* Mobile layout improvements */
  .hero-section {
    padding: 80px 20px 60px !important;
  }
  
  .container {
    padding: 0 20px !important;
  }
  
  /* CTA container improvements */
  .hero-cta-container {
    flex-direction: column !important;
    align-items: stretch !important;
    gap: 16px !important;
    margin: 32px 0 !important;
  }
  
  .hero-cta-container a {
    width: 100% !important;
    max-width: 300px !important;
    margin: 0 auto !important;
  }
  
  /* Social proof mobile optimization */
  .social-proof {
    flex-direction: column !important;
    gap: 24px !important;
    margin: 32px 0 !important;
  }
  
  .proof-item {
    text-align: center !important;
    padding: 16px !important;
    background: rgba(255,255,255,0.05) !important;
    border-radius: 12px !important;
  }
  
  /* Hide desktop navigation on mobile */
  .landing-nav-links {
    display: none !important;
  }
  
  /* Mobile menu toggle button */
  .mobile-menu-toggle {
    display: flex !important;
    flex-direction: column !important;
    background: none !important;
    border: none !important;
    cursor: pointer !important;
    padding: 8px !important;
  }
  
  .mobile-menu-toggle span {
    width: 25px !important;
    height: 3px !important;
    background: var(--text-primary) !important;
    margin: 3px 0 !important;
    transition: 0.3s !important;
  }
  
  /* Mobile menu */
  .mobile-menu {
    display: none !important;
    position: absolute !important;
    top: 100% !important;
    left: 0 !important;
    right: 0 !important;
    background: var(--bg-primary) !important;
    border-top: 1px solid var(--border-color) !important;
    padding: 20px !important;
    flex-direction: column !important;
    gap: 16px !important;
  }
  
  .mobile-menu.active {
    display: flex !important;
  }
  
  .mobile-menu a {
    padding: 12px 0 !important;
    border-bottom: 1px solid var(--border-color) !important;
    font-size: 16px !important;
    font-weight: 500 !important;
  }
  
  .mobile-cta {
    background: var(--accent-green) !important;
    color: var(--bg-primary) !important;
    padding: 12px 20px !important;
    border-radius: var(--border-radius) !important;
    text-align: center !important;
    font-weight: bold !important;
    margin-top: 16px !important;
  }
}

/* Performance optimizations for mobile */
@media (max-width: 768px) {
  /* Optimize images */
  img {
    max-width: 100% !important;
    height: auto !important;
  }
  
  /* Reduce animation duration for better performance */
  * {
    animation-duration: 0.3s !important;
    transition-duration: 0.3s !important;
  }
  
  /* Optimize grid layouts */
  .features-grid,
  .testimonials-grid,
  .pricing-grid {
    grid-template-columns: 1fr !important;
    gap: 24px !important;
  }
  
  /* Consistent card styling */
  .card {
    padding: 24px !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
  }
}

/* Show/hide utilities for mobile */
@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }
  
  .mobile-only {
    display: block !important;
  }
}

@media (min-width: 769px) {
  .mobile-only {
    display: none !important;
  }
  
  .desktop-only {
    display: block !important;
  }
}
"""
        
        # Add the mobile optimizations to the end of the file
        content += mobile_optimizations
        
        with open(responsive_css, 'w') as f:
            f.write(content)
        
        print("✅ Applied mobile optimizations to responsive.css")
    else:
        print("⚠️ responsive.css not found, skipping...")
    
    # 2. Update landing.html with mobile menu
    print("\n📱 Adding mobile menu to landing.html...")
    landing_html = "landing.html"
    
    if os.path.exists(landing_html):
        backup_file(landing_html)
        
        with open(landing_html, 'r') as f:
            content = f.read()
        
        # Add mobile menu button to navigation
        nav_pattern = r'(<div class="landing-nav-links">.*?</div>)'
        mobile_nav_replacement = r'''\1
                <!-- Mobile Menu Button -->
                <button class="mobile-menu-toggle mobile-only" aria-label="Toggle menu">
                    <span></span>
                    <span></span>
                    <span></span>
                </button>'''
        
        content = re.sub(nav_pattern, mobile_nav_replacement, content, flags=re.DOTALL)
        
        # Add mobile menu after header
        header_pattern = r'(</header>)'
        mobile_menu = r'''\1
        <!-- Mobile Menu -->
        <div class="mobile-menu mobile-only">
            <a href="#features">Features</a>
            <a href="#testimonials">Testimonials</a>
            <a href="#pricing">Pricing</a>
            <a href="/login" class="mobile-cta">Determine Your Plan</a>
        </div>'''
        
        content = re.sub(header_pattern, mobile_menu, content)
        
        # Add mobile menu JavaScript before closing body tag
        body_pattern = r'(</body>)'
        mobile_js = r'''        <!-- Mobile Menu JavaScript -->
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
                const mobileMenu = document.querySelector('.mobile-menu');
                
                if (mobileMenuToggle && mobileMenu) {
                    mobileMenuToggle.addEventListener('click', function() {
                        mobileMenu.classList.toggle('active');
                        
                        // Animate hamburger menu
                        const spans = this.querySelectorAll('span');
                        if (mobileMenu.classList.contains('active')) {
                            spans[0].style.transform = 'rotate(45deg) translate(5px, 5px)';
                            spans[1].style.opacity = '0';
                            spans[2].style.transform = 'rotate(-45deg) translate(7px, -6px)';
                        } else {
                            spans[0].style.transform = 'none';
                            spans[1].style.opacity = '1';
                            spans[2].style.transform = 'none';
                        }
                    });
                    
                    // Close menu when clicking outside
                    document.addEventListener('click', function(e) {
                        if (!mobileMenuToggle.contains(e.target) && !mobileMenu.contains(e.target)) {
                            mobileMenu.classList.remove('active');
                            const spans = mobileMenuToggle.querySelectorAll('span');
                            spans[0].style.transform = 'none';
                            spans[1].style.opacity = '1';
                            spans[2].style.transform = 'none';
                        }
                    });
                }
                
                // Add touch feedback to all buttons
                const buttons = document.querySelectorAll('.hero-cta-primary, .hero-cta-secondary, .landing-nav-cta');
                buttons.forEach(button => {
                    button.addEventListener('touchstart', function() {
                        this.style.transform = 'scale(0.95)';
                    });
                    
                    button.addEventListener('touchend', function() {
                        this.style.transform = 'scale(1)';
                    });
                });
            });
        </script>
\1'''
        
        content = re.sub(body_pattern, mobile_js, content)
        
        with open(landing_html, 'w') as f:
            f.write(content)
        
        print("✅ Added mobile menu to landing.html")
    else:
        print("⚠️ landing.html not found, skipping...")
    
    # 3. Create mobile-specific CSS file
    print("\n📱 Creating mobile-specific CSS...")
    mobile_css = "static/styles/mobile-optimizations.css"
    
    mobile_css_content = """/* Mobile-Specific Optimizations */
/* This file contains additional mobile optimizations */

/* Mobile performance optimizations */
@media (max-width: 768px) {
  /* Optimize font loading */
  @font-face {
    font-display: swap;
  }
  
  /* Reduce paint complexity */
  .hero-section::before {
    display: none;
  }
  
  /* Optimize animations */
  .hero-badge::before {
    animation: none;
  }
  
  /* Improve scrolling performance */
  .landing-container {
    -webkit-overflow-scrolling: touch;
  }
}

/* Mobile accessibility improvements */
@media (max-width: 768px) {
  /* Ensure sufficient color contrast */
  .hero-subtitle {
    color: #e5e7eb !important;
  }
  
  /* Improve focus indicators */
  a:focus,
  button:focus {
    outline: 2px solid var(--accent-green) !important;
    outline-offset: 2px !important;
  }
  
  /* Ensure text is readable */
  * {
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
  }
}

/* Mobile-specific animations */
@media (max-width: 768px) {
  .hero-cta-primary {
    position: relative;
    overflow: hidden;
  }
  
  .hero-cta-primary::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
  }
  
  .hero-cta-primary:active::before {
    left: 100%;
  }
}

/* Mobile loading optimizations */
@media (max-width: 768px) {
  /* Prioritize above-the-fold content */
  .hero-section {
    contain: layout style paint;
  }
  
  /* Defer non-critical animations */
  .hero-visual {
    animation-delay: 0.5s;
  }
}
"""
    
    with open(mobile_css, 'w') as f:
        f.write(mobile_css_content)
    
    print("✅ Created mobile-specific CSS file")
    
    # 4. Update landing.html to include mobile CSS
    if os.path.exists(landing_html):
        with open(landing_html, 'r') as f:
            content = f.read()
        
        # Add mobile CSS link
        css_pattern = r'(<link rel="stylesheet" href="static/styles/responsive.css">)'
        mobile_css_link = r'\1\n    <link rel="stylesheet" href="static/styles/mobile-optimizations.css">'
        
        content = re.sub(css_pattern, mobile_css_link, content)
        
        with open(landing_html, 'w') as f:
            f.write(content)
        
        print("✅ Added mobile CSS link to landing.html")
    
    print("\n🎉 Mobile optimizations applied successfully!")
    print("\n📋 What was optimized:")
    print("✅ Touch target sizes (44px minimum)")
    print("✅ Mobile typography and readability")
    print("✅ Mobile navigation menu")
    print("✅ Touch feedback animations")
    print("✅ Performance optimizations")
    print("✅ Accessibility improvements")
    
    print("\n🚀 Next steps:")
    print("1. Test the landing page on mobile devices")
    print("2. Run the mobile testing suite: python mobile_landing_page_test.py")
    print("3. Check performance with Chrome DevTools")
    print("4. Gather user feedback on mobile experience")

if __name__ == "__main__":
    apply_mobile_optimizations()
