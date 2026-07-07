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
import logging

# ============================================
# WITHDRAWAL MANAGER - SAFETY & LIMITS
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
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('withdrawal.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file):
        """Load or create withdrawal config"""
        default_config = {
            "max_daily_withdrawal": 5000.0,  # Maximum per day
            "max_single_withdrawal": 1000.0,  # Maximum per transaction
            "min_balance_threshold": 500.0,   # Minimum balance to keep
            "withdrawal_cooldown_seconds": 300,  # 5 minutes between withdrawals
            "require_confirmation": True,
            "enable_safety_limits": True,
            "auto_stop_on_failure": True,
            "max_retries_per_account": 3
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Merge with defaults
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
        """Load withdrawal history"""
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
        """Save withdrawal history"""
        data = {
            'date': self.today.isoformat(),
            'daily_withdrawn': self.daily_withdrawn,
            'history': self.withdrawal_history[-100:]  # Keep last 100 entries
        }
        with open('withdrawal_history.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def check_reset_daily(self):
        """Reset daily counter if new day"""
        today = date.today()
        if today > self.today:
            self.daily_withdrawn = 0
            self.today = today
            self.save_history()
            self.logger.info("🔄 Daily withdrawal counter reset")
    
    def can_withdraw(self, amount, account_phone, balance=None):
        """Check if withdrawal is allowed"""
        self.check_reset_daily()
        
        if not self.config.get("enable_safety_limits", True):
            return {"allowed": True}
        
        # Check daily limit
        if self.daily_withdrawn + amount > self.config["max_daily_withdrawal"]:
            remaining = self.config["max_daily_withdrawal"] - self.daily_withdrawn
            return {
                "allowed": False,
                "reason": f"Daily limit exceeded. Remaining: ${remaining:.2f}",
                "remaining": remaining
            }
        
        # Check single withdrawal limit
        if amount > self.config["max_single_withdrawal"]:
            return {
                "allowed": False,
                "reason": f"Amount exceeds single withdrawal limit of ${self.config['max_single_withdrawal']}",
                "max_allowed": self.config["max_single_withdrawal"]
            }
        
        # Check cooldown
        time_since_last = time.time() - self.last_withdrawal_time
        if time_since_last < self.config["withdrawal_cooldown_seconds"]:
            wait_time = self.config["withdrawal_cooldown_seconds"] - time_since_last
            return {
                "allowed": False,
                "reason": f"Cooldown active. Wait {wait_time:.0f} seconds",
                "wait_seconds": wait_time
            }
        
        # Check account-specific limits (recent failures)
        recent_failures = self.get_recent_failures(account_phone)
        if recent_failures >= self.config.get("max_retries_per_account", 3):
            return {
                "allowed": False,
                "reason": f"Too many recent failures ({recent_failures}). Pausing account",
                "failures": recent_failures
            }
        
        return {"allowed": True}
    
    def get_recent_failures(self, account_phone, hours=24):
        """Get number of recent failures for an account"""
        cutoff = time.time() - (hours * 3600)
        failures = 0
        for entry in self.withdrawal_history:
            if (entry.get('account') == account_phone and 
                entry.get('status') == 'failed' and
                entry.get('timestamp', 0) > cutoff):
                failures += 1
        return failures
    
    def log_withdrawal(self, account_phone, amount, status, details=""):
        """Log a withdrawal attempt"""
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
            self.logger.info(f"✅ Withdrawal logged: ${amount:.2f} from {account_phone}")
        else:
            self.logger.warning(f"❌ Failed withdrawal: {details}")
        
        self.save_history()
        
        # Print safety summary
        remaining = self.config["max_daily_withdrawal"] - self.daily_withdrawn
        print(f"   📊 Daily remaining: ${remaining:.2f}")
    
    def get_daily_summary(self):
        """Get daily summary"""
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
        
        # Track balance per account
        self.account_balances = {}

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
            print(f"   💾 Saved HTML: {filename}")
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
            print(f"❌ Bot {self.bot_id} Error loading logins.csv: {e}")
            self.logins = [{'phone': '08057536473', 'password': 'people56', 'real_name': 'John Penn', 'bank_name': 'OPAY', 'bank_account': '9074331299', 'fund_password': '3333'}]

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
    # ENHANCED LOGIN WITH BALANCE CHECK
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
                
                # Try to get balance
                self.get_account_balance()
                
                return True
            else:
                print("   ❌ Login failed")
                return False
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

    def get_account_balance(self):
        """Try to get current account balance"""
        try:
            # Look for balance element
            balance_selectors = [
                "//*[contains(@class, 'balance')]",
                "//*[contains(text(), 'Balance')]",
                "//*[contains(@class, 'total')]",
                "//span[contains(@class, 'amount')]",
                "//div[contains(@class, 'amount')]"
            ]
            
            for selector in balance_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    # Try to extract number
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', text)
                    if numbers:
                        balance = float(numbers[0].replace(',', ''))
                        print(f"   💰 Balance: ${balance:.2f}")
                        return balance
                except:
                    continue
        except:
            pass
        return None

    # ============================================
    # ENHANCED WITHDRAWAL WITH SAFETY CHECKS
    # ============================================

    def select_withdrawal_method(self, bank_name):
        """Select the bank for withdrawal"""
        print(f"   🔘 Looking for withdrawal method field...")
        
        # Click the withdrawal method field
        method_selectors = [
            "//*[contains(text(), 'Select withdrawal method')]",
            "//*[contains(text(), 'Withdrawal method')]",
            "//*[contains(@class, 'withdrawal-method')]",
            "//*[contains(@class, 'method-select')]",
            "//div[contains(@class, 'dropdown')]"
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
            self.screenshot("method_clicked")
            print("   ✅ Clicked withdrawal method")
        else:
            print("   ❌ Could not find withdrawal method")
            return False

        # Select OPAY
        print(f"   🔘 Looking for {bank_name}...")
        bank_selectors = [
            f"//*[contains(text(), '{bank_name}')]",
            f"//*[contains(text(), '{bank_name.upper()}')]",
            "//li[contains(text(), 'OPAY')]",
            "//div[contains(text(), 'OPAY')]",
            "//span[contains(text(), 'OPAY')]"
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

    def enter_withdrawal_amount(self, amount):
        """Enter withdrawal amount"""
        print(f"   💰 Entering amount: ${amount:.2f}")
        try:
            # Look for amount input
            amount_selectors = [
                "//input[@placeholder='Please enter amount']",
                "//input[contains(@placeholder, 'amount')]",
                "//input[contains(@name, 'amount')]",
                "//input[contains(@class, 'amount')]"
            ]
            
            for selector in amount_selectors:
                try:
                    amount_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    if amount_field:
                        self.type_text(amount_field, str(amount))
                        print(f"   ✅ Entered amount: ${amount:.2f}")
                        self.screenshot("amount_entered")
                        return True
                except:
                    continue
        except Exception as e:
            print(f"   ❌ Amount entry error: {e}")
        return False

    def enter_fund_password(self, fund_password):
        """Enter the fund password"""
        print("   🔘 Looking for fund password field...")
        fund_selectors = [
            "//input[@placeholder='Please input fund password']",
            "//input[contains(@placeholder, 'fund')]",
            "//input[@type='password']"
        ]
        
        fund_field = None
        for selector in fund_selectors:
            try:
                fund_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if fund_field:
                    print("   ✅ Found fund password field")
                    break
            except:
                continue
        
        if fund_field:
            self.type_text(fund_field, fund_password)
            print(f"   🔑 Entered fund password: {fund_password}")
            self.screenshot("fund_password_entered")
            return True
        else:
            print("   ❌ Could not find fund password field")
            return False

    def click_submit_button(self):
        """Click the green Submit button"""
        print("   🔘 Clicking Submit button...")
        
        submit_selectors = [
            "//button[text()='Submit']",
            "//button[contains(text(), 'Submit')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'green')]",
            "//button[contains(@class, 'primary')]",
            "//button[contains(@class, 'btn')]"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    self.click_element(submit_btn)
                    print("   ✅ Clicked Submit")
                    time.sleep(2)
                    self.screenshot("submit_clicked")
                    return True
            except:
                continue
        
        # JavaScript fallback
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", submit_btn)
            print("   ✅ Clicked Submit (JavaScript)")
            time.sleep(2)
            self.screenshot("submit_clicked")
            return True
        except:
            pass
        
        print("   ❌ Could not find Submit button")
        return False

    def check_withdrawal_result(self):
        """Check if withdrawal was successful"""
        time.sleep(3)
        page_source = self.driver.page_source.lower()
        
        success_indicators = [
            "success",
            "withdrawal successful",
            "withdrawal submitted",
            "pending approval",
            "processing"
        ]
        
        failure_indicators = [
            "insufficient balance",
            "minimum withdrawal",
            "maximum withdrawal",
            "limit",
            "error",
            "failed"
        ]
        
        for indicator in success_indicators:
            if indicator in page_source:
                return "success"
        
        for indicator in failure_indicators:
            if indicator in page_source:
                return "failed"
        
        return "unknown"

    def perform_withdrawal(self, login_data):
        """Perform withdrawal with safety checks"""
        phone = login_data['phone']
        bank_name = login_data['bank_name']
        fund_password = login_data['fund_password']
        real_name = login_data['real_name']
        
        print(f"\n💸 Processing withdrawal for {phone}")
        
        # Get account balance if available
        balance = self.get_account_balance()
        
        # Default withdrawal amount - you can modify this logic
        # For safety, let's withdraw a fixed amount or percentage
        withdrawal_amount = 100.0  # Default amount - CHANGE THIS TO YOUR NEEDS
        
        # Check if withdrawal is allowed
        safety_check = self.safety.can_withdraw(withdrawal_amount, phone, balance)
        
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
            print(f"   Daily remaining: ${self.safety.config['max_daily_withdrawal'] - self.safety.daily_withdrawn:.2f}")
            
            response = input("   Confirm withdrawal? (yes/no): ").strip().lower()
            if response != 'yes':
                print("   ❌ Withdrawal cancelled by user")
                self.safety.log_withdrawal(phone, withdrawal_amount, "cancelled", "User cancelled")
                return False

        # Go to withdrawal page
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(3)
            self.screenshot("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", f"Page load error: {e}")
            return False

        # Step 1: Select withdrawal method
        if not self.select_withdrawal_method(bank_name):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not select bank")
            return False

        # Step 2: Enter amount
        if not self.enter_withdrawal_amount(withdrawal_amount):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not enter amount")
            return False

        # Step 3: Enter fund password
        if not self.enter_fund_password(fund_password):
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Could not enter fund password")
            return False

        # Step 4: Click Submit
        if self.click_submit_button():
            # Check result
            result = self.check_withdrawal_result()
            if result == "success":
                print("   ✅ Withdrawal completed successfully!")
                self.safety.log_withdrawal(phone, withdrawal_amount, "success", "Withdrawal successful")
                return True
            else:
                print(f"   ⚠️ Withdrawal result: {result}")
                self.safety.log_withdrawal(phone, withdrawal_amount, "unknown", f"Result: {result}")
                return True  # Consider it might be pending
        else:
            print("   ❌ Could not complete withdrawal")
            self.safety.log_withdrawal(phone, withdrawal_amount, "failed", "Submit button failed")
            return False

    # ============================================
    # RUN WITH SAFETY
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
        print(f"   Total withdrawals: {summary['total_withdrawals']}")
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
                
            # Add delay between accounts
            time.sleep(5)

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