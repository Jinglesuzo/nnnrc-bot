from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
        
        # Track withdrawal amounts
        self.withdrawal_amounts = [1800, 3000, 8000, 25000, 70000, 200000, 500000, 1000000, 3000000]
        self.amount_to_withdraw = 1800  # Default to smallest amount

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

    def click_element(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                element.click()
                return True
            except:
                return False

    def type_text(self, element, text):
        try:
            element.click()
            time.sleep(0.1)
            element.clear()
            time.sleep(0.1)
        except:
            try:
                self.driver.execute_script("arguments[0].value = '';", element)
            except:
                pass
        
        for char in text:
            element.send_keys(char)
            time.sleep(0.05)
        time.sleep(0.1)

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
            time.sleep(2)
            self.screenshot("01_login_page")

            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")

            password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter login password']")
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
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            print("   ✅ Found 'Log in now'")
            return btn
        except:
            pass
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            print("   ✅ Found submit button")
            return btn
        except:
            pass
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    text = btn.text.lower()
                    if 'log' in text or 'in' in text or 'submit' in text:
                        print(f"   ✅ Found button: '{btn.text}'")
                        return btn
        except:
            pass
        print("   ❌ No login button found")
        return None

    # ============================================
    # GET BALANCE FROM WITHDRAWAL PAGE
    # ============================================

    def get_balance_from_page(self):
        """Extract balance from the withdrawal page"""
        try:
            # Look for "Balance: X" text pattern
            page_text = self.driver.page_source
            balance_match = re.search(r'Balance:\s*([\d,]+\.?\d*)', page_text)
            if balance_match:
                balance = float(balance_match.group(1).replace(',', ''))
                print(f"   💰 Balance: ${balance:.2f}")
                return balance
        except:
            pass
        
        # Alternative: look for span/div with balance class
        try:
            balance_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Balance:')]")
            text = balance_element.text
            balance_match = re.search(r'[\d,]+\.?\d*', text)
            if balance_match:
                balance = float(balance_match.group().replace(',', ''))
                print(f"   💰 Balance: ${balance:.2f}")
                return balance
        except:
            pass
        
        return None

    # ============================================
    # WITHDRAWAL - SPECIFIC TO YOUR UI
    # ============================================

    def select_withdrawal_method(self, bank_name="OPAY"):
        """
        Click the withdrawal method dropdown and select OPAY
        Based on your screenshot: "Withdrawal method" field
        """
        print(f"   🔘 Selecting withdrawal method...")
        
        # Step 1: Find and click the withdrawal method field
        method_selectors = [
            "//*[contains(text(), 'Withdrawal method')]",
            "//*[contains(text(), 'Withdrawal')]",
            "//div[contains(@class, 'withdrawal-method')]",
            "//div[contains(text(), 'Select withdrawal method')]",
            "//div[contains(@class, 'select')]"
        ]
        
        method_field = None
        for selector in method_selectors:
            try:
                method_field = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if method_field:
                    print(f"   ✅ Found method field")
                    break
            except:
                continue
        
        if method_field:
            self.click_element(method_field)
            time.sleep(1.5)
            self.screenshot("method_dropdown_clicked")
            print("   ✅ Clicked withdrawal method dropdown")
        else:
            print("   ❌ Could not find withdrawal method field")
            return False

        # Step 2: Select OPAY from dropdown
        print(f"   🔘 Looking for {bank_name} option...")
        bank_selectors = [
            f"//*[contains(text(), '{bank_name}')]",
            f"//*[contains(text(), '{bank_name.upper()}')]",
            "//li[contains(text(), 'OPAY')]",
            "//div[contains(text(), 'OPAY')]",
            "//span[contains(text(), 'OPAY')]",
            "//*[contains(@class, 'option') and contains(text(), 'OPAY')]"
        ]
        
        for selector in bank_selectors:
            try:
                bank_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if bank_element:
                    self.click_element(bank_element)
                    print(f"   ✅ Selected {bank_name}")
                    time.sleep(1)
                    self.screenshot("bank_selected")
                    return True
            except:
                continue
        
        print(f"   ❌ Could not select {bank_name}")
        return False

    def select_withdrawal_amount(self, amount):
        """
        Click a preset amount button from the grid
        Based on your screenshot: 1800, 3000, 8000, etc.
        """
        print(f"   💰 Selecting withdrawal amount: {amount}")
        
        # Try to find the amount button by exact text
        try:
            amount_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[text()='{amount}']"))
            )
            self.click_element(amount_btn)
            print(f"   ✅ Clicked amount: {amount}")
            self.screenshot("amount_selected")
            return True
        except:
            pass
        
        # Try to find by contains text
        try:
            amount_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{amount}')]"))
            )
            self.click_element(amount_btn)
            print(f"   ✅ Clicked amount: {amount}")
            self.screenshot("amount_selected")
            return True
        except:
            pass
        
        # Try to find in a grid/button container
        try:
            # Look for any button/div that contains the amount
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{amount}')]")
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    self.click_element(elem)
                    print(f"   ✅ Clicked amount: {amount}")
                    self.screenshot("amount_selected")
                    return True
        except:
            pass
        
        print(f"   ❌ Could not find amount button: {amount}")
        return False

    def get_fund_password_field(self):
        """
        Find the fund password input field
        Based on your screenshot: "Fund password" field
        """
        print("   🔘 Looking for fund password field...")
        
        fund_selectors = [
            "//input[@placeholder='Please input fund password']",
            "//input[@placeholder='Fund password']",
            "//input[contains(@placeholder, 'fund')]",
            "//input[@type='password' and contains(@placeholder, 'fund')]",
            "//input[contains(@class, 'fund')]",
            "//input[contains(@name, 'fund')]",
            "//input[@type='password']"
        ]
        
        for selector in fund_selectors:
            try:
                fund_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if fund_field and fund_field.is_displayed():
                    print("   ✅ Found fund password field")
                    return fund_field
            except:
                continue
        
        print("   ❌ Could not find fund password field")
        return None

    def click_submit_button(self):
        """
        Click the green Submit button
        Based on your screenshot: Green "Submit" button at bottom
        """
        print("   🔘 Clicking Submit button...")
        
        submit_selectors = [
            "//button[text()='Submit']",
            "//button[contains(text(), 'Submit')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'green')]",
            "//button[contains(@style, 'green')]",
            "//div[contains(@class, 'submit')]/button",
            "//*[contains(@class, 'btn-submit')]",
            "//button[contains(@class, 'primary')]",
            "//button[@color='green']"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                    time.sleep(0.5)
                    self.click_element(submit_btn)
                    print("   ✅ Clicked Submit")
                    time.sleep(2)
                    self.screenshot("submit_clicked")
                    return True
            except:
                continue
        
        # JavaScript fallback
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[text()='Submit']")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", submit_btn)
            print("   ✅ Clicked Submit (JavaScript)")
            time.sleep(2)
            self.screenshot("submit_clicked")
            return True
        except:
            pass
        
        print("   ❌ Could not find Submit button")
        return False

    def perform_withdrawal(self, login_data):
        """
        Complete withdrawal process based on your screenshot:
        1. Select withdrawal method (OPAY)
        2. Select withdrawal amount (preset amount)
        3. Enter fund password
        4. Click Submit
        """
        phone = login_data['phone']
        bank_name = login_data['bank_name']
        fund_password = login_data['fund_password']
        
        print(f"\n💸 Processing withdrawal for {phone}")
        
        # Go to withdrawal page
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(4)
            self.screenshot("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        # Get current balance
        balance = self.get_balance_from_page()
        
        # Determine withdrawal amount based on balance
        withdrawal_amount = self.amount_to_withdraw
        
        # Check if balance can cover the withdrawal
        if balance:
            # Calculate fee (taxation) - appears to be 10% based on your screenshot
            # 1800 withdrawal with 180 tax = 10%
            fee_percentage = 0.10
            total_needed = withdrawal_amount * (1 + fee_percentage)
            
            if balance < total_needed:
                print(f"   ⚠️ Insufficient balance: ${balance:.2f} < ${total_needed:.2f} (amount + fee)")
                # Try the next smaller amount
                for amount in self.withdrawal_amounts:
                    if amount < withdrawal_amount:
                        total_needed = amount * (1 + fee_percentage)
                        if balance >= total_needed:
                            withdrawal_amount = amount
                            print(f"   📊 Adjusted withdrawal to: ${withdrawal_amount:.2f}")
                            break
        
        # Safety check
        safety_check = self.safety.can_withdraw(withdrawal_amount, phone)
        if not safety_check["allowed"]:
            print(f"   ⚠️ Withdrawal blocked: {safety_check['reason']}")
            self.safety.log_withdrawal(phone, withdrawal_amount, "blocked", safety_check['reason'])
            return False
        
        # User confirmation
        if self.safety.config.get("require_confirmation", True):
            print(f"\n   ⚠️  WITHDRAWAL CONFIRMATION")
            print(f"   Account: {phone}")
            print(f"   Amount: ${withdrawal_amount:.2f}")
            print(f"   Bank: {bank_name}")
            print(f"   Balance: ${balance if balance else 'Unknown'}")
            
            response = input("   Confirm withdrawal? (yes/no): ").strip().lower()
            if response != 'yes':
                print("   ❌ Withdrawal cancelled")
                self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
                return False

        # Step 1: Select withdrawal method
        if not self.select_withdrawal_method(bank_name):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select bank")
            return False

        # Step 2: Select withdrawal amount
        if not self.select_withdrawal_amount(withdrawal_amount):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select amount")
            return False

        # Step 3: Enter fund password
        fund_field = self.get_fund_password_field()
        if fund_field:
            self.type_text(fund_field, fund_password)
            print(f"   🔑 Entered fund password")
            self.screenshot("fund_password_entered")
        else:
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not find fund password field")
            return False

        # Step 4: Click Submit
        if self.click_submit_button():
            print("   ✅ Withdrawal submitted!")
            self.safety.log_withdrawal(phone, withdrawal_amount, "success", "Withdrawal submitted")
            return True
        else:
            print("   ❌ Could not submit withdrawal")
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Submit button failed")
            return False

    # ============================================
    # RUN
    # ============================================

    def run(self):
        print("="*50)
        print(f"🤖 WITHDRAWAL BOT {self.bot_id} STARTING")
        print("="*50)
        
        # Show daily summary
        summary = self.safety.get_daily_summary()
        print(f"\n📊 DAILY SUMMARY")
        print(f"   Withdrawn today: ${summary['withdrawn_today']:.2f}")
        print(f"   Daily limit: ${summary['daily_limit']:.2f}")
        print(f"   Remaining: ${summary['remaining']:.2f}")
        print("="*50)

        failed_accounts = []
        
        for login_data in self.logins:
            phone = login_data['phone']
            password = login_data['password']

            print(f"\n📱 Account: {phone}")

            if not self.login(phone, password):
                print(f"   ❌ Login failed for {phone}")
                failed_accounts.append(phone)
                continue

            success = self.perform_withdrawal(login_data)
            
            if not success:
                failed_accounts.append(phone)
                
            # Delay between accounts
            time.sleep(3)

        # Final summary
        print("\n" + "="*50)
        print(f"📊 FINAL SUMMARY")
        print(f"   Total accounts: {len(self.logins)}")
        print(f"   Successful: {len(self.logins) - len(failed_accounts)}")
        print(f"   Failed: {len(failed_accounts)}")
        
        summary = self.safety.get_daily_summary()
        print(f"   Total withdrawn today: ${summary['withdrawn_today']:.2f}")
        print("="*50)

        self.driver.quit()
        print(f"\n✅ Withdrawal Bot {self.bot_id} Done!")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = WithdrawalBot(bot_id=bot_id)
    bot.run()