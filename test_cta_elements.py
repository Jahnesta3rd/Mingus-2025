#!/usr/bin/env python3
"""
Comprehensive CTA Testing Script for MINGUS Landing Page
Tests all call-to-action elements for effectiveness and optimization
"""

import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path
import requests
from urllib.parse import urljoin, urlparse
import time

class CTATester:
    def __init__(self, html_file_path="landing.html"):
        self.html_file_path = html_file_path
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "total_ctas": 0,
            "cta_analysis": [],
            "strategic_placement_score": 0,
            "visual_prominence_score": 0,
            "copy_quality_score": 0,
            "conversion_paths": [],
            "urgency_messaging": [],
            "consistency_analysis": {},
            "recommendations": []
        }
        
    def load_landing_page(self):
        """Load and parse the landing page HTML"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            self.soup = BeautifulSoup(html_content, 'html.parser')
            return True
        except Exception as e:
            print(f"Error loading HTML file: {e}")
            return False
    
    def find_all_ctas(self):
        """Find all call-to-action elements on the page"""
        ctas = []
        
        # Find buttons and links that could be CTAs
        cta_selectors = [
            'a[href*="quiz"]',
            'a[href*="login"]',
            'a[href*="register"]',
            'a[href*="signup"]',
            'a[href*="demo"]',
            'a[href*="trial"]',
            'button',
            '.hero-cta-primary',
            '.hero-cta-secondary',
            '.landing-nav-cta',
            '.plan-cta',
            '[class*="cta"]',
            '[class*="btn"]'
        ]
        
        for selector in cta_selectors:
            elements = self.soup.select(selector)
            for element in elements:
                # Filter out navigation links that aren't CTAs
                if self._is_actual_cta(element):
                    ctas.append(element)
        
        # Remove duplicates
        unique_ctas = []
        seen_texts = set()
        for cta in ctas:
            text = self._get_cta_text(cta).strip()
            if text and text not in seen_texts:
                unique_ctas.append(cta)
                seen_texts.add(text)
        
        return unique_ctas
    
    def _is_actual_cta(self, element):
        """Determine if an element is actually a CTA"""
        # Skip navigation links that aren't conversion-focused
        nav_links = ['features', 'testimonials', 'pricing', 'about', 'contact', 'help']
        href = element.get('href', '')
        text = self._get_cta_text(element).lower()
        
        # Skip if it's just a navigation link
        if any(nav in href.lower() for nav in nav_links) and not any(cta_word in text for cta_word in ['sign', 'login', 'register', 'start', 'get', 'try', 'determine']):
            return False
        
        return True
    
    def _get_cta_text(self, element):
        """Extract text content from CTA element"""
        return element.get_text(strip=True)
    
    def analyze_cta_placement(self, cta, index):
        """Analyze strategic placement of CTA"""
        placement_analysis = {
            "section": self._get_section_name(cta),
            "position_in_section": self._get_position_in_section(cta),
            "above_the_fold": self._is_above_fold(cta),
            "surrounding_context": self._get_surrounding_context(cta),
            "placement_score": 0
        }
        
        # Score placement based on strategic factors
        score = 0
        
        # Above the fold gets high score
        if placement_analysis["above_the_fold"]:
            score += 30
        
        # Hero section gets high score
        if "hero" in placement_analysis["section"].lower():
            score += 25
        
        # End of sections get good score
        if placement_analysis["position_in_section"] == "end":
            score += 20
        
        # Pricing section gets good score
        if "pricing" in placement_analysis["section"].lower():
            score += 15
        
        # Final CTA section gets high score
        if "final" in placement_analysis["section"].lower():
            score += 25
        
        placement_analysis["placement_score"] = min(score, 100)
        return placement_analysis
    
    def _get_section_name(self, cta):
        """Get the section name where CTA is located"""
        parent_section = cta.find_parent(['section', 'div'], class_=re.compile(r'section|hero|pricing|features|testimonials'))
        if parent_section:
            classes = parent_section.get('class', [])
            for cls in classes:
                if 'section' in cls or 'hero' in cls:
                    return cls.replace('-', ' ').title()
        return "Unknown Section"
    
    def _get_position_in_section(self, cta):
        """Determine position within section (start, middle, end)"""
        parent = cta.find_parent(['section', 'div'], class_=re.compile(r'section|hero|pricing|features|testimonials'))
        if parent:
            # Find all CTA elements within the parent
            cta_elements = parent.find_all(['a', 'button'], class_=re.compile(r'cta|btn|primary|secondary'))
            if not cta_elements:
                return "only"
            
            try:
                cta_index = cta_elements.index(cta)
                total_ctas = len(cta_elements)
                
                if cta_index < total_ctas * 0.33:
                    return "start"
                elif cta_index > total_ctas * 0.66:
                    return "end"
                else:
                    return "middle"
            except ValueError:
                return "unknown"
        return "unknown"
    
    def _is_above_fold(self, cta):
        """Check if CTA is above the fold (first 800px)"""
        # This is a simplified check - in real testing, you'd use browser automation
        # For now, we'll assume hero section CTAs are above the fold
        parent_section = cta.find_parent(['section', 'div'], class_=re.compile(r'hero'))
        return parent_section is not None
    
    def _get_surrounding_context(self, cta):
        """Get surrounding context for CTA"""
        context = {
            "preceding_text": "",
            "following_text": "",
            "has_urgency": False,
            "has_social_proof": False
        }
        
        # Get preceding text
        prev_element = cta.find_previous_sibling()
        if prev_element:
            context["preceding_text"] = prev_element.get_text(strip=True)[:100]
        
        # Get following text
        next_element = cta.find_next_sibling()
        if next_element:
            context["following_text"] = next_element.get_text(strip=True)[:100]
        
        # Check for urgency indicators
        urgency_words = ['limited', 'offer', 'today', 'now', 'expires', 'deadline', 'last chance', 'hurry']
        surrounding_text = context["preceding_text"] + " " + context["following_text"]
        context["has_urgency"] = any(word in surrounding_text.lower() for word in urgency_words)
        
        # Check for social proof
        social_proof_words = ['users', 'customers', 'reviews', 'testimonials', 'join', 'thousands']
        context["has_social_proof"] = any(word in surrounding_text.lower() for word in social_proof_words)
        
        return context
    
    def analyze_visual_prominence(self, cta):
        """Analyze visual prominence of CTA"""
        visual_analysis = {
            "button_type": self._get_button_type(cta),
            "color_scheme": self._get_color_scheme(cta),
            "size_analysis": self._get_size_analysis(cta),
            "contrast_score": 0,
            "prominence_score": 0
        }
        
        # Analyze button type
        button_type = visual_analysis["button_type"]
        if button_type == "primary":
            visual_analysis["prominence_score"] += 40
        elif button_type == "secondary":
            visual_analysis["prominence_score"] += 20
        
        # Analyze color scheme
        color_scheme = visual_analysis["color_scheme"]
        if "green" in color_scheme.lower():
            visual_analysis["prominence_score"] += 30
        elif "accent" in color_scheme.lower():
            visual_analysis["prominence_score"] += 25
        
        # Analyze size
        size_analysis = visual_analysis["size_analysis"]
        if "large" in size_analysis:
            visual_analysis["prominence_score"] += 20
        elif "medium" in size_analysis:
            visual_analysis["prominence_score"] += 15
        
        # Contrast score (simplified)
        if "green" in color_scheme.lower() and "white" in color_scheme.lower():
            visual_analysis["contrast_score"] = 90
        elif "accent" in color_scheme.lower():
            visual_analysis["contrast_score"] = 80
        else:
            visual_analysis["contrast_score"] = 60
        
        visual_analysis["prominence_score"] = min(visual_analysis["prominence_score"], 100)
        return visual_analysis
    
    def _get_button_type(self, cta):
        """Determine button type (primary, secondary, etc.)"""
        classes = cta.get('class', [])
        if any('primary' in cls for cls in classes):
            return "primary"
        elif any('secondary' in cls for cls in classes):
            return "secondary"
        elif any('cta' in cls for cls in classes):
            return "cta"
        else:
            return "standard"
    
    def _get_color_scheme(self, cta):
        """Extract color scheme from CSS classes"""
        classes = cta.get('class', [])
        color_classes = [cls for cls in classes if any(color in cls for color in ['green', 'accent', 'primary', 'secondary'])]
        return " ".join(color_classes) if color_classes else "default"
    
    def _get_size_analysis(self, cta):
        """Analyze button size"""
        classes = cta.get('class', [])
        if any('lg' in cls or 'large' in cls for cls in classes):
            return "large"
        elif any('md' in cls or 'medium' in cls for cls in classes):
            return "medium"
        elif any('sm' in cls or 'small' in cls for cls in classes):
            return "small"
        else:
            return "default"
    
    def analyze_copy_quality(self, cta):
        """Analyze CTA copy quality"""
        text = self._get_cta_text(cta)
        copy_analysis = {
            "text": text,
            "word_count": len(text.split()),
            "action_words": self._count_action_words(text),
            "clarity_score": 0,
            "urgency_score": 0,
            "benefit_score": 0,
            "overall_score": 0
        }
        
        # Clarity score
        if copy_analysis["word_count"] <= 8:
            copy_analysis["clarity_score"] += 30
        elif copy_analysis["word_count"] <= 12:
            copy_analysis["clarity_score"] += 20
        else:
            copy_analysis["clarity_score"] += 10
        
        # Action words score
        action_ratio = copy_analysis["action_words"] / max(copy_analysis["word_count"], 1)
        copy_analysis["clarity_score"] += min(action_ratio * 40, 40)
        
        # Urgency score
        urgency_words = ['now', 'today', 'start', 'get', 'try', 'begin', 'join', 'sign']
        urgency_count = sum(1 for word in urgency_words if word.lower() in text.lower())
        copy_analysis["urgency_score"] = min(urgency_count * 20, 60)
        
        # Benefit score
        benefit_words = ['free', 'save', 'earn', 'gain', 'improve', 'transform', 'achieve', 'success']
        benefit_count = sum(1 for word in benefit_words if word.lower() in text.lower())
        copy_analysis["benefit_score"] = min(benefit_count * 15, 40)
        
        # Overall score
        copy_analysis["overall_score"] = (
            copy_analysis["clarity_score"] * 0.4 +
            copy_analysis["urgency_score"] * 0.3 +
            copy_analysis["benefit_score"] * 0.3
        )
        
        return copy_analysis
    
    def _count_action_words(self, text):
        """Count action words in CTA text"""
        action_words = ['get', 'start', 'try', 'begin', 'join', 'sign', 'download', 'learn', 'discover', 'explore', 'determine']
        return sum(1 for word in action_words if word.lower() in text.lower())
    
    def analyze_conversion_paths(self):
        """Analyze different conversion paths available"""
        conversion_paths = []
        
        for cta in self.ctas:
            href = cta.get('href', '')
            text = self._get_cta_text(cta)
            
            path_type = self._categorize_conversion_path(href, text)
            if path_type:
                conversion_paths.append({
                    "text": text,
                    "href": href,
                    "type": path_type,
                    "section": self._get_section_name(cta)
                })
        
        return conversion_paths
    
    def _categorize_conversion_path(self, href, text):
        """Categorize conversion path type"""
        href_lower = href.lower()
        text_lower = text.lower()
        
        if 'quiz' in href_lower or 'determine' in text_lower:
            return "assessment/quiz"
        elif 'login' in href_lower or 'sign in' in text_lower:
            return "login"
        elif 'register' in href_lower or 'sign up' in text_lower:
            return "registration"
        elif 'demo' in href_lower or 'demo' in text_lower:
            return "demo"
        elif 'trial' in href_lower or 'free' in text_lower:
            return "free trial"
        else:
            return "general conversion"
    
    def analyze_urgency_messaging(self):
        """Analyze urgency and scarcity messaging"""
        urgency_elements = []
        
        # Find urgency messaging in the page
        urgency_selectors = [
            '.urgency',
            '[class*="urgency"]',
            '[class*="scarcity"]',
            '[class*="limited"]',
            '[class*="offer"]'
        ]
        
        for selector in urgency_selectors:
            elements = self.soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                urgency_elements.append({
                    "text": text,
                    "type": self._categorize_urgency_type(text),
                    "location": self._get_section_name(element),
                    "effectiveness_score": self._score_urgency_effectiveness(text)
                })
        
        return urgency_elements
    
    def _categorize_urgency_type(self, text):
        """Categorize urgency messaging type"""
        text_lower = text.lower()
        
        if 'limited time' in text_lower or 'expires' in text_lower:
            return "time-based"
        elif 'offer' in text_lower or 'discount' in text_lower:
            return "offer-based"
        elif 'last chance' in text_lower or 'final' in text_lower:
            return "scarcity-based"
        elif 'today' in text_lower or 'now' in text_lower:
            return "immediate-action"
        else:
            return "general-urgency"
    
    def _score_urgency_effectiveness(self, text):
        """Score urgency messaging effectiveness"""
        score = 0
        text_lower = text.lower()
        
        # Time pressure
        if any(word in text_lower for word in ['limited', 'expires', 'deadline', 'today']):
            score += 25
        
        # Specific offer
        if any(word in text_lower for word in ['50%', 'discount', 'offer', 'save']):
            score += 25
        
        # Clear benefit
        if any(word in text_lower for word in ['free', 'save', 'gain', 'get']):
            score += 25
        
        # Action-oriented
        if any(word in text_lower for word in ['sign up', 'start', 'join', 'get']):
            score += 25
        
        return min(score, 100)
    
    def analyze_consistency(self):
        """Analyze CTA consistency across different page sections"""
        consistency_analysis = {
            "button_styles": {},
            "copy_patterns": {},
            "placement_patterns": {},
            "consistency_score": 0
        }
        
        # Analyze button styles
        for cta in self.ctas:
            button_type = self._get_button_type(cta)
            section = self._get_section_name(cta)
            
            if button_type not in consistency_analysis["button_styles"]:
                consistency_analysis["button_styles"][button_type] = []
            consistency_analysis["button_styles"][button_type].append(section)
        
        # Analyze copy patterns
        for cta in self.ctas:
            text = self._get_cta_text(cta)
            section = self._get_section_name(cta)
            
            # Extract key action words
            action_words = [word for word in text.lower().split() if word in ['determine', 'sign', 'get', 'start', 'try']]
            for word in action_words:
                if word not in consistency_analysis["copy_patterns"]:
                    consistency_analysis["copy_patterns"][word] = []
                consistency_analysis["copy_patterns"][word].append(section)
        
        # Calculate consistency score
        style_consistency = len(consistency_analysis["button_styles"]) / max(len(self.ctas), 1) * 100
        copy_consistency = len(consistency_analysis["copy_patterns"]) / max(len(self.ctas), 1) * 100
        
        consistency_analysis["consistency_score"] = (style_consistency + copy_consistency) / 2
        
        return consistency_analysis
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        recommendations = []
        
        # Analyze overall scores
        avg_placement_score = sum(cta["placement_analysis"]["placement_score"] for cta in self.results["cta_analysis"]) / max(len(self.results["cta_analysis"]), 1)
        avg_prominence_score = sum(cta["visual_analysis"]["prominence_score"] for cta in self.results["cta_analysis"]) / max(len(self.results["cta_analysis"]), 1)
        avg_copy_score = sum(cta["copy_analysis"]["overall_score"] for cta in self.results["cta_analysis"]) / max(len(self.results["cta_analysis"]), 1)
        
        # Placement recommendations
        if avg_placement_score < 70:
            recommendations.append({
                "category": "Placement",
                "priority": "High",
                "recommendation": "Consider adding more CTAs in high-converting sections like hero and pricing",
                "impact": "High"
            })
        
        # Visual prominence recommendations
        if avg_prominence_score < 70:
            recommendations.append({
                "category": "Visual Design",
                "priority": "Medium",
                "recommendation": "Enhance CTA button contrast and size for better visibility",
                "impact": "Medium"
            })
        
        # Copy recommendations
        if avg_copy_score < 70:
            recommendations.append({
                "category": "Copy",
                "priority": "High",
                "recommendation": "Optimize CTA copy to be more action-oriented and benefit-focused",
                "impact": "High"
            })
        
        # Conversion path recommendations
        conversion_types = set(path["type"] for path in self.results["conversion_paths"])
        if len(conversion_types) < 3:
            recommendations.append({
                "category": "Conversion Paths",
                "priority": "Medium",
                "recommendation": "Add more diverse conversion paths (demo, free trial, assessment)",
                "impact": "Medium"
            })
        
        # Urgency recommendations
        if not self.results["urgency_messaging"]:
            recommendations.append({
                "category": "Urgency",
                "priority": "Medium",
                "recommendation": "Add urgency messaging to increase conversion rates",
                "impact": "Medium"
            })
        
        return recommendations
    
    def run_comprehensive_test(self):
        """Run the complete CTA analysis"""
        print("🔍 Starting comprehensive CTA analysis...")
        
        if not self.load_landing_page():
            return False
        
        # Find all CTAs
        self.ctas = self.find_all_ctas()
        self.results["total_ctas"] = len(self.ctas)
        
        print(f"📊 Found {len(self.ctas)} CTA elements")
        
        # Analyze each CTA
        for i, cta in enumerate(self.ctas):
            print(f"  Analyzing CTA {i+1}/{len(self.ctas)}: {self._get_cta_text(cta)[:50]}...")
            
            cta_analysis = {
                "index": i + 1,
                "text": self._get_cta_text(cta),
                "href": cta.get('href', ''),
                "placement_analysis": self.analyze_cta_placement(cta, i),
                "visual_analysis": self.analyze_visual_prominence(cta),
                "copy_analysis": self.analyze_copy_quality(cta)
            }
            
            self.results["cta_analysis"].append(cta_analysis)
        
        # Analyze conversion paths
        print("🛤️  Analyzing conversion paths...")
        self.results["conversion_paths"] = self.analyze_conversion_paths()
        
        # Analyze urgency messaging
        print("⏰ Analyzing urgency messaging...")
        self.results["urgency_messaging"] = self.analyze_urgency_messaging()
        
        # Analyze consistency
        print("🔄 Analyzing CTA consistency...")
        self.results["consistency_analysis"] = self.analyze_consistency()
        
        # Generate recommendations
        print("💡 Generating recommendations...")
        self.results["recommendations"] = self.generate_recommendations()
        
        # Calculate overall scores
        if self.results["cta_analysis"]:
            self.results["strategic_placement_score"] = sum(cta["placement_analysis"]["placement_score"] for cta in self.results["cta_analysis"]) / len(self.results["cta_analysis"])
            self.results["visual_prominence_score"] = sum(cta["visual_analysis"]["prominence_score"] for cta in self.results["cta_analysis"]) / len(self.results["cta_analysis"])
            self.results["copy_quality_score"] = sum(cta["copy_analysis"]["overall_score"] for cta in self.results["cta_analysis"]) / len(self.results["cta_analysis"])
        
        return True
    
    def generate_report(self):
        """Generate a comprehensive CTA analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"cta_analysis_report_{timestamp}.md"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# MINGUS Landing Page CTA Analysis Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total CTAs Found:** {self.results['total_ctas']}\n")
            f.write(f"- **Strategic Placement Score:** {self.results['strategic_placement_score']:.1f}/100\n")
            f.write(f"- **Visual Prominence Score:** {self.results['visual_prominence_score']:.1f}/100\n")
            f.write(f"- **Copy Quality Score:** {self.results['copy_quality_score']:.1f}/100\n")
            f.write(f"- **Consistency Score:** {self.results['consistency_analysis']['consistency_score']:.1f}/100\n\n")
            
            # CTA Inventory
            f.write("## CTA Inventory\n\n")
            for cta in self.results["cta_analysis"]:
                f.write(f"### CTA {cta['index']}: {cta['text']}\n")
                f.write(f"- **Location:** {cta['placement_analysis']['section']}\n")
                f.write(f"- **Placement Score:** {cta['placement_analysis']['placement_score']}/100\n")
                f.write(f"- **Visual Score:** {cta['visual_analysis']['prominence_score']}/100\n")
                f.write(f"- **Copy Score:** {cta['copy_analysis']['overall_score']:.1f}/100\n")
                f.write(f"- **Button Type:** {cta['visual_analysis']['button_type']}\n")
                f.write(f"- **Above the Fold:** {'Yes' if cta['placement_analysis']['above_the_fold'] else 'No'}\n\n")
            
            # Conversion Paths Analysis
            f.write("## Conversion Paths Analysis\n\n")
            path_types = {}
            for path in self.results["conversion_paths"]:
                path_type = path["type"]
                if path_type not in path_types:
                    path_types[path_type] = []
                path_types[path_type].append(path)
            
            for path_type, paths in path_types.items():
                f.write(f"### {path_type.title()}\n")
                for path in paths:
                    f.write(f"- **{path['text']}** ({path['section']})\n")
                f.write("\n")
            
            # Urgency Messaging Analysis
            if self.results["urgency_messaging"]:
                f.write("## Urgency Messaging Analysis\n\n")
                for urgency in self.results["urgency_messaging"]:
                    f.write(f"### {urgency['type'].title()}\n")
                    f.write(f"- **Text:** {urgency['text']}\n")
                    f.write(f"- **Location:** {urgency['location']}\n")
                    f.write(f"- **Effectiveness Score:** {urgency['effectiveness_score']}/100\n\n")
            else:
                f.write("## Urgency Messaging Analysis\n\n")
                f.write("❌ **No urgency messaging found on the page**\n\n")
            
            # Consistency Analysis
            f.write("## Consistency Analysis\n\n")
            f.write(f"**Overall Consistency Score:** {self.results['consistency_analysis']['consistency_score']:.1f}/100\n\n")
            
            f.write("### Button Style Distribution\n")
            for style, sections in self.results["consistency_analysis"]["button_styles"].items():
                f.write(f"- **{style.title()}:** {len(sections)} instances\n")
            f.write("\n")
            
            f.write("### Copy Pattern Distribution\n")
            for pattern, sections in self.results["consistency_analysis"]["copy_patterns"].items():
                f.write(f"- **'{pattern}'**: {len(sections)} instances\n")
            f.write("\n")
            
            # Recommendations
            f.write("## Recommendations\n\n")
            for rec in self.results["recommendations"]:
                f.write(f"### {rec['category']} - {rec['priority']} Priority\n")
                f.write(f"**Recommendation:** {rec['recommendation']}\n")
                f.write(f"**Impact:** {rec['impact']}\n\n")
            
            # Detailed CTA Analysis
            f.write("## Detailed CTA Analysis\n\n")
            for cta in self.results["cta_analysis"]:
                f.write(f"### CTA {cta['index']}: {cta['text']}\n\n")
                
                f.write("**Placement Analysis:**\n")
                f.write(f"- Section: {cta['placement_analysis']['section']}\n")
                f.write(f"- Position: {cta['placement_analysis']['position_in_section']}\n")
                f.write(f"- Above the fold: {cta['placement_analysis']['above_the_fold']}\n")
                f.write(f"- Has urgency context: {cta['placement_analysis']['surrounding_context']['has_urgency']}\n")
                f.write(f"- Has social proof: {cta['placement_analysis']['surrounding_context']['has_social_proof']}\n\n")
                
                f.write("**Visual Analysis:**\n")
                f.write(f"- Button type: {cta['visual_analysis']['button_type']}\n")
                f.write(f"- Color scheme: {cta['visual_analysis']['color_scheme']}\n")
                f.write(f"- Size: {cta['visual_analysis']['size_analysis']}\n")
                f.write(f"- Contrast score: {cta['visual_analysis']['contrast_score']}/100\n\n")
                
                f.write("**Copy Analysis:**\n")
                f.write(f"- Word count: {cta['copy_analysis']['word_count']}\n")
                f.write(f"- Action words: {cta['copy_analysis']['action_words']}\n")
                f.write(f"- Clarity score: {cta['copy_analysis']['clarity_score']:.1f}/100\n")
                f.write(f"- Urgency score: {cta['copy_analysis']['urgency_score']:.1f}/100\n")
                f.write(f"- Benefit score: {cta['copy_analysis']['benefit_score']:.1f}/100\n\n")
                
                f.write("---\n\n")
        
        print(f"📄 Report generated: {report_file}")
        return report_file
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"cta_analysis_results_{timestamp}.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved: {json_file}")
        return json_file

def main():
    """Main function to run CTA testing"""
    print("🚀 MINGUS Landing Page CTA Analysis")
    print("=" * 50)
    
    tester = CTATester()
    
    if tester.run_comprehensive_test():
        report_file = tester.generate_report()
        json_file = tester.save_results()
        
        print("\n✅ Analysis Complete!")
        print(f"📊 Found {tester.results['total_ctas']} CTAs")
        print(f"📄 Report: {report_file}")
        print(f"💾 Data: {json_file}")
        
        # Print quick summary
        print("\n📋 Quick Summary:")
        print(f"  • Strategic Placement: {tester.results['strategic_placement_score']:.1f}/100")
        print(f"  • Visual Prominence: {tester.results['visual_prominence_score']:.1f}/100")
        print(f"  • Copy Quality: {tester.results['copy_quality_score']:.1f}/100")
        print(f"  • Consistency: {tester.results['consistency_analysis']['consistency_score']:.1f}/100")
        
        if tester.results['recommendations']:
            print(f"\n💡 Top Recommendations:")
            for rec in tester.results['recommendations'][:3]:
                print(f"  • {rec['category']}: {rec['recommendation']}")
    else:
        print("❌ Analysis failed. Please check the HTML file.")

if __name__ == "__main__":
    main()
