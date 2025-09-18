#!/usr/bin/env python3
"""
Automated Button Analysis for MINGUS Application
Simulates Chrome DevTools mobile emulation and button inspection
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

class MingusButtonAnalyzer:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.results = {
            "analysis_time": datetime.now().isoformat(),
            "device": "iPhone 12 (375x812px)",
            "total_buttons": 0,
            "critical_issues": 0,
            "medium_issues": 0,
            "passed_buttons": 0,
            "button_details": [],
            "issues_breakdown": []
        }
    
    def setup_mobile_chrome(self):
        """Setup Chrome with mobile emulation"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=375,812")
        
        # Mobile device emulation
        mobile_emulation = {
            "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
            "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        }
        chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(375, 812)
            return driver
        except Exception as e:
            print(f"Error setting up Chrome: {e}")
            return None
    
    def analyze_buttons(self, driver):
        """Analyze all buttons on the page"""
        print("🔍 Starting Button Analysis...")
        
        # Find all interactive elements
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, 
            "button, a[role='button'], a[href^='#'], [tabindex='0'], input[type='button'], input[type='submit'], input[type='reset']")
        
        print(f"Found {len(interactive_elements)} interactive elements")
        
        critical_issues = 0
        medium_issues = 0
        passed_buttons = 0
        
        for index, element in enumerate(interactive_elements):
            try:
                # Get element properties
                rect = driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    return {
                        width: rect.width,
                        height: rect.height,
                        top: rect.top,
                        left: rect.left
                    };
                """, element)
                
                # Get computed styles
                computed_styles = driver.execute_script("""
                    var styles = window.getComputedStyle(arguments[0]);
                    return {
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: styles.opacity,
                        minHeight: styles.minHeight,
                        minWidth: styles.minWidth,
                        padding: styles.padding
                    };
                """, element)
                
                # Get element text
                try:
                    text = element.text.strip()
                except:
                    text = ""
                
                # Get element attributes
                try:
                    class_name = element.get_attribute("class") or ""
                    element_id = element.get_attribute("id") or ""
                    tag_name = element.tag_name
                except:
                    class_name = ""
                    element_id = ""
                    tag_name = "unknown"
                
                # Calculate dimensions
                width = round(rect['width'])
                height = round(rect['height'])
                min_size = 44
                
                # Determine visibility
                is_visible = (width > 0 and height > 0 and 
                            computed_styles['display'] != 'none' and 
                            computed_styles['visibility'] != 'hidden' and 
                            computed_styles['opacity'] != '0')
                
                # Check if dimensions meet requirements
                width_pass = width >= min_size
                height_pass = height >= min_size
                overall_pass = width_pass and height_pass and is_visible
                
                # Categorize issues
                issue_type = "PASS"
                if not is_visible:
                    issue_type = "INVISIBLE"
                    critical_issues += 1
                elif not overall_pass:
                    if width < min_size or height < min_size:
                        issue_type = "TOO_SMALL"
                        critical_issues += 1
                    else:
                        issue_type = "OTHER_ISSUE"
                        medium_issues += 1
                else:
                    passed_buttons += 1
                
                # Store button details
                button_info = {
                    "index": index,
                    "tag_name": tag_name,
                    "text": text[:40] + "..." if len(text) > 40 else text,
                    "dimensions": f"{width}x{height}",
                    "is_visible": is_visible,
                    "width_pass": width_pass,
                    "height_pass": height_pass,
                    "overall_pass": overall_pass,
                    "issue_type": issue_type,
                    "computed_styles": computed_styles,
                    "class_name": class_name,
                    "element_id": element_id,
                    "position": {"top": rect['top'], "left": rect['left']}
                }
                
                self.results["button_details"].append(button_info)
                
                # Print results
                if issue_type == "INVISIBLE":
                    print(f"❌ CRITICAL - Button {index}: INVISIBLE ({width}x{height})")
                elif issue_type == "TOO_SMALL":
                    print(f"❌ CRITICAL - Button {index}: TOO SMALL ({width}x{height}) - \"{text[:30]}...\"")
                elif issue_type == "OTHER_ISSUE":
                    print(f"⚠️  MEDIUM - Button {index}: ISSUES ({width}x{height}) - \"{text[:30]}...\"")
                else:
                    print(f"✅ PASS - Button {index}: GOOD ({width}x{height}) - \"{text[:30]}...\"")
                
            except Exception as e:
                print(f"⚠️  Error analyzing button {index}: {e}")
                continue
        
        # Update results
        self.results["total_buttons"] = len(interactive_elements)
        self.results["critical_issues"] = critical_issues
        self.results["medium_issues"] = medium_issues
        self.results["passed_buttons"] = passed_buttons
        
        return critical_issues, medium_issues, passed_buttons
    
    def highlight_problematic_buttons(self, driver):
        """Highlight problematic buttons on the page"""
        print("🎯 Highlighting problematic buttons...")
        
        critical_buttons = [btn for btn in self.results["button_details"] 
                          if btn["issue_type"] in ["INVISIBLE", "TOO_SMALL"]]
        
        for button_info in critical_buttons:
            try:
                # Find the element by index
                elements = driver.find_elements(By.CSS_SELECTOR, 
                    "button, a[role='button'], a[href^='#'], [tabindex='0'], input[type='button'], input[type='submit'], input[type='reset']")
                
                if button_info["index"] < len(elements):
                    element = elements[button_info["index"]]
                    
                    # Highlight the element
                    driver.execute_script("""
                        arguments[0].style.outline = '3px solid red';
                        arguments[0].style.backgroundColor = 'rgba(255, 0, 0, 0.1)';
                    """, element)
                    
            except Exception as e:
                print(f"⚠️  Could not highlight button {button_info['index']}: {e}")
    
    def generate_detailed_report(self):
        """Generate detailed analysis report"""
        print("\n📊 ANALYSIS SUMMARY")
        print("=" * 30)
        print(f"Total Buttons: {self.results['total_buttons']}")
        print(f"✅ Passed: {self.results['passed_buttons']}")
        print(f"❌ Critical Issues: {self.results['critical_issues']}")
        print(f"⚠️  Medium Issues: {self.results['medium_issues']}")
        
        success_rate = (self.results['passed_buttons'] / self.results['total_buttons'] * 100) if self.results['total_buttons'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Critical issues breakdown
        if self.results['critical_issues'] > 0:
            print("\n🚨 CRITICAL ISSUES BREAKDOWN")
            print("=" * 35)
            
            critical_buttons = [btn for btn in self.results["button_details"] 
                              if btn["issue_type"] in ["INVISIBLE", "TOO_SMALL"]]
            
            for btn in critical_buttons:
                print(f"Button {btn['index']}:")
                print(f"  Text: \"{btn['text']}\"")
                print(f"  Dimensions: {btn['dimensions']}")
                print(f"  Visible: {btn['is_visible']}")
                print(f"  Min Height: {btn['computed_styles']['minHeight']}")
                print(f"  Min Width: {btn['computed_styles']['minWidth']}")
                print(f"  Display: {btn['computed_styles']['display']}")
                print(f"  Class: {btn['class_name']}")
                print(f"  ID: {btn['element_id']}")
                print("---")
        
        # Quick fix suggestion
        print("\n🔧 QUICK FIX SUGGESTION")
        print("=" * 30)
        print("Add this CSS to fix critical issues:")
        print("""
