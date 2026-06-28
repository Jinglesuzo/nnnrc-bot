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

class NigerianAccountBot:
    def __init__(self):
        self.phone = "08012345678"
        self.password = "123456"
        self.codes_to_test = ['0041140', '0041141', '0041142', '0041143', '0041144', '0041145']
        self.created_accounts = []
        
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
            print(f"❌ Failed to start Chrome: {e}")
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

    def fill_form(self):
        try:
            wait = WebDriverWait(self.driver, 10)
            
            print(f"\n📱 Phone: {self.phone}")
            print(f"🔒 Password: {self.password}")

            phone_field = wait.until(EC.presence_of_element_located((By.XPATH, self.selectors['phone'])))
            self.clear_field(phone_field)
            phone_field.send_keys(self.phone)

            password_field = self.driver.find_element(By.XPATH, self.selectors['password'])
            self.clear_field(password_field)
            password_field.send_keys(self.password)

            confirm_field = self.driver.find_element(By.XPATH, self.selectors['confirm_password'])
            self.clear_field(confirm_field)
            confirm_field.send_keys(self.password)

            print("✅ Form filled!")
            return True
        except Exception as e:
            print(f"❌ Failed to fill form: {e}")
            return False

    def update_invitation_code(self, code):
        try:
            code_field = self.driver.find_element(By.XPATH, self.selectors['invitation_code'])
            self.clear_field(code_field)
            code_field.send_keys(code)
            print(f"   ✅ Code: {code}")
            return True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False

    def click_register(self):
        try:
            button = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Register now')]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
            time.sleep(0.2)
            self.driver.execute_script("arguments[0].click();", button)
            print("   ✅ Clicked Register!")
            return True
        except:
            try:
                button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Register')]")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.2)
                self.driver.execute_script("arguments[0].click();", button)
                print("   ✅ Clicked Register!")
                return True
            except:
                try:
                    form = self.driver.find_element(By.TAG_NAME, "form")
                    self.driver.execute_script("arguments[0].submit();", form)
                    print("   ✅ Submitted form!")
                    return True
                except:
                    print("   ❌ Could not click Register!")
                    return False

    def check_success(self):
        try:
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            if "please upgrade your level" in page_source or "upgrade your level" in page_source:
                return False
            
            success_words = [
                "cooperative wealth zone",
                "deposit principal",
                "invite newcomers",
                "wealth center",
                "wish book",
                "surprise code",
                "benefit savings",
                "dashboard",
                "home",
                "welcome",
                "success"
            ]
            
            for word in success_words:
                if word in page_source:
                    return True
            
            if "dashboard" in current_url or "home" in current_url:
                return True
            
            return False
        except:
            return False

    def logout(self):
        try:
            self.driver.delete_all_cookies()
            self.driver.get("https://nnnrc.com/#/register")
            time.sleep(2)
            print("   ✅ Logged out")
            return True
        except:
            return False

    def run(self):
        print("="*60)
        print("🇳🇬 NIGERIAN ACCOUNT CREATION BOT - TEST")
        print(f"Codes: {', '.join(self.codes_to_test)}")
        print("="*60)
        
        self.driver.get("https://nnnrc.com/#/register")
        print("✅ Website loaded")
        time.sleep(3)
        
        if not self.fill_form():
            self.driver.quit()
            return
        
        for code in self.codes_to_test:
            print(f"\n--- Testing Code: {code} ---")
            
            if not self.update_invitation_code(code):
                continue
            
            if not self.click_register():
                continue
            
            time.sleep(3)
            
            if self.check_success():
                print(f"\n✅✅✅ ACCOUNT CREATED! Code: {code}")
                account_info = {
                    'phone': self.phone,
                    'password': self.password,
                    'invitation_code': code
                }
                self.created_accounts.append(account_info)
                self.save_account(account_info)
                self.logout()
                break
            else:
                print(f"   ❌ Code {code} failed")
        
        print("\n" + "="*60)
        print("📊 SUMMARY")
        if self.created_accounts:
            print(f"✅ SUCCESS! Account created with code: {self.created_accounts[0]['invitation_code']}")
            print(f"   Phone: {self.phone}")
            print(f"   Password: {self.password}")
        else:
            print("❌ No account created")
        print("="*60)
        
        self.driver.quit()

    def save_account(self, account):
        file_exists = os.path.isfile('accounts.csv')
        with open('accounts.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Phone', 'Password', 'Invitation Code', 'Timestamp'])
            writer.writerow([
                account['phone'],
                account['password'],
                account['invitation_code'],
                time.ctime()
            ])
        print(f"   💾 Saved to accounts.csv")

# ============================================
# RUN THE TEST
# ============================================

bot = NigerianAccountBot()
bot.run()