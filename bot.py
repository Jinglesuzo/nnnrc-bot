from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
import time
import random
import csv
import os
import sys

class NRCBot:
    def __init__(self, bot_id=1, start_index=0):
        self.bot_id = bot_id
        self.start_index = start_index
        self.logins = []
        self.step_counter = 0
        self.password_typed = False  # Track if password was typed

        self.load_logins()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

        print(f"🤖 Bot {self.bot_id} Starting...")
        try:
            options.binary_location = "/usr/bin/google-chrome"
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Failed: {e}")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ Bot {self.bot_id} Chrome started with fallback!")
            except Exception as e2:
                print(f"❌ Bot {self.bot_id} Still failed: {e2}")
                sys.exit(1)

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
            print(f"📋 Bot {self.bot_id} Loaded {len(self.logins)} logins")
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Failed to load logins: {e}")
            sys.exit(1)

    def screenshot(self, name):
        self.step_counter += 1
        try:
            filename = f"bot{self.bot_id}_{self.step_counter:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
            return True
        except:
            return False

    def type_text_once(self, element, text):
        """Type text ONLY ONCE - properly cleared"""
        try:
            # Click and clear
            element.click()
            time.sleep(0.2)
            element.clear()
            time.sleep(0.1)
            
            # Type each character ONCE
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.03, 0.07))
            
            # Verify the value
            time.sleep(0.1)
            return True
        except Exception as e:
            print(f"   ⚠️ Type error: {e}")
            return False

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

    def wait_for_page(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print(f"   ⏰ Page load timeout")
            return False

    def find_login_button(self):
        print(f"   🔍 Looking for login button...")
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[text()='Log in now']")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found 'Log in now'")
                return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found 'Log in now' (contains)")
                return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found 'Log in'")
                return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found submit button")
                return btn
        except:
            pass
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    text = btn.text.lower()
                    if 'log' in text or 'in' in text:
                        print(f"   ✅ Found button: '{btn.text}'")
                        return btn
        except:
            pass
        
        print(f"   ❌ No login button found")
        return None

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        print(f"   📝 Password: {password}")
        self.password_typed = False  # Reset flag
        
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")
            
            if not self.wait_for_page(30):
                print(f"   ⏰ Timeout, reloading...")
                self.driver.refresh()
                time.sleep(2)
            
            # --- PHONE (ONCE) ---
            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            self.type_text_once(phone_field, phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")
            
            # --- PASSWORD (ONCE) ---
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
            self.type_text_once(password_field, password)
            self.password_typed = True
            print(f"   ✅ Password entered (once)")
            self.screenshot("03_password_entered")
            
            # --- LOGIN BUTTON ---
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print(f"   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print(f"   ❌ No login button found")
                return False
            
            time.sleep(5)
            self.screenshot("05_after_login_wait")
            
            # Check result
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            if "important notice" in page_source:
                print(f"   ✅✅✅ LOGIN SUCCESS!")
                self.screenshot("06_login_success")
                return True
            
            if "cooperative wealth zone" in page_source or "dashboard" in current_url:
                print(f"   ✅✅✅ LOGIN SUCCESS!")
                self.screenshot("06_login_success")
                return True
            
            if "invalid" in page_source or "incorrect" in page_source:
                print(f"   ❌ Invalid credentials")
                self.screenshot("06_login_invalid")
                return False
            
            print(f"   ❌ Login failed - unknown reason")
            self.screenshot("06_login_failed")
            return False
            
        except Exception as e:
            print(f"   ⚠️ Login error: {e}")
            self.screenshot("06_login_error")
            return False

    def logout(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print("   ✅ Logged out")
            self.screenshot("07_logged_out")
            return True
        except:
            return False

    def run(self):
        print("="*60)
        print(f"🤖 BOT {self.bot_id} - LOGIN TEST")
        print(f"📋 Total logins: {len(self.logins)}")
        print("="*60)

        for i, login_data in enumerate(self.logins):
            print(f"\n{'#'*50}")
            print(f"📱 Account {i + 1}/{len(self.logins)}")
            print(f"📱 Phone: {login_data['phone']}")
            print(f"{'#'*50}")

            success = self.login(login_data['phone'], login_data['password'])
            
            if success:
                print(f"   ✅ Login SUCCESS!")
                self.logout()
            else:
                print(f"   ❌ Login FAILED!")

            if i < len(self.logins) - 1:
                time.sleep(3)

        print("\n" + "="*60)
        print(f"📊 BOT {self.bot_id} COMPLETE")
        print("="*60)

        self.driver.quit()

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    start_index = int(os.environ.get('START_INDEX', 0))

    bot = NRCBot(bot_id=bot_id, start_index=start_index)
    bot.run()