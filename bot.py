from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
import random
import csv
import os
import sys

class NigerianAccountBot:
    def __init__(self, start_code=41140):
        self.current_code = start_code
        self.created_accounts = []
        self.account_counter = 0
        self.nigerian_prefixes = ['080', '081', '090', '091', '070', '071']
        self.current_phone = None
        self.current_password = None
        self.last_result = "Waiting to start..."
        self.consecutive_failures = 0
        self.max_failures = 5  # Stop if 5 consecutive failures

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

        print("🔄 Starting Chrome...")
        try:
            service = Service('/usr/lib/chromium-browser/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome started!")
        except Exception as e:
            print(f"❌ Failed: {e}")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("✅ Chrome started with fallback!")
            except Exception as e2:
                print(f"❌ Still failed: {e2}")
                sys.exit(1)

        self.selectors = {
            'phone': "//input[@placeholder='Please enter your phone number']",
            'password': "//input[@placeholder='Please enter the login password']",
            'confirm_password': "//input[@placeholder='Please confirm your password']",
            'invitation_code': "//input[@placeholder='Please enter the invitation code']",
        }

    def take_screenshot(self, name):
        try:
            self.driver.save_screenshot(f"{name}.png")
        except:
            pass

    def generate_nigerian_phone(self):
        prefix = random.choice(self.nigerian_prefixes)
        number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return prefix + number

    def generate_password(self):
        return ''.join([str(random.randint(0, 9)) for _ in range(6)])

    def format_code(self, code):
        return str(code).zfill(7)

    def clear_field(self, element):
        try:
            element.click()
            time.sleep(0.2)
            self.driver.execute_script("arguments[0].value = '';", element)
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            element.clear()
            self.driver.execute_script("arguments[0].value = '';", element)
            return True
        except:
            return False

    def wait_for_page_load(self, timeout=15):
        """Wait for page to be fully loaded"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            time.sleep(2)  # Extra wait for dynamic content
            return True
        except:
            return False

    def fill_form_once(self):
        try:
            # Wait for page to be ready
            self.wait_for_page_load()
            
            wait = WebDriverWait(self.driver, 15)
            
            self.current_phone = self.generate_nigerian_phone()
            self.current_password = self.generate_password()

            print(f"\n📱 Phone: {self.current_phone}")
            print(f"🔒 Password: {self.current_password}")

            # Find and fill phone
            phone_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['phone'])))
            self.clear_field(phone_field)
            phone_field.send_keys(self.current_phone)

            # Fill password
            password_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['password'])))
            self.clear_field(password_field)
            password_field.send_keys(self.current_password)

            # Fill confirm password
            confirm_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['confirm_password'])))
            self.clear_field(confirm_field)
            confirm_field.send_keys(self.current_password)

            print("✅ Form filled!")
            self.take_screenshot("after_form_fill")
            return True

        except Exception as e:
            print(f"❌ Failed to fill form: {e}")
            return False

    def update_invitation_code(self, code):
        try:
            formatted_code = self.format_code(code)
            
            # Wait for the page to be ready
            self.wait_for_page_load()
            
            # Wait for the code field to be present
            wait = WebDriverWait(self.driver, 10)
            code_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['invitation_code'])))
            
            self.clear_field(code_field)
            code_field.send_keys(formatted_code)
            print(f"   ✅ Code: {formatted_code}")
            return True
        except Exception as e:
            print(f"   ❌ Failed to update code: {e}")
            return False

    def click_register_button(self):
        try:
            # Wait for button to be clickable
            wait = WebDriverWait(self.driver, 10)
            
            # Try different selectors
            try:
                button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Register now')]")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", button)
                print("   ✅ Clicked Register!")
                return True
            except:
                pass
            
            try:
                button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Register')]")))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", button)
                print("   ✅ Clicked Register!")
                return True
            except:
                pass
            
            try:
                form = self.driver.find_element(By.TAG_NAME, "form")
                self.driver.execute_script("arguments[0].submit();", form)
                print("   ✅ Submitted form!")
                return True
            except:
                pass
                
            print("   ❌ Could not click Register!")
            return False
            
        except Exception as e:
            print(f"   ❌ Register click error: {e}")
            return False

    def check_success(self):
        try:
            page_source = self.driver.page_source.lower()
            
            # SUCCESS: Important Notice
            if "important notice" in page_source:
                self.last_result = "✅ SUCCESS! Important Notice found"
                self.take_screenshot("success_important_notice")
                return True
            
            if "limited-time free upgrade" in page_source:
                self.last_result = "✅ SUCCESS! Free Upgrade found"
                self.take_screenshot("success_free_upgrade")
                return True
            
            # FAILURE: Upgrade message
            if "please upgrade your level" in page_source or "upgrade your level" in page_source:
                self.last_result = "❌ Upgrade message - code failed"
                return False
            
            # Other success indicators
            success_words = [
                "cooperative wealth zone", "deposit principal", "invite newcomers",
                "wealth center", "wish book", "surprise code", "benefit savings",
                "dashboard", "home", "welcome", "success"
            ]
            
            for word in success_words:
                if word in page_source:
                    self.last_result = f"✅ Success: '{word}' found"
                    self.take_screenshot(f"success_{word.replace(' ', '_')}")
                    return True
            
            self.last_result = "❌ No success indicators found"
            return False
            
        except Exception as e:
            self.last_result = f"❌ Error: {e}"
            return False

    def attempt_creation(self, code):
        try:
            # Update code - wait for page first
            if not self.update_invitation_code(code):
                return False, None
            
            # Wait before clicking
            time.sleep(0.5)
            
            # Click Register
            if not self.click_register_button():
                return False, None
            
            # WAIT FOR PAGE TO RESPOND (CRITICAL)
            time.sleep(4)
            self.wait_for_page_load()
            
            # Check if success
            if self.check_success():
                account_info = {
                    'phone': self.current_phone,
                    'password': self.current_password,
                    'invitation_code': self.format_code(code)
                }
                self.created_accounts.append(account_info)
                self.save_account(account_info)
                print(f"   ✅✅✅ SUCCESS! Account created with code: {self.format_code(code)}")
                self.last_result = f"✅ SUCCESS! Code {self.format_code(code)} worked!"
                self.consecutive_failures = 0  # Reset failure counter
                return True, account_info
            
            # Failed
            self.consecutive_failures += 1
            return False, None
            
        except Exception as e:
            print(f"   ⚠️ Error in attempt: {e}")
            self.consecutive_failures += 1
            time.sleep(3)  # Wait longer after error
            return False, None

    def create_one_account(self):
        print("\n" + "="*50)
        print(f"🆕 Account #{self.account_counter + 1}")
        print(f"Starting code: {self.format_code(self.current_code)}")
        
        # Reset failure counter for this account
        self.consecutive_failures = 0

        if not self.fill_form_once():
            print("❌ Could not fill form - skipping this account")
            return False

        attempts = 0
        max_tries = 15

        while attempts < max_tries and self.consecutive_failures < self.max_failures:
            code = self.current_code
            print(f"   Testing: {self.format_code(code)}", end=" ", flush=True)

            success, account = self.attempt_creation(code)

            if success:
                print(f"✅")
                print(f"\n✅ ACCOUNT CREATED!")
                print(f"   📱 Phone: {account['phone']}")
                print(f"   🔑 Password: {account['password']}")
                print(f"   🎯 Invitation Code: {account['invitation_code']}")
                
                # Logout
                self.logout()
                
                # Go back to register page
                self.go_to_register_page()
                
                # Move to next code
                self.current_code = code + 1
                self.account_counter += 1
                print(f"📊 Accounts created: {self.account_counter}")
                print(f"➡️  Next code: {self.format_code(self.current_code)}")
                
                return True

            print(f"❌ ({self.consecutive_failures}/{self.max_failures} failures)")
            self.current_code = code + 1
            attempts += 1
            
            # Wait between attempts
            time.sleep(1)

        if self.consecutive_failures >= self.max_failures:
            print(f"❌ Too many failures ({self.max_failures}) - skipping this account")
        else:
            print(f"❌ Could not find working code after {max_tries} attempts")
        return False

    def logout(self):
        try:
            print(f"   🔄 Logging out...")
            self.driver.get("https://nnnrc.com/#/logout")
            self.wait_for_page_load()
            time.sleep(2)
            print(f"   ✅ Logged out")
            return True
        except Exception as e:
            print(f"   ⚠️ Logout error: {e}")
            return False

    def go_to_register_page(self):
        try:
            self.driver.get("https://nnnrc.com/#/register")
            self.wait_for_page_load()
            time.sleep(2)
            print("   ✅ Back to register page")
            return True
        except Exception as e:
            print(f"   ⚠️ Navigation error: {e}")
            return False

    def run(self, url, num_accounts=3):
        print("="*60)
        print("🇳🇬 NIGERIAN ACCOUNT CREATION BOT (FIXED)")
        print(f"Starting code: {self.format_code(self.current_code)}")
        print(f"Target: {num_accounts} accounts")
        print("="*60)

        try:
            self.driver.get(url)
            self.wait_for_page_load()
            print("✅ Website loaded")
            self.take_screenshot("page_loaded")
            time.sleep(3)
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            return

        for i in range(num_accounts):
            print(f"\n🎯 Creating Account #{i + 1} of {num_accounts}")
            success = self.create_one_account()

            if not success:
                print(f"⚠️ Failed to create account #{i + 1}")
                # Try to recover
                self.driver.get("https://nnnrc.com/#/register")
                self.wait_for_page_load()
                time.sleep(2)

            if i < num_accounts - 1:
                delay = random.uniform(3, 6)
                print(f"⏳ Waiting {delay:.1f}s before next account...")
                time.sleep(delay)

        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print(f"Total accounts created: {len(self.created_accounts)}")
        print("\nAccount details:")
        for idx, acc in enumerate(self.created_accounts, 1):
            print(f"   #{idx}: Code: {acc['invitation_code']} | Phone: {acc['phone']} | Password: {acc['password']}")
        print("="*60)
        
        self.take_screenshot("final")
        self.driver.quit()

    def save_account(self, account):
        file_exists = os.path.isfile('accounts.csv')
        with open('accounts.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Account #', 'Phone', 'Password', 'Invitation Code', 'Timestamp'])
            writer.writerow([
                len(self.created_accounts),
                account['phone'],
                account['password'],
                account['invitation_code'],
                time.ctime()
            ])
        print(f"   💾 Saved to accounts.csv")

# ============================================
# RUN THE BOT
# ============================================

target_url = "https://nnnrc.com/#/register"
NUM_ACCOUNTS = 5  # Start with 5 for testing

bot = NigerianAccountBot(start_code=50400)
bot.run(target_url, num_accounts=NUM_ACCOUNTS)