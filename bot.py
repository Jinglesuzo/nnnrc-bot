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

    def save_html(self, name):
        try:
            filename = f"bot{self.bot_id}_{name}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"   💾 Saved HTML: {filename}")
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
            try:
                self.driver.execute_script("arguments[0].value = '';", element)
            except:
                pass
        
        for char in text:
            element.send_keys(char)
            time.sleep(0.05)
        time.sleep(0.1)

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
    # WITHDRAWAL - FULL PROCESS
    # ============================================

    def select_withdrawal_method(self, bank_name):
        """Select the bank for withdrawal"""
        print(f"   🔘 Looking for withdrawal method field...")
        
        # Click the withdrawal method field
        method_selectors = [
            "//*[contains(text(), 'Select withdrawal method')]",
            "//*[contains(text(), 'Withdrawal method')]",
            "//*[contains(@class, 'withdrawal-method')]",
            "//*[contains(@class, 'method-select')]",
            "//div[contains(@class, 'dropdown')]"
        ]
        
        method_field = None
        for selector in method_selectors:
            try:
                method_field = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if method_field:
                    print(f"   ✅ Found method field")
                    break
            except:
                continue
        
        if method_field:
            self.click_element(method_field)
            time.sleep(1.5)
            self.screenshot("method_clicked")
            print("   ✅ Clicked withdrawal method")
        else:
            print("   ❌ Could not find withdrawal method")
            return False

        # Select OPAY
        print(f"   🔘 Looking for {bank_name}...")
        bank_selectors = [
            f"//*[contains(text(), '{bank_name}')]",
            f"//*[contains(text(), '{bank_name.upper()}')]",
            "//li[contains(text(), 'OPAY')]",
            "//div[contains(text(), 'OPAY')]",
            "//span[contains(text(), 'OPAY')]"
        ]
        
        for selector in bank_selectors:
            try:
                bank_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if bank_element:
                    self.click_element(bank_element)
                    print(f"   ✅ Selected {bank_name}")
                    time.sleep(1)
                    self.screenshot("bank_selected")
                    return True
            except:
                continue
        
        print(f"   ❌ Could not select {bank_name}")
        return False

    def enter_fund_password(self, fund_password):
        """Enter the fund password"""
        print("   🔘 Looking for fund password field...")
        fund_selectors = [
            "//input[@placeholder='Please input fund password']",
            "//input[contains(@placeholder, 'fund')]",
            "//input[@type='password']"
        ]
        
        fund_field = None
        for selector in fund_selectors:
            try:
                fund_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if fund_field:
                    print("   ✅ Found fund password field")
                    break
            except:
                continue
        
        if fund_field:
            self.type_text(fund_field, fund_password)
            print(f"   🔑 Entered fund password: {fund_password}")
            self.screenshot("fund_password_entered")
            return True
        else:
            print("   ❌ Could not find fund password field")
            return False

    def click_submit_button(self):
        """Click the green Submit button"""
        print("   🔘 Clicking Submit button...")
        
        submit_selectors = [
            "//button[text()='Submit']",
            "//button[contains(text(), 'Submit')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'submit')]",
            "//button[contains(@class, 'green')]",
            "//button[contains(@class, 'primary')]",
            "//button[contains(@class, 'btn')]"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if submit_btn.is_displayed() and submit_btn.is_enabled():
                    self.click_element(submit_btn)
                    print("   ✅ Clicked Submit")
                    time.sleep(2)
                    self.screenshot("submit_clicked")
                    return True
            except:
                continue
        
        # JavaScript fallback
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", submit_btn)
            print("   ✅ Clicked Submit (JavaScript)")
            time.sleep(2)
            self.screenshot("submit_clicked")
            return True
        except:
            pass
        
        print("   ❌ Could not find Submit button")
        return False

    def perform_withdrawal(self, login_data):
        print(f"\n💸 Processing withdrawal for {login_data['phone']}")
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

        # Step 2: Select withdrawal method (OPAY)
        if not self.select_withdrawal_method(bank_name):
            return False

        # Step 3: Enter fund password
        if not self.enter_fund_password(fund_password):
            return False

        # Step 4: Click Submit
        if self.click_submit_button():
            print("   ✅ Withdrawal completed successfully!")
            return True
        else:
            print("   ❌ Could not complete withdrawal")
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