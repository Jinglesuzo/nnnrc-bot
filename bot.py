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
# WITHDRAWAL BOT - BASED ON SCREENSHOTS
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
        # Uncomment to see browser
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
    # LOGIN - FIXED
    # ============================================

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
                "//input[@type='tel']",
                "//input[contains(@class, 'phone')]",
                "//input[contains(@name, 'phone')]",
                "//input[@id='phone']"
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
                "//input[contains(@class, 'password')]",
                "//input[contains(@name, 'password')]",
                "//input[@id='password']"
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

            # Find login button - FIXED with better detection
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print("   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print("   ❌ Login button not found")
                self.save_html("login_button_not_found")
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

    def find_login_button(self):
        """Find login button - multiple strategies"""
        print("   🔍 Looking for login button...")
        
        time.sleep(1)
        
        # Strategy 1: Look for any button with login-related text
        login_texts = [
            "Log in now", "Log in", "Login", "Sign in", 
            "Sign In", "log in", "login", "Sign in now",
            "Log In", "LOGIN", "SIGN IN", "Log In Now"
        ]
        
        for text in login_texts:
            try:
                # Try exact match on button
                btn = self.driver.find_element(By.XPATH, f"//button[normalize-space()='{text}']")
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found login button: '{text}'")
                    return btn
            except:
                pass
            
            try:
                # Try contains on any element
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        tag = elem.tag_name.lower()
                        if tag == 'button' or tag == 'a' or elem.get_attribute('role') == 'button':
                            print(f"   ✅ Found login button: '{text}'")
                            return elem
            except:
                pass
        
        # Strategy 2: Look for input type submit
        try:
            btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
            if btn.is_displayed() and btn.is_enabled():
                print("   ✅ Found submit input")
                return btn
        except:
            pass
        
        # Strategy 3: Look for button by class
        class_selectors = [
            "//button[contains(@class, 'login')]",
            "//button[contains(@class, 'btn-login')]",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'primary')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'ant-btn')]",
            "//a[contains(@class, 'login')]"
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
        
        # Strategy 4: Find any visible button on the page
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            print(f"   🔍 Found {len(buttons)} buttons on page")
            for btn in buttons:
                text = btn.text.strip()
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   Button text: '{text}'")
                    # If it's the only visible button, or has login text
                    if text and any(word in text.lower() for word in ['log', 'in', 'sign', 'submit']):
                        print(f"   ✅ Found login button: '{text}'")
                        return btn
        except:
            pass
        
        # Strategy 5: JavaScript to find any clickable login element
        try:
            js_script = """
            var elements = document.querySelectorAll('button, a, div[role="button"]');
            for (var i = 0; i < elements.length; i++) {
                var text = elements[i].textContent.toLowerCase();
                if (text.includes('log in') || text.includes('login') || text.includes('sign in')) {
                    if (elements[i].offsetParent !== null) {
                        return elements[i];
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
        return None

    # ============================================
    # WITHDRAWAL - BASED ON SCREENSHOT
    # ============================================

    def click_withdrawal_method(self):
        """Click the 'Withdrawal method' field based on screenshot"""
        print("   🔘 Clicking 'Withdrawal method'...")
        
        # The screenshot shows: "Withdrawal method" as a label and "Select withdrawal method" as placeholder
        
        # Method 1: Click on "Select withdrawal method" text
        try:
            element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
            if element.is_displayed():
                self.click_element(element)
                print("   ✅ Clicked 'Select withdrawal method'")
                time.sleep(1)
                return True
        except:
            pass
        
        # Method 2: Click on "Withdrawal method" label or its container
        try:
            label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
            print("   ✅ Found 'Withdrawal method' label")
            
            # Try to find clickable container
            parent = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'form') or contains(@class, 'item')]")
            if parent:
                # Look for clickable divs in parent
                clickable = parent.find_elements(By.XPATH, ".//div[contains(@class, 'select') or contains(@class, 'dropdown')]")
                if clickable:
                    self.click_element(clickable[0])
                    print("   ✅ Clicked dropdown container")
                    time.sleep(1)
                    return True
                
                # Click any div in parent
                divs = parent.find_elements(By.TAG_NAME, "div")
                for div in divs:
                    if div.is_displayed() and div != label and div.text.strip() == "":
                        self.click_element(div)
                        print("   ✅ Clicked container div")
                        time.sleep(1)
                        return True
        except:
            pass
        
        # Method 3: Find by class
        try:
            elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'ant-select-selector') or contains(@class, 'select-container')]")
            for elem in elements:
                if elem.is_displayed():
                    self.click_element(elem)
                    print("   ✅ Clicked by class")
                    time.sleep(1)
                    return True
        except:
            pass
        
        print("   ❌ Could not click withdrawal method")
        return False

    def select_opay(self):
        """Select OPAY from dropdown"""
        print("   🔘 Selecting OPAY...")
        
        # Wait for dropdown to appear
        time.sleep(1)
        
        # Method 1: Find by text
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
        
        # Method 2: Find list items
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
        """Click withdrawal amount button based on screenshot"""
        print(f"   💰 Clicking amount: {amount}")
        
        # The screenshot shows amounts as clickable boxes/buttons
        # Method 1: Find by exact number
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[normalize-space()='{amount}']")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    self.click_element(elem)
                    print(f"   ✅ Clicked {amount}")
                    return True
        except:
            pass
        
        # Method 2: Find by contains
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{amount}')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    # Make sure it's not a partial match
                    if elem.text.strip() == str(amount):
                        self.click_element(elem)
                        print(f"   ✅ Clicked {amount}")
                        return True
        except:
            pass
        
        # Method 3: Find buttons/clickable divs with the number
        try:
            elements = self.driver.find_elements(By.XPATH, "//button | //div[@role='button'] | //div[contains(@class, 'amount')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    try:
                        text = elem.text.replace(',', '').strip()
                        if text.isdigit() and int(text) == amount:
                            self.click_element(elem)
                            print(f"   ✅ Clicked {amount}")
                            return True
                    except:
                        continue
        except:
            pass
        
        print(f"   ❌ Could not click amount {amount}")
        return False

    def enter_fund_password(self, password):
        """Enter fund password based on screenshot"""
        print("   🔑 Entering fund password...")
        
        # The screenshot shows: "Fund password" label and "Please input fund password" placeholder
        
        # Method 1: Find by placeholder
        try:
            field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please input fund password']")
            if field.is_displayed():
                self.type_text(field, password)
                print("   ✅ Fund password entered")
                self.screenshot("fund_password_entered")
                return True
        except:
            pass
        
        # Method 2: Find by type password
        try:
            fields = self.driver.find_elements(By.XPATH, "//input[@type='password']")
            for field in fields:
                if field.is_displayed():
                    # Check if it's the fund password (usually the last one or near "Fund password" label)
                    self.type_text(field, password)
                    print("   ✅ Fund password entered")
                    self.screenshot("fund_password_entered")
                    return True
        except:
            pass
        
        # Method 3: Find by label
        try:
            label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Fund password')]")
            parent = label.find_element(By.XPATH, "./ancestor::div[contains(@class, 'form') or contains(@class, 'item')]")
            if parent:
                inputs = parent.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.is_displayed():
                        self.type_text(inp, password)
                        print("   ✅ Fund password entered")
                        self.screenshot("fund_password_entered")
                        return True
        except:
            pass
        
        print("   ❌ Could not find fund password field")
        return False

    def click_submit_button(self):
        """Click Submit button based on screenshot"""
        print("   📤 Clicking Submit...")
        
        # The screenshot shows a green "Submit" button at the bottom
        
        # Method 1: Find by text
        try:
            btn = self.driver.find_element(By.XPATH, "//button[text()='Submit']")
            if btn.is_displayed() and btn.is_enabled():
                self.click_element(btn)
                print("   ✅ Clicked Submit")
                return True
        except:
            pass
        
        # Method 2: Find by contains text
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
        
        # Method 3: Find by class
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'submit') or contains(@class, 'primary') or contains(@class, 'green')]")
            if btn.is_displayed() and btn.is_enabled():
                self.click_element(btn)
                print("   ✅ Clicked Submit")
                return True
        except:
            pass
        
        print("   ❌ Could not find Submit button")
        return False

    def confirm_withdrawal(self, phone, amount, bank_name):
        """Handle confirmation"""
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
        """Complete withdrawal based on screenshot"""
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