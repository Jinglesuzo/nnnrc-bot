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

class WithdrawalBot:
    def __init__(self, bot_id=1):
        self.bot_id = bot_id
        self.step = 0
        self.logged_in_accounts = []
        self.load_logins()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        print(f"🤖 Bot {self.bot_id} Starting Chrome...")
        try:
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")
        except:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")

    def screenshot(self, name):
        self.step += 1
        try:
            filename = f"bot{self.bot_id}_{self.step:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
        except:
            pass

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

    def type_text(self, element, text):
        try:
            element.click()
            time.sleep(0.1)
            element.clear()
            time.sleep(0.1)
        except:
            self.driver.execute_script("arguments[0].value = '';", element)
        
        for char in text:
            element.send_keys(char)
            time.sleep(0.05)

    def load_logins(self):
        try:
            with open('logins.csv', 'r') as f:
                reader = csv.reader(f)
                next(reader)
                self.logins = []
                for row in reader:
                    if len(row) >= 6:
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip(),
                            'real_name': row[2].strip(),
                            'bank_name': row[3].strip(),
                            'bank_account': row[4].strip(),
                            'fund_password': row[5].strip()
                        })
                    elif len(row) >= 2:
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip(),
                            'real_name': 'John Penn',
                            'bank_name': 'OPAY',
                            'bank_account': '9074331299',
                            'fund_password': '3333'
                        })
            print(f"📋 Bot {self.bot_id} Loaded {len(self.logins)} login(s)")
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Error loading logins.csv: {e}")
            self.logins = [{'phone': '08057536473', 'password': 'people56', 'real_name': 'John Penn', 'bank_name': 'OPAY', 'bank_account': '9074331299', 'fund_password': '3333'}]

    def find_login_button(self):
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            return btn
        except:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            return btn

    # ============================================
    # LOGIN
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")

            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
            password_field.clear()
            password_field.send_keys(password)
            print("   ✅ Password entered")
            self.screenshot("03_password_entered")

            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print("   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print("   ❌ Login button not found")
                return False

            time.sleep(5)
            self.screenshot("05_after_login_wait")

            page_source = self.driver.page_source.lower()
            if "important notice" in page_source or "cooperative wealth zone" in page_source:
                print("   ✅ Login success!")
                return True
            else:
                print("   ❌ Login failed")
                return False
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

    # ============================================
    # WITHDRAWAL - SIMPLE 3 STEPS
    # ============================================

    def perform_withdrawal(self, login_data):
        print(f"\n💸 Withdrawal for {login_data['phone']}")
        bank_name = login_data['bank_name']
        fund_password = login_data['fund_password']

        # Step 1: Go to withdrawal page
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(3)
            self.screenshot("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        # ============================================
        # STEP 1: SELECT BANK (OPAY)
        # ============================================
        print("   🔘 Step 1: Selecting bank...")
        
        # Click the withdrawal method field
        try:
            method_field = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Select withdrawal method')]"))
            )
            self.click_element(method_field)
            time.sleep(1)
            print("   ✅ Clicked withdrawal method")
        except:
            try:
                method_field = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal method')]")
                self.click_element(method_field)
                time.sleep(1)
                print("   ✅ Clicked withdrawal method")
            except:
                print("   ❌ Could not find withdrawal method")
                return False

        # Click OPAY
        try:
            opay = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{bank_name}')]"))
            )
            self.click_element(opay)
            time.sleep(1)
            print(f"   ✅ Selected {bank_name}")
            self.screenshot("bank_selected")
        except:
            try:
                opay = self.driver.find_element(By.XPATH, "//*[contains(text(), 'OPAY')]")
                self.click_element(opay)
                time.sleep(1)
                print(f"   ✅ Selected {bank_name}")
                self.screenshot("bank_selected")
            except:
                print(f"   ❌ Could not select {bank_name}")
                return False

        # ============================================
        # STEP 2: ENTER FUND PASSWORD
        # ============================================
        print("   🔘 Step 2: Entering fund password...")
        
        try:
            fund_field = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please input fund password']"))
            )
            self.type_text(fund_field, fund_password)
            print(f"   ✅ Entered fund password: {fund_password}")
            self.screenshot("fund_password_entered")
        except:
            try:
                fund_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
                self.type_text(fund_field, fund_password)
                print(f"   ✅ Entered fund password: {fund_password}")
                self.screenshot("fund_password_entered")
            except:
                print("   ❌ Could not find fund password field")
                return False

        # ============================================
        # STEP 3: CLICK SUBMIT
        # ============================================
        print("   🔘 Step 3: Clicking Submit...")
        
        try:
            submit_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
            )
            self.click_element(submit_btn)
            print("   ✅ Clicked Submit")
            time.sleep(2)
            self.screenshot("submit_clicked")
            print("   ✅ Withdrawal completed!")
            return True
        except:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit")
                time.sleep(2)
                self.screenshot("submit_clicked")
                print("   ✅ Withdrawal completed!")
                return True
            except:
                print("   ❌ Could not find Submit button")
                return False

    # ============================================
    # RUN
    # ============================================

    def run(self):
        print("="*50)
        print(f"🤖 WITHDRAWAL BOT {self.bot_id} STARTING")
        print("="*50)

        for login_data in self.logins:
            phone = login_data['phone']
            password = login_data['password']

            print(f"\n📱 Account: {phone}")

            if not self.login(phone, password):
                print(f"   ❌ Login failed for {phone}")
                continue

            self.perform_withdrawal(login_data)

            time.sleep(2)

        self.driver.quit()
        print(f"\n✅ Withdrawal Bot {self.bot_id} Done!")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = WithdrawalBot(bot_id=bot_id)
    bot.run()