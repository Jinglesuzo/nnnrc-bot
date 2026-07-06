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
        except:
            self.logins = [{'phone': '08053655423', 'password': 'high555', 'real_name': 'John Penn', 'bank_name': 'OPAY', 'bank_account': '9074331299', 'fund_password': '3333'}]

    def type_text(self, element, text):
        element.click()
        element.clear()
        time.sleep(0.1)
        element.send_keys(text)
        time.sleep(0.1)

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

    # ============================================
    # LOGIN BUTTON - ALL METHODS
    # ============================================

    def click_login_button(self):
        """Click login button using EVERY possible method"""
        print("   🔘 Clicking login button...")
        
        # Method 1: Find by text "Log in now" and click
        try:
            btn = self.driver.find_element(By.XPATH, "//button[text()='Log in now']")
            if btn.is_displayed():
                self.click_element(btn)
                print("   ✅ Clicked by exact text: 'Log in now'")
                return True
        except:
            pass
        
        # Method 2: Find by contains text "Log in now"
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if btn.is_displayed():
                self.click_element(btn)
                print("   ✅ Clicked by contains text: 'Log in now'")
                return True
        except:
            pass
        
        # Method 3: Find by text "Login"
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            if btn.is_displayed():
                self.click_element(btn)
                print("   ✅ Clicked by contains text: 'Login'")
                return True
        except:
            pass
        
        # Method 4: Find by type="submit"
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if btn.is_displayed():
                self.click_element(btn)
                print("   ✅ Clicked by type='submit'")
                return True
        except:
            pass
        
        # Method 5: Find by CSS class
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='login'], button[class*='green'], button[class*='primary'], button[class*='submit']")
            if btn.is_displayed():
                self.click_element(btn)
                print("   ✅ Clicked by CSS class")
                return True
        except:
            pass
        
        # Method 6: Find any button with "log" in text
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    text = btn.text.lower()
                    if 'log' in text or 'in' in text:
                        self.click_element(btn)
                        print(f"   ✅ Clicked button by text: '{btn.text}'")
                        return True
        except:
            pass
        
        # Method 7: JavaScript click directly
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            self.driver.execute_script("arguments[0].click();", btn)
            print("   ✅ Clicked with JavaScript")
            return True
        except:
            pass
        
        # Method 8: Submit the form
        try:
            form = self.driver.find_element(By.TAG_NAME, "form")
            self.driver.execute_script("arguments[0].submit();", form)
            print("   ✅ Submitted form directly")
            return True
        except:
            pass
        
        # Method 9: Click using ActionChains
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            actions = ActionChains(self.driver)
            actions.move_to_element(btn).click().perform()
            print("   ✅ Clicked with ActionChains")
            return True
        except:
            pass
        
        print("   ❌ Could not click login button")
        return False

    # ============================================
    # LOGIN
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")
            
            # Phone
            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            self.type_text(phone_field, phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")
            
            # Password
            password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter login password']")
            self.type_text(password_field, password)
            print(f"   ✅ Password entered")
            self.screenshot("03_password_entered")
            
            # Click login button (ALL METHODS)
            if not self.click_login_button():
                print("   ❌ Could not click login button")
                self.screenshot("04_login_button_failed")
                return False
            
            time.sleep(5)
            self.screenshot("05_after_login_wait")
            
            # Check result
            page_source = self.driver.page_source.lower()
            
            if "important notice" in page_source or "cooperative wealth zone" in page_source:
                print(f"   ✅ Login success!")
                self.logged_in_accounts.append(phone)
                return True
            
            if "invalid" in page_source or "incorrect" in page_source:
                print(f"   ❌ Invalid credentials - wrong password")
                self.screenshot("06_invalid_credentials")
                return False
            
            if "log in now" in page_source:
                print(f"   ❌ Still on login page - login failed")
                self.screenshot("06_still_on_login")
                return False
            
            print(f"   ❌ Login failed - unknown reason")
            self.screenshot("06_login_failed")
            return False
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    # ============================================
    # POPUP REMOVAL
    # ============================================

    def remove_important_notice(self):
        try:
            notice = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Important Notice')]")
            if notice.is_displayed():
                print("   📋 Found Important Notice")
                self.screenshot("important_notice_found")
                
                try:
                    news_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'NEWS')] | //button[contains(text(), 'NEWS')]")
                    if news_btn.is_displayed() and news_btn.is_enabled():
                        self.click_element(news_btn)
                        print("   📰 Clicked NEWS button")
                        time.sleep(2)
                        self.screenshot("after_news_click")
                        
                        try:
                            close_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Got it')] | //button[contains(text(), 'OK')] | //*[contains(@class, 'modal-close')] | //*[text()='×']")
                            if close_btn.is_displayed():
                                self.click_element(close_btn)
                                print("   🚫 Closed Welcome popup")
                                time.sleep(1)
                        except:
                            pass
                        
                        try:
                            close_btns = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'close')] | //*[text()='×']")
                            for btn in close_btns:
                                if btn.is_displayed() and btn.is_enabled():
                                    self.click_element(btn)
                                    time.sleep(0.3)
                        except:
                            pass
                        
                        self.screenshot("popups_removed")
                        return True
                except:
                    print("   ⚠️ NEWS button not found")
                    return False
        except:
            print("   ℹ️ No Important Notice found")
            return True
        return True

    # ============================================
    # TASKS
    # ============================================

    def do_tasks(self):
        print("   📋 Starting tasks...")
        
        try:
            task_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Task')]")
            self.click_element(task_tab)
            time.sleep(2)
            self.screenshot("tasks_page")
        except:
            print("   ⚠️ Could not find Task tab")
        
        total = 0
        for i in range(6):
            try:
                read_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'read')]")
                if read_btn.is_displayed() and read_btn.is_enabled():
                    self.click_element(read_btn)
                    total += 1
                    print(f"   📖 Task {total} started")
                    time.sleep(20)
                    print(f"   ✅ Task {total} done")
            except:
                break
        
        print(f"   ✅ Completed {total} tasks")
        self.screenshot("tasks_completed")
        return total

    # ============================================
    # WITHDRAWAL
    # ============================================

    def complete_withdrawal(self):
        print(f"   💰 Processing withdrawal...")
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            self.screenshot("withdrawal_page")
            
            confirm_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm')]"))
            )
            confirm_btn.click()
            print("   ✅ Clicked Confirm")
            time.sleep(2)
            self.screenshot("confirm_clicked")
            return True
        except:
            print("   ❌ Could not complete withdrawal")
            return False

    # ============================================
    # FUND PASSWORD
    # ============================================

    def set_fund_password(self, fund_password):
        print("   🔑 Setting fund password...")
        try:
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(2)
            self.screenshot("user_info_page")
            
            fund_pw_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Fund password')]"))
            )
            fund_pw_btn.click()
            time.sleep(1)
            self.screenshot("fund_password_clicked")
            
            new_pw = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the new funds password']"))
            )
            new_pw.clear()
            new_pw.send_keys(fund_password)
            
            confirm_pw = self.driver.find_element(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
            confirm_pw.clear()
            confirm_pw.send_keys(fund_password)
            self.screenshot("fund_password_entered")
            
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
            )
            submit_btn.click()
            print("   ✅ Fund password set")
            time.sleep(2)
            self.screenshot("fund_password_submitted")
            return True
        except Exception as e:
            print(f"   ❌ Could not set fund password: {e}")
            return False

    # ============================================
    # ADD BANK ACCOUNT
    # ============================================

    def add_bank_account(self, login_data):
        print("   🏦 Adding bank account...")
        try:
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(2)
            self.screenshot("bank_page")
            
            add_bank = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Add a bank account')]"))
            )
            add_bank.click()
            time.sleep(1)
            self.screenshot("add_bank_clicked")
            
            auth_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Authenticate now')]"))
            )
            auth_btn.click()
            time.sleep(1)
            self.screenshot("authenticate_clicked")
            
            name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter a real name']"))
            )
            name_input.clear()
            name_input.send_keys(login_data['real_name'])
            print(f"   👤 Entered name: {login_data['real_name']}")
            self.screenshot("name_entered")
            
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
            )
            submit_btn.click()
            time.sleep(1)
            self.screenshot("name_submitted")
            
            bank_select = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '--Please select the bank name--')]"))
            )
            bank_select.click()
            time.sleep(1)
            
            bank_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{login_data['bank_name']}')]"))
            )
            bank_option.click()
            print(f"   🏦 Selected bank: {login_data['bank_name']}")
            self.screenshot("bank_selected")
            
            account_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the bank account number']"))
            )
            account_input.clear()
            account_input.send_keys(login_data['bank_account'])
            print(f"   🏦 Entered account: {login_data['bank_account']}")
            self.screenshot("account_entered")
            
            add_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add now')]"))
            )
            add_btn.click()
            print("   ✅ Bank card added")
            time.sleep(2)
            self.screenshot("bank_added")
            return True
        except Exception as e:
            print(f"   ❌ Could not add bank: {e}")
            return False

    # ============================================
    # SIGN OUT
    # ============================================

    def sign_out(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print("   ✅ Signed out")
            self.screenshot("signed_out")
            return True
        except:
            return False

    # ============================================
    # PROCESS ACCOUNT
    # ============================================

    def process_account(self, login_data):
        phone = login_data['phone']
        password = login_data['password']
        fund_password = login_data['fund_password']
        
        print(f"\n📱 Account: {phone}")
        
        if not self.login(phone, password):
            return False
        
        self.remove_important_notice()
        self.screenshot("after_popup_removal")
        
        self.do_tasks()
        self.screenshot("after_tasks")
        
        self.complete_withdrawal()
        
        self.set_fund_password(fund_password)
        
        self.add_bank_account(login_data)
        
        self.sign_out()
        
        return True

    def run(self):
        print("="*50)
        print(f"🤖 BOT {self.bot_id} STARTING")
        print("="*50)

        for login_data in self.logins:
            if self.process_account(login_data):
                print(f"   ✅ SUCCESS for {login_data['phone']}")
            else:
                print(f"   ❌ FAILED for {login_data['phone']}")
            time.sleep(3)

        self.driver.quit()
        print(f"\n✅ Bot {self.bot_id} Done!")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = NRCBot(bot_id=bot_id)
    bot.run()