button, a, input, select {
  min-height: 44px !important;
  min-width: 44px !important;
  padding: 12px 16px !important;
}
        """)
    
    def save_results(self):
        """Save analysis results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mingus_button_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n💾 Results saved to: {filename}")
        return filename
    
    def run_analysis(self):
        """Run complete button analysis"""
        print("🚀 Starting MINGUS Button Analysis")
        print("=" * 50)
        
        driver = self.setup_mobile_chrome()
        if not driver:
            print("❌ Failed to setup Chrome driver")
            return False
        
        try:
            # Load the page
            print("📱 Loading MINGUS page in mobile emulation...")
            driver.get(self.base_url)
            time.sleep(3)  # Wait for page to load
            
            # Analyze buttons
            critical_issues, medium_issues, passed_buttons = self.analyze_buttons(driver)
            
            # Highlight problematic buttons
            self.highlight_problematic_buttons(driver)
            
            # Generate report
            self.generate_detailed_report()
            
            # Save results
            filename = self.save_results()
            
            # Keep browser open for manual inspection
            print(f"\n✅ Analysis complete! Browser will stay open for 30 seconds for manual inspection.")
            print("Check the highlighted red buttons on the page.")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return False
        finally:
            driver.quit()

if __name__ == "__main__":
    analyzer = MingusButtonAnalyzer()
    success = analyzer.run_analysis()
    
    if success:
        print("\n🎉 Button analysis completed successfully!")
    else:
        print("\n⚠️  Button analysis failed - check the error messages above")
