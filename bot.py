from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import random
import csv
import os
import sys
import string

# === WORD LIST FOR HUMAN-LIKE PASSWORDS ===
COMMON_WORDS = [
    'apple', 'banana', 'cherry', 'dragon', 'eagle', 'falcon', 'garden', 'honey',
    'island', 'jungle', 'knight', 'lionel', 'magic', 'noble', 'ocean', 'piano',
    'queen', 'river', 'star', 'tiger', 'uncle', 'victor', 'water', 'xenon',
    'yellow', 'zebra', 'angel', 'blaze', 'cloud', 'dream', 'eagle', 'flame',
    'grace', 'heart', 'ivory', 'joker', 'king', 'lunar', 'moon', 'night',
    'orbit', 'peace', 'rain', 'storm', 'titan', 'ultra', 'vivid', 'whale',
    'crystal', 'diamond', 'emerald', 'forest', 'golden', 'hero', 'iron',
    'jade', 'koala', 'lemon', 'mango', 'nova', 'opal', 'pearl', 'ruby',
    'sapphire', 'topaz', 'amber', 'bronze', 'copper', 'denver', 'elite',
    'frost', 'glacier', 'hunter', 'indigo', 'jupiter', 'karma', 'legend',
    'mystic', 'neon', 'oracle', 'phoenix', 'quantum', 'radiant', 'shadow',
    'thunder', 'unity', 'valkyrie', 'wisdom', 'zenith'
]

