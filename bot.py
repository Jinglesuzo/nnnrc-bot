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

    def type_text(self, element, text):
        element.click()
        element.clear()
        time.sleep(0.1)
        for char in text:
            element.send_keys(char)
            time.sleep(0.05)
        time.sleep(0.1)

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
    # WITHDRAWAL - WITH SUBMIT BUTTON FIX
    # ============================================

    def click_green_submit_button(self):
        """Click the green Submit button using multiple methods"""
        print("   🔘 Looking for green Submit button...")
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

        # Method 4: By CSS class (green, submit, primary)
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

        # Method 6: Scan all buttons for "Submit" or "Confirm"
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

        # Method 7: ActionChains
        if not submit_clicked:
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                actions = ActionChains(self.driver)
                actions.move_to_element(submit_btn).click().perform()
                submit_clicked = True
                print("   ✅ Clicked Submit (ActionChains)")
            except:
                pass

        if submit_clicked:
            time.sleep(2)
            self.screenshot("17_submit_clicked")
            return True
        else:
            print("   ❌ Could not find Submit button")
            self.screenshot("17_submit_not_found")
            return False

    def perform_withdrawal(self, login_data):
        print(f"\n💸 Starting withdrawal process for {login_data['phone']}")
        fund_password = login_data['fund_password']
        bank_name = login_data['bank_name']

        # Step 1: Go to withdrawal page
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(3)
            self.screenshot("10_withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False

        self.save_html("withdrawal_page")

        # Step 2: Click the "Withdrawal Method" custom UI
        print("   🔘 Looking for withdrawal method field...")
        method_clicked = False
        method_selectors = [
            "//*[contains(text(), 'Select withdrawal method')]",
            "//*[contains(text(), 'Withdrawal method')]",
            "//*[contains(@class, 'withdrawal-method')]",
            "//*[contains(@class, 'withdraw-method')]",
            "//*[contains(@class, 'method-select')]",
            "//div[contains(@class, 'dropdown')]",
            "//*[contains(@class, 'select')]",
            "//*[contains(@placeholder, 'Withdrawal method')]"
        ]

        method_field = None
        for selector in method_selectors:
            try:
                method_field = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if method_field:
                    method_clicked = True
                    print(f"   ✅ Found method field: {selector}")
                    break
            except:
                continue

        if method_field:
            self.click_element(method_field)
            time.sleep(1.5)
            self.screenshot("11_method_clicked")
            print("   ✅ Clicked withdrawal method field")
        else:
            try:
                label = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal Method')]")
                if label:
                    self.click_element(label)
                    time.sleep(1.5)
                    method_clicked = True
                    print("   ✅ Clicked 'Withdrawal Method' label")
                    self.screenshot("11_method_clicked")
            except:
                pass

        if not method_clicked:
            try:
                divs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'method')]")
                for div in divs:
                    if div.is_displayed() and 'method' in div.text.lower():
                        self.click_element(div)
                        method_clicked = True
                        print("   ✅ Clicked method div")
                        time.sleep(1.5)
                        self.screenshot("11_method_clicked")
                        break
            except:
                pass

        if not method_clicked:
            print("   ❌ Could not find withdrawal method field")
            self.screenshot("11_method_not_found")
            return False

        # Step 3: Select OPAY
        print(f"   🔘 Looking for {bank_name}...")
        bank_clicked = False
        bank_selectors = [
            f"//*[contains(text(), '{bank_name}')]",
            f"//*[contains(text(), '{bank_name.upper()}')]",
            f"//*[contains(text(), '{bank_name.lower()}')]",
            "//li[contains(text(), 'OPAY')]",
            "//div[contains(text(), 'OPAY')]",
            "//span[contains(text(), 'OPAY')]",
            "//button[contains(text(), 'OPAY')]"
        ]

        for selector in bank_selectors:
            try:
                bank_element = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if bank_element:
                    self.click_element(bank_element)
                    bank_clicked = True
                    print(f"   ✅ Selected {bank_name}")
                    time.sleep(1)
                    self.screenshot("12_bank_selected")
                    break
            except:
                continue

        if not bank_clicked:
            try:
                all_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'OPAY')]")
                for element in all_elements:
                    if element.is_displayed():
                        self.click_element(element)
                        bank_clicked = True
                        print("   ✅ Selected OPAY (by scanning)")
                        time.sleep(1)
                        self.screenshot("12_bank_selected")
                        break
            except:
                pass

        if not bank_clicked:
            print(f"   ❌ Could not select {bank_name}")
            self.screenshot("12_bank_not_found")
            return False

        # Step 4: Click Confirm button if present
        try:
            confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
            if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                self.click_element(confirm_btn)
                print("   ✅ Clicked Confirm")
                time.sleep(1)
                self.screenshot("13_confirm_clicked")
        except:
            print("   ℹ️ No Confirm button needed")

        # Step 5: Enter fund password
        print("   🔘 Looking for fund password field...")
        fund_password_field = None
        fund_selectors = [
            "//input[@placeholder='Please input fund password']",
            "//input[contains(@placeholder, 'fund')]",
            "//input[@type='password']"
        ]

        for selector in fund_selectors:
            try:
                fund_password_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if fund_password_field:
                    print(f"   ✅ Found fund password field")
                    break
            except:
                continue

        if fund_password_field:
            self.type_text(fund_password_field, fund_password)
            print(f"   🔑 Entered fund password: {fund_password}")
            self.screenshot("14_fund_password_entered")
        else:
            print("   ❌ Could not find fund password field")
            self.screenshot("14_fund_password_not_found")
            return False

        # Step 6: Enter withdrawal amount
        print("   🔘 Looking for amount field...")
        amount_field = None
        amount_selectors = [
            "//input[@placeholder='Withdrawal amount']",
            "//input[contains(@placeholder, 'amount')]",
            "//input[contains(@name, 'amount')]"
        ]

        for selector in amount_selectors:
            try:
                amount_field = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if amount_field:
                    print(f"   ✅ Found amount field")
                    break
            except:
                continue

        if amount_field:
            amount = "1800"
            self.type_text(amount_field, amount)
            print(f"   💰 Entered amount: {amount}")
            self.screenshot("15_amount_entered")
        else:
            print("   ❌ Could not find amount field")
            self.screenshot("15_amount_not_found")
            return False

        # Step 7: Click SUBMIT - USING ALL METHODS
        print("   🔘 Clicking green Submit button...")
        submit_clicked = self.click_green_submit_button()

        if submit_clicked:
            print("   ✅ Withdrawal submitted successfully!")
            self.screenshot("18_withdrawal_complete")
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