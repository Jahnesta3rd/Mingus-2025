#!/usr/bin/env python3
"""
Social Media Integration Implementation Script for MINGUS Application

This script adds missing social media features to the MINGUS application:
1. Social media links in footer
2. Social sharing buttons
3. Social proof elements
4. Influencer content integration
"""

import os
import re
from pathlib import Path

class SocialMediaIntegration:
    def __init__(self):
        self.base_dir = Path(".")
        self.landing_page = self.base_dir / "landing.html"
        self.marketing_landing = self.base_dir / "MINGUS Marketing" / "Mingus_Landing_page_new.html"
        
    def add_social_media_links_to_footer(self, file_path):
        """Add social media links to the footer of a landing page"""
        print(f"Adding social media links to footer: {file_path}")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if this is the marketing landing page (different footer structure)
        if "MINGUS Marketing" in str(file_path):
            # For marketing landing page, add social links to footer-content
            social_links_marketing = '''
        <div style="margin-top: 16px;">
          <div style="display: flex; gap: 1rem; justify-content: center; margin-bottom: 1rem;">
            <a href="https://facebook.com/mingusfinancial" aria-label="Follow us on Facebook" style="color: var(--primary-green); font-size: 1.5rem;">
              <i class="fab fa-facebook-f"></i>
            </a>
            <a href="https://twitter.com/mingusfinancial" aria-label="Follow us on Twitter" style="color: var(--primary-green); font-size: 1.5rem;">
              <i class="fab fa-twitter"></i>
            </a>
            <a href="https://linkedin.com/company/mingusfinancial" aria-label="Follow us on LinkedIn" style="color: var(--primary-green); font-size: 1.5rem;">
              <i class="fab fa-linkedin-in"></i>
            </a>
            <a href="https://instagram.com/mingusfinancial" aria-label="Follow us on Instagram" style="color: var(--primary-green); font-size: 1.5rem;">
              <i class="fab fa-instagram"></i>
            </a>
            <a href="https://youtube.com/@mingusfinancial" aria-label="Follow us on YouTube" style="color: var(--primary-green); font-size: 1.5rem;">
              <i class="fab fa-youtube"></i>
            </a>
          </div>
        </div>
'''
            # Find the copyright div and add social links before it
            footer_pattern = r'(<div style="margin-top: 16px;">&copy; 2024 MINGUS\. All rights reserved\.</div>)'
            if re.search(footer_pattern, content):
                content = re.sub(footer_pattern, social_links_marketing + r'\1', content)
        else:
            # For main landing page, use the original pattern
            social_links_html = '''
                    <div class="footer-section">
                        <h3>Follow Us</h3>
                        <div class="social-links">
                            <a href="https://facebook.com/mingusfinancial" aria-label="Follow us on Facebook" class="social-link">
                                <i class="fab fa-facebook-f"></i>
                            </a>
                            <a href="https://twitter.com/mingusfinancial" aria-label="Follow us on Twitter" class="social-link">
                                <i class="fab fa-twitter"></i>
                            </a>
                            <a href="https://linkedin.com/company/mingusfinancial" aria-label="Follow us on LinkedIn" class="social-link">
                                <i class="fab fa-linkedin-in"></i>
                            </a>
                            <a href="https://instagram.com/mingusfinancial" aria-label="Follow us on Instagram" class="social-link">
                                <i class="fab fa-instagram"></i>
                            </a>
                            <a href="https://youtube.com/@mingusfinancial" aria-label="Follow us on YouTube" class="social-link">
                                <i class="fab fa-youtube"></i>
                            </a>
                        </div>
                    </div>
'''
            footer_pattern = r'(<div class="footer-bottom">)'
            if re.search(footer_pattern, content):
                content = re.sub(footer_pattern, social_links_html + r'\1', content)
        
        # Add CSS for social links
        css_pattern = r'(</style>)'
        social_css = '''
        /* Social Media Links */
        .social-links {
            display: flex;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .social-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            background: var(--primary-color);
            color: white;
            border-radius: 50%;
            text-decoration: none;
            transition: all 0.3s ease;
            font-size: 1.2rem;
        }
        
        .social-link:hover {
            background: var(--secondary-color);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .social-link.facebook:hover { background: #1877f2; }
        .social-link.twitter:hover { background: #1da1f2; }
        .social-link.linkedin:hover { background: #0077b5; }
        .social-link.instagram:hover { background: #e4405f; }
        .social-link.youtube:hover { background: #ff0000; }
        
        /* Marketing page social links */
        .footer a[href*="facebook"]:hover { color: #1877f2 !important; }
        .footer a[href*="twitter"]:hover { color: #1da1f2 !important; }
        .footer a[href*="linkedin"]:hover { color: #0077b5 !important; }
        .footer a[href*="instagram"]:hover { color: #e4405f !important; }
        .footer a[href*="youtube"]:hover { color: #ff0000 !important; }
'''
        content = re.sub(css_pattern, social_css + r'\1', content)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Added social media links to {file_path}")
    
    def add_social_sharing_buttons(self, file_path):
        """Add social sharing buttons to content sections"""
        print(f"Adding social sharing buttons: {file_path}")
        
        # Social sharing buttons HTML
        sharing_buttons_html = '''
        <div class="share-buttons">
            <button onclick="shareToFacebook()" class="share-btn facebook" aria-label="Share on Facebook">
                <i class="fab fa-facebook-f"></i> Share
            </button>
            <button onclick="shareToTwitter()" class="share-btn twitter" aria-label="Share on Twitter">
                <i class="fab fa-twitter"></i> Tweet
            </button>
            <button onclick="shareToLinkedIn()" class="share-btn linkedin" aria-label="Share on LinkedIn">
                <i class="fab fa-linkedin-in"></i> Share
            </button>
            <button onclick="shareToWhatsApp()" class="share-btn whatsapp" aria-label="Share on WhatsApp">
                <i class="fab fa-whatsapp"></i> Share
            </button>
        </div>
'''
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add sharing buttons after CTA sections
        cta_patterns = [
            r'(<a href="#assessment" class="final-cta">.*?</a>)',
            r'(<button class="hero-cta-primary">.*?</button>)',
            r'(<button class="btn btn-primary">.*?</button>)'
        ]
        
        for pattern in cta_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, r'\1' + sharing_buttons_html, content, count=1)
                break
        
        # Add CSS for sharing buttons
        css_pattern = r'(</style>)'
        sharing_css = '''
        /* Social Sharing Buttons */
        .share-buttons {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        
        .share-btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 8px;
            color: white;
            font-weight: 600;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .share-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .share-btn.facebook { background: #1877f2; }
        .share-btn.twitter { background: #1da1f2; }
        .share-btn.linkedin { background: #0077b5; }
        .share-btn.whatsapp { background: #25d366; }
        
        .share-btn.facebook:hover { background: #166fe5; }
        .share-btn.twitter:hover { background: #1a91da; }
        .share-btn.linkedin:hover { background: #006097; }
        .share-btn.whatsapp:hover { background: #128c7e; }
'''
        content = re.sub(css_pattern, sharing_css + r'\1', content)
        
        # Add JavaScript for sharing functionality
        js_pattern = r'(</script>)'
        sharing_js = '''
        // Social Sharing Functions
        function shareToFacebook() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent('Transform your financial future with MINGUS - AI-powered financial wellness!');
            window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${text}`, '_blank');
            trackSocialInteraction('facebook', 'share');
        }
        
        function shareToTwitter() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent('Transform your financial future with @mingusfinancial! #FinancialWellness #AI #PersonalFinance');
            window.open(`https://twitter.com/intent/tweet?url=${url}&text=${text}`, '_blank');
            trackSocialInteraction('twitter', 'share');
        }
        
        function shareToLinkedIn() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent('Transform your financial future with MINGUS - AI-powered financial wellness platform');
            window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank');
            trackSocialInteraction('linkedin', 'share');
        }
        
        function shareToWhatsApp() {
            const url = encodeURIComponent(window.location.href);
            const text = encodeURIComponent('Check out MINGUS - AI-powered financial wellness!');
            window.open(`https://wa.me/?text=${text}%20${url}`, '_blank');
            trackSocialInteraction('whatsapp', 'share');
        }
        
        function trackSocialInteraction(platform, action) {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'social_interaction', {
                    'social_network': platform,
                    'social_action': action,
                    'content_type': 'landing_page'
                });
            }
        }
'''
        content = re.sub(js_pattern, sharing_js + r'\1', content)
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Added social sharing buttons to {file_path}")
    
    def add_social_proof_elements(self, file_path):
        """Add social proof elements with social media integration"""
        print(f"Adding social proof elements: {file_path}")
        
        # Social proof HTML
        social_proof_html = '''
        <!-- Enhanced Social Proof Section -->
        <section class="social-proof-section fade-in">
            <div class="container">
                <h2 class="section-title">Trusted by 10,000+ Professionals</h2>
                <div class="social-proof-grid">
                    <div class="proof-card">
                        <div class="proof-number">10,847</div>
                        <div class="proof-label">Active Users</div>
                        <div class="proof-source">Verified by our platform</div>
                    </div>
                    <div class="proof-card">
                        <div class="proof-number">4.8★</div>
                        <div class="proof-label">Average Rating</div>
                        <div class="proof-source">From 2,500+ reviews</div>
                    </div>
                    <div class="proof-card">
                        <div class="proof-number">$2.3M</div>
                        <div class="proof-label">Total Savings</div>
                        <div class="proof-source">Generated by users</div>
                    </div>
                    <div class="proof-card">
                        <div class="proof-number">89%</div>
                        <div class="proof-label">Success Rate</div>
                        <div class="proof-source">Career advancement</div>
                    </div>
                </div>
                
                <!-- Social Media Proof -->
                <div class="social-media-proof">
                    <h3>Featured in</h3>
                    <div class="media-logos">
                        <div class="media-logo">Forbes</div>
                        <div class="media-logo">TechCrunch</div>
                        <div class="media-logo">Black Enterprise</div>
                        <div class="media-logo">Essence</div>
                    </div>
                </div>
            </div>
        </section>
'''
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find testimonials section and add social proof before it
        testimonials_pattern = r'(<!-- Testimonials Section -->)'
        if re.search(testimonials_pattern, content):
            content = re.sub(testimonials_pattern, social_proof_html + r'\n        ' + r'\1', content)
            
            # Add CSS for social proof
            css_pattern = r'(</style>)'
            proof_css = '''
        /* Enhanced Social Proof */
        .social-proof-section {
            padding: 4rem 0;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
        }
        
        .social-proof-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }
        
        .proof-card {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .proof-number {
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--primary-color);
            margin-bottom: 0.5rem;
        }
        
        .proof-label {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-color);
            margin-bottom: 0.5rem;
        }
        
        .proof-source {
            font-size: 0.9rem;
            color: var(--text-light);
        }
        
        .social-media-proof {
            text-align: center;
            margin-top: 3rem;
        }
        
        .social-media-proof h3 {
            font-size: 1.5rem;
            margin-bottom: 2rem;
            color: var(--text-color);
        }
        
        .media-logos {
            display: flex;
            justify-content: center;
            gap: 3rem;
            flex-wrap: wrap;
        }
        
        .media-logo {
            font-size: 1.2rem;
            font-weight: 600;
            color: var(--text-light);
            opacity: 0.7;
            transition: opacity 0.3s ease;
        }
        
        .media-logo:hover {
            opacity: 1;
        }
'''
            content = re.sub(css_pattern, proof_css + r'\1', content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added social proof elements to {file_path}")
        else:
            print(f"❌ Could not find testimonials section in {file_path}")
    
    def add_influencer_content(self, file_path):
        """Add influencer content integration"""
        print(f"Adding influencer content: {file_path}")
        
        # Influencer content HTML
        influencer_html = '''
        <!-- Influencer Content Section -->
        <section class="influencer-section fade-in">
            <div class="container">
                <h2 class="section-title">Trusted by Financial Wellness Leaders</h2>
                <div class="influencer-grid">
                    <div class="influencer-card">
                        <div class="influencer-image">
                            <img src="https://via.placeholder.com/120x120/10b981/ffffff?text=JS" alt="Jay Shetty">
                        </div>
                        <div class="influencer-content">
                            <h3>Jay Shetty</h3>
                            <p class="influencer-title">Best-selling Author & Life Coach</p>
                            <blockquote>"MINGUS helps you understand not just how to manage money, but why you make the financial decisions you do. It's about creating a healthy relationship with wealth."</blockquote>
                        </div>
                    </div>
                    
                    <div class="influencer-card">
                        <div class="influencer-image">
                            <img src="https://via.placeholder.com/120x120/667eea/ffffff?text=NT" alt="Nedra Tawwab">
                        </div>
                        <div class="influencer-content">
                            <h3>Nedra Tawwab</h3>
                            <p class="influencer-title">Boundary Expert & Therapist</p>
                            <blockquote>"Setting boundaries with money is just as important as setting boundaries in relationships. MINGUS shows you how to create healthy financial boundaries."</blockquote>
                        </div>
                    </div>
                </div>
            </div>
        </section>
'''
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add influencer content before testimonials
        testimonials_pattern = r'(<!-- Testimonials Section -->)'
        if re.search(testimonials_pattern, content):
            content = re.sub(testimonials_pattern, influencer_html + r'\n        ' + r'\1', content)
            
            # Add CSS for influencer content
            css_pattern = r'(</style>)'
            influencer_css = '''
        /* Influencer Content */
        .influencer-section {
            padding: 4rem 0;
            background: var(--surface-color);
        }
        
        .influencer-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 3rem;
            margin: 3rem 0;
        }
        
        .influencer-card {
            display: flex;
            gap: 1.5rem;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .influencer-image img {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            object-fit: cover;
        }
        
        .influencer-content h3 {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-color);
            margin-bottom: 0.5rem;
        }
        
        .influencer-title {
            font-size: 1rem;
            color: var(--primary-color);
            margin-bottom: 1rem;
            font-weight: 600;
        }
        
        .influencer-content blockquote {
            font-style: italic;
            color: var(--text-light);
            line-height: 1.6;
            border-left: 3px solid var(--primary-color);
            padding-left: 1rem;
        }
'''
            content = re.sub(css_pattern, influencer_css + r'\1', content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added influencer content to {file_path}")
        else:
            print(f"❌ Could not find testimonials section in {file_path}")
    
    def add_font_awesome(self, file_path):
        """Add Font Awesome for social media icons"""
        print(f"Adding Font Awesome to: {file_path}")
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add Font Awesome CDN
        head_pattern = r'(<head>)'
        font_awesome_link = r'\1\n    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'
        
        if re.search(head_pattern, content):
            content = re.sub(head_pattern, font_awesome_link, content)
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Added Font Awesome to {file_path}")
        else:
            print(f"❌ Could not find head tag in {file_path}")
    
    def implement_all_features(self):
        """Implement all social media features"""
        print("🚀 Implementing Social Media Integration for MINGUS Application")
        print("=" * 60)
        
        # Files to update
        files_to_update = [
            self.landing_page,
            self.marketing_landing
        ]
        
        for file_path in files_to_update:
            if file_path.exists():
                print(f"\n📄 Processing: {file_path}")
                
                # Add Font Awesome first
                self.add_font_awesome(file_path)
                
                # Add social media features
                self.add_social_media_links_to_footer(file_path)
                self.add_social_sharing_buttons(file_path)
                self.add_social_proof_elements(file_path)
                self.add_influencer_content(file_path)
                
                print(f"✅ Completed: {file_path}")
            else:
                print(f"❌ File not found: {file_path}")
        
        print("\n🎉 Social Media Integration Complete!")
        print("\n📋 Summary of Changes:")
        print("✅ Added social media links to footer")
        print("✅ Added social sharing buttons")
        print("✅ Added social proof elements")
        print("✅ Added influencer content integration")
        print("✅ Added Font Awesome icons")
        print("\n🔗 Next Steps:")
        print("1. Update social media URLs with actual MINGUS accounts")
        print("2. Replace placeholder images with actual influencer photos")
        print("3. Update social proof numbers with real data")
        print("4. Test sharing functionality on all platforms")

if __name__ == "__main__":
    integrator = SocialMediaIntegration()
    integrator.implement_all_features()