class NigerianAccountBot:
    def __init__(self, start_code=7000100):
        self.current_code = start_code
        self.step_size = 1
        self.created_accounts = []
        self.account_counter = 0
        self.nigerian_prefixes = ['080', '081', '090', '091', '070', '071']
        self.current_phone = None
        self.current_password = None
        self.last_result = "Waiting to start..."
        self.consecutive_failures = 0
        self.max_failures = 5
        self.max_retries = 3

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

        print("🔄 Starting Chrome...")
        try:
            options.binary_location = "/usr/bin/google-chrome"
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome started (pre-installed)!")
        except Exception as e:
            print(f"❌ Failed with pre-installed: {e}")
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

    # === HUMAN BEHAVIOR FUNCTIONS ===

    def human_type(self, element, text):
        """Type like a human with random delays between keystrokes"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.25))

    def human_click(self, element):
        """Click like a human with natural movement"""
        try:
            actions = ActionChains(self.driver)
            actions.move_to_element(element).perform()
            time.sleep(random.uniform(0.2, 0.6))
            element.click()
            return True
        except:
            self.driver.execute_script("arguments[0].click();", element)
            return True

    def random_pause(self, min_sec=0.5, max_sec=2.0):
        """Random pause to simulate human thinking"""
        time.sleep(random.uniform(min_sec, max_sec))

    def random_scroll(self):
        """Scroll the page randomly like a human reading"""
        try:
            scroll_amount = random.randint(100, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.2, 0.5))
            if random.random() > 0.5:
                scroll_back = random.randint(50, 200)
                self.driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
        except:
            pass

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
        """Generate a human-like password: word + number (e.g., 'apple123', 'tiger456')"""
        # Pick a random word
        word = random.choice(COMMON_WORDS)
        # Add random number at the end (1-3 digits)
        number = random.randint(10, 999)
        # Randomly capitalize first letter sometimes
        if random.random() > 0.5:
            word = word.capitalize()
        return f"{word}{number}"

    def format_code(self, code):
        return str(code).zfill(7)

    def clear_field(self, element):
        try:
            element.click()
            time.sleep(random.uniform(0.1, 0.3))
            self.driver.execute_script("arguments[0].value = '';", element)
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            element.clear()
            self.driver.execute_script("arguments[0].value = '';", element)
            return True
        except:
            return False

    def wait_for_page_load(self, timeout=15):
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            self.random_pause(0.5, 1.5)
            return True
        except:
            return False

    def safe_find_element(self, by, selector, timeout=10):
        for attempt in range(self.max_retries):
            try:
                wait = WebDriverWait(self.driver, timeout)
                return wait.until(EC.presence_of_element_located((by, selector)))
            except Exception as e:
                print(f"   ⚠️ Attempt {attempt + 1} failed: {e}")
                time.sleep(1)
                if attempt == self.max_retries - 1:
                    raise
        return None

    def fill_form_once(self):
        try:
            self.wait_for_page_load()
            wait = WebDriverWait(self.driver, 15)
            
            self.current_phone = self.generate_nigerian_phone()
            self.current_password = self.generate_password()

            print(f"\n📱 Phone: {self.current_phone}")
            print(f"🔒 Password: {self.current_password}")

            self.random_scroll()
            self.random_pause(0.5, 1.5)

            phone_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['phone'])))
            self.clear_field(phone_field)
            self.human_type(phone_field, self.current_phone)
            self.random_pause(0.3, 0.8)

            password_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['password'])))
            self.clear_field(password_field)
            self.human_type(password_field, self.current_password)
            self.random_pause(0.3, 0.8)

            confirm_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['confirm_password'])))
            self.clear_field(confirm_field)
            self.human_type(confirm_field, self.current_password)
            self.random_pause(0.3, 0.8)

            self.random_scroll()
            self.random_pause(0.5, 1.5)

            print("✅ Form filled!")
            self.take_screenshot("after_form_fill")
            return True

        except Exception as e:
            print(f"❌ Failed to fill form: {e}")
            return False

    def update_invitation_code(self, code):
        try:
            formatted_code = self.format_code(code)
            self.wait_for_page_load()
            
            self.random_pause(0.5, 1.5)
            
            code_field = self.safe_find_element(By.XPATH, self.selectors['invitation_code'])
            if not code_field:
                print(f"   ❌ Code field not found")
                return False
            
            self.clear_field(code_field)
            self.human_type(code_field, formatted_code)
            print(f"   ✅ Code: {formatted_code}")
            
            self.random_pause(0.3, 0.8)
            return True
        except Exception as e:
            print(f"   ❌ Failed to update code: {e}")
            return False

    def click_register_button(self):
        try:
            self.random_scroll()
            self.random_pause(0.5, 1.5)
            
            wait = WebDriverWait(self.driver, 10)
            
            selectors = [
                "//*[contains(text(), 'Register now')]",
                "//button[contains(text(), 'Register')]",
                "//button[@type='submit']",
                "//input[@type='submit']"
            ]
            
            for selector in selectors:
                try:
                    button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    self.human_click(button)
                    print("   ✅ Clicked Register!")
                    return True
                except:
                    continue
            
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
            self.random_pause(1.0, 2.5)
            
            page_source = self.driver.page_source.lower()
            
            if "important notice" in page_source:
                self.last_result = "✅ SUCCESS! Important Notice found"
                self.take_screenshot("success_important_notice")
                return True
            if "limited-time free upgrade" in page_source:
                self.last_result = "✅ SUCCESS! Free Upgrade found"
                self.take_screenshot("success_free_upgrade")
                return True
            
            if "please upgrade your level" in page_source or "upgrade your level" in page_source:
                self.last_result = "❌ Upgrade message - code failed"
                return False
            
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
            if not self.update_invitation_code(code):
                return False, None
            
            self.random_pause(0.5, 1.5)
            
            if not self.click_register_button():
                return False, None
            
            self.random_pause(2.0, 4.0)
            self.wait_for_page_load()
            
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
                self.consecutive_failures = 0
                return True, account_info
            
            self.consecutive_failures += 1
            return False, None
            
        except Exception as e:
            print(f"   ⚠️ Error in attempt: {e}")
            self.consecutive_failures += 1
            time.sleep(3)
            return False, None

    def create_one_account(self):
        print("\n" + "="*50)
        print(f"🆕 Account #{self.account_counter + 1}")
        print(f"Starting code: {self.format_code(self.current_code)}")
        self.consecutive_failures = 0

        self.random_pause(1.0, 3.0)

        if not self.fill_form_once():
            print("❌ Could not fill form - skipping this account")
            return False

        attempts = 0
        max_tries = 10

        while attempts < max_tries and self.consecutive_failures < self.max_failures:
            code = self.current_code
            print(f"   Testing: {self.format_code(code)}", end=" ", flush=True)

            success, account = self.attempt_creation(code)

            if success:
                print(f"✅")
                print("\n" + "="*60)
                print("✅ ACCOUNT CREATED - COPY BELOW:")
                print("="*60)
                print(f"📱 Phone: {account['phone']}")
                print(f"🔑 Password: {account['password']}")
                print(f"🎯 Code: {account['invitation_code']}")
                print("="*60)
                print("\n📋 COPY THIS LINE:")
                print(f"{account['phone']} | {account['password']} | {account['invitation_code']}")
                print("="*60)
                
                self.logout()
                self.go_to_register_page()
                
                self.current_code = code + self.step_size
                self.account_counter += 1
                print(f"📊 Accounts created: {self.account_counter}")
                print(f"➡️  Next code: {self.format_code(self.current_code)}")
                return True

            print(f"❌ ({self.consecutive_failures}/{self.max_failures} failures)")
            self.current_code = code + self.step_size
            attempts += 1
            self.random_pause(0.5, 2.0)

        if self.consecutive_failures >= self.max_failures:
            print(f"❌ Too many failures ({self.max_failures}) - skipping this account")
        else:
            print(f"❌ Could not find working code after {max_tries} attempts")
        return False

    def logout(self):
        try:
            print(f"   🔄 Logging out...")
            self.random_pause(0.5, 1.5)
            self.driver.get("https://nnnrc.com/#/logout")
            self.wait_for_page_load()
            time.sleep(random.uniform(1.0, 2.0))
            print(f"   ✅ Logged out")
            return True
        except Exception as e:
            print(f"   ⚠️ Logout error: {e}")
            return False

    def go_to_register_page(self):
        try:
            self.driver.get("https://nnnrc.com/#/register")
            self.wait_for_page_load()
            time.sleep(random.uniform(1.0, 2.0))
            print("   ✅ Back to register page")
            return True
        except Exception as e:
            print(f"   ⚠️ Navigation error: {e}")
            return False

    def run(self, url, num_accounts=5):
        print("="*60)
        print("🇳🇬 NIGERIAN ACCOUNT CREATION BOT (HUMAN MODE)")
        print(f"Starting code: {self.format_code(self.current_code)}")
        print(f"Step size: +{self.step_size}")
        print(f"Target: {num_accounts} accounts this run")
        print("="*60)

        try:
            self.driver.get(url)
            self.wait_for_page_load()
            print("✅ Website loaded")
            self.take_screenshot("page_loaded")
            self.random_pause(1.0, 3.0)
        except Exception as e:
            print(f"❌ Failed to load: {e}")
            return

        for i in range(num_accounts):
            print(f"\n🎯 Creating Account #{i + 1} of {num_accounts}")
            success = self.create_one_account()

            if not success:
                print(f"⚠️ Failed to create account #{i + 1}")
                self.driver.get("https://nnnrc.com/#/register")
                self.wait_for_page_load()
                self.random_pause(1.0, 2.0)

            if i < num_accounts - 1:
                delay = random.uniform(5.0, 10.0)
                print(f"⏳ Human-like pause {delay:.1f}s before next account...")
                time.sleep(delay)

        print("\n" + "="*60)
        print("📊 FINAL SUMMARY")
        print(f"Total accounts created: {len(self.created_accounts)}")
        
        print("\n" + "="*60)
        print("📋 COPY ALL ACCOUNTS BELOW:")
        print("="*60)
        for idx, acc in enumerate(self.created_accounts, 1):
            print(f"{idx}. {acc['phone']} | {acc['password']} | {acc['invitation_code']}")
        print("="*60)
        
        print("\n📱 Login Credentials:")
        for idx, acc in enumerate(self.created_accounts, 1):
            print(f"   #{idx} → Phone: {acc['phone']} | Password: {acc['password']}")
        print("="*60)
        print(f"➡️  Next run will start from: {self.format_code(self.current_code)}")
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
# RUN THE BOT (START: 7000100, STEP: +1)
# ============================================

target_url = "https://nnnrc.com/#/register"
NUM_ACCOUNTS = 3

bot = NigerianAccountBot(start_code=3069170)
bot.run(target_url, num_accounts=NUM_ACCOUNTS)