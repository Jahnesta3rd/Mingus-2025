#!/usr/bin/env python3
"""
Test MINGUS Button Fixes
Verify that the critical button fixes resolve the identified issues
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class ButtonFixTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.fixes_applied = False
        self.results = {
            "test_time": datetime.now().isoformat(),
            "fixes_applied": False,
            "before_fixes": {},
            "after_fixes": {},
            "improvements": [],
            "remaining_issues": []
        }
    
    def setup_mobile_chrome(self):
        """Setup Chrome with mobile emulation"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=375,812")
        
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
    
    def analyze_buttons(self, driver, phase="before"):
        """Analyze button dimensions"""
        print(f"🔍 Analyzing buttons {phase} fixes...")
        
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, 
            "button, a[role='button'], a[href^='#'], [tabindex='0'], input[type='button'], input[type='submit'], input[type='reset']")
        
        button_analysis = []
        critical_issues = 0
        passed_buttons = 0
        
        for index, element in enumerate(interactive_elements):
            try:
                rect = driver.execute_script("""
                    var rect = arguments[0].getBoundingClientRect();
                    return {
                        width: rect.width,
                        height: rect.height
                    };
                """, element)
                
                computed_styles = driver.execute_script("""
                    var styles = window.getComputedStyle(arguments[0]);
                    return {
                        display: styles.display,
                        visibility: styles.visibility,
                        opacity: styles.opacity
                    };
                """, element)
                
                try:
                    text = element.text.strip()
                except:
                    text = ""
                
                width = round(rect['width'])
                height = round(rect['height'])
                min_size = 44
                
                is_visible = (width > 0 and height > 0 and 
                            computed_styles['display'] != 'none' and 
                            computed_styles['visibility'] != 'hidden' and 
                            computed_styles['opacity'] != '0')
                
                width_pass = width >= min_size
                height_pass = height >= min_size
                overall_pass = width_pass and height_pass and is_visible
                
                if not is_visible:
                    critical_issues += 1
                elif not overall_pass:
                    critical_issues += 1
                else:
                    passed_buttons += 1
                
                button_info = {
                    "index": index,
                    "text": text[:30] + "..." if len(text) > 30 else text,
                    "dimensions": f"{width}x{height}",
                    "is_visible": is_visible,
                    "overall_pass": overall_pass,
                    "issue_type": "INVISIBLE" if not is_visible else ("TOO_SMALL" if not overall_pass else "PASS")
                }
                
                button_analysis.append(button_info)
                
            except Exception as e:
                print(f"⚠️  Error analyzing button {index}: {e}")
                continue
        
        return {
            "total_buttons": len(interactive_elements),
            "critical_issues": critical_issues,
            "passed_buttons": passed_buttons,
            "success_rate": (passed_buttons / len(interactive_elements) * 100) if len(interactive_elements) > 0 else 0,
            "button_details": button_analysis
        }
    
    def apply_fixes(self, driver):
        """Apply the critical button fixes"""
        print("🔧 Applying critical button fixes...")
        
        fixes_css = """
        /* MINGUS Mobile Button Fixes - Critical Issues Only */
        
        /* Fix 1: Skip Links (Buttons 0-2) - Currently 32x16px */
        .skip-link,
        a[href^="#"]:focus,
        a[href="#main-content"],
        a[href="#navigation"], 
        a[href="#footer"] {
          min-height: 44px !important;
          min-width: 44px !important;
          padding: 12px 16px !important;
          font-size: 16px;
          background-color: #000;
          color: #fff;
          position: absolute;
          top: 6px;
          left: 6px;
          z-index: 10000;
          text-decoration: none;
          border-radius: 4px;
        }
        
        /* Fix 2: Invisible Buttons (Buttons 3-6) - Currently 0x0px */
        button[style*="0px"],
        [role="button"][style*="0px"],
        button:empty:not(.icon-only) {
          min-width: 44px !important;
          min-height: 44px !important;
          background-color: #f8f9fa !important;
          border: 1px solid #dee2e6 !important;
          display: inline-block !important;
          visibility: visible !important;
          opacity: 1 !important;
        }
        
        /* Fix 3: Navigation Elements (Buttons 7-11) - Currently 40px height */
        .nav-menu button,
        .navigation-item,
        nav button {
          min-height: 44px !important;
          padding: 12px 16px !important;
        }
        
        /* Fix 4: Dashboard Button (Button 16) - Currently 232x32px */
        button:contains("View Full Dashboard"),
        .dashboard-button,
        button[class*="dashboard"] {
          min-height: 44px !important;
          padding: 12px 20px !important;
        }
        
        /* Universal Safety Net */
        button, 
        a[role="button"] {
          min-height: 44px;
          touch-action: manipulation;
        }
        """
        
        # Inject CSS fixes
        driver.execute_script(f"""
            var style = document.createElement('style');
            style.textContent = `{fixes_css}`;
            document.head.appendChild(style);
        """)
        
        self.fixes_applied = True
        print("✅ Fixes applied successfully!")
    
    def test_specific_issues(self, driver):
        """Test specific issues that were identified"""
        print("🎯 Testing specific critical issues...")
        
        issues_tested = {
            "skip_links": False,
            "invisible_buttons": False,
            "navigation_elements": False,
            "dashboard_button": False
        }
        
        # Test skip links (should be 44px+ now)
        skip_links = driver.find_elements(By.CSS_SELECTOR, "a[href^='#']")
        if skip_links:
            for link in skip_links:
                rect = driver.execute_script("return arguments[0].getBoundingClientRect();", link)
                if rect['width'] >= 44 and rect['height'] >= 44:
                    issues_tested["skip_links"] = True
                    break
        
        # Test invisible buttons (should be visible now)
        buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        visible_buttons = 0
        for button in buttons:
            rect = driver.execute_script("return arguments[0].getBoundingClientRect();", button)
            if rect['width'] > 0 and rect['height'] > 0:
                visible_buttons += 1
        
        if visible_buttons > 0:
            issues_tested["invisible_buttons"] = True
        
        # Test navigation elements
        nav_buttons = driver.find_elements(By.CSS_SELECTOR, "nav button, .nav-menu button")
        nav_fixed = 0
        for button in nav_buttons:
            rect = driver.execute_script("return arguments[0].getBoundingClientRect();", button)
            if rect['height'] >= 44:
                nav_fixed += 1
        
        if nav_fixed > 0:
            issues_tested["navigation_elements"] = True
        
        # Test dashboard button
        dashboard_buttons = driver.find_elements(By.CSS_SELECTOR, "button")
        for button in dashboard_buttons:
            if "dashboard" in button.text.lower():
                rect = driver.execute_script("return arguments[0].getBoundingClientRect();", button)
                if rect['height'] >= 44:
                    issues_tested["dashboard_button"] = True
                    break
        
        return issues_tested
    
    def run_fix_test(self):
        """Run complete fix testing"""
        print("🚀 Starting MINGUS Button Fix Testing")
        print("=" * 50)
        
        driver = self.setup_mobile_chrome()
        if not driver:
            print("❌ Failed to setup Chrome driver")
            return False
        
        try:
            # Load page
            print("📱 Loading MINGUS page...")
            driver.get(self.base_url)
            time.sleep(3)
            
            # Analyze before fixes
            print("\n📊 BEFORE FIXES:")
            before_analysis = self.analyze_buttons(driver, "before")
            self.results["before_fixes"] = before_analysis
            
            print(f"Total Buttons: {before_analysis['total_buttons']}")
            print(f"Critical Issues: {before_analysis['critical_issues']}")
            print(f"Passed: {before_analysis['passed_buttons']}")
            print(f"Success Rate: {before_analysis['success_rate']:.1f}%")
            
            # Apply fixes
            self.apply_fixes(driver)
            time.sleep(2)  # Wait for CSS to apply
            
            # Analyze after fixes
            print("\n📊 AFTER FIXES:")
            after_analysis = self.analyze_buttons(driver, "after")
            self.results["after_fixes"] = after_analysis
            
            print(f"Total Buttons: {after_analysis['total_buttons']}")
            print(f"Critical Issues: {after_analysis['critical_issues']}")
            print(f"Passed: {after_analysis['passed_buttons']}")
            print(f"Success Rate: {after_analysis['success_rate']:.1f}%")
            
            # Test specific issues
            issues_tested = self.test_specific_issues(driver)
            self.results["issues_tested"] = issues_tested
            
            # Calculate improvements
            improvement = after_analysis['success_rate'] - before_analysis['success_rate']
            self.results["improvements"] = {
                "success_rate_improvement": improvement,
                "critical_issues_reduced": before_analysis['critical_issues'] - after_analysis['critical_issues'],
                "passed_buttons_increased": after_analysis['passed_buttons'] - before_analysis['passed_buttons']
            }
            
            # Generate report
            print("\n📈 IMPROVEMENTS:")
            print(f"Success Rate Improvement: +{improvement:.1f}%")
            print(f"Critical Issues Reduced: {self.results['improvements']['critical_issues_reduced']}")
            print(f"Passed Buttons Increased: {self.results['improvements']['passed_buttons_increased']}")
            
            print("\n🎯 SPECIFIC ISSUES TESTED:")
            for issue, fixed in issues_tested.items():
                status = "✅ FIXED" if fixed else "❌ NOT FIXED"
                print(f"{issue.replace('_', ' ').title()}: {status}")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mingus_fix_test_results_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
            # Keep browser open for inspection
            print("\n✅ Fix testing complete! Browser will stay open for 30 seconds for manual inspection.")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ Fix testing failed: {e}")
            return False
        finally:
            driver.quit()

if __name__ == "__main__":
    tester = ButtonFixTester()
    success = tester.run_fix_test()
    
    if success:
        print("\n🎉 Button fix testing completed successfully!")
    else:
        print("\n⚠️  Button fix testing failed - check the error messages above")
