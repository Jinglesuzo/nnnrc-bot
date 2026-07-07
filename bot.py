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
        print("   🔍 Looking for login button...")
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            print("   ✅ Found 'Log in now'")
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

            password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter login password']")
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
                self.logged_in_accounts.append(phone)
                return True
            else:
                print("   ❌ Login failed")
                return False
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False

    # ============================================
    # CLICK SUBMIT BUTTON ONLY
    # ============================================

    def click_submit_button(self):
        """Click the green Submit button using multiple methods"""
        print("   🔘 Looking for Submit button...")
        submit_clicked = False

        # Method 1: By text "Submit"
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[text()='Submit']")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                self.click_element(submit_btn)
                submit_clicked = True
                print("   ✅ Clicked Submit (by exact text)")
        except:
            pass

        # Method 2: By contains text "Submit"
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    self.click_element(submit_btn)
                    submit_clicked = True
                    print("   ✅ Clicked Submit (by contains text)")
            except:
                pass

        # Method 3: By type="submit"
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    self.click_element(submit_btn)
                    submit_clicked = True
                    print("   ✅ Clicked Submit (by type)")
            except:
                pass

        # Method 4: By CSS class
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='submit'], button[class*='green'], button[class*='primary'], button[class*='btn']")
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    self.click_element(submit_btn)
                    submit_clicked = True
                    print("   ✅ Clicked Submit (by class)")
            except:
                pass

        # Method 5: JavaScript click
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", submit_btn)
                submit_clicked = True
                print("   ✅ Clicked Submit (JavaScript)")
            except:
                pass

        # Method 6: Scan all buttons
        if not submit_clicked:
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        text = btn.text.lower()
                        if 'submit' in text or 'confirm' in text:
                            self.click_element(btn)
                            submit_clicked = True
                            print(f"   ✅ Clicked button: '{btn.text}' (by scanning)")
                            break
            except:
                pass

        if submit_clicked:
            time.sleep(2)
            self.screenshot("submit_clicked")
            return True
        else:
            print("   ❌ Could not find Submit button")
            self.screenshot("submit_not_found")
            return False

    # ============================================
    # WITHDRAWAL - GO TO PAGE AND CLICK SUBMIT
    # ============================================

    def perform_withdrawal(self, login_data):
        print(f"\n💸 Processing withdrawal for {login_data['phone']}")

        # Go to withdrawal page
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(3)
            self.screenshot("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        # Click Submit button
        if self.click_submit_button():
            print("   ✅ Withdrawal submitted successfully!")
            return True
        else:
            print("   ❌ Could not submit withdrawal")
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