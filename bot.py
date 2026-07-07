from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
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
    """Manages withdrawal safety limits and tracking"""
    
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
            "require_confirmation": True,
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
# ENHANCED WITHDRAWAL BOT
# ============================================

class WithdrawalBot:
    def __init__(self, bot_id=1):
        self.bot_id = bot_id
        self.step = 0
        self.logged_in_accounts = []
        self.load_logins()
        
        # Initialize safety manager
        self.safety = WithdrawalSafetyManager()
        
        # Withdrawal amounts from screenshot
        self.withdrawal_amounts = [1800, 3000, 8000, 25000, 70000, 200000, 500000, 1000000, 3000000]
        self.amount_to_withdraw = 1800

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # options.add_argument("--headless=false")  # Uncomment to see browser

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
        """Save HTML for debugging"""
        try:
            filename = f"bot{self.bot_id}_{name}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"   💾 Saved HTML: {filename}")
        except:
            pass

    def click_element(self, element):
        """Click element using multiple methods"""
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

    def type_text(self, element, text):
        """Type text with proper clearing"""
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

    def find_login_button(self):
        """Find login button with multiple methods"""
        print("   🔍 Looking for login button...")
        
        time.sleep(1)
        self.save_html("login_page_debug")
        
        # Try different button texts
        login_texts = [
            "Log in now", "Log in", "Login", "Sign in", 
            "Sign In", "log in", "login", "Sign in now",
            "Log In", "LOGIN", "SIGN IN"
        ]
        
        for text in login_texts:
            try:
                btn = self.driver.find_element(By.XPATH, f"//button[text()='{text}']")
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found login button with text: '{text}'")
                    return btn
            except:
                pass
            
            try:
                btn = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found login button with text containing: '{text}'")
                    return btn
            except:
                pass
        
        # Try by class
        class_selectors = [
            "//button[contains(@class, 'login')]",
            "//button[contains(@class, 'btn-login')]",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'primary')]",
            "//button[@type='submit']",
            "//a[contains(@class, 'login')]//button"
        ]
        
        for selector in class_selectors:
            try:
                buttons = self.driver.find_elements(By.XPATH, selector)
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        text = btn.text.strip()
                        print(f"   ✅ Found button with class: '{text}'")
                        return btn
            except:
                pass
        
        # Try to find any visible button
        try:
            all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"   🔍 Found {len(all_buttons)} total buttons")
            
            for btn in all_buttons:
                text = btn.text.strip()
                if btn.is_displayed() and btn.is_enabled():
                    if any(keyword in text.lower() for keyword in ['log', 'in', 'sign', 'login', 'submit']):
                        print(f"   ✅ Found potential login button: '{text}'")
                        return btn
        except:
            pass
        
        # JavaScript fallback
        try:
            js_script = """
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                var text = buttons[i].textContent.toLowerCase();
                if (text.includes('log') || text.includes('in') || text.includes('sign') || text.includes('submit')) {
                    if (buttons[i].offsetParent !== null) {
                        return buttons[i];
                    }
                }
            }
            return null;
            """
            element = self.driver.execute_script(js_script)
            if element:
                print(f"   ✅ Found login button via JavaScript")
                return element
        except:
            pass
        
        print("   ❌ No login button found")
        print(f"   📄 Page title: {self.driver.title}")
        print(f"   🌐 URL: {self.driver.current_url}")
        return None

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(3)
            self.screenshot("01_login_page")
            self.save_html("login_page")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Find phone field
            phone_field = None
            phone_selectors = [
                "//input[@placeholder='Please enter your phone number']",
                "//input[@type='text' and contains(@placeholder, 'phone')]",
                "//input[contains(@class, 'phone')]",
                "//input[contains(@name, 'phone')]"
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
                self.save_html("phone_field_not_found")
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
                "//input[contains(@name, 'password')]"
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
                self.save_html("password_field_not_found")
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
                # Check for error
                error_patterns = ["invalid", "error", "failed", "incorrect", "wrong"]
                for pattern in error_patterns:
                    if pattern in page_source:
                        print(f"   ❌ Login failed: {pattern} error")
                        return False
                
                print("   ❌ Login failed - unknown reason")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            self.save_html("login_error")
            return False

    def select_withdrawal_method(self, bank_name="OPAY"):
        """Select withdrawal method and choose OPAY"""
        print(f"\n   🔘 STEP 1: Selecting withdrawal method...")
        
        time.sleep(2)
        
        # Try to find and click withdrawal method field
        method_found = False
        
        # Look for "Withdrawal method" text
        try:
            method_label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
            print(f"   ✅ Found 'Withdrawal method' label")
            
            # Try clicking the parent or nearby element
            parent = method_label.find_element(By.XPATH, "..")
            clickable = parent.find_elements(By.XPATH, ".//div[contains(@class, 'select')]")
            if clickable:
                self.click_element(clickable[0])
                method_found = True
                time.sleep(1.5)
        except:
            pass
        
        # Look for "Select withdrawal method" text
        if not method_found:
            try:
                element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
                self.click_element(element)
                method_found = True
                time.sleep(1.5)
            except:
                pass
        
        # Try by class
        if not method_found:
            selectors = [
                "//div[contains(@class, 'withdrawal-method')]",
                "//div[contains(@class, 'dropdown')]",
                "//div[contains(@class, 'select')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            self.click_element(elem)
                            method_found = True
                            time.sleep(1.5)
                            break
                    if method_found:
                        break
                except:
                    continue
        
        if not method_found:
            print("   ❌ Could not find withdrawal method field")
            return False
        
        self.screenshot("after_method_click")
        
        # Select OPAY
        print(f"   🔘 Looking for {bank_name}...")
        time.sleep(1)
        
        opay_found = False
        opay_selectors = [
            f"//*[contains(text(), '{bank_name}')]",
            f"//*[contains(text(), '{bank_name.upper()}')]",
            "//li[contains(text(), 'OPAY')]",
            "//div[contains(text(), 'OPAY')]",
            "//span[contains(text(), 'OPAY')]"
        ]
        
        for selector in opay_selectors:
            try:
                opay_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if opay_element.is_displayed():
                    self.click_element(opay_element)
                    opay_found = True
                    print(f"   ✅ Selected {bank_name}")
                    self.screenshot("opay_selected")
                    time.sleep(1)
                    break
            except:
                continue
        
        if not opay_found:
            print(f"   ❌ Could not find {bank_name}")
            return False
        
        return True

    def select_withdrawal_amount(self, amount):
        """Select withdrawal amount preset"""
        print(f"\n   💰 STEP 2: Selecting amount: {amount}")
        
        time.sleep(1)
        amount_found = False
        
        # Try to find amount button
        try:
            amount_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{amount}')]"))
            )
            if amount_btn:
                self.click_element(amount_btn)
                amount_found = True
                print(f"   ✅ Clicked amount: {amount}")
                time.sleep(1)
        except:
            pass
        
        # Try by text
        if not amount_found:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{amount}')]")
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        self.click_element(elem)
                        amount_found = True
                        print(f"   ✅ Clicked amount: {amount}")
                        time.sleep(1)
                        break
            except:
                pass
        
        if not amount_found:
            print(f"   ❌ Could not find amount button: {amount}")
            return False
        
        self.screenshot("amount_selected")
        return True

    def enter_fund_password(self, fund_password):
        """Enter fund password"""
        print(f"\n   🔑 STEP 3: Entering fund password...")
        
        password_field = None
        
        # Try to find password field
        try:
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please input fund password']"))
            )
            print("   ✅ Found fund password field")
        except:
            pass
        
        if not password_field:
            try:
                password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                print("   ✅ Found password field by type")
            except:
                pass
        
        if not password_field:
            try:
                password_field = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'fund')]")
                print("   ✅ Found password field by placeholder")
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
        
        submit_found = False
        
        # Try to find Submit button
        try:
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit']"))
            )
            if submit_btn:
                self.click_element(submit_btn)
                submit_found = True
                print("   ✅ Clicked Submit")
                time.sleep(2)
        except:
            pass
        
        if not submit_found:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                self.click_element(submit_btn)
                submit_found = True
                print("   ✅ Clicked Submit (contains text)")
                time.sleep(2)
            except:
                pass
        
        if not submit_found:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'submit')]")
                self.click_element(submit_btn)
                submit_found = True
                print("   ✅ Clicked Submit (by class)")
                time.sleep(2)
            except:
                pass
        
        if not submit_found:
            print("   ❌ Could not find Submit button")
            return False
        
        self.screenshot("submit_clicked")
        return True

    def perform_withdrawal(self, login_data):
        """Complete withdrawal process"""
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
        
        # Confirm
        if self.safety.config.get("require_confirmation", True):
            print(f"\n   ⚠️  WITHDRAWAL CONFIRMATION")
            print(f"   Account: {phone}")
            print(f"   Amount: ${withdrawal_amount}")
            print(f"   Bank: {bank_name}")
            
            response = input("   Confirm? (yes/no): ").strip().lower()
            if response != 'yes':
                print("   ❌ Cancelled")
                self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
                return False

        # Execute withdrawal steps
        if not self.select_withdrawal_method(bank_name):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select bank")
            return False

        if not self.select_withdrawal_amount(withdrawal_amount):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select amount")
            return False

        if not self.enter_fund_password(fund_password):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not enter password")
            return False

        if not self.click_submit_button():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Submit failed")
            return False

        print(f"\n   ✅ Withdrawal submitted!")
        self.safety.log_withdrawal(phone, withdrawal_amount, "success", "Withdrawal submitted")
        
        time.sleep(3)
        self.screenshot("withdrawal_complete")
        return True

    def run(self):