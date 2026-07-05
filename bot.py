from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import csv
import os
import sys

class NRCBot:
    def __init__(self, bot_id=1):
        self.bot_id = bot_id
        self.logins = []
        self.step = 0
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
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✅ Chrome started!")

    def screenshot(self, name):
        self.step += 1
        try:
            filename = f"bot{self.bot_id}_{self.step:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
        except:
            pass

    def load_logins(self):
        try:
            with open('logins.csv', 'r') as f:
                reader = csv.reader(f)
                next(reader)
                self.logins = []
                for row in reader:
                    if len(row) >= 2:
                        self.logins.append({'phone': row[0].strip(), 'password': row[1].strip()})
            print(f"📋 Loaded {len(self.logins)} logins")
        except:
            print("❌ No logins.csv")
            sys.exit(1)

    def type_text(self, element, text):
        """Type text ONCE - guaranteed"""
        element.click()
        time.sleep(0.1)
        element.clear()
        time.sleep(0.1)
        element.send_keys(text)
        time.sleep(0.1)

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")
            
            # --- PHONE ---
            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            self.type_text(phone_field, phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")
            
            # --- PASSWORD (ONCE) ---
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
            self.type_text(password_field, password)
            print(f"   ✅ Password: {password[:3]}***")
            self.screenshot("03_password_entered")
            
            # --- LOGIN BUTTON ---
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in now')]"))
            )
            login_btn.click()
            print(f"   ✅ Clicked login")
            self.screenshot("04_after_login_click")
            
            time.sleep(5)
            self.screenshot("05_after_login_wait")
            
            # --- CHECK SUCCESS ---
            page = self.driver.page_source.lower()
            if "important notice" in page or "cooperative wealth zone" in page:
                print(f"   ✅✅✅ LOGIN SUCCESS!")
                self.screenshot("06_login_success")
                return True
            else:
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
        print("="*50)

        for i, login_data in enumerate(self.logins):
            print(f"\n📱 Account {i+1}/{len(self.logins)}")
            if self.login(login_data['phone'], login_data['password']):
                self.logout()
            time.sleep(2)

        self.driver.quit()
        print("\n✅ Done!")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = NRCBot(bot_id=bot_id)
    bot.run()