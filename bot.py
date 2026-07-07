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
            "enable_safety_limits": True,
            "auto_stop_on_failure": True,
            "max_retries_per_account": 3
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
        self.withdrawal_amounts = [1800, 3000, 8000, 25000, 70000, 200000, 500000, 1000000, 3000000, 100000000, 1000000000]
        self.amount_to_withdraw = 1800  # Default

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # Uncomment for debugging (shows browser)
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

    def click_element(self, element):
        """Click element using multiple methods"""
        try:
            # Method 1: JavaScript click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
            time.sleep(0.5)
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
                    return False

    def type_text(self, element, text):
        """Type text with proper clearing"""
        try:
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            
            # Click and clear
            element.click()
            time.sleep(0.2)
            element.clear()
            time.sleep(0.2)
            
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

    # ============================================
    # LOGIN
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(3)
            self.screenshot("01_login_page")

            # Wait for phone field
            phone_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")

            # Password field
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
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
                print("   ❌ Login failed - check credentials")
                self.screenshot("login_failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            self.screenshot("login_error")
            return False

    def find_login_button(self):
        """Find login button with multiple selectors"""
        print("   🔍 Looking for login button...")
        
        login_selectors = [
            "//button[contains(text(), 'Log in now')]",
            "//button[contains(text(), 'Log in')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'login')]",
            "//button[contains(@class, 'submit')]",
            "//button[contains(text(), 'Sign in')]"
        ]
        
        for selector in login_selectors:
            try:
                btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if btn.is_displayed():
                    print(f"   ✅ Found login button")
                    return btn
            except:
                continue
        
        # Fallback: find any visible button
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.text.strip().lower() in ['log in', 'login', 'sign in', 'submit']:
                    print(f"   ✅ Found button: '{btn.text}'")
                    return btn
        except:
            pass
        
        return None

    # ============================================
    # WITHDRAWAL PAGE INTERACTIONS
    # ============================================

    def select_withdrawal_method(self, bank_name="OPAY"):
        """
        Click the withdrawal method dropdown and select bank
        Based on screenshot: "Withdrawal method - Select withdrawal method"
        """
        print(f"\n   🔘 STEP 1: Selecting withdrawal method...")
        
        # First, wait for the page to fully load
        time.sleep(2)
        
        # Try multiple approaches to find and click the withdrawal method field
        method_found = False
        
        # Approach 1: Find by text "Withdrawal method"
        try:
            # Find the parent element containing "Withdrawal method"
            method_label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
            print(f"   ✅ Found 'Withdrawal method' label")
            
            # Try to find the clickable element near it
            parent = method_label.find_element(By.XPATH, "..")
            
            # Look for clickable elements in parent
            clickable = parent.find_elements(By.XPATH, ".//div[contains(@class, 'select')]")
            if clickable:
                self.click_element(clickable[0])
                method_found = True
                print("   ✅ Clicked withdrawal method field")
                time.sleep(1.5)
            else:
                # Try clicking the label itself
                self.click_element(method_label)
                method_found = True
                print("   ✅ Clicked withdrawal method label")
                time.sleep(1.5)
        except:
            pass
        
        # Approach 2: Find by placeholder text "Select withdrawal method"
        if not method_found:
            try:
                element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
                self.click_element(element)
                method_found = True
                print("   ✅ Clicked 'Select withdrawal method'")
                time.sleep(1.5)
            except:
                pass
        
        # Approach 3: Find by class selectors
        if not method_found:
            selectors = [
                "//div[contains(@class, 'withdrawal-method')]",
                "//div[contains(@class, 'method-select')]",
                "//div[contains(@class, 'dropdown')]",
                "//div[contains(@class, 'select')]",
                "//div[contains(@class, 'picker')]"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            self.click_element(elem)
                            method_found = True
                            print(f"   ✅ Clicked element: {selector}")
                            time.sleep(1.5)
                            break
                    if method_found:
                        break
                except:
                    continue
        
        # Approach 4: Try to find input or clickable div with specific attributes
        if not method_found:
            try:
                # Look for any element that might be the dropdown
                elements = self.driver.find_elements(By.XPATH, "//*[@placeholder='Select withdrawal method' or contains(@class, 'ant-select')]")
                for elem in elements:
                    if elem.is_displayed():
                        self.click_element(elem)
                        method_found = True
                        print("   ✅ Clicked dropdown by placeholder")
                        time.sleep(1.5)
                        break
            except:
                pass
        
        if not method_found:
            print("   ❌ Could not find withdrawal method field")
            self.screenshot("method_not_found")
            return False
        
        # Take screenshot after clicking
        self.screenshot("after_method_click")
        
        # Now find and select OPAY from the dropdown
        print(f"   🔘 Looking for {bank_name} in dropdown...")
        time.sleep(1)
        
        opay_found = False
        
        # Try to find OPAY in the dropdown
        opay_selectors = [
            f"//*[contains(text(), '{bank_name}')]",
            f"//*[contains(text(), '{bank_name.upper()}')]",
            "//li[contains(text(), 'OPAY')]",
            "//div[contains(text(), 'OPAY')]",
            "//span[contains(text(), 'OPAY')]",
            "//*[contains(@class, 'option') and contains(text(), 'OPAY')]",
            "//*[contains(@class, 'item') and contains(text(), 'OPAY')]"
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
            print(f"   ❌ Could not find {bank_name} in dropdown")
            self.screenshot("opay_not_found")
            return False
        
        return True

    def select_withdrawal_amount(self, amount):
        """
        Click a preset withdrawal amount button
        Based on screenshot: Amount buttons (1800, 3000, 8000, etc.)
        """
        print(f"\n   💰 STEP 2: Selecting amount: {amount}")
        
        # Wait for amount buttons to be visible
        time.sleep(1)
        
        amount_found = False
        
        # Try to find amount by exact text
        try:
            amount_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{amount}')]"))
            )
            if amount_btn:
                self.click_element(amount_btn)
                amount_found = True
                print(f"   ✅ Clicked amount: {amount}")
                self.screenshot("amount_selected")
                time.sleep(1)
        except:
            pass
        
        # Try to find by span or div containing the number
        if not amount_found:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{amount}')]")
                for elem in elements:
                    # Check if it's likely a button/clickable element
                    if elem.is_displayed() and elem.is_enabled():
                        self.click_element(elem)
                        amount_found = True
                        print(f"   ✅ Clicked amount: {amount}")
                        self.screenshot("amount_selected")
                        time.sleep(1)
                        break
            except:
                pass
        
        # Try to find by class
        if not amount_found:
            try:
                amount_btns = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'amount')]")
                for btn in amount_btns:
                    text = btn.text.strip()
                    # Remove commas and parse
                    cleaned = text.replace(',', '')
                    if cleaned.isdigit() and int(cleaned) == amount:
                        self.click_element(btn)
                        amount_found = True
                        print(f"   ✅ Clicked amount: {amount}")
                        self.screenshot("amount_selected")
                        time.sleep(1)
                        break
            except:
                pass
        
        if not amount_found:
            print(f"   ❌ Could not find amount button: {amount}")
            self.screenshot("amount_not_found")
            return False
        
        return True

    def enter_fund_password(self, fund_password):
        """
        Enter the fund password in the password field
        Based on screenshot: "Fund password - Please input fund password"
        """
        print(f"\n   🔑 STEP 3: Entering fund password...")
        
        password_field = None
        
        # Try to find password field by placeholder
        try:
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please input fund password']"))
            )
            print("   ✅ Found fund password field by placeholder")
        except:
            pass
        
        # Try by type password
        if not password_field:
            try:
                password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                print("   ✅ Found fund password field by type")
            except:
                pass
        
        # Try by containing "fund" in placeholder
        if not password_field:
            try:
                password_field = self.driver.find_element(By.XPATH, "//input[contains(@placeholder, 'fund')]")
                print("   ✅ Found fund password field by placeholder contains 'fund'")
            except:
                pass
        
        # Try by class
        if not password_field:
            try:
                password_field = self.driver.find_element(By.XPATH, "//input[contains(@class, 'fund')]")
                print("   ✅ Found fund password field by class")
            except:
                pass
        
        if not password_field:
            print("   ❌ Could not find fund password field")
            self.screenshot("password_field_not_found")
            return False
        
        # Type the password
        if self.type_text(password_field, fund_password):
            print(f"   ✅ Fund password entered")
            self.screenshot("password_entered")
            return True
        else:
            print("   ❌ Failed to enter fund password")
            return False

    def click_submit_button(self):
        """
        Click the Submit button
        Based on screenshot: "Submit" button at bottom
        """
        print(f"\n   📤 STEP 4: Clicking Submit...")
        
        submit_found = False
        
        # Try to find by exact text
        try:
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Submit']"))
            )
            if submit_btn:
                self.click_element(submit_btn)
                submit_found = True
                print("   ✅ Clicked Submit")
                self.screenshot("submit_clicked")
                time.sleep(2)
        except:
            pass
        
        # Try to find by containing text
        if not submit_found:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                self.click_element(submit_btn)
                submit_found = True
                print("   ✅ Clicked Submit (contains text)")
                self.screenshot("submit_clicked")
                time.sleep(2)
            except:
                pass
        
        # Try to find by class
        if not submit_found:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'submit')]")
                self.click_element(submit_btn)
                submit_found = True
                print("   ✅ Clicked Submit (by class)")
                self.screenshot("submit_clicked")
                time.sleep(2)
            except:
                pass
        
        # Try to find any green button
        if not submit_found:
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.is_displayed():
                        # Check if button has green color or is at bottom
                        color = btn.value_of_css_property("background-color")
                        if color and "rgb(0, 128, 0)" in color or "rgb(34, 139, 34)" in color:
                            self.click_element(btn)
                            submit_found = True
                            print("   ✅ Clicked Submit (green button)")
                            self.screenshot("submit_clicked")
                            time.sleep(2)
                            break
            except:
                pass
        
        if not submit_found:
            print("   ❌ Could not find Submit button")
            self.screenshot("submit_not_found")
            return False
        
        return True

    def get_balance_from_page(self):
        """Extract balance from the page"""
        try:
            # Look for "Balance: 630" pattern
            page_text = self.driver.page_source
            balance_match = re.search(r'Balance:\s*([\d,]+\.?\d*)', page_text)
            if balance_match:
                balance = float(balance_match.group(1).replace(',', ''))
                print(f"   💰 Current balance: ${balance:.2f}")
                return balance
        except:
            pass
        return None

    # ============================================
    # MAIN WITHDRAWAL PROCESS
    # ============================================

    def perform_withdrawal(self, login_data):
        """
        Complete the withdrawal process with proper steps
        Based on screenshot UI:
        1. Click "Withdrawal method" -> Select OPAY
        2. Enter "Fund password"
        3. Click Submit
        """
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
            self.screenshot("withdrawal_page_loaded")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        # Get current balance
        balance = self.get_balance_from_page()
        
        # Determine withdrawal amount (use smallest that fits balance)
        withdrawal_amount = 1800  # Default to smallest
        
        if balance:
            # Check which amount fits with fee
            fee_percentage = 0.10  # 10% fee
            for amount in self.withdrawal_amounts:
                total_needed = amount * (1 + fee_percentage)
                if balance >= total_needed:
                    withdrawal_amount = amount
                    break
                else:
                    # Try next smaller amount
                    continue
            print(f"   📊 Using withdrawal amount: ${withdrawal_amount}")
        
        # Safety check
        safety_check = self.safety.can_withdraw(withdrawal_amount, phone)
        if not safety_check["allowed"]:
            print(f"   ⚠️ Withdrawal blocked: {safety_check['reason']}")
            self.safety.log_withdrawal(phone, withdrawal_amount, "blocked", safety_check['reason'])
            return False
        
        # User confirmation (if enabled)
        if self.safety.config.get("require_confirmation", True):
            print(f"\n   ⚠️  WITHDRAWAL CONFIRMATION")
            print(f"   Account: {phone}")
            print(f"   Amount: ${withdrawal_amount}")
            print(f"   Bank: {bank_name}")
            print(f"   Balance: ${balance if balance else 'Unknown'}")
            print(f"   Fund Password: {fund_password}")
            
            response = input("   Confirm withdrawal? (yes/no): ").strip().lower()
            if response != 'yes':
                print("   ❌ Withdrawal cancelled")
                self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
                return False

        # STEP 1: Select withdrawal method
        if not self.select_withdrawal_method(bank_name):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select bank")
            return False

        # STEP 2: Select amount
        if not self.select_withdrawal_amount(withdrawal_amount):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select amount")
            return False

        # STEP 3: Enter fund password
        if not self.enter_fund_password(fund_password):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not enter fund password")
            return False

        # STEP 4: Click Submit
        if not self.click_submit_button():
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Submit button failed")
            return False

        # Success!
        print(f"\n   ✅ Withdrawal submitted successfully!")
        print(f"   💰 Amount: ${withdrawal_amount}")
        print(f"   🏦 Bank: {bank_name}")
        print(f"   📱 Account: {phone}")
        
        self.safety.log_withdrawal(phone, withdrawal_amount, "success", "Withdrawal submitted")
        
        # Wait for result
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

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = WithdrawalBot(bot_id=bot_id)
    bot.run()