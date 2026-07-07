from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
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
# WITHDRAWAL BOT WITH DEBUGGING
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
        """Click element using multiple methods"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.3)
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

    def type_text(self, element, text):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            element.click()
            time.sleep(0.2)
            element.clear()
            time.sleep(0.2)
            for char in text:
                element.send_keys(char)
                time.sleep(0.05)
            time.sleep(0.2)
            return True
        except:
            try:
                self.driver.execute_script(f"arguments[0].value = '{text}';", element)
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
    # DEBUGGING FUNCTIONS
    # ============================================

    def debug_page_elements(self):
        """Print all interactive elements on page for debugging"""
        print("\n   🔍 DEBUG - Page Elements:")
        print("   " + "-"*40)
        
        # Find all inputs
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        print(f"   📝 Inputs ({len(inputs)}):")
        for i, inp in enumerate(inputs[:10]):
            placeholder = inp.get_attribute("placeholder") or ""
            class_name = inp.get_attribute("class") or ""
            input_type = inp.get_attribute("type") or ""
            print(f"      {i+1}. type='{input_type}' placeholder='{placeholder}' class='{class_name}'")
        
        # Find all buttons
        buttons = self.driver.find_elements(By.TAG_NAME, "button")
        print(f"\n   🔘 Buttons ({len(buttons)}):")
        for i, btn in enumerate(buttons[:10]):
            text = btn.text.strip() or ""
            class_name = btn.get_attribute("class") or ""
            print(f"      {i+1}. text='{text}' class='{class_name}'")
        
        # Find all divs with text or classes
        divs = self.driver.find_elements(By.XPATH, "//div[text() or @class]")
        print(f"\n   📦 Divs with text/class ({len(divs)}):")
        count = 0
        for div in divs:
            if count >= 15:
                break
            text = div.text.strip()[:50] or ""
            class_name = div.get_attribute("class") or ""
            if text or class_name:
                print(f"      {count+1}. text='{text}' class='{class_name}'")
                count += 1
        
        # Find clickable elements
        clickable = self.driver.find_elements(By.XPATH, "//*[@role='button' or @role='combobox' or @role='listbox']")
        print(f"\n   🖱️  Clickable elements ({len(clickable)}):")
        for i, elem in enumerate(clickable[:10]):
            role = elem.get_attribute("role") or ""
            text = elem.text.strip()[:50] or ""
            print(f"      {i+1}. role='{role}' text='{text}'")
        
        print("   " + "-"*40 + "\n")

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

            # Find phone field
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

            # Find password field
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

            # Find login button
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
        
        # Try direct text match
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
        
        # Try by class
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
    # WITHDRAWAL - WITH DEBUGGING
    # ============================================

    def click_withdrawal_method(self):
        """Click the 'Withdrawal method' field - with debugging"""
        print("   🔘 Clicking 'Withdrawal method'...")
        
        # Debug the page first
        self.debug_page_elements()
        
        # Try all possible ways to find and click the withdrawal method
        
        # Attempt 1: Click the text "Select withdrawal method"
        try:
            element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
            if element.is_displayed():
                print("   ✅ Found 'Select withdrawal method' text")
                self.click_element(element)
                print("   ✅ Clicked 'Select withdrawal method'")
                time.sleep(1)
                return True
        except Exception as e:
            print(f"   Attempt 1 failed: {e}")
        
        # Attempt 2: Click the "Withdrawal method" label's parent container
        try:
            label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
            print("   ✅ Found 'Withdrawal method' label")
            
            # Find the parent container
            parent = label.find_element(By.XPATH, "./ancestor::div[1]")
            if parent:
                print(f"   Found parent: {parent.get_attribute('class')}")
                # Click the parent div
                self.click_element(parent)
                print("   ✅ Clicked parent container")
                time.sleep(1)
                return True
        except Exception as e:
            print(f"   Attempt 2 failed: {e}")
        
        # Attempt 3: Find by class (common UI frameworks)
        class_selectors = [
            "//div[contains(@class, 'ant-select-selector')]",
            "//div[contains(@class, 'select-container')]",
            "//div[contains(@class, 'dropdown')]",
            "//div[contains(@class, 'picker')]",
            "//div[contains(@class, 'form-control')]",
            "//div[@role='combobox']",
            "//div[@role='listbox']"
        ]
        
        for selector in class_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        print(f"   Found element with class: {selector}")
                        self.click_element(elem)
                        print(f"   ✅ Clicked element: {selector}")
                        time.sleep(1)
                        return True
            except Exception as e:
                continue
        
        # Attempt 4: Find any clickable div near "Withdrawal method"
        try:
            # Get all divs
            divs = self.driver.find_elements(By.XPATH, "//div")
            for div in divs:
                try:
                    if div.is_displayed() and div.is_enabled():
                        # Check if it's near the label
                        parent_text = div.text
                        if "Withdrawal method" in parent_text or "Select withdrawal method" in parent_text:
                            self.click_element(div)
                            print("   ✅ Clicked div containing withdrawal text")
                            time.sleep(1)
                            return True
                except:
                    continue
        except Exception as e:
            print(f"   Attempt 4 failed: {e}")
        
        # Attempt 5: Use JavaScript to find and click
        try:
            js_script = """
            var elements = document.querySelectorAll('div, input, button');
            for (var i = 0; i < elements.length; i++) {
                var text = elements[i].textContent || '';
                var placeholder = elements[i].getAttribute('placeholder') || '';
                var className = elements[i].className || '';
                
                if (text.includes('Select withdrawal method') || 
                    placeholder.includes('Select withdrawal method') ||
                    text.includes('Withdrawal method')) {
                    // Click the element or its parent
                    if (elements[i].offsetParent !== null) {
                        return elements[i];
                    }
                }
            }
            return null;
            """
            element = self.driver.execute_script(js_script)
            if element:
                print("   ✅ Found element via JavaScript")
                self.click_element(element)
                print("   ✅ Clicked element via JavaScript")
                time.sleep(1)
                return True
        except Exception as e:
            print(f"   Attempt 5 failed: {e}")
        
        print("   ❌ Could not click withdrawal method")
        return False

    def select_opay(self):
        """Select OPAY from dropdown"""
        print("   🔘 Selecting OPAY...")
        
        time.sleep(1)
        
        # Try to find OPAY in dropdown
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
        
        # Try list items
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
        """Click withdrawal amount button"""
        print(f"   💰 Clicking amount: {amount}")
        
        # Try to find by exact number
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[normalize-space()='{amount}']")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    self.click_element(elem)
                    print(f"   ✅ Clicked {amount}")
                    return True
        except:
            pass
        
        # Try to find by contains
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
        """Enter fund password"""
        print("   🔑 Entering fund password...")
        
        # Try to find by placeholder
        try:
            field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please input fund password']")
            if field.is_displayed():
                self.type_text(field, password)
                print("   ✅ Fund password entered")
                return True
        except:
            pass
        
        # Try to find by type password
        try:
            fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
            for field in fields:
                if field.is_displayed():
                    self.type_text(field, password)
                    print("   ✅ Fund password entered")
                    return True
        except:
            pass
        
        print("   ❌ Could not find fund password field")
        return False

    def click_submit_button(self):
        """Click Submit button"""
        print("   📤 Clicking Submit...")
        
        # Try to find by text
        try:
            btn = self.driver.find_element(By.XPATH, "//button[text()='Submit']")
            if btn.is_displayed() and btn.is_enabled():
                self.click_element(btn)
                print("   ✅ Clicked Submit")
                return True
        except:
            pass
        
        # Try to find by contains text
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Submit')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    tag = elem.tag_name.lower()
                    if tag == 'button' or tag == 'a' or elem.get_attribute('role') == 'button':
                        self.click_element(elem)
                        print("   ✅ Clicked Submit")
                        return True
        except:
            pass
        
        # Try to find by class
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'submit') or contains(@class, 'primary')]")
            if btn.is_displayed() and btn.is_enabled():
                self.click_element(btn)
                print("   ✅ Clicked Submit")
                return True
        except:
            pass
        
        print("   ❌ Could not find Submit button")
        return False

    def confirm_withdrawal(self, phone, amount, bank_name):
        if self.is_headless or not self.safety.config.get("require_confirmation", True):
            print(f"   ✅ Auto-confirming withdrawal")
            return True
        
        try:
            print(f"\n   ⚠️  WITHDRAWAL CONFIRMATION")
            print(f"   Account: {phone}")
            print(f"   Amount: ${amount}")
            print(f"   Bank: {bank_name}")
            
            response = input("   Confirm? (yes/no): ").strip().lower()
            return response == 'yes'
        except (EOFError, KeyboardInterrupt):
            print("   ⚠️ No input - auto-confirming")
            return True

    def perform_withdrawal(self, login_data):
        phone = login_data['phone']
        bank_name = login_data['bank_name']
        fund_password = login_data['fund_password']
        
        print(f"\n{'='*50}")
        print(f"💸 Processing withdrawal for {phone}")
        print(f"{'='*50}")
        
        # Navigate to withdrawal page
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
        
        # Safety check
        safety_check = self.safety.can_withdraw(withdrawal_amount, phone)
        if not safety_check["allowed"]:
            print(f"   ⚠️ Blocked: {safety_check['reason']}")
            self.safety.log_withdrawal(phone, withdrawal_amount, "blocked", safety_check['reason'])
            return False
        
        # Confirm
        if not self.confirm_withdrawal(phone, withdrawal_amount, bank_name):
            print("   ❌ Cancelled")
            self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
            return False

        # STEP 1: Click withdrawal method
        if not self.click_withdrawal_method():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not click method")
            return False
        
        # STEP 2: Select OPAY
        if not self.select_opay():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select OPAY")
            return False

        # STEP 3: Click amount
        if not self.click_amount(withdrawal_amount):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select amount")
            return False

        # STEP 4: Enter fund password
        if not self.enter_fund_password(fund_password):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not enter password")
            return False

        # STEP 5: Click Submit
        if not self.click_submit_button():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Submit failed")
            return False

        print(f"\n   ✅ Withdrawal submitted!")
        self.safety.log_withdrawal(phone, withdrawal_amount, "success", "Withdrawal submitted")
        
        time.sleep(3)
        self.screenshot("withdrawal_complete")
        return True

    # ============================================
    # RUN
    # ============================================

    def run(self):
        print("="*60)
        print(f"🤖 WITHDRAWAL BOT {self.bot_id} STARTING")
        print("="*60)
        
        summary = self.safety.get_daily_summary()
        print(f"\n📊 DAILY SUMMARY")
        print(f"   Withdrawn today: ${summary['withdrawn_today']:.2f}")
        print(f"   Daily limit: ${summary['daily_limit']:.2f}")
        print(f"   Remaining: ${summary['remaining']:.2f}")
        print("="*60)

        failed_accounts = []
        
        for index, login_data in enumerate(self.logins, 1):
            phone = login_data['phone']
            password = login_data['password']

            print(f"\n📱 Account {index}/{len(self.logins)}: {phone}")

            if not self.login(phone, password):
                print(f"   ❌ Login failed for {phone}")
                failed_accounts.append(phone)
                continue

            success = self.perform_withdrawal(login_data)
            
            if not success:
                failed_accounts.append(phone)
            
            if index < len(self.logins):
                print(f"\n⏳ Waiting 5 seconds...")
                time.sleep(5)

        print("\n" + "="*60)
        print(f"📊 FINAL SUMMARY")
        print(f"   Total accounts: {len(self.logins)}")
        print(f"   Successful: {len(self.logins) - len(failed_accounts)}")
        print(f"   Failed: {len(failed_accounts)}")
        
        summary = self.safety.get_daily_summary()
        print(f"   Total withdrawn today: ${summary['withdrawn_today']:.2f}")
        print("="*60)

        self.driver.quit()
        print(f"\n✅ Withdrawal Bot {self.bot_id} Done!")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = WithdrawalBot(bot_id=bot_id)
    bot.run()