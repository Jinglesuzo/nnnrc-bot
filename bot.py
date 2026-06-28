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

        # Chrome options for headless mode
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

        print("🔄 Starting Chrome in headless mode...")
        try:
            # Use the chromium driver directly
            service = Service('/usr/lib/chromium-browser/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome started successfully!")
        except Exception as e:
            print(f"❌ Failed to start Chrome: {e}")
            # Fallback: Try using webdriver-manager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                print("🔄 Trying webdriver-manager fallback...")
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("✅ Chrome started successfully with webdriver-manager!")
            except Exception as e2:
                print(f"❌ Still failed: {e2}")
                sys.exit(1)

        self.selectors = {
            'phone': "//input[@placeholder='Please enter your phone number']",
            'password': "//input[@placeholder='Please enter the login password']",
            'confirm_password': "//input[@placeholder='Please confirm your password']",
            'invitation_code': "//input[@placeholder='Please enter the invitation code']",
            'submit': [
                "//button[contains(text(), 'Register now')]",
                "//button[contains(text(), 'Register')]",
                "//button[@type='submit']",
                "//input[@type='submit']"
            ],
            'logout': [
                "//a[contains(text(), 'Logout')]",
                "//button[contains(text(), 'Logout')]",
                "//a[contains(@href, 'logout')]"
            ]
        }

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
            time.sleep(0.1)
            self.driver.execute_script("arguments[0].value = '';", element)
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            element.clear()
            self.driver.execute_script("arguments[0].value = '';", element)
            return True
        except:
            return False

    def fill_form_once(self):
        try:
            wait = WebDriverWait(self.driver, 10)

            self.current_phone = self.generate_nigerian_phone()
            self.current_password = self.generate_password()

            print(f"\n📱 Phone: {self.current_phone}")
            print(f"🔒 Password: {self.current_password}")

            phone_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['phone'])))
            self.clear_field(phone_field)
            phone_field.send_keys(self.current_phone)

            password_field = self.driver.find_element(By.XPATH, self.selectors['password'])
            self.clear_field(password_field)
            password_field.send_keys(self.current_password)

            confirm_field = self.driver.find_element(By.XPATH, self.selectors['confirm_password'])
            self.clear_field(confirm_field)
            confirm_field.send_keys(self.current_password)

            return True

        except Exception as e:
            print(f"❌ Failed to fill form: {e}")
            return False

    def update_invitation_code(self, code):
        try:
            formatted_code = self.format_code(code)
            code_field = self.driver.find_element(By.XPATH, self.selectors['invitation_code'])

            self.driver.execute_script("arguments[0].value = '';", code_field)
            code_field.click()
            code_field.send_keys(Keys.CONTROL + "a")
            code_field.send_keys(Keys.DELETE)
            code_field.clear()
            self.driver.execute_script("arguments[0].value = '';", code_field)

            code_field.send_keys(formatted_code)
            return True

        except Exception as e:
            print(f"❌ Failed to update code: {e}")
            return False

    def click_register_button(self):
        for selector in self.selectors['submit']:
            try:
                button = self.driver.find_element(By.XPATH, selector)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", button)
                return True
            except:
                continue
        return False

    def check_success(self):
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()

            if "please upgrade your level" in page_source or "upgrade your level" in page_source:
                return False, "Upgrade message found - code failed"

            success_indicators = [
                "cooperative wealth zone",
                "deposit principal",
                "invite newcomers",
                "wealth center",
                "wish book",
                "surprise code",
                "benefit savings",
                "dashboard",
                "home",
                "welcome"
            ]

            for indicator in success_indicators:
                if indicator in page_source:
                    return True, f"Success: {indicator} found"

            if "dashboard" in current_url or "home" in current_url:
                return True, "Redirected to dashboard"

            return False, "No success indicators found"

        except Exception as e:
            return False, f"Error: {e}"

    def logout(self):
        for selector in self.selectors['logout']:
            try:
                logout_elements = self.driver.find_elements(By.XPATH, selector)
                if logout_elements:
                    self.driver.execute_script("arguments[0].click();", logout_elements[0])
                    time.sleep(2)
                    return True
            except:
                continue

        try:
            self.driver.delete_all_cookies()
            self.driver.get("https://nnnrc.com/#/register")
            time.sleep(2)
            return True
        except:
            pass

        return False

    def attempt_creation(self, code):
        try:
            if not self.update_invitation_code(code):
                return False, None

            if not self.click_register_button():
                return False, None

            time.sleep(3)

            success, message = self.check_success()

            if success:
                account_info = {
                    'phone': self.current_phone,
                    'password': self.current_password,
                    'invitation_code': self.format_code(code),
                    'success_indicator': message
                }
                self.created_accounts.append(account_info)
                self.save_account(account_info)
                print(f"   ✅ SUCCESS! {message}")
                return True, account_info

            return False, None

        except Exception as e:
            return False, None

    def create_one_account(self):
        print("\n" + "="*50)
        print(f"🆕 Account #{self.account_counter + 1}")
        print(f"Starting code: {self.format_code(self.current_code)}")

        if not self.fill_form_once():
            return False

        attempts = 0
        max_tries = 200

        while attempts < max_tries:
            code = self.current_code
            print(f"   Testing: {self.format_code(code)}", end=" ", flush=True)

            success, account = self.attempt_creation(code)

            if success:
                print(f"✅")
                print(f"\n✅ ACCOUNT CREATED!")
                print(f"   Phone: {account['phone']}")
                print(f"   Password: {account['password']}")
                print(f"   Invitation Code: {account['invitation_code']}")

                self.logout()
                self.driver.get("https://nnnrc.com/#/register")
                time.sleep(2)

                self.current_code = code + 1
                self.account_counter += 1
                print(f"📊 Accounts created: {self.account_counter}")
                print(f"➡️  Next code: {self.format_code(self.current_code)}")

                return True

            print(f"❌")
            self.current_code = code + 1
            attempts += 1

            time.sleep(random.uniform(0.3, 0.8))

        print(f"❌ Could not find working code")
        return False

    def run(self, url, num_accounts=10):
        print("="*60)
        print("🇳🇬 NIGERIAN ACCOUNT CREATION BOT (GitHub Actions)")
        print(f"Starting code: {self.format_code(self.current_code)}")
        print(f"Target: {num_accounts} accounts")
        print("="*60)

        try:
            self.driver.get(url)
            print("✅ Website loaded")
            time.sleep(3)
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            return

        for i in range(num_accounts):
            print(f"\n🎯 Creating Account #{i + 1} of {num_accounts}")
            success = self.create_one_account()

            if not success:
                print(f"⚠️ Failed to create account #{i + 1}")
                self.driver.get("https://nnnrc.com/#/register")
                time.sleep(2)

            if i < num_accounts - 1:
                time.sleep(random.uniform(2, 4))

        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print(f"Total accounts created: {len(self.created_accounts)}")
        for idx, acc in enumerate(self.created_accounts, 1):
            print(f"   #{idx}: Code: {acc['invitation_code']} | Phone: {acc['phone']} | Password: {acc['password']}")
        print("="*60)

        self.driver.quit()

    def save_account(self, account):
        file_exists = os.path.isfile('accounts.csv')
        with open('accounts.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Account #', 'Phone', 'Password', 'Invitation Code', 'Timestamp', 'Success Indicator'])
            writer.writerow([
                len(self.created_accounts),
                account['phone'],
                account['password'],
                account['invitation_code'],
                time.ctime(),
                account.get('success_indicator', 'Dashboard detected')
            ])

        print("="*50)
        print("✅ NEW ACCOUNT CREATED!")
        print(f"📱 Phone: {account['phone']}")
        print(f"🔑 Password: {account['password']}")
        print(f"🎯 Invitation Code: {account['invitation_code']}")
        print("="*50)

# ============================================
# RUN THE BOT
# ============================================

target_url = "https://nnnrc.com/#/register"
NUM_ACCOUNTS = 10

bot = NigerianAccountBot(start_code=41140)
bot.run(target_url, num_accounts=NUM_ACCOUNTS)