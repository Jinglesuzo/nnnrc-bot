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
    def __init__(self):
        self.step = 0
        self.load_logins()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        print("🤖 Starting Chrome...")
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
            filename = f"bot_{self.step:03d}_{name}.png"
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
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip()
                        })
            print(f"📋 Loaded {len(self.logins)} login(s)")
        except:
            print("❌ No logins.csv found")
            self.logins = [{'phone': '08057536473', 'password': 'people56'}]

    def type_text(self, element, text):
        """Type text ONCE"""
        element.click()
        time.sleep(0.1)
        element.clear()
        time.sleep(0.1)
        element.send_keys(text)
        time.sleep(0.1)

    def click_element(self, element):
        """Click using JavaScript (most reliable)"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", element)

    def find_login_button(self):
        """Find the green 'Log in now' button"""
        print("   🔍 Looking for login button...")
        
        # Try multiple ways to find it
        try:
            # By exact text
            btn = self.driver.find_element(By.XPATH, "//button[text()='Log in now']")
            print("   ✅ Found 'Log in now'")
            return btn
        except:
            pass
        
        try:
            # By contains text
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            print("   ✅ Found 'Log in now' (contains)")
            return btn
        except:
            pass
        
        try:
            # By type submit
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            print("   ✅ Found submit button")
            return btn
        except:
            pass
        
        try:
            # By CSS selector - any button with green class
            btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='green'], button[class*='login'], button[class*='primary']")
            print("   ✅ Found button by class")
            return btn
        except:
            pass
        
        try:
            # Any visible button with 'log' or 'in' in text
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

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        
        try:
            # Load login page
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
            
            # --- PASSWORD ---
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
            self.type_text(password_field, password)
            print(f"   ✅ Password: {password[:3]}***")
            self.screenshot("03_password_entered")
            
            # --- FIND AND CLICK GREEN LOGIN BUTTON ---
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print(f"   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print(f"   ❌ Login button not found")
                self.screenshot("04_login_button_not_found")
                return False
            
            # Wait for response
            time.sleep(5)
            self.screenshot("05_after_login_wait")
            
            # --- CHECK SUCCESS ---
            page_source = self.driver.page_source.lower()
            
            if "important notice" in page_source:
                print(f"   ✅✅✅ LOGIN SUCCESS! (Important Notice)")
                self.screenshot("06_login_success")
                return True
            
            if "cooperative wealth zone" in page_source:
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
        print("🤖 ONE BOT - LOGIN TEST")
        print("="*50)

        for login_data in self.logins:
            phone = login_data['phone']
            password = login_data['password']
            print(f"\n📱 Account: {phone}")
            
            if self.login(phone, password):
                self.logout()
            else:
                print(f"   ❌ Login FAILED for {phone}")

        self.driver.quit()
        print("\n✅ Done!")

if __name__ == "__main__":
    bot = NRCBot()
    bot.run()