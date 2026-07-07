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
# ENHANCED WITHDRAWAL BOT WITH CUSTOM UI SUPPORT
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
        
        # Withdrawal amounts from screenshot
        self.withdrawal_amounts = [1800, 3000, 8000, 25000, 70000, 200000, 500000, 1000000, 3000000]
        self.amount_to_withdraw = 1800

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # Uncomment for debugging
        # options.add_argument("--headless=false")

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
            print(f"   💾 Saved HTML: {filename}")
        except:
            pass

    def click_element(self, element):
        """Click element using multiple methods for custom UI"""
        try:
            # Method 1: Scroll and JavaScript click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                # Method 2: Action chains
                actions = ActionChains(self.driver)
                actions.move_to_element(element).click().perform()
                return True
            except:
                try:
                    # Method 3: Regular click
                    element.click()
                    return True
                except:
                    try:
                        # Method 4: Click via JavaScript without scrolling
                        self.driver.execute_script("arguments[0].click();", element)
                        return True
                    except:
                        return False

    def type_text(self, element, text):
        """Type text with proper clearing for custom UI"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            
            # Try multiple ways to clear and type
            try:
                element.click()
                time.sleep(0.2)
                element.clear()
                time.sleep(0.2)
            except:
                self.driver.execute_script("arguments[0].value = '';", element)
            
            # Type character by character
            for char in text:
                element.send_keys(char)
                time.sleep(0.05)
            time.sleep(0.2)
            return True
        except:
            try:
                # JavaScript fallback
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

    def find_login_button(self):
        """Find login button with multiple methods for custom UI"""
        print("   🔍 Looking for login button...")
        
        time.sleep(1)
        
        # Try different button texts
        login_texts = [
            "Log in now", "Log in", "Login", "Sign in", 
            "Sign In", "log in", "login", "Sign in now",
            "Log In", "LOGIN", "SIGN IN", "Log in",
            "Log In Now", "LOG IN NOW"
        ]
        
        # Try exact text matches
        for text in login_texts:
            try:
                # Find by button tag
                btn = self.driver.find_element(By.XPATH, f"//button[normalize-space(text())='{text}']")
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found login button with text: '{text}'")
                    return btn
            except:
                pass
            
            try:
                # Find by any element with text
                btn = self.driver.find_element(By.XPATH, f"//*[normalize-space(text())='{text}' and (self::button or self::a or self::div[@role='button'])]")
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found login button with text: '{text}'")
                    return btn
            except:
                pass
        
        # Try contains text
        for text in login_texts:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        # Check if it's clickable
                        tag = elem.tag_name.lower()
                        if tag in ['button', 'a'] or elem.get_attribute('role') == 'button':
                            print(f"   ✅ Found login button containing: '{text}'")
                            return elem
            except:
                pass
        
        # Try by class names
        class_selectors = [
            "//button[contains(@class, 'login')]",
            "//button[contains(@class, 'btn-login')]",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'primary')]",
            "//button[@type='submit']",
            "//a[contains(@class, 'login')]",
            "//div[contains(@class, 'login-btn')]",
            "//*[contains(@class, 'login-button')]"
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

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(3)
            self.screenshot("01_login_page")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Find phone field - try multiple selectors
            phone_field = None
            phone_selectors = [
                "//input[@placeholder='Please enter your phone number']",
                "//input[@type='text' and contains(@placeholder, 'phone')]",
                "//input[@type='tel']",
                "//input[contains(@class, 'phone')]",
                "//input[contains(@name, 'phone')]",
                "//input[@id='phone']",
                "//input[contains(@placeholder, 'Phone')]"
            ]
            
            for selector in phone_selectors:
                try:
                    phone_field = WebDriverWait(self.driver, 3).until(
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
                "//input[contains(@class, 'password')]",
                "//input[contains(@name, 'password')]",
                "//input[@id='password']"
            ]
            
            for selector in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 3).until(
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

            # Find and click login button
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

            # Check if login successful
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

    # ============================================
    # CUSTOM UI INTERACTIONS
    # ============================================

    def click_withdrawal_method_dropdown(self):
        """Click the withdrawal method dropdown using custom UI detection"""
        print("   🔍 Finding withdrawal method dropdown...")
        
        # Save page for debugging
        self.save_html("withdrawal_page")
        
        # Method 1: Find by the "Withdrawal method" label and click next sibling/container
        try:
            label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
            print("   ✅ Found 'Withdrawal method' label")
            
            # Try to find clickable element after the label
            parent = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'form') or contains(@class, 'item') or contains(@class, 'group')]")
            if parent:
                # Find clickable elements in parent
                clickable = parent.find_elements(By.XPATH, ".//div[contains(@class, 'select') or contains(@class, 'dropdown') or contains(@class, 'picker')]")
                if clickable:
                    self.click_element(clickable[0])
                    print("   ✅ Clicked dropdown via parent container")
                    time.sleep(1)
                    return True
                
                # Try clicking any div with text "Select withdrawal method"
                clickable = parent.find_elements(By.XPATH, ".//*[contains(text(), 'Select withdrawal method')]")
                if clickable:
                    self.click_element(clickable[0])
                    print("   ✅ Clicked 'Select withdrawal method' text")
                    time.sleep(1)
                    return True
        except:
            pass
        
        # Method 2: Find by text "Select withdrawal method" directly
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
            for elem in elements:
                if elem.is_displayed():
                    self.click_element(elem)
                    print("   ✅ Clicked 'Select withdrawal method' directly")
                    time.sleep(1)
                    return True
        except:
            pass
        
        # Method 3: Find by common custom UI classes
        class_selectors = [
            "//div[contains(@class, 'ant-select-selector')]",
            "//div[contains(@class, 'select-container')]",
            "//div[contains(@class, 'dropdown-container')]",
            "//div[contains(@class, 'picker')]",
            "//div[contains(@role, 'combobox')]",
            "//div[contains(@class, 'custom-select')]",
            "//div[contains(@class, 'form-control')]"
        ]
        
        for selector in class_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        # Check if it's near "Withdrawal method" text
                        parent_text = elem.find_element(By.XPATH, "./ancestor::div").text
                        if "Withdrawal method" in parent_text:
                            self.click_element(elem)
                            print(f"   ✅ Clicked dropdown by class: {selector}")
                            time.sleep(1)
                            return True
            except:
                continue
        
        # Method 4: JavaScript to find and click any visible dropdown
        try:
            js_script = """
            var elements = document.querySelectorAll('div, input');
            for (var i = 0; i < elements.length; i++) {
                var text = elements[i].textContent || '';
                var placeholder = elements[i].getAttribute('placeholder') || '';
                
                if (text.includes('Select withdrawal method') || 
                    placeholder.includes('Select withdrawal method') ||
                    text.includes('Withdrawal method')) {
                    // Find the clickable parent
                    var parent = elements[i];
                    while (parent && !parent.classList.contains('select') && !parent.classList.contains('dropdown')) {
                        parent = parent.parentElement;
                        if (parent && (parent.classList.contains('select') || parent.classList.contains('dropdown'))) {
                            return parent;
                        }
                    }
                    return elements[i];
                }
            }
            return null;
            """
            element = self.driver.execute_script(js_script)
            if element:
                self.click_element(element)
                print("   ✅ Clicked dropdown via JavaScript")
                time.sleep(1)
                return True
        except:
            pass
        
        print("   ❌ Could not find withdrawal method dropdown")
        return False

    def select_opay_bank(self):
        """Select OPAY from the dropdown options"""
        print("   🔍 Looking for OPAY in dropdown...")
        
        # Method 1: Try to find OPAY by text
        opay_texts = ["OPAY", "Opay", "opay", "OPAY Payment", "OPAY Bank"]
        
        for text in opay_texts:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        self.click_element(elem)
                        print(f"   ✅ Selected OPAY")
                        time.sleep(0.5)
                        return True
            except:
                continue
        
        # Method 2: Find by li or option elements
        try:
            options = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'option') or contains(@class, 'item')]")
            for opt in options:
                if "OPAY" in opt.text.upper():
                    self.click_element(opt)
                    print("   ✅ Selected OPAY from list item")
                    time.sleep(0.5)
                    return True
        except:
            pass
        
        # Method 3: JavaScript to find and click OPAY
        try:
            js_script = """
            var items = document.querySelectorAll('li, div, span, a');
            for (var i = 0; i < items.length; i++) {
                var text = items[i].textContent || '';
                if (text.trim().toUpperCase() === 'OPAY' || text.includes('OPAY')) {
                    if (items[i].offsetParent !== null) {
                        return items[i];
                    }
                }
            }
            return null;
            """
            element = self.driver.execute_script(js_script)
            if element:
                self.click_element(element)
                print("   ✅ Selected OPAY via JavaScript")
                time.sleep(0.5)
                return True
        except:
            pass
        
        print("   ❌ Could not find OPAY option")
        return False

    def select_withdrawal_amount(self, amount):
        """Select withdrawal amount preset"""
        print(f"\n   💰 STEP 2: Selecting amount: {amount}")
        
        time.sleep(1)
        
        # Try to find amount by exact text
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[normalize-space(text())='{amount}']")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    self.click_element(elem)
                    print(f"   ✅ Clicked amount: {amount}")
                    self.screenshot("amount_selected")
                    return True
        except:
            pass
        
        # Try by contains text
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{amount}')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    # Make sure it's not just a partial match
                    if elem.text.strip() == str(amount):
                        self.click_element(elem)
                        print(f"   ✅ Clicked amount: {amount}")
                        self.screenshot("amount_selected")
                        return True
        except:
            pass
        
        # Try to find in grid/buttons
        try:
            buttons = self.driver.find_elements(By.XPATH, "//button | //div[@role='button']")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    try:
                        btn_text = btn.text.replace(',', '').strip()
                        if btn_text.isdigit() and int(btn_text) == amount:
                            self.click_element(btn)
                            print(f"   ✅ Clicked amount: {amount}")
                            self.screenshot("amount_selected")
                            return True
                    except:
                        continue
        except:
            pass
        
        print(f"   ❌ Could not find amount button: {amount}")
        return False

    def enter_fund_password(self, fund_password):
        """Enter fund password"""
        print(f"\n   🔑 STEP 3: Entering fund password...")
        
        password_field = None
        
        # Try different selectors for fund password
        password_selectors = [
            "//input[@placeholder='Please input fund password']",
            "//input[@placeholder='Fund password']",
            "//input[@type='password' and contains(@placeholder, 'fund')]",
            "//input[contains(@class, 'fund')]",
            "//input[contains(@name, 'fund')]",
            "//input[contains(@id, 'fund')]"
        ]
        
        for selector in password_selectors:
            try:
                password_field = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if password_field and password_field.is_displayed():
                    print(f"   ✅ Found fund password field")
                    break
            except:
                continue
        
        if not password_field:
            # Try to find any password input
            try:
                password_fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
                if password_fields:
                    # Usually the fund password is the last password field
                    password_field = password_fields[-1]
                    print("   ✅ Found fund password field by type")
            except:
                pass
        
        if not password_field:
            print("   ❌ Could not find fund password field")
            return False
        
        if self.type_text(password_field, fund_password):
            print(f"   ✅ Fund password entered")
            self.screenshot("password_entered")
            return True
        
        return False

    def click_submit_button(self):
        """Click Submit button"""
        print(f"\n   📤 STEP 4: Clicking Submit...")
        
        # Try different selectors for Submit
        submit_selectors = [
            "//button[normalize-space(text())='Submit']",
            "//button[contains(text(), 'Submit')]",
            "//button[@type='submit']",
            "//*[@type='submit']",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'primary')]",
            "//button[contains(@style, 'green')]",
            "//div[contains(@class, 'submit-btn')]/button",
            "//*[contains(@class, 'btn-submit')]"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if submit_btn and submit_btn.is_displayed():
                    self.click_element(submit_btn)
                    print("   ✅ Clicked Submit")
                    self.screenshot("submit_clicked")
                    return True
            except:
                continue
        
        # Try to find by text "Submit" in any element
        try:
            elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Submit')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    # Check if it's a button or clickable
                    tag = elem.tag_name.lower()
                    if tag in ['button', 'a'] or elem.get_attribute('role') == 'button':
                        self.click_element(elem)
                        print("   ✅ Clicked Submit by text")
                        self.screenshot("submit_clicked")
                        return True
        except:
            pass
        
        print("   ❌ Could not find Submit button")
        return False

    def confirm_withdrawal(self, phone, amount, bank_name):
        """Handle confirmation - works in both headless and interactive mode"""
        if self.is_headless or not self.safety.config.get("require_confirmation", True):
            print(f"   ✅ Auto-confirming withdrawal for {phone}")
            return True
        
        # Interactive mode - ask for confirmation
        try:
            print(f"\n   ⚠️  WITHDRAWAL CONFIRMATION")
            print(f"   Account: {phone}")
            print(f"   Amount: ${amount}")
            print(f"   Bank: {bank_name}")
            
            response = input("   Confirm? (yes/no): ").strip().lower()
            return response == 'yes'
        except (EOFError, KeyboardInterrupt):
            print("   ⚠️ No input available - auto-confirming")
            return True

    def perform_withdrawal(self, login_data):
        """Complete withdrawal process with custom UI"""
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
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        # Use default amount
        withdrawal_amount = 1800
        
        # Safety check
        safety_check = self.safety.can_withdraw(withdrawal_amount, phone)
        if not safety_check["allowed"]:
            print(f"   ⚠️ Withdrawal blocked: {safety_check['reason']}")
            self.safety.log_withdrawal(phone, withdrawal_amount, "blocked", safety_check['reason'])
            return False
        
        # Confirm withdrawal
        if not self.confirm_withdrawal(phone, withdrawal_amount, bank_name):
            print("   ❌ Cancelled")
            self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
            return False

        # STEP 1: Click withdrawal method dropdown
        if not self.click_withdrawal_method_dropdown():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not click dropdown")
            return False
        
        # STEP 2: Select OPAY from dropdown
        if not self.select_opay_bank():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select OPAY")
            return False

        # STEP 3: Select amount
        if not self.select_withdrawal_amount(withdrawal_amount):
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
    # RUN METHOD
    # ============================================

    def run(self):
        """Main run method"""
        print("="*60)
        print(f"🤖 WITHDRAWAL BOT {self.bot_id} STARTING")
        print("="*60)
        
        # Show daily summary
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
            
            # Delay between accounts
            if index < len(self.logins):
                print(f"\n⏳ Waiting 5 seconds before next account...")
                time.sleep(5)

        # Final summary
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

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = WithdrawalBot(bot_id=bot_id)
    bot.run()