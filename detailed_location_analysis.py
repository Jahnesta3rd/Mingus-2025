#!/usr/bin/env python3
"""
Detailed Location Analysis for MINGUS Application
Analyzes specific location implementations found in the codebase
"""

import json
import re
from typing import Dict, List, Any
from datetime import datetime
import os

class DetailedLocationAnalyzer:
    """Detailed analysis of location-specific implementations"""
    
    def __init__(self):
        self.location_files = {
            "income_analysis_form": "templates/income_analysis_form.html",
            "mingus_landing_page": "templates/mingus_landing_page.html",
            "salary_data_service": "backend/services/salary_data_service.py",
            "sms_templates": "backend/services/sms_message_templates.py",
            "geographic_predictor": "backend/ml/models/geographic_predictor.py",
            "income_comparator": "backend/ml/models/income_comparator.py",
            "use_salary_predictions": "frontend/hooks/useSalaryPredictions.js",
            "career_simulator": "frontend/components/CareerSimulator.jsx"
        }

    def analyze_location_implementations(self) -> Dict[str, Any]:
        """Analyze all location implementations in the codebase"""
        results = {
            "location_selectors": {},
            "metro_area_data": {},
            "local_testimonials": {},
            "cultural_context": {},
            "salary_multipliers": {},
            "cost_of_living_data": {},
            "regional_personalization": {},
            "local_seo_implementation": {},
            "recommendations": []
        }
        
        # Analyze each file
        for file_name, file_path in self.location_files.items():
            if os.path.exists(file_path):
                file_analysis = self.analyze_file(file_path, file_name)
                for key, value in file_analysis.items():
                    if key in results:
                        if isinstance(results[key], dict):
                            results[key].update(value)
                        elif isinstance(results[key], list):
                            results[key].extend(value)
        
        return results

    def analyze_file(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """Analyze a specific file for location implementations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {}
            
            if file_name == "income_analysis_form":
                analysis = self.analyze_income_form(content)
            elif file_name == "mingus_landing_page":
                analysis = self.analyze_landing_page(content)
            elif file_name == "salary_data_service":
                analysis = self.analyze_salary_service(content)
            elif file_name == "sms_templates":
                analysis = self.analyze_sms_templates(content)
            elif file_name == "use_salary_predictions":
                analysis = self.analyze_salary_predictions(content)
            elif file_name == "career_simulator":
                analysis = self.analyze_career_simulator(content)
            
            return analysis
            
        except Exception as e:
            return {"error": f"Failed to analyze {file_path}: {str(e)}"}

    def analyze_income_form(self, content: str) -> Dict[str, Any]:
        """Analyze income analysis form for location selectors"""
        analysis = {
            "location_selectors": {},
            "metro_area_data": {}
        }
        
        # Extract location options
        location_pattern = r'<option value="([^"]+)">([^<]+)</option>'
        matches = re.findall(location_pattern, content)
        
        for value, label in matches:
            if any(metro.lower() in value.lower() for metro in ["atlanta", "houston", "dc", "dallas", "new york", "los angeles", "chicago", "philadelphia", "miami"]):
                analysis["location_selectors"][value] = label
                analysis["metro_area_data"][label] = {
                    "form_value": value,
                    "display_name": label
                }
        
        return analysis

    def analyze_landing_page(self, content: str) -> Dict[str, Any]:
        """Analyze landing page for local testimonials and content"""
        analysis = {
            "local_testimonials": {},
            "local_seo_implementation": {}
        }
        
        # Extract testimonials with locations
        testimonial_pattern = r'<div class="author-location">([^<]+)</div>'
        location_matches = re.findall(testimonial_pattern, content)
        
        for location in location_matches:
            analysis["local_testimonials"][location] = {
                "found": True,
                "type": "testimonial_location"
            }
        
        # Check for local SEO elements
        seo_elements = {
            "schema_org": len(re.findall(r'schema\.org', content, re.IGNORECASE)),
            "local_business": len(re.findall(r'LocalBusiness', content, re.IGNORECASE)),
            "place_schema": len(re.findall(r'"@type":\s*"Place"', content, re.IGNORECASE)),
            "geo_tags": len(re.findall(r'geo\.', content, re.IGNORECASE))
        }
        
        analysis["local_seo_implementation"] = seo_elements
        
        return analysis

    def analyze_salary_service(self, content: str) -> Dict[str, Any]:
        """Analyze salary data service for location data"""
        analysis = {
            "metro_area_data": {},
            "cost_of_living_data": {},
            "salary_multipliers": {}
        }
        
        # Extract BLS series IDs
        bls_pattern = r"'([^']+)':\s*'([^']+)'"
        bls_matches = re.findall(bls_pattern, content)
        
        for location, series_id in bls_matches:
            if any(metro.lower() in location.lower() for metro in ["atlanta", "houston", "washington", "dallas", "new york", "philadelphia", "chicago", "charlotte", "miami", "baltimore"]):
                analysis["metro_area_data"][location] = {
                    "bls_series_id": series_id,
                    "data_source": "BLS"
                }
        
        # Extract cost of living data
        col_patterns = [
            r'cost_of_living_index.*?(\d+)',
            r'housing_cost_index.*?(\d+)',
            r'transportation_cost_index.*?(\d+)'
        ]
        
        for pattern in col_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                analysis["cost_of_living_data"]["indices"] = matches
        
        return analysis

    def analyze_sms_templates(self, content: str) -> Dict[str, Any]:
        """Analyze SMS templates for cultural context"""
        analysis = {
            "cultural_context": {},
            "regional_personalization": {}
        }
        
        # Extract regional context data
        context_pattern = r"'([^']+)':\s*{[^}]+'city_name':\s*'([^']+)'[^}]+'cultural_refs':\s*\[([^\]]+)\][^}]+'cost_of_living':\s*'([^']+)'[^}]+'community_focus':\s*'([^']+)'"
        context_matches = re.findall(context_pattern, content, re.DOTALL)
        
        for key, city, refs, col, focus in context_matches:
            analysis["cultural_context"][city] = {
                "cultural_references": [ref.strip().strip("'\"") for ref in refs.split(',')],
                "cost_of_living": col,
                "community_focus": focus
            }
        
        return analysis

    def analyze_salary_predictions(self, content: str) -> Dict[str, Any]:
        """Analyze salary predictions for location multipliers"""
        analysis = {
            "salary_multipliers": {},
            "metro_area_data": {}
        }
        
        # Extract location multipliers
        multiplier_pattern = r"'([^']+)':\s*([\d.]+)"
        multiplier_matches = re.findall(multiplier_pattern, content)
        
        for location, multiplier in multiplier_matches:
            if any(metro.lower() in location.lower() for metro in ["atlanta", "houston", "washington", "dallas", "new york", "philadelphia", "chicago", "charlotte", "miami", "baltimore"]):
                analysis["salary_multipliers"][location] = float(multiplier)
                analysis["metro_area_data"][location] = {
                    "salary_multiplier": float(multiplier),
                    "relative_cost": "high" if float(multiplier) > 1.2 else "medium" if float(multiplier) > 1.0 else "low"
                }
        
        return analysis

    def analyze_career_simulator(self, content: str) -> Dict[str, Any]:
        """Analyze career simulator for location options"""
        analysis = {
            "location_selectors": {},
            "metro_area_data": {}
        }
        
        # Extract location options
        location_pattern = r'{\s*value:\s*[\'"]([^\'"]+)[\'"],\s*label:\s*[\'"]([^\'"]+)[\'"],\s*multiplier:\s*([\d.]+)\s*}'
        location_matches = re.findall(location_pattern, content)
        
        for value, label, multiplier in location_matches:
            analysis["location_selectors"][value] = {
                "label": label,
                "multiplier": float(multiplier)
            }
            analysis["metro_area_data"][label] = {
                "form_value": value,
                "salary_multiplier": float(multiplier)
            }
        
        return analysis

    def generate_detailed_report(self, analysis: Dict[str, Any]) -> str:
        """Generate detailed location analysis report"""
        report = []
        report.append("# Detailed MINGUS Location Implementation Analysis")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Location Selectors
        report.append("## 1. Location Selectors Implementation")
        if analysis["location_selectors"]:
            report.append("### Found in Forms:")
            for location, data in analysis["location_selectors"].items():
                if isinstance(data, dict):
                    report.append(f"- **{location}**: {data.get('label', 'N/A')} (Multiplier: {data.get('multiplier', 'N/A')})")
                else:
                    report.append(f"- **{location}**: {data}")
        else:
            report.append("❌ No location selectors found in forms")
        report.append("")
        
        # Metro Area Data
        report.append("## 2. Metro Area Data Implementation")
        if analysis["metro_area_data"]:
            report.append("### Available Metro Areas:")
            for metro, data in analysis["metro_area_data"].items():
                report.append(f"- **{metro}**:")
                for key, value in data.items():
                    report.append(f"  - {key}: {value}")
        else:
            report.append("❌ No metro area data found")
        report.append("")
        
        # Local Testimonials
        report.append("## 3. Local Testimonials")
        if analysis["local_testimonials"]:
            report.append("### Found Testimonials:")
            for location, data in analysis["local_testimonials"].items():
                report.append(f"- **{location}**: {data.get('type', 'N/A')}")
        else:
            report.append("❌ No local testimonials found")
        report.append("")
        
        # Cultural Context
        report.append("## 4. Cultural Context Implementation")
        if analysis["cultural_context"]:
            report.append("### Regional Cultural Data:")
            for city, data in analysis["cultural_context"].items():
                report.append(f"- **{city}**:")
                report.append(f"  - Cultural References: {', '.join(data.get('cultural_references', []))}")
                report.append(f"  - Cost of Living: {data.get('cost_of_living', 'N/A')}")
                report.append(f"  - Community Focus: {data.get('community_focus', 'N/A')}")
        else:
            report.append("❌ No cultural context data found")
        report.append("")
        
        # Salary Multipliers
        report.append("## 5. Location-Based Salary Multipliers")
        if analysis["salary_multipliers"]:
            report.append("### Salary Adjustment Factors:")
            for location, multiplier in analysis["salary_multipliers"].items():
                cost_level = "High" if multiplier > 1.2 else "Medium" if multiplier > 1.0 else "Low"
                report.append(f"- **{location}**: {multiplier}x ({cost_level} cost of living)")
        else:
            report.append("❌ No salary multipliers found")
        report.append("")
        
        # Cost of Living Data
        report.append("## 6. Cost of Living Data")
        if analysis["cost_of_living_data"]:
            report.append("### Available Cost Indices:")
            for key, value in analysis["cost_of_living_data"].items():
                report.append(f"- **{key}**: {value}")
        else:
            report.append("❌ No cost of living data found")
        report.append("")
        
        # Local SEO Implementation
        report.append("## 7. Local SEO Implementation")
        if analysis["local_seo_implementation"]:
            report.append("### SEO Elements Found:")
            for element, count in analysis["local_seo_implementation"].items():
                status = "✅" if count > 0 else "❌"
                report.append(f"- **{element}**: {count} instances {status}")
        else:
            report.append("❌ No local SEO implementation found")
        report.append("")
        
        # Recommendations
        report.append("## 8. Optimization Recommendations")
        recommendations = []
        
        if not analysis["location_selectors"]:
            recommendations.append("Add location selector dropdown to main forms")
        
        if not analysis["local_testimonials"]:
            recommendations.append("Add testimonials from residents of target metro areas")
        
        if not analysis["cultural_context"]:
            recommendations.append("Implement cultural context personalization")
        
        if not analysis["local_seo_implementation"]:
            recommendations.append("Add local SEO structured data (LocalBusiness, Place schemas)")
        
        if not analysis["cost_of_living_data"]:
            recommendations.append("Include cost of living data for target metro areas")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. {rec}")
        else:
            report.append("✅ All major location optimizations are implemented")
        
        return "\n".join(report)

def main():
    """Main analysis execution"""
    print("🔍 Starting Detailed MINGUS Location Analysis...")
    
    analyzer = DetailedLocationAnalyzer()
    
    # Run analysis
    print("📊 Analyzing location implementations...")
    analysis = analyzer.analyze_location_implementations()
    
    # Generate report
    print("📝 Generating detailed report...")
    report = analyzer.generate_detailed_report(analysis)
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"detailed_location_analysis_{timestamp}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Detailed report saved to: {report_filename}")
    
    # Print summary
    print(f"\n📈 Analysis Summary:")
    print(f"- Location Selectors: {len(analysis['location_selectors'])}")
    print(f"- Metro Areas with Data: {len(analysis['metro_area_data'])}")
    print(f"- Local Testimonials: {len(analysis['local_testimonials'])}")
    print(f"- Cultural Context: {len(analysis['cultural_context'])}")
    print(f"- Salary Multipliers: {len(analysis['salary_multipliers'])}")
    print(f"- Local SEO Elements: {sum(analysis['local_seo_implementation'].values()) if analysis['local_seo_implementation'] else 0}")

if __name__ == "__main__":
    main()
