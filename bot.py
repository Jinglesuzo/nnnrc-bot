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

class NRCBot:
    def __init__(self, bot_id=1):
        self.bot_id = bot_id
        self.logins = []
        self.step = 0
        
        # === MANUAL CONTROL: Set how many times to type password ===
        # Bot 1 types once, Bot 2 types once (set to 1 for both)
        if bot_id == 1:
            self.password_typing_count = 1  # Bot 1 types ONCE
        elif bot_id == 2:
            self.password_typing_count = 1  # Bot 2 types ONCE (change to 1)
        else:
            self.password_typing_count = 1  # Default
        
        print(f"🤖 Bot {self.bot_id} - Password typing count: {self.password_typing_count}")
        
        self.load_logins()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        print(f"🤖 Bot {self.bot_id} Starting...")
        try:
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome started!")
        except:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print("✅ Chrome started with fallback!")
            except Exception as e:
                print(f"❌ Failed: {e}")
                sys.exit(1)

    def screenshot(self, name):
        self.step += 1
        try:
            filename = f"bot{self.bot_id}_{self.step:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
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
                    if len(row) >= 2:
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip()
                        })
            print(f"📋 Loaded {len(self.logins)} logins")
        except Exception as e:
            print(f"❌ No logins.csv found: {e}")
            sys.exit(1)

    def type_text(self, element, text, count=1):
        """Type text a specific number of times"""
        element.click()
        element.clear()
        time.sleep(0.1)
        
        # Type the password the specified number of times
        for _ in range(count):
            for char in text:
                element.send_keys(char)
                time.sleep(0.04)
            # If typing more than once, add a small delay
            if count > 1:
                time.sleep(0.1)
        
        # Verify the value
        entered_value = element.get_attribute('value')
        if count == 1:
            print(f"   ✅ Typed: {text[:3]}*** (once)")
        else:
            print(f"   ⚠️ Typed {count} times: {entered_value}")

    def wait_and_find(self, by, selector, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except:
            return None

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")
            
            # Phone
            phone_field = self.wait_and_find(By.XPATH, "//input[@placeholder='Please enter your phone number']")
            if not phone_field:
                phone_field = self.wait_and_find(By.CSS_SELECTOR, "input[type='tel']")
            if phone_field:
                self.type_text(phone_field, phone, 1)  # Phone always typed once
                self.screenshot("02_phone_entered")
                print(f"   ✅ Phone: {phone}")
            else:
                print(f"   ❌ Phone field not found")
                self.screenshot("02_phone_not_found")
                return False
            
            # Password with manual control
            password_field = self.wait_and_find(By.XPATH, "//input[@placeholder='Please enter login password']")
            if not password_field:
                password_field = self.wait_and_find(By.CSS_SELECTOR, "input[type='password']")
            if password_field:
                # Use the password_typing_count set in __init__
                self.type_text(password_field, password, self.password_typing_count)
                self.screenshot("03_password_entered")
                print(f"   ✅ Password entered ({self.password_typing_count} time(s))")
            else:
                print(f"   ❌ Password field not found")
                self.screenshot("03_password_not_found")
                return False
            
            # Login button
            login_btn = self.wait_and_find(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if not login_btn:
                login_btn = self.wait_and_find(By.CSS_SELECTOR, "button[type='submit']")
            if login_btn:
                login_btn.click()
                print(f"   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print(f"   ❌ Login button not found")
                self.screenshot("04_login_button_not_found")
                return False
            
            time.sleep(5)
            self.screenshot("05_after_login_wait")
            
            # Check success
            page = self.driver.page_source.lower()
            if "important notice" in page:
                print(f"   ✅✅✅ LOGIN SUCCESS! (Important Notice)")
                self.screenshot("06_login_success")
                return True
            
            if "cooperative wealth zone" in page:
                print(f"   ✅✅✅ LOGIN SUCCESS! (Dashboard)")
                self.screenshot("06_login_success")
                return True
            
            print(f"   ❌ Login failed")
            self.screenshot("06_login_failed")
            return False
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.screenshot("06_login_error")
            return False

    def logout(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print("   ✅ Logged out")
            self.screenshot("07_logged_out")
        except:
            pass

    def run(self):
        print("="*50)
        print(f"🤖 BOT {self.bot_id} STARTING")
        print(f"📝 Password typing count: {self.password_typing_count}")
        print("="*50)

        for i, login_data in enumerate(self.logins):
            print(f"\n📱 Account {i+1}/{len(self.logins)}")
            if self.login(login_data['phone'], login_data['password']):
                self.logout()
            time.sleep(2)

        self.driver.quit()
        print("\n✅ Done!")
        self.screenshot("99_final")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = NRCBot(bot_id=bot_id)
    bot.run()