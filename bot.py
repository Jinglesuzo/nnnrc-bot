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
            print(f"   📸 Screenshot: {name}.png")
        except:
            pass

    def generate_nigerian_phone(self):
        prefix = random.choice(self.nigerian_prefixes)
        number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        return prefix + number

    def generate_password(self):
        """Generate a human-like password: word + number (e.g., 'apple123', 'tiger456')"""
        word = random.choice(COMMON_WORDS)
        number = random.randint(10, 999)
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

    # ============================================
    # POPUP HANDLING METHODS
    # ============================================

    def click_news_button(self):
        """Click the NEWS button to trigger the welcome popup"""
        try:
            news_selectors = [
                "//*[contains(text(), 'NEWS')]",
                "//*[contains(text(), 'News')]",
                "//button[contains(text(), 'NEWS')]",
                "//*[contains(@class, 'news')]",
                "//*[contains(@id, 'news')]",
                "//div[contains(text(), 'NEWS')]",
                "//span[contains(text(), 'NEWS')]"
            ]
            
            for selector in news_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            print("   📰 Clicked NEWS button")
                            time.sleep(1.5)
                            return True
                except:
                    continue
            
            # Fallback: click any visible green button
            try:
                green_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@style, 'green')] | //*[contains(@class, 'green')]")
                for btn in green_buttons:
                    if btn.is_displayed():
                        self.human_click(btn)
                        print("   📰 Clicked green button (NEWS)")
                        time.sleep(1.5)
                        return True
            except:
                pass
            
            print("   ⚠️ Could not find NEWS button")
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error clicking NEWS: {e}")
            return False

    def close_welcome_popup(self):
        """Close the 'Welcome to join NRC' popup"""
        try:
            welcome_selectors = [
                "//*[contains(text(), 'Welcome to join NRC')]",
                "//*[contains(text(), 'Thank you for your trust')]",
                "//*[contains(@class, 'welcome')]",
                "//button[contains(text(), 'Got it')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Close')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[text()='×']"
            ]
            
            for selector in welcome_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            self.human_click(element)
                            print("   🚫 Closed Welcome popup")
                            time.sleep(0.5)
                            return True
                except:
                    continue
            return False
        except Exception as e:
            print(f"   ⚠️ Could not close welcome popup: {e}")
            return False

    def close_remaining_popups(self):
        """Close any remaining popups or ads"""
        try:
            close_selectors = [
                "//*[contains(@class, 'close')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[text()='×']",
                "//*[text()='✕']",
                "//button[contains(@class, 'btn-close')]",
                "//*[contains(@class, 'ad-close')]"
            ]
            
            closed = 0
            for selector in close_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            closed += 1
                            time.sleep(0.3)
                except:
                    continue
            
            if closed > 0:
                print(f"   🚫 Closed {closed} remaining popup(s)")
            return True
        except:
            return False

    def handle_success_popups(self):
        """Complete flow for handling success popups"""
        print("   📋 Handling success popups...")
        
        # Step 1: Click NEWS button
        if self.click_news_button():
            # Step 2: Close Welcome popup
            self.close_welcome_popup()
            
            # Step 3: Close any remaining popups
            self.close_remaining_popups()
            
            print("   ✅ All popups handled")
            return True
        else:
            print("   ⚠️ Could not find NEWS button, skipping popup handling")
            return False

    # ============================================
    # TASK BUTTON AND LOGOUT METHODS
    # ============================================

    def click_task_tab(self):
        """Click the Task tab at the bottom"""
        try:
            task_selectors = [
                "//*[contains(text(), 'Task')]",
                "//*[contains(text(), 'task')]",
                "//*[contains(@class, 'task')]",
                "//button[contains(text(), 'Task')]",
                "//div[contains(text(), 'Task')]",
                "//span[contains(text(), 'Task')]",
                "//*[@id='task']",
                "//*[contains(@class, 'tab-task')]"
            ]
            
            for selector in task_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            print("   📋 Clicked Task tab")
                            time.sleep(1)
                            return True
                except:
                    continue
            
            print("   ⚠️ Could not find Task tab")
            return False
            
        except Exception as e:
            print(f"   ⚠️ Error clicking Task: {e}")
            return False

    def check_success(self):
        try:
            self.random_pause(1.0, 2.5)
            
            page_source = self.driver.page_source.lower()
            
            # CHECK FOR SUCCESS - Important Notice is the key indicator
            if "important notice" in page_source:
                self.last_result = "✅ SUCCESS! Important Notice found"
                self.take_screenshot("01_success_important_notice")
                
                # === HANDLE POPUPS (NEWS → Welcome → Close) ===
                self.handle_success_popups()
                
                # === CLICK TASK TAB ===
                self.click_task_tab()
                self.take_screenshot("02_after_task_click")
                
                return True
            
            # Check for other success indicators
            if "welcome to join nrc" in page_source:
                self.last_result = "✅ SUCCESS! Welcome found"
                self.take_screenshot("01_success_welcome")
                self.handle_success_popups()
                self.click_task_tab()
                self.take_screenshot("02_after_task_click")
                return True
            
            if "cooperative wealth zone" in page_source:
                self.last_result = "✅ SUCCESS! Dashboard found"
                self.take_screenshot("01_success_dashboard")
                self.handle_success_popups()
                self.click_task_tab()
                self.take_screenshot("02_after_task_click")
                return True
            
            # CHECK FOR FAILURE
            if "please upgrade your level" in page_source or "upgrade your level" in page_source:
                self.last_result = "❌ Upgrade message - code failed"
                self.take_screenshot("01_failure_upgrade")
                return False
            
            # OTHER SUCCESS INDICATORS
            success_words = [
                "cooperative wealth zone", "deposit principal", "invite newcomers",
                "wealth center", "wish book", "surprise code", "benefit savings",
                "dashboard", "home", "welcome", "success"
            ]
            
            for word in success_words:
                if word in page_source:
                    self.last_result = f"✅ Success: '{word}' found"
                    self.take_screenshot(f"01_success_{word.replace(' ', '_')}")
                    self.handle_success_popups()
                    self.click_task_tab()
                    self.take_screenshot("02_after_task_click")
                    return True
            
            self.last_result = "❌ No success indicators found"
            self.take_screenshot("01_no_success")
            return False
            
        except Exception as e:
            self.last_result = f"❌ Error: {e}"
            self.take_screenshot("01_error")
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
                
                # === TAKE FINAL SCREENSHOT ===
                self.take_screenshot("03_final_dashboard")
                
                return True, account_info
            
            self.consecutive_failures += 1
            return False, None
            
        except Exception as e:
            print(f"   ⚠️ Error in attempt: {e}")
            self.take_screenshot("01_error")
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
            self.take_screenshot("04_logged_out")
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
            self.take_screenshot("00_page_loaded")
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
                self.take_screenshot("05_recovery")

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
        
        self.take_screenshot("99_final_summary")
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
NUM_ACCOUNTS = 1

bot = NigerianAccountBot(start_code=50420)
bot.run(target_url, num_accounts=NUM_ACCOUNTS)