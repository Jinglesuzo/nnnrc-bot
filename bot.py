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
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Error loading logins.csv: {e}")
            self.logins = [{'phone': '08057536473', 'password': 'people56', 'real_name': 'John Penn', 'bank_name': 'OPAY', 'bank_account': '9074331299', 'fund_password': '3333'}]

    def clear_field(self, element):
        try:
            element.click()
            time.sleep(0.1)
            element.send_keys(Keys.CONTROL + "a")
            time.sleep(0.1)
            element.send_keys(Keys.DELETE)
            time.sleep(0.1)
            self.driver.execute_script("arguments[0].value = '';", element)
            time.sleep(0.1)
            return True
        except:
            return False

    def type_text(self, element, text):
        self.clear_field(element)
        for char in text:
            element.send_keys(char)
            time.sleep(0.05)
        entered = element.get_attribute('value')
        print(f"   📝 Typed: {entered} (length: {len(entered)})")
        time.sleep(0.2)

    def click_element(self, element):
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", element)

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
        
        self.driver.get("https://nnnrc.com/#/mytask")
        time.sleep(3)
        self.screenshot("tasks_page")
        print("   ✅ Task page loaded")
        
        total_tasks = 0
        max_tasks = 6
        
        while total_tasks < max_tasks:
            try:
                read_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'read')] | //*[contains(text(), 'read')]")
                visible_btns = [btn for btn in read_btns if btn.is_displayed() and btn.is_enabled()]
                
                if not visible_btns:
                    print(f"   ℹ️ No more tasks found (completed {total_tasks})")
                    self.screenshot("no_more_tasks")
                    break
                
                btn = visible_btns[0]
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                
                self.click_element(btn)
                total_tasks += 1
                print(f"   📖 Clicked read task {total_tasks}")
                self.screenshot(f"task_{total_tasks}_clicked")
                
                print(f"   ⏳ Waiting 20 seconds for task {total_tasks} to complete...")
                time.sleep(20)
                self.screenshot(f"task_{total_tasks}_done")
                
                try:
                    close_btns = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'close')] | //*[text()='×']")
                    for close_btn in close_btns:
                        if close_btn.is_displayed() and close_btn.is_enabled():
                            self.click_element(close_btn)
                            time.sleep(0.3)
                except:
                    pass
                
            except Exception as e:
                print(f"   ⚠️ Task error: {e}")
                self.screenshot(f"task_error")
                time.sleep(1)
                continue
        
        print(f"   ✅ Completed {total_tasks} tasks")
        self.screenshot("tasks_completed")
        return total_tasks

    # ============================================
    # FUND PASSWORD - FIXED SELECTORS
    # ============================================

    def set_fund_password(self, fund_password):
        print("   🔑 Setting fund password...")
        
        self.driver.get("https://nnnrc.com/#/user/info")
        time.sleep(3)
        self.screenshot("01_user_info_page")
        print("   ✅ User info page loaded")
        
        # Click Fund password
        try:
            fund_pw_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Fund password')]"))
            )
            self.click_element(fund_pw_btn)
            time.sleep(2)
            self.screenshot("02_fund_password_clicked")
            print("   ✅ Clicked Fund password")
        except Exception as e:
            print(f"   ❌ Could not find Fund password: {e}")
            return False

        # Enter new fund password
        try:
            new_pw = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the new funds password']"))
            )
            self.type_text(new_pw, fund_password)
            print(f"   ✅ Entered new fund password: {fund_password}")
            self.screenshot("03_new_password_entered")
        except Exception as e:
            print(f"   ❌ Could not find new password field: {e}")
            return False

        # Confirm fund password
        try:
            confirm_pw = self.driver.find_element(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
            self.type_text(confirm_pw, fund_password)
            print(f"   ✅ Confirmed fund password: {fund_password}")
            self.screenshot("04_confirm_password_entered")
        except Exception as e:
            print(f"   ❌ Could not find confirm password field: {e}")
            return False

        # Click Submit - MULTIPLE SELECTORS
        print("   🔘 Looking for Submit button...")
        submit_clicked = False
        
        # Method 1: By text
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[text()='Submit']")
            self.click_element(submit_btn)
            print("   ✅ Clicked Submit (by exact text)")
            submit_clicked = True
        except:
            pass
        
        # Method 2: By contains text
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by contains text)")
                submit_clicked = True
            except:
                pass
        
        # Method 3: By type
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by type)")
                submit_clicked = True
            except:
                pass
        
        # Method 4: By class
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='submit'], button[class*='green']")
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by class)")
                submit_clicked = True
            except:
                pass
        
        # Method 5: JavaScript click
        if not submit_clicked:
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                self.driver.execute_script("arguments[0].click();", submit_btn)
                print("   ✅ Clicked Submit (JavaScript)")
                submit_clicked = True
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
                            print(f"   ✅ Clicked button: '{btn.text}'")
                            submit_clicked = True
                            break
            except:
                pass
        
        if submit_clicked:
            time.sleep(2)
            self.screenshot("05_submit_clicked")
            print("   ✅ Fund password set successfully!")
            return True
        else:
            print("   ❌ Could not find Submit button")
            self.screenshot("05_submit_not_found")
            return False

    # ============================================
    # ADD BANK ACCOUNT - FIXED SELECTORS
    # ============================================

    def add_bank_account(self, login_data):
        print("   🏦 Adding bank account...")
        
        self.driver.get("https://nnnrc.com/#/user/set/info")
        time.sleep(3)
        self.screenshot("01_bank_page")
        print("   ✅ Bank setup page loaded")
        
        # Find and click "Authenticate now" if present
        try:
            auth_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Authenticate now')]")
            if auth_btn.is_displayed():
                self.click_element(auth_btn)
                time.sleep(2)
                self.screenshot("02_authenticate_clicked")
                print("   ✅ Clicked Authenticate now")
        except:
            print("   ℹ️ No Authenticate now button needed")

        # Enter real name - MULTIPLE SELECTORS
        name_input = None
        name_selectors = [
            "//input[@placeholder='Please enter a real name']",
            "//input[contains(@placeholder, 'real name')]",
            "//input[contains(@placeholder, 'name')]",
            "//input[contains(@name, 'name')]",
            "//input[contains(@id, 'name')]"
        ]
        
        for selector in name_selectors:
            try:
                name_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if name_input:
                    break
            except:
                continue
        
        if not name_input:
            print("   ❌ Could not find real name field")
            self.screenshot("03_name_field_not_found")
            return False
        
        self.type_text(name_input, login_data['real_name'])
        print(f"   👤 Entered real name: {login_data['real_name']}")
        self.screenshot("04_real_name_entered")

        # Submit real name
        submit_clicked = False
        submit_selectors = [
            "//button[contains(text(), 'Submit')]",
            "//button[contains(text(), 'submit')]",
            "//button[@type='submit']",
            "//button[contains(@class, 'submit')]"
        ]
        
        for selector in submit_selectors:
            try:
                submit_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if submit_btn:
                    self.click_element(submit_btn)
                    submit_clicked = True
                    print(f"   ✅ Submitted real name")
                    self.screenshot("05_real_name_submitted")
                    time.sleep(2)
                    break
            except:
                continue
        
        if not submit_clicked:
            print("   ⚠️ Could not submit real name (may already be submitted)")
            time.sleep(1)

        # Select bank
        try:
            bank_select = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '--Please select the bank name--')]"))
            )
            self.click_element(bank_select)
            time.sleep(1)
            self.screenshot("06_bank_select_clicked")
            print("   ✅ Clicked bank selector")
        except Exception as e:
            print(f"   ❌ Could not find bank selector: {e}")
            return False

        # Select the bank
        try:
            bank_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{login_data['bank_name']}')]"))
            )
            self.click_element(bank_option)
            time.sleep(1)
            self.screenshot("07_bank_selected")
            print(f"   🏦 Selected bank: {login_data['bank_name']}")
        except Exception as e:
            print(f"   ❌ Could not select bank: {e}")
            return False

        # Enter bank account number
        try:
            account_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the bank account number']"))
            )
            self.type_text(account_input, login_data['bank_account'])
            self.screenshot("08_account_entered")
            print(f"   🏦 Entered account: {login_data['bank_account']}")
        except Exception as e:
            print(f"   ❌ Could not find account number field: {e}")
            return False

        # Click Add now
        try:
            add_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Add now')]"))
            )
            self.click_element(add_btn)
            time.sleep(2)
            self.screenshot("09_bank_added")
            print("   ✅ Bank card added successfully!")
            return True
        except Exception as e:
            print(f"   ❌ Could not add bank: {e}")
            return False

    # ============================================
    # LOGIN
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Bot {self.bot_id} Logging in: {phone}")
        
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")
            
            phone_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
            )
            self.type_text(phone_field, phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")
            
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
            self.type_text(password_field, password)
            print(f"   ✅ Password entered")
            self.screenshot("03_password_entered")
            
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print(f"   ✅ Clicked login")
                self.screenshot("04_after_login_click")
            else:
                print(f"   ❌ Login button not found")
                return False
            
            print("   ⏳ Waiting 10 seconds for login to process...")
            time.sleep(10)
            self.screenshot("05_after_login_wait")
            
            page_source = self.driver.page_source.lower()
            if "important notice" in page_source or "cooperative wealth zone" in page_source:
                print(f"   ✅ Login success!")
                self.logged_in_accounts.append(phone)
                return True
            else:
                print(f"   ❌ Login failed")
                return False
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
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
            print(f"   ❌ Login failed for {phone}")
            return False
        
        self.remove_important_notice()
        self.screenshot("after_popup_removal")
        
        self.do_tasks()
        self.screenshot("after_tasks")
        
        self.set_fund_password(fund_password)
        
        self.add_bank_account(login_data)
        
        return True

    def logout_all(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print(f"   ✅ Logged out all accounts")
            self.screenshot("08_logged_out")
            return True
        except:
            return False

    # ============================================
    # RUN
    # ============================================

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

        if self.logged_in_accounts:
            self.logout_all()
        else:
            print("   ⚠️ No accounts were processed successfully")

        self.driver.quit()
        print(f"\n✅ Bot {self.bot_id} Done!")
        print(f"📊 Successful accounts: {len(self.logged_in_accounts)}")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = NRCBot(bot_id=bot_id)
    bot.run()