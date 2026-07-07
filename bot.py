from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import csv
import os
import sys
import json
from datetime import datetime, date
import re

# ============================================
# WITHDRAWAL SAFETY MANAGER
# ============================================

class WithdrawalSafetyManager:
    def __init__(self, config_file="withdrawal_config.json"):
        self.config = self.load_config(config_file)
        self.daily_withdrawn = 0
        self.last_withdrawal_time = 0
        self.today = date.today()
        self.withdrawal_history = []
        self.load_history()
        self.check_reset_daily()
        
    def load_config(self, config_file):
        default_config = {
            "max_daily_withdrawal": 5000.0,
            "max_single_withdrawal": 3000.0,
            "min_balance_threshold": 100.0,
            "withdrawal_cooldown_seconds": 60,
            "require_confirmation": False,
            "enable_safety_limits": True
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"📝 Created default config: {config_file}")
            return default_config
    
    def load_history(self):
        try:
            with open('withdrawal_history.json', 'r') as f:
                data = json.load(f)
                self.withdrawal_history = data.get('history', [])
                self.daily_withdrawn = data.get('daily_withdrawn', 0)
                self.today = datetime.strptime(data.get('date', date.today().isoformat()), '%Y-%m-%d').date()
        except (FileNotFoundError, json.JSONDecodeError):
            self.withdrawal_history = []
            self.daily_withdrawn = 0
    
    def save_history(self):
        data = {
            'date': self.today.isoformat(),
            'daily_withdrawn': self.daily_withdrawn,
            'history': self.withdrawal_history[-100:]
        }
        with open('withdrawal_history.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_reset_daily(self):
        today = date.today()
        if today > self.today:
            self.daily_withdrawn = 0
            self.today = today
            self.save_history()
            print("🔄 Daily withdrawal counter reset")
    
    def can_withdraw(self, amount, account_phone):
        self.check_reset_daily()
        
        if not self.config.get("enable_safety_limits", True):
            return {"allowed": True}
        
        if self.daily_withdrawn + amount > self.config["max_daily_withdrawal"]:
            remaining = self.config["max_daily_withdrawal"] - self.daily_withdrawn
            return {
                "allowed": False,
                "reason": f"Daily limit exceeded. Remaining: ${remaining:.2f}",
                "remaining": remaining
            }
        
        if amount > self.config["max_single_withdrawal"]:
            return {
                "allowed": False,
                "reason": f"Amount exceeds single withdrawal limit of ${self.config['max_single_withdrawal']}",
                "max_allowed": self.config["max_single_withdrawal"]
            }
        
        time_since_last = time.time() - self.last_withdrawal_time
        if time_since_last < self.config["withdrawal_cooldown_seconds"]:
            wait_time = self.config["withdrawal_cooldown_seconds"] - time_since_last
            return {
                "allowed": False,
                "reason": f"Cooldown active. Wait {wait_time:.0f} seconds",
                "wait_seconds": wait_time
            }
        
        return {"allowed": True}
    
    def log_withdrawal(self, account_phone, amount, status, details=""):
        entry = {
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat(),
            'account': account_phone,
            'amount': amount,
            'status': status,
            'details': details
        }
        self.withdrawal_history.append(entry)
        
        if status == 'success':
            self.daily_withdrawn += amount
            self.last_withdrawal_time = time.time()
            print(f"   ✅ Logged: ${amount:.2f} from {account_phone}")
        else:
            print(f"   ❌ Failed: {details}")
        
        self.save_history()
    
    def get_daily_summary(self):
        self.check_reset_daily()
        return {
            'today': self.today.isoformat(),
            'withdrawn_today': self.daily_withdrawn,
            'daily_limit': self.config["max_daily_withdrawal"],
            'remaining': self.config["max_daily_withdrawal"] - self.daily_withdrawn,
            'total_withdrawals': len(self.withdrawal_history)
        }

# ============================================
# WITHDRAWAL BOT - WITH EXTENSIVE DEBUGGING
# ============================================

class WithdrawalBot:
    def __init__(self, bot_id=1):
        self.bot_id = bot_id
        self.step = 0
        self.logged_in_accounts = []
        self.load_logins()
        
        # Initialize safety manager
        self.safety = WithdrawalSafetyManager()
        
        # Check if running in headless/CI environment
        self.is_headless = os.environ.get('CI', 'false').lower() == 'true' or \
                          'GITHUB_ACTIONS' in os.environ or \
                          'HEADLESS' in os.environ
        
        if self.is_headless:
            print("🤖 Running in headless/CI mode - auto-confirming withdrawals")
            self.safety.config["require_confirmation"] = False

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        print(f"🤖 Bot {self.bot_id} Starting Chrome...")
        try:
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")
        except:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")

    def screenshot(self, name):
        self.step += 1
        try:
            filename = f"bot{self.bot_id}_{self.step:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
        except:
            pass

    def save_html(self, name):
        try:
            filename = f"bot{self.bot_id}_{name}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"   💾 Saved HTML: {name}.html")
        except:
            pass

    def click_element(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                return True
            except:
                try:
                    element.click()
                    return True
                except:
                    return False

    def load_logins(self):
        try:
            with open('logins.csv', 'r') as f:
                reader = csv.reader(f)
                next(reader)
                self.logins = []
                for row in reader:
                    if len(row) >= 6:
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip(),
                            'real_name': row[2].strip(),
                            'bank_name': row[3].strip(),
                            'bank_account': row[4].strip(),
                            'fund_password': row[5].strip()
                        })
                    elif len(row) >= 2:
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip(),
                            'real_name': 'John Penn',
                            'bank_name': 'OPAY',
                            'bank_account': '9074331299',
                            'fund_password': '3333'
                        })
            print(f"📋 Bot {self.bot_id} Loaded {len(self.logins)} login(s)")
        except Exception as e:
            print(f"❌ Error loading logins.csv: {e}")
            self.logins = [{'phone': '08057536473', 'password': 'people56', 'real_name': 'John Penn', 'bank_name': 'OPAY', 'bank_account': '9074331299', 'fund_password': '3333'}]

    # ============================================
    # LOGIN
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(3)
            self.screenshot("01_login_page")
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            phone_field = None
            phone_selectors = [
                "//input[@placeholder='Please enter your phone number']",
                "//input[@type='text' and contains(@placeholder, 'phone')]",
                "//input[@type='tel']",
                "//input[contains(@class, 'phone')]"
            ]
            
            for selector in phone_selectors:
                try:
                    phone_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if phone_field:
                        print(f"   ✅ Found phone field")
                        break
                except:
                    continue
            
            if not phone_field:
                print("   ❌ Could not find phone field")
                return False
            
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")

            password_field = None
            password_selectors = [
                "//input[@placeholder='Please enter login password']",
                "//input[@type='password']",
                "//input[contains(@class, 'password')]"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if password_field:
                        print(f"   ✅ Found password field")
                        break
                except:
                    continue
            
            if not password_field:
                print("   ❌ Could not find password field")
                return False
            
            password_field.clear()
            password_field.send_keys(password)
            print("   ✅ Password entered")
            self.screenshot("03_password_entered")

            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print("   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print("   ❌ Login button not found")
                return False

            time.sleep(5)
            self.screenshot("05_after_login_wait")

            page_source = self.driver.page_source.lower()
            if "important notice" in page_source or "cooperative wealth zone" in page_source:
                print("   ✅ Login success!")
                self.logged_in_accounts.append(phone)
                return True
            else:
                print("   ❌ Login failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

    def find_login_button(self):
        print("   🔍 Looking for login button...")
        time.sleep(1)
        
        login_texts = ["Log in now", "Log in", "Login", "Sign in", "Log In", "LOGIN"]
        
        for text in login_texts:
            try:
                btn = self.driver.find_element(By.XPATH, f"//button[normalize-space()='{text}']")
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found login button: '{text}'")
                    return btn
            except:
                pass
            
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        tag = elem.tag_name.lower()
                        if tag == 'button' or tag == 'a' or elem.get_attribute('role') == 'button':
                            print(f"   ✅ Found login button: '{text}'")
                            return elem
            except:
                pass
        
        class_selectors = [
            "//button[contains(@class, 'login')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'primary')]"
        ]
        
        for selector in class_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        print(f"   ✅ Found login button by class")
                        return elem
            except:
                pass
        
        print("   ❌ No login button found")
        return None

    # ============================================
    # EXTENSIVE DEBUGGING FOR SUBMIT BUTTON
    # ============================================

    def debug_submit_button(self):
        """Extensive debugging of the Submit button"""
        print("\n   🔍 EXTENSIVE SUBMIT BUTTON DEBUGGING")
        print("   " + "="*50)
        
        try:
            # Find all buttons on the page
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"   Total buttons on page: {len(all_buttons)}")
            
            for i, btn in enumerate(all_buttons):
                try:
                    text = btn.text.strip()
                    class_name = btn.get_attribute("class") or ""
                    id_attr = btn.get_attribute("id") or ""
                    is_displayed = btn.is_displayed()
                    is_enabled = btn.is_enabled()
                    tag_name = btn.tag_name
                    
                    # Get CSS properties
                    display = btn.value_of_css_property("display")
                    visibility = btn.value_of_css_property("visibility")
                    opacity = btn.value_of_css_property("opacity")
                    pointer_events = btn.value_of_css_property("pointer-events")
                    position = btn.value_of_css_property("position")
                    z_index = btn.value_of_css_property("z-index")
                    
                    print(f"\n   Button {i+1}:")
                    print(f"      Text: '{text}'")
                    print(f"      Class: '{class_name}'")
                    print(f"      ID: '{id_attr}'")
                    print(f"      Displayed: {is_displayed}")
                    print(f"      Enabled: {is_enabled}")
                    print(f"      CSS - display: {display}, visibility: {visibility}, opacity: {opacity}")
                    print(f"      CSS - pointer-events: {pointer_events}, position: {position}, z-index: {z_index}")
                    
                    # Check if it's the Submit button
                    if "Submit" in text or "submit" in text.lower():
                        print(f"      *** THIS IS THE SUBMIT BUTTON ***")
                        # Try to find what's covering it
                        self.debug_overlay_elements(btn)
                except Exception as e:
                    print(f"      Error getting button info: {e}")
            
            # Find the Submit button specifically
            print("\n   🔍 Looking for Submit button specifically...")
            submit_selectors = [
                "//button[normalize-space()='Submit']",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(@class, 'submit')]",
                "//button[@type='submit']"
            ]
            
            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"   Found {len(elements)} with selector: {selector}")
                        for elem in elements:
                            print(f"      Displayed: {elem.is_displayed()}, Enabled: {elem.is_enabled()}")
                except:
                    pass
            
            # Check if there's a form and find its action
            try:
                forms = self.driver.find_elements(By.TAG_NAME, "form")
                print(f"\n   Forms found: {len(forms)}")
                for i, form in enumerate(forms):
                    action = form.get_attribute("action") or "No action"
                    method = form.get_attribute("method") or "No method"
                    print(f"   Form {i+1}: action='{action}', method='{method}'")
            except:
                pass
            
            print("   " + "="*50 + "\n")
            
        except Exception as e:
            print(f"   Debug error: {e}")

    def debug_overlay_elements(self, element):
        """Check what might be covering the element"""
        try:
            # Get element position
            rect = self.driver.execute_script("""
                var rect = arguments[0].getBoundingClientRect();
                return {
                    top: rect.top,
                    left: rect.left,
                    bottom: rect.bottom,
                    right: rect.right,
                    width: rect.width,
                    height: rect.height
                };
            """, element)
            
            print(f"      Element position: top={rect['top']}, left={rect['left']}, width={rect['width']}, height={rect['height']}")
            
            # Check for elements that might be covering it
            js_check = """
                var rect = arguments[0].getBoundingClientRect();
                var centerX = rect.left + rect.width/2;
                var centerY = rect.top + rect.height/2;
                var topElement = document.elementFromPoint(centerX, centerY);
                if (topElement) {
                    return {
                        tag: topElement.tagName,
                        text: topElement.textContent,
                        class: topElement.className,
                        id: topElement.id,
                        isButton: topElement.tagName === 'BUTTON'
                    };
                }
                return null;
            """
            covering = self.driver.execute_script(js_check, element)
            if covering:
                print(f"      Element at center point: {covering}")
                if covering.get('isButton'):
                    print(f"      *** The element at center is the Submit button itself! ***")
                else:
                    print(f"      *** Something else is covering the Submit button! ***")
        except:
            pass

    def click_withdrawal_method(self):
        print("   🔘 Clicking 'Withdrawal method'...")
        
        try:
            element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
            if element.is_displayed():
                self.click_element(element)
                print("   ✅ Clicked 'Select withdrawal method'")
                time.sleep(1)
                return True
        except:
            pass
        
        try:
            label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
            print("   ✅ Found 'Withdrawal method' label")
            parent = label.find_element(By.XPATH, "./ancestor::div[1]")
            if parent:
                self.click_element(parent)
                print("   ✅ Clicked parent container")
                time.sleep(1)
                return True
        except:
            pass
        
        print("   ❌ Could not click withdrawal method")
        return False

    def select_opay(self):
        print("   🔘 Selecting OPAY...")
        
        time.sleep(1)
        
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'OPAY') or contains(text(), 'Opay')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    self.click_element(elem)
                    print("   ✅ Selected OPAY")
                    time.sleep(0.5)
                    return True
        except:
            pass
        
        try:
            items = self.driver.find_elements(By.XPATH, "//li | //div[@role='option']")
            for item in items:
                if "OPAY" in item.text.upper():
                    self.click_element(item)
                    print("   ✅ Selected OPAY from list")
                    time.sleep(0.5)
                    return True
        except:
            pass
        
        print("   ❌ Could not select OPAY")
        return False

    def click_amount(self, amount):
        print(f"   💰 Clicking amount: {amount}")
        
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[normalize-space()='{amount}']")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    self.click_element(elem)
                    print(f"   ✅ Clicked {amount}")
                    return True
        except:
            pass
        
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{amount}')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    if elem.text.strip() == str(amount):
                        self.click_element(elem)
                        print(f"   ✅ Clicked {amount}")
                        return True
        except:
            pass
        
        print(f"   ❌ Could not click amount {amount}")
        return False

    def enter_fund_password(self, password):
        print(f"   🔑 Entering fund password: {password}")
        
        time.sleep(1)
        
        fund_field = None
        
        try:
            fund_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please input fund password']")
            print("   ✅ Found fund password field by placeholder")
        except:
            pass
        
        if not fund_field:
            try:
                password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
                if password_fields:
                    fund_field = password_fields[-1]
                    print("   ✅ Found fund password field by type")
            except:
                pass
        
        if not fund_field:
            try:
                fund_field = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'fund') or contains(@placeholder, 'Fund')]")
                print("   ✅ Found fund password field by placeholder contains 'fund'")
            except:
                pass
        
        if not fund_field:
            print("   ❌ Could not find fund password field")
            self.screenshot("fund_password_field_not_found")
            return None
        
        try:
            self.driver.execute_script("""
                arguments[0].scrollIntoView({block: 'center'});
                arguments[0].focus();
                arguments[0].value = '';
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
            """, fund_field, password)
            time.sleep(0.5)
            
            typed_value = fund_field.get_attribute('value')
            if typed_value == password:
                print(f"   ✅ Fund password verified: '{typed_value}'")
                self.screenshot("fund_password_entered")
                return fund_field
            else:
                print(f"   ⚠️ Value mismatch. Got: '{typed_value}'")
                return None
                
        except Exception as e:
            print(f"   ❌ Error setting fund password: {e}")
            return None

    def click_submit_with_debug(self):
        """Click Submit with extensive debugging"""
        print("   📤 Attempting to click Submit...")
        
        # Run extensive debugging first
        self.debug_submit_button()
        
        # Try multiple methods
        methods_tried = []
        
        # Method 1: Find by exact text and click with JavaScript
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
            if submit_btn.is_displayed():
                methods_tried.append("JavaScript click on exact text")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", submit_btn)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", submit_btn)
                print("   ✅ Clicked with JavaScript")
                time.sleep(2)
                if self.verify_submit_worked():
                    return True
        except Exception as e:
            print(f"   ⚠️ Method 1 failed: {e}")
        
        # Method 2: Click with ActionChains
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
            if submit_btn.is_displayed():
                methods_tried.append("ActionChains")
                actions = ActionChains(self.driver)
                actions.move_to_element(submit_btn).click().perform()
                print("   ✅ Clicked with ActionChains")
                time.sleep(2)
                if self.verify_submit_worked():
                    return True
        except Exception as e:
            print(f"   ⚠️ Method 2 failed: {e}")
        
        # Method 3: Click using JavaScript events
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
            if submit_btn.is_displayed():
                methods_tried.append("JavaScript events")
                self.driver.execute_script("""
                    arguments[0].scrollIntoView({block: 'center'});
                    arguments[0].dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                    arguments[0].dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                    arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));
                """, submit_btn)
                print("   ✅ Clicked with JavaScript events")
                time.sleep(2)
                if self.verify_submit_worked():
                    return True
        except Exception as e:
            print(f"   ⚠️ Method 3 failed: {e}")
        
        # Method 4: Press Enter on the button
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
            if submit_btn.is_displayed():
                methods_tried.append("Enter key")
                submit_btn.send_keys(Keys.ENTER)
                print("   ✅ Pressed Enter on button")
                time.sleep(2)
                if self.verify_submit_worked():
                    return True
        except Exception as e:
            print(f"   ⚠️ Method 4 failed: {e}")
        
        # Method 5: Submit the form directly
        try:
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            for form in forms:
                methods_tried.append("form.submit()")
                self.driver.execute_script("arguments[0].submit();", form)
                print("   ✅ Submitted form")
                time.sleep(2)
                if self.verify_submit_worked():
                    return True
        except Exception as e:
            print(f"   ⚠️ Method 5 failed: {e}")
        
        # Method 6: Try clicking with JavaScript on the parent
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
            parent = submit_btn.find_element(By.XPATH, "..")
            if parent.is_displayed():
                methods_tried.append("Parent click")
                self.driver.execute_script("arguments[0].click();", parent)
                print("   ✅ Clicked parent element")
                time.sleep(2)
                if self.verify_submit_worked():
                    return True
        except Exception as e:
            print(f"   ⚠️ Method 6 failed: {e}")
        
        print(f"\n   ❌ All methods failed. Methods tried: {', '.join(methods_tried)}")
        return False

    def verify_submit_worked(self):
        """Verify that the submit worked"""
        time.sleep(1)
        
        # Check if confirmation dialog appeared
        try:
            dialog = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Confirm') or contains(text(), 'Cancel')]")
            if dialog.is_displayed():
                print("   ✅ Confirmation dialog detected!")
                return True
        except:
            pass
        
        # Check if Submit button disappeared
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Submit']")
            if submit_btn.is_displayed():
                print("   ❌ Submit button still visible")
                return False
        except:
            print("   ✅ Submit button disappeared!")
            return True
        
        return False

    def handle_confirmation_dialog(self):
        print("   🔘 Handling confirmation dialog...")
        
        time.sleep(2)
        
        # Check if dialog appeared
        dialog_found = False
        
        try:
            confirm_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Confirm']")
            if confirm_btn.is_displayed():
                dialog_found = True
                print("   ✅ Confirmation dialog found")
        except:
            pass
        
        if not dialog_found:
            try:
                cancel_btn = self.driver.find_element(By.XPATH, "//button[normalize-space()='Cancel']")
                if cancel_btn.is_displayed():
                    dialog_found = True
                    print("   ✅ Confirmation dialog found")
            except:
                pass
        
        if not dialog_found:
            print("   ⚠️ No confirmation dialog found")
            return False
        
        # Click Confirm
        confirm_selectors = [
            "//button[normalize-space()='Confirm']",
            "//button[contains(text(), 'Confirm')]",
            "//button[contains(@class, 'confirm')]"
        ]
        
        for selector in confirm_selectors:
            try:
                confirm_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", confirm_btn)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", confirm_btn)
                    print("   ✅ Clicked Confirm")
                    self.screenshot("confirmation_clicked")
                    time.sleep(2)
                    return True
            except:
                continue
        
        print("   ❌ Could not click Confirm")
        return False

    def verify_withdrawal_complete(self):
        time.sleep(2)
        
        page_source = self.driver.page_source.lower()
        success_indicators = [
            "withdrawal successful",
            "withdrawal submitted",
            "pending approval",
            "success"
        ]
        
        for indicator in success_indicators:
            if indicator in page_source:
                print(f"   ✅ Found success indicator: '{indicator}'")
                return True
        
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            if submit_btn.is_displayed():
                print("   ❌ Submit button still visible!")
                return False
        except:
            print("   ✅ Submit button is gone")
            return True
        
        return False

    def confirm_withdrawal(self, phone, amount, bank_name):
        if self.is_headless or not self.safety.config.get("require_confirmation", True):
            return True
        
        try:
            print(f"\n   ⚠️  WITHDRAWAL CONFIRMATION")
            print(f"   Account: {phone}")
            print(f"   Amount: ${amount}")
            print(f"   Bank: {bank_name}")
            
            response = input("   Confirm? (yes/no): ").strip().lower()
            return response == 'yes'
        except (EOFError, KeyboardInterrupt):
            return True

    def perform_withdrawal(self, login_data):
        phone = login_data['phone']
        bank_name = login_data['bank_name']
        fund_password = login_data['fund_password']
        
        print(f"\n{'='*50}")
        print(f"💸 Processing withdrawal for {phone}")
        print(f"{'='*50}")
        
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(4)
            self.screenshot("withdrawal_page")
            self.save_html("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        withdrawal_amount = 1800
        
        safety_check = self.safety.can_withdraw(withdrawal_amount, phone)
        if not safety_check["allowed"]:
            print(f"   ⚠️ Blocked: {safety_check['reason']}")
            self.safety.log_withdrawal(phone, withdrawal_amount, "blocked", safety_check['reason'])
            return False
        
        if not self.confirm_withdrawal(phone, withdrawal_amount, bank_name):
            print("   ❌ Cancelled")
            self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
            return False

        print("\n   📋 STEP 1: Select withdrawal method")
        if not self.click_withdrawal_method():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not click method")
            return False
        
        print("\n   📋 STEP 2: Select OPAY")
        if not self.select_opay():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select OPAY")
            return False

        print("\n   📋 STEP 3: Select amount")
        if not self.click_amount(withdrawal_amount):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select amount")
            return False

        print("\n   📋 STEP 4: Enter fund password")
        fund_field = self.enter_fund_password(fund_password)
        if not fund_field:
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not enter password")
            return False
        
        self.screenshot("after_password_entry")
        print("   📸 Screenshot after password entry")

        print("\n   📋 STEP 5: Submit form with debugging")
        if not self.click_submit_with_debug():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Submit failed")
            return False

        print("\n   📋 STEP 6: Handle confirmation")
        if not self.handle_confirmation_dialog():
            print("   ⚠️ No confirmation dialog")
            if self.verify_withdrawal_complete():
                print("   ✅ Withdrawal completed despite no dialog")
            else:
                self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "No confirmation dialog")
                return False

        print("\n   📋 STEP 7: Verify withdrawal")
        if self.verify_withdrawal_complete():
            print("   ✅ Withdrawal verified!")
        else:
            print("   ❌ Withdrawal verification failed!")
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Verification failed")
            return False

        print(f"\n   ✅ Withdrawal process completed!")
        self.safety.log_withdrawal(phone, withdrawal_amount, "success", "Withdrawal process completed")
        
        time.sleep(3)
        self.screenshot("withdrawal_complete")
        return True

    # ============================================
    # RUN
    # ===========================================