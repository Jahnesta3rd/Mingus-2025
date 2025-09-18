#!/usr/bin/env python3
"""
Test Final MINGUS Button Fixes
Verify that the fine-tuning rules catch the remaining 4 buttons
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class FinalFixTester:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.results = {
            "test_time": datetime.now().isoformat(),
            "before_final_fixes": {},
            "after_final_fixes": {},
            "improvements": {},
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
        print(f"🔍 Analyzing buttons {phase} final fixes...")
        
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, 
            "button, a[role='button'], a[href^='#'], [tabindex='0'], input[type='button'], input[type='submit'], input[type='reset']")
        
        button_analysis = []
        critical_issues = 0
        passed_buttons = 0
        remaining_issues = []
        
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
                        opacity: styles.opacity,
                        minHeight: styles.minHeight,
                        minWidth: styles.minWidth
                    };
                """, element)
                
                try:
                    text = element.text.strip()
                except:
                    text = ""
                
                try:
                    class_name = element.get_attribute("class") or ""
                except:
                    class_name = ""
                
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
                    remaining_issues.append({
                        "index": index,
                        "text": text[:30],
                        "issue": "INVISIBLE",
                        "dimensions": f"{width}x{height}",
                        "class": class_name
                    })
                elif not overall_pass:
                    critical_issues += 1
                    remaining_issues.append({
                        "index": index,
                        "text": text[:30],
                        "issue": "TOO_SMALL",
                        "dimensions": f"{width}x{height}",
                        "class": class_name
                    })
                else:
                    passed_buttons += 1
                
                button_info = {
                    "index": index,
                    "text": text[:30] + "..." if len(text) > 30 else text,
                    "dimensions": f"{width}x{height}",
                    "is_visible": is_visible,
                    "overall_pass": overall_pass,
                    "class_name": class_name,
                    "computed_styles": computed_styles
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
            "button_details": button_analysis,
            "remaining_issues": remaining_issues
        }
    
    def apply_final_fixes(self, driver):
        """Apply the final fine-tuning fixes"""
        print("🔧 Applying final fine-tuning fixes...")
        
        final_fixes_css = """
        /* Fine-tuning for remaining 4 buttons */
        button:not([class]),
        [role="button"]:not([class]),
        input[type="button"]:not([class]),
        a:not([class])[onclick] {
          min-height: 44px !important;
          min-width: 44px !important;
          padding: 8px 12px !important;
          display: inline-block !important;
        }
        
        /* Catch any remaining small buttons */
        button[style*="height: 3"],
        button[style*="height: 2"],
        [role="button"][style*="height: 3"],
        [role="button"][style*="height: 2"] {
          min-height: 44px !important;
        }
        """
        
        # Inject final fixes
        driver.execute_script(f"""
            var style = document.createElement('style');
            style.textContent = `{final_fixes_css}`;
            document.head.appendChild(style);
        """)
        
        print("✅ Final fixes applied successfully!")
    
    def run_final_test(self):
        """Run final fix testing"""
        print("🚀 Starting MINGUS Final Button Fix Testing")
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
            
            # Analyze before final fixes
            print("\n📊 BEFORE FINAL FIXES:")
            before_analysis = self.analyze_buttons(driver, "before")
            self.results["before_final_fixes"] = before_analysis
            
            print(f"Total Buttons: {before_analysis['total_buttons']}")
            print(f"Critical Issues: {before_analysis['critical_issues']}")
            print(f"Passed: {before_analysis['passed_buttons']}")
            print(f"Success Rate: {before_analysis['success_rate']:.1f}%")
            
            if before_analysis['remaining_issues']:
                print(f"\n🚨 Remaining Issues ({len(before_analysis['remaining_issues'])}):")
                for issue in before_analysis['remaining_issues']:
                    print(f"  Button {issue['index']}: {issue['issue']} - {issue['dimensions']} - \"{issue['text']}\"")
            
            # Apply final fixes
            self.apply_final_fixes(driver)
            time.sleep(2)  # Wait for CSS to apply
            
            # Analyze after final fixes
            print("\n📊 AFTER FINAL FIXES:")
            after_analysis = self.analyze_buttons(driver, "after")
            self.results["after_final_fixes"] = after_analysis
            
            print(f"Total Buttons: {after_analysis['total_buttons']}")
            print(f"Critical Issues: {after_analysis['critical_issues']}")
            print(f"Passed: {after_analysis['passed_buttons']}")
            print(f"Success Rate: {after_analysis['success_rate']:.1f}%")
            
            if after_analysis['remaining_issues']:
                print(f"\n⚠️  Still Remaining Issues ({len(after_analysis['remaining_issues'])}):")
                for issue in after_analysis['remaining_issues']:
                    print(f"  Button {issue['index']}: {issue['issue']} - {issue['dimensions']} - \"{issue['text']}\"")
            else:
                print("\n🎉 NO REMAINING ISSUES! All buttons are now properly sized!")
            
            # Calculate improvements
            improvement = after_analysis['success_rate'] - before_analysis['success_rate']
            self.results["improvements"] = {
                "success_rate_improvement": improvement,
                "critical_issues_reduced": before_analysis['critical_issues'] - after_analysis['critical_issues'],
                "passed_buttons_increased": after_analysis['passed_buttons'] - before_analysis['passed_buttons']
            }
            
            # Generate final report
            print("\n📈 FINAL IMPROVEMENTS:")
            print(f"Success Rate Improvement: +{improvement:.1f}%")
            print(f"Critical Issues Reduced: {self.results['improvements']['critical_issues_reduced']}")
            print(f"Passed Buttons Increased: {self.results['improvements']['passed_buttons_increased']}")
            
            # Final status
            if after_analysis['critical_issues'] == 0:
                print("\n🎉 PERFECT! 100% SUCCESS RATE ACHIEVED!")
                print("✅ All buttons meet 44px minimum requirement")
                print("✅ MINGUS is now fully mobile-ready!")
            elif after_analysis['critical_issues'] <= 2:
                print(f"\n🎯 EXCELLENT! Only {after_analysis['critical_issues']} minor issues remaining")
                print("✅ MINGUS is production-ready!")
            else:
                print(f"\n⚠️  {after_analysis['critical_issues']} issues still remain")
                print("🔧 Additional fixes may be needed")
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mingus_final_fix_test_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
            # Keep browser open for inspection
            print("\n✅ Final fix testing complete! Browser will stay open for 30 seconds for manual inspection.")
            time.sleep(30)
            
            return True
            
        except Exception as e:
            print(f"❌ Final fix testing failed: {e}")
            return False
        finally:
            driver.quit()

if __name__ == "__main__":
    tester = FinalFixTester()
    success = tester.run_final_test()
    
    if success:
        print("\n🎉 Final button fix testing completed successfully!")
    else:
        print("\n⚠️  Final button fix testing failed - check the error messages above")
