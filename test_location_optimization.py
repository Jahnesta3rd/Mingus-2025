#!/usr/bin/env python3
"""
Location Optimization Test Suite for MINGUS Application
Tests optimization for top 10 target metro areas
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os

@dataclass
class LocationOptimizationTest:
    """Test results for location optimization"""
    metro_area: str
    mentions_found: bool
    location_specific_features: List[str]
    local_seo_implemented: bool
    local_testimonials: List[str]
    region_specific_content: List[str]
    local_market_data: Dict[str, Any]
    optimization_score: float
    recommendations: List[str]

class LocationOptimizationAnalyzer:
    """Analyzes location-specific optimizations for target metro areas"""
    
    def __init__(self):
        self.target_metros = [
            "Atlanta", "Houston", "DC Metro", "Washington DC", "New York", 
            "Los Angeles", "Chicago", "Dallas", "Phoenix", "Philadelphia",
            "San Antonio", "San Diego", "San Jose", "Austin", "Jacksonville",
            "Fort Worth", "Columbus", "Charlotte", "San Francisco", "Indianapolis",
            "Seattle", "Denver", "Boston", "Nashville", "Detroit", "Portland",
            "Memphis", "Oklahoma City", "Las Vegas", "Louisville", "Baltimore",
            "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento", "Mesa",
            "Kansas City", "Long Beach", "Virginia Beach", "Raleigh", "Omaha",
            "Miami", "Oakland", "Minneapolis", "Tulsa", "Arlington", "Tampa",
            "New Orleans", "Wichita", "Cleveland", "Bakersfield", "Aurora",
            "Anaheim", "Honolulu", "Santa Ana", "Corpus Christi", "Riverside",
            "Lexington", "Stockton", "Henderson", "Saint Paul", "St. Louis",
            "Cincinnati", "Pittsburgh", "Anchorage", "Greensboro", "Plano",
            "Newark", "Lincoln", "Orlando", "Irvine", "Durham", "Chula Vista",
            "Jersey City", "Chandler", "Madison", "Laredo", "Lubbock", "Scottsdale",
            "Reno", "Glendale", "Gilbert", "Winston-Salem", "North Las Vegas",
            "Norfolk", "Chesapeake", "Garland", "Irving", "Hialeah", "Fremont",
            "Boise", "Richmond", "Baton Rouge", "Spokane", "Birmingham",
            "Montgomery", "Rochester", "Des Moines", "Modesto", "Fayetteville",
            "Tacoma", "Oxnard", "Fontana", "Moreno Valley", "Columbus",
            "Little Rock", "Amarillo", "Glendale", "Huntington Beach",
            "Salt Lake City", "Grand Rapids", "Tallahassee", "Huntsville",
            "Knoxville", "Worcester", "Newport News", "Brownsville",
            "Santa Clarita", "Overland Park", "Garden Grove", "Oceanside",
            "Tempe", "Dayton", "Mobile", "Chattanooga", "Shreveport",
            "Fort Wayne", "Frisco", "Cary", "Hapeville", "McKinney"
        ]
        
        self.top_10_metros = [
            "Atlanta", "Houston", "Washington DC", "Dallas", "New York",
            "Los Angeles", "Chicago", "Phoenix", "Philadelphia", "San Antonio"
        ]
        
        self.location_data = {
            "Atlanta": {
                "median_income": 72000,
                "cost_of_living_index": 100,
                "cultural_refs": ["ATL", "Black Wall Street", "HBCU", "civil rights"],
                "focus_areas": ["entrepreneurship", "career advancement", "home ownership"]
            },
            "Houston": {
                "median_income": 68000,
                "cost_of_living_index": 95,
                "cultural_refs": ["H-Town", "energy capital", "diversity", "space city"],
                "focus_areas": ["energy_industry", "family support"]
            },
            "Washington DC": {
                "median_income": 95000,
                "cost_of_living_index": 130,
                "cultural_refs": ["DMV", "government", "Howard University", "policy"],
                "focus_areas": ["government_careers", "networking", "policy_influence"]
            },
            "Dallas": {
                "median_income": 70000,
                "cost_of_living_index": 98,
                "cultural_refs": ["DFW", "tech", "energy"],
                "focus_areas": ["tech", "energy", "family_support"]
            },
            "New York": {
                "median_income": 85000,
                "cost_of_living_index": 150,
                "cultural_refs": ["NYC", "Brooklyn", "Harlem", "Wall Street"],
                "focus_areas": ["finance_careers", "investment_opportunities"]
            },
            "Los Angeles": {
                "median_income": 75000,
                "cost_of_living_index": 140,
                "cultural_refs": ["LA", "Hollywood", "South LA", "entertainment"],
                "focus_areas": ["entertainment", "tech", "real_estate"]
            },
            "Chicago": {
                "median_income": 75000,
                "cost_of_living_index": 110,
                "cultural_refs": ["Chi-Town", "South Side", "business", "Midwest"],
                "focus_areas": ["business_careers", "manufacturing"]
            },
            "Phoenix": {
                "median_income": 65000,
                "cost_of_living_index": 105,
                "cultural_refs": ["Valley of the Sun", "desert", "retirement"],
                "focus_areas": ["healthcare", "tourism", "real_estate"]
            },
            "Philadelphia": {
                "median_income": 65000,
                "cost_of_living_index": 105,
                "cultural_refs": ["Philly", "City of Brotherly Love", "history"],
                "focus_areas": ["healthcare", "education", "manufacturing"]
            },
            "San Antonio": {
                "median_income": 60000,
                "cost_of_living_index": 90,
                "cultural_refs": ["Alamo City", "military", "tourism"],
                "focus_areas": ["military", "tourism", "healthcare"]
            }
        }

    def analyze_landing_page_content(self, file_path: str) -> Dict[str, Any]:
        """Analyze landing page for location-specific content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            results = {
                "metro_mentions": [],
                "location_specific_features": [],
                "local_seo_elements": [],
                "local_testimonials": [],
                "region_specific_content": [],
                "local_market_data": [],
                "structured_data": [],
                "meta_tags": []
            }
            
            # Check for metro area mentions
            for metro in self.target_metros:
                if re.search(rf'\b{re.escape(metro)}\b', content, re.IGNORECASE):
                    results["metro_mentions"].append(metro)
            
            # Check for location-specific features
            location_patterns = [
                r'location.*select|city.*select|metro.*area|geographic.*targeting',
                r'cost.*of.*living|salary.*data|market.*data|regional.*pricing',
                r'local.*market|area.*specific|region.*specific'
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                results["location_specific_features"].extend(matches)
            
            # Check for local SEO elements
            seo_patterns = [
                r'schema\.org.*LocalBusiness|schema\.org.*Place',
                r'geo.*latitude|geo.*longitude|geo.*coordinates',
                r'address.*location|contact.*address|business.*address'
            ]
            
            for pattern in seo_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                results["local_seo_elements"].extend(matches)
            
            # Check for local testimonials
            testimonial_patterns = [
                r'testimonial.*\b(atlanta|houston|dc|washington|new york|los angeles|chicago|dallas|phoenix|philadelphia|san antonio)\b',
                r'author.*location.*\b(atlanta|houston|dc|washington|new york|los angeles|chicago|dallas|phoenix|philadelphia|san antonio)\b'
            ]
            
            for pattern in testimonial_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                results["local_testimonials"].extend(matches)
            
            # Check for region-specific content
            region_patterns = [
                r'financial.*challenges.*\b(atlanta|houston|dc|washington|new york|los angeles|chicago|dallas|phoenix|philadelphia|san antonio)\b',
                r'cost.*of.*living.*\b(atlanta|houston|dc|washington|new york|los angeles|chicago|dallas|phoenix|philadelphia|san antonio)\b',
                r'salary.*data.*\b(atlanta|houston|dc|washington|new york|los angeles|chicago|dallas|phoenix|philadelphia|san antonio)\b'
            ]
            
            for pattern in region_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                results["region_specific_content"].extend(matches)
            
            # Check for structured data
            schema_patterns = [
                r'"@type":\s*"LocalBusiness"',
                r'"@type":\s*"Place"',
                r'"address":\s*{',
                r'"geo":\s*{',
                r'"latitude":',
                r'"longitude":'
            ]
            
            for pattern in schema_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                results["structured_data"].extend(matches)
            
            # Check for meta tags
            meta_patterns = [
                r'<meta.*name="geo\.region"',
                r'<meta.*name="geo\.position"',
                r'<meta.*name="geo\.placename"',
                r'<meta.*property="og:locale"'
            ]
            
            for pattern in meta_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                results["meta_tags"].extend(matches)
            
            return results
            
        except Exception as e:
            return {"error": f"Failed to analyze {file_path}: {str(e)}"}

    def analyze_backend_location_data(self) -> Dict[str, Any]:
        """Analyze backend location data implementation"""
        results = {
            "location_services": [],
            "metro_area_data": [],
            "cost_of_living_data": [],
            "salary_data_by_location": [],
            "cultural_context": [],
            "regional_personalization": []
        }
        
        # Check for location services
        service_files = [
            "backend/services/salary_data_service.py",
            "backend/services/sms_message_templates.py",
            "backend/ml/models/geographic_predictor.py",
            "backend/ml/models/income_comparator.py"
        ]
        
        for file_path in service_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check for metro area data
                    metro_matches = re.findall(r'["\'](atlanta|houston|washington|dc|dallas|new york|los angeles|chicago|phoenix|philadelphia|san antonio)["\']', content, re.IGNORECASE)
                    if metro_matches:
                        results["metro_area_data"].extend(metro_matches)
                    
                    # Check for cost of living data
                    col_matches = re.findall(r'cost.*of.*living|cost_index|housing_cost|transportation_cost', content, re.IGNORECASE)
                    if col_matches:
                        results["cost_of_living_data"].extend(col_matches)
                    
                    # Check for salary data by location
                    salary_matches = re.findall(r'salary.*data.*location|location.*salary|metro.*salary', content, re.IGNORECASE)
                    if salary_matches:
                        results["salary_data_by_location"].extend(salary_matches)
                    
                    # Check for cultural context
                    cultural_matches = re.findall(r'cultural.*context|regional.*personalization|cultural.*refs', content, re.IGNORECASE)
                    if cultural_matches:
                        results["cultural_context"].extend(cultural_matches)
                    
                except Exception as e:
                    continue
        
        return results

    def test_location_optimization(self) -> List[LocationOptimizationTest]:
        """Run comprehensive location optimization tests"""
        tests = []
        
        # Analyze landing page
        landing_analysis = self.analyze_landing_page_content("landing.html")
        
        # Analyze backend data
        backend_analysis = self.analyze_backend_location_data()
        
        # Test each top 10 metro area
        for metro in self.top_10_metros:
            test = LocationOptimizationTest(
                metro_area=metro,
                mentions_found=metro in landing_analysis.get("metro_mentions", []),
                location_specific_features=landing_analysis.get("location_specific_features", []),
                local_seo_implemented=len(landing_analysis.get("local_seo_elements", [])) > 0,
                local_testimonials=[t for t in landing_analysis.get("local_testimonials", []) if metro.lower() in t.lower()],
                region_specific_content=[c for c in landing_analysis.get("region_specific_content", []) if metro.lower() in c.lower()],
                local_market_data=self.location_data.get(metro, {}),
                optimization_score=0.0,
                recommendations=[]
            )
            
            # Calculate optimization score
            score = 0.0
            if test.mentions_found:
                score += 20.0
            if test.location_specific_features:
                score += 15.0
            if test.local_seo_implemented:
                score += 20.0
            if test.local_testimonials:
                score += 15.0
            if test.region_specific_content:
                score += 15.0
            if test.local_market_data:
                score += 15.0
            
            test.optimization_score = score
            
            # Generate recommendations
            recommendations = []
            if not test.mentions_found:
                recommendations.append(f"Add explicit mentions of {metro} in landing page content")
            if not test.location_specific_features:
                recommendations.append(f"Implement location-specific features for {metro}")
            if not test.local_seo_implemented:
                recommendations.append(f"Add local SEO structured data for {metro}")
            if not test.local_testimonials:
                recommendations.append(f"Add testimonials from {metro} residents")
            if not test.region_specific_content:
                recommendations.append(f"Create region-specific financial content for {metro}")
            if not test.local_market_data:
                recommendations.append(f"Include local market data for {metro}")
            
            test.recommendations = recommendations
            tests.append(test)
        
        return tests

    def generate_report(self, tests: List[LocationOptimizationTest]) -> str:
        """Generate comprehensive location optimization report"""
        report = []
        report.append("# MINGUS Location Optimization Test Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Executive Summary
        total_score = sum(test.optimization_score for test in tests)
        avg_score = total_score / len(tests) if tests else 0
        report.append("## Executive Summary")
        report.append(f"- **Average Optimization Score**: {avg_score:.1f}/100")
        report.append(f"- **Metro Areas Tested**: {len(tests)}")
        report.append(f"- **Areas with High Optimization**: {len([t for t in tests if t.optimization_score >= 70])}")
        report.append(f"- **Areas Needing Improvement**: {len([t for t in tests if t.optimization_score < 50])}")
        report.append("")
        
        # Detailed Results
        report.append("## Detailed Results by Metro Area")
        for test in tests:
            report.append(f"### {test.metro_area}")
            report.append(f"- **Optimization Score**: {test.optimization_score:.1f}/100")
            report.append(f"- **Mentions Found**: {'✅' if test.mentions_found else '❌'}")
            report.append(f"- **Location-Specific Features**: {'✅' if test.location_specific_features else '❌'}")
            report.append(f"- **Local SEO Implemented**: {'✅' if test.local_seo_implemented else '❌'}")
            report.append(f"- **Local Testimonials**: {'✅' if test.local_testimonials else '❌'}")
            report.append(f"- **Region-Specific Content**: {'✅' if test.region_specific_content else '❌'}")
            report.append(f"- **Local Market Data**: {'✅' if test.local_market_data else '❌'}")
            
            if test.recommendations:
                report.append("- **Recommendations**:")
                for rec in test.recommendations:
                    report.append(f"  - {rec}")
            report.append("")
        
        # Top Recommendations
        report.append("## Top Priority Recommendations")
        all_recommendations = []
        for test in tests:
            all_recommendations.extend(test.recommendations)
        
        # Count and sort recommendations
        rec_counts = {}
        for rec in all_recommendations:
            rec_counts[rec] = rec_counts.get(rec, 0) + 1
        
        sorted_recs = sorted(rec_counts.items(), key=lambda x: x[1], reverse=True)
        for rec, count in sorted_recs[:10]:
            report.append(f"- {rec} (affects {count} metro areas)")
        
        return "\n".join(report)

def main():
    """Main test execution"""
    print("🔍 Starting MINGUS Location Optimization Analysis...")
    
    analyzer = LocationOptimizationAnalyzer()
    
    # Run tests
    print("📊 Running location optimization tests...")
    tests = analyzer.test_location_optimization()
    
    # Generate report
    print("📝 Generating comprehensive report...")
    report = analyzer.generate_report(tests)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"location_optimization_report_{timestamp}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_filename}")
    
    # Print summary
    avg_score = sum(test.optimization_score for test in tests) / len(tests) if tests else 0
    print(f"\n📈 Summary:")
    print(f"- Average Optimization Score: {avg_score:.1f}/100")
    print(f"- Metro Areas Tested: {len(tests)}")
    print(f"- High Optimization Areas: {len([t for t in tests if t.optimization_score >= 70])}")
    print(f"- Areas Needing Improvement: {len([t for t in tests if t.optimization_score < 50])}")

if __name__ == "__main__":
    main()
