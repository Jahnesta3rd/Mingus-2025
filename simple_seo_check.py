#!/usr/bin/env python3
"""
Simple SEO Validation Script for MINGUS Landing Page
Validates the implemented SEO improvements without external dependencies.
"""

import re
import os
import json

class SimpleSEOValidator:
    def __init__(self, html_file='landing.html'):
        self.html_file = html_file
        self.results = {}
        
    def load_html(self):
        """Load the HTML file content."""
        try:
            with open(self.html_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ Error: {self.html_file} not found")
            return None
    
    def validate_meta_tags(self, content):
        """Validate meta tags implementation."""
        print("\n🔍 Validating Meta Tags...")
        
        # Check title
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title_text = title_match.group(1).strip()
            self.results['title'] = {
                'exists': True,
                'length': len(title_text),
                'content': title_text,
                'score': 100 if 50 <= len(title_text) <= 60 else 50
            }
            print(f"✅ Title: {title_text[:50]}... ({len(title_text)} chars)")
        else:
            self.results['title'] = {'exists': False, 'score': 0}
            print("❌ Title tag missing")
        
        # Check meta description
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if desc_match:
            desc_content = desc_match.group(1)
            self.results['meta_description'] = {
                'exists': True,
                'length': len(desc_content),
                'content': desc_content,
                'score': 100 if 150 <= len(desc_content) <= 160 else 50
            }
            print(f"✅ Meta Description: {desc_content[:50]}... ({len(desc_content)} chars)")
        else:
            self.results['meta_description'] = {'exists': False, 'score': 0}
            print("❌ Meta description missing")
        
        # Check meta keywords
        keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if keywords_match:
            keywords = keywords_match.group(1)
            self.results['meta_keywords'] = {
                'exists': True,
                'keywords': keywords,
                'score': 100
            }
            print(f"✅ Meta Keywords: {keywords}")
        else:
            self.results['meta_keywords'] = {'exists': False, 'score': 0}
            print("❌ Meta keywords missing")
        
        # Check Open Graph tags
        og_tags = re.findall(r'<meta[^>]*property=["\']og:[^"\']*["\'][^>]*>', content, re.IGNORECASE)
        self.results['open_graph'] = {
            'count': len(og_tags),
            'score': min(100, len(og_tags) * 20)
        }
        print(f"✅ Open Graph Tags: {len(og_tags)} tags found")
        
        # Check Twitter Card tags
        twitter_tags = re.findall(r'<meta[^>]*name=["\']twitter:[^"\']*["\'][^>]*>', content, re.IGNORECASE)
        self.results['twitter_cards'] = {
            'count': len(twitter_tags),
            'score': min(100, len(twitter_tags) * 25)
        }
        print(f"✅ Twitter Card Tags: {len(twitter_tags)} tags found")
    
    def validate_structured_data(self, content):
        """Validate structured data implementation."""
        print("\n🔍 Validating Structured Data...")
        
        # Check for JSON-LD scripts
        json_ld_scripts = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', content, re.IGNORECASE | re.DOTALL)
        self.results['structured_data'] = {
            'count': len(json_ld_scripts),
            'score': min(100, len(json_ld_scripts) * 50)
        }
        
        if json_ld_scripts:
            print(f"✅ Structured Data: {len(json_ld_scripts)} JSON-LD scripts found")
            for i, script in enumerate(json_ld_scripts):
                # Try to extract schema type
                type_match = re.search(r'"@type"\s*:\s*"([^"]*)"', script)
                if type_match:
                    schema_type = type_match.group(1)
                    print(f"   - Schema Type: {schema_type}")
                else:
                    print(f"   - Schema Type: Unknown")
        else:
            print("❌ No structured data found")
    
    def validate_images(self, content):
        """Validate image optimization."""
        print("\n🔍 Validating Image Optimization...")
        
        # Find all img tags
        img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
        optimized_count = 0
        total_images = len(img_tags)
        
        for img_tag in img_tags:
            # Check for alt attribute
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
            if alt_match and alt_match.group(1) and alt_match.group(1) != 'Mingus Logo':
                optimized_count += 1
            
            # Check for loading attribute
            if 'loading="lazy"' in img_tag.lower():
                optimized_count += 1
        
        self.results['images'] = {
            'total': total_images,
            'optimized': optimized_count,
            'score': min(100, (optimized_count / (total_images * 2)) * 100) if total_images > 0 else 100
        }
        
        print(f"✅ Images: {total_images} total, {optimized_count} optimized")
    
    def validate_headings(self, content):
        """Validate heading structure."""
        print("\n🔍 Validating Heading Structure...")
        
        # Count headings
        h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
        total_headings = h1_count + h2_count + h3_count
        
        self.results['headings'] = {
            'total': total_headings,
            'h1_count': h1_count,
            'h2_count': h2_count,
            'h3_count': h3_count,
            'score': 100 if h1_count == 1 and h2_count > 0 else 50
        }
        
        print(f"✅ Headings: {total_headings} total, {h1_count} H1, {h2_count} H2, {h3_count} H3")
    
    def validate_technical_seo(self):
        """Validate technical SEO files."""
        print("\n🔍 Validating Technical SEO...")
        
        # Check robots.txt
        robots_exists = os.path.exists('robots.txt')
        self.results['robots_txt'] = {
            'exists': robots_exists,
            'score': 100 if robots_exists else 0
        }
        print(f"{'✅' if robots_exists else '❌'} robots.txt: {'Found' if robots_exists else 'Missing'}")
        
        # Check sitemap.xml
        sitemap_exists = os.path.exists('sitemap.xml')
        self.results['sitemap'] = {
            'exists': sitemap_exists,
            'score': 100 if sitemap_exists else 0
        }
        print(f"{'✅' if sitemap_exists else '❌'} sitemap.xml: {'Found' if sitemap_exists else 'Missing'}")
    
    def validate_keyword_targeting(self, content):
        """Validate keyword targeting."""
        print("\n🔍 Validating Keyword Targeting...")
        
        target_keywords = [
            'personal finance app',
            'black professionals',
            'financial wellness',
            'AI-powered',
            'career advancement',
            'wealth building'
        ]
        
        content_lower = content.lower()
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        title_text = title_match.group(1).lower() if title_match else ''
        
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        desc_text = desc_match.group(1).lower() if desc_match else ''
        
        keyword_scores = {}
        total_score = 0
        
        for keyword in target_keywords:
            content_count = content_lower.count(keyword.lower())
            title_count = title_text.count(keyword.lower())
            desc_count = desc_text.count(keyword.lower())
            
            score = min(100, (content_count + title_count * 3 + desc_count * 2) * 10)
            keyword_scores[keyword] = {
                'content': content_count,
                'title': title_count,
                'description': desc_count,
                'score': score
            }
            total_score += score
        
        self.results['keyword_targeting'] = {
            'keywords': keyword_scores,
            'average_score': total_score / len(target_keywords)
        }
        
        print(f"✅ Keyword Targeting: Average score {total_score / len(target_keywords):.1f}/100")
        for keyword, data in keyword_scores.items():
            print(f"   - {keyword}: {data['score']:.1f}/100")
    
    def generate_report(self):
        """Generate comprehensive SEO report."""
        print("\n" + "="*60)
        print("📊 SEO VALIDATION REPORT")
        print("="*60)
        
        total_score = 0
        max_score = 0
        
        for category, data in self.results.items():
            if 'score' in data:
                score = data['score']
                total_score += score
                max_score += 100
                status = "✅" if score >= 80 else "⚠️" if score >= 50 else "❌"
                print(f"{status} {category.replace('_', ' ').title()}: {score:.1f}/100")
        
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0
        print(f"\n🎯 Overall SEO Score: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print("🌟 Excellent! Your landing page is well-optimized for SEO.")
        elif overall_score >= 60:
            print("👍 Good! Some improvements needed for better rankings.")
        else:
            print("⚠️ Needs work! Implement the recommended improvements.")
        
        # Recommendations
        print("\n📋 RECOMMENDATIONS:")
        if not self.results.get('meta_description', {}).get('exists'):
            print("- Add a compelling meta description")
        if not self.results.get('robots_txt', {}).get('exists'):
            print("- Create a robots.txt file")
        if not self.results.get('sitemap', {}).get('exists'):
            print("- Generate an XML sitemap")
        if self.results.get('structured_data', {}).get('count', 0) == 0:
            print("- Implement structured data markup")
        
        return overall_score
    
    def run_validation(self):
        """Run complete SEO validation."""
        print("🚀 Starting SEO Validation for MINGUS Landing Page...")
        
        content = self.load_html()
        if not content:
            return
        
        self.validate_meta_tags(content)
        self.validate_structured_data(content)
        self.validate_images(content)
        self.validate_headings(content)
        self.validate_technical_seo()
        self.validate_keyword_targeting(content)
        
        return self.generate_report()

if __name__ == "__main__":
    validator = SimpleSEOValidator()
    score = validator.run_validation()
    
    # Save results to file
    with open('seo_validation_results.json', 'w') as f:
        json.dump(validator.results, f, indent=2)
    
    print(f"\n📄 Results saved to seo_validation_results.json")
    print(f"🎯 Final Score: {score:.1f}/100")
