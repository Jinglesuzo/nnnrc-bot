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
        self.load_logins()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        print(f"🤖 Bot {self.bot_id} Starting...")
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=options)
        print("✅ Chrome started!")

    def load_logins(self):
        try:
            with open('logins.csv', 'r') as f:
                reader = csv.reader(f)
                next(reader)
                self.logins = list(reader)
            print(f"📋 Loaded {len(self.logins)} logins")
        except:
            print("❌ No logins.csv found")
            sys.exit(1)

    def type_text(self, element, text):
        element.click()
        element.clear()
        time.sleep(0.1)
        for char in text:
            element.send_keys(char)
            time.sleep(0.04)

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
            
            # Phone
            phone_field = self.wait_and_find(By.XPATH, "//input[@placeholder='Please enter your phone number']")
            if not phone_field:
                phone_field = self.wait_and_find(By.CSS_SELECTOR, "input[type='tel']")
            if phone_field:
                self.type_text(phone_field, phone)
                print(f"   ✅ Phone: {phone}")
            
            # Password
            password_field = self.wait_and_find(By.XPATH, "//input[@placeholder='Please enter login password']")
            if not password_field:
                password_field = self.wait_and_find(By.CSS_SELECTOR, "input[type='password']")
            if password_field:
                self.type_text(password_field, password)
                print(f"   ✅ Password: {password[:3]}***")
            
            # Login button
            login_btn = self.wait_and_find(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if not login_btn:
                login_btn = self.wait_and_find(By.CSS_SELECTOR, "button[type='submit']")
            if login_btn:
                login_btn.click()
                print(f"   ✅ Clicked login")
            
            time.sleep(4)
            
            # Check success
            page = self.driver.page_source.lower()
            if "important notice" in page or "cooperative wealth zone" in page:
                print(f"   ✅✅✅ LOGIN SUCCESS!")
                return True
            
            print(f"   ❌ Login failed")
            return False
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    def logout(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print("   ✅ Logged out")
        except:
            pass

    def run(self):
        print("="*50)
        print(f"🤖 BOT {self.bot_id} STARTING")
        print("="*50)

        for i, row in enumerate(self.logins):
            if len(row) >= 2:
                phone = row[0].strip()
                password = row[1].strip()
                print(f"\n📱 Account {i+1}/{len(self.logins)}")
                if self.login(phone, password):
                    self.logout()
                time.sleep(2)

        self.driver.quit()
        print("\n✅ Done!")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = NRCBot(bot_id=bot_id)
    bot.run()