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
        except Exception as e:
            print(f"❌ Error loading logins.csv: {e}")
            self.logins = [{'phone': '08057536473', 'password': 'people56'}]

    def type_text(self, element, text):
        """Type text ONCE - exactly as provided"""
        element.click()
        time.sleep(0.2)
        element.clear()
        time.sleep(0.2)
        
        # Type each character one by one (more reliable)
        for char in text:
            element.send_keys(char)
            time.sleep(0.05)
        
        # Verify the text was entered
        entered = element.get_attribute('value')
        print(f"   📝 Typed: {entered} (length: {len(entered)})")
        
        # Check if password length is 7 (just222)
        if len(entered) == 7:
            print(f"   ✅ Password is 7 characters - ready to login!")
        
        time.sleep(0.2)

    def click_element(self, element):
        """Click using JavaScript"""
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", element)

    def find_login_button(self):
        """Find the green 'Log in now' button"""
        print("   🔍 Looking for login button...")
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[text()='Log in now']")
            print("   ✅ Found 'Log in now'")
            return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            print("   ✅ Found 'Log in now' (contains)")
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
            btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='green'], button[class*='login']")
            print("   ✅ Found button by class")
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

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        print(f"   📝 Password: {password} (length: {len(password)})")
        
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
            print(f"   ✅ Password entered: {password[:3]}***")
            self.screenshot("03_password_entered")
            
            # --- WAIT FOR PASSWORD TO BE FULLY TYPED ---
            time.sleep(1)
            
            # --- FIND AND CLICK LOGIN BUTTON ---
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print(f"   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print(f"   ❌ Login button not found")
                self.screenshot("04_login_button_not_found")
                return False
            
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
            print(f"📝 Password length: {len(password)}")
            
            if self.login(phone, password):
                self.logout()
                print(f"   ✅ SUCCESS for {phone}")
            else:
                print(f"   ❌ FAILED for {phone}")
            
            time.sleep(2)

        self.driver.quit()
        print("\n✅ Done!")

if __name__ == "__main__":
    bot = NRCBot()
    bot.run()