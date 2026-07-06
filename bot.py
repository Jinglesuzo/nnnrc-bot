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

    def scroll_down(self, amount=250):
        try:
            self.driver.execute_script(f"window.scrollBy(0, {amount});")
            time.sleep(0.3)
            return True
        except:
            return False

    # ============================================
    # CLICK GREEN BUTTON (MULTIPLE METHODS)
    # ============================================

    def click_green_button(self, button_text=None):
        """Click any green button using multiple methods"""
        print(f"   🔘 Looking for green button...")
        
        if button_text:
            try:
                btn = self.driver.find_element(By.XPATH, f"//button[text()='{button_text}']")
                if btn.is_displayed() and btn.is_enabled():
                    self.click_element(btn)
                    print(f"   ✅ Clicked '{button_text}' (by exact text)")
                    return True
            except:
                pass
            
            try:
                btn = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{button_text}')]")
                if btn.is_displayed() and btn.is_enabled():
                    self.click_element(btn)
                    print(f"   ✅ Clicked '{button_text}' (by contains text)")
                    return True
            except:
                pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if btn.is_displayed() and btn.is_enabled():
                self.click_element(btn)
                print(f"   ✅ Clicked submit button (by type)")
                return True
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='green'], button[class*='Green'], button[class*='primary'], button[class*='btn-primary']")
            if btn.is_displayed() and btn.is_enabled():
                self.click_element(btn)
                print(f"   ✅ Clicked green button (by class)")
                return True
        except:
            pass
        
        if button_text:
            try:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    if btn.is_displayed() and btn.is_enabled():
                        text = btn.text.lower()
                        if button_text.lower() in text:
                            self.click_element(btn)
                            print(f"   ✅ Clicked button: '{btn.text}' (by scanning)")
                            return True
            except:
                pass
        
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    self.click_element(btn)
                    print(f"   ✅ Clicked any visible button: '{btn.text}'")
                    return True
        except:
            pass
        
        print(f"   ❌ Could not find green button")
        return False

    # ============================================
    # LOGIN BUTTON CLICK (FIXED)
    # ============================================

    def click_login_button(self):
        """Click the login button using EVERY possible method"""
        print("   🔘 Clicking login button...")
        
        # Method 1: Find by text and click with JavaScript
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", btn)
                print("   ✅ Clicked 'Log in now' (JavaScript)")
                return True
        except:
            pass
        
        # Method 2: Find by text and click normally
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if btn.is_displayed():
                btn.click()
                print("   ✅ Clicked 'Log in now' (normal click)")
                return True
        except:
            pass
        
        # Method 3: By type submit
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", btn)
                print("   ✅ Clicked submit button")
                return True
        except:
            pass
        
        # Method 4: By CSS class
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='login'], button[class*='Login'], button[class*='green'], button[class*='primary']")
            if btn.is_displayed():
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.3)
                self.driver.execute_script("arguments[0].click();", btn)
                print("   ✅ Clicked button by class")
                return True
        except:
            pass
        
        # Method 5: Find any button with "log" or "in" in text
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    text = btn.text.lower()
                    if 'log' in text or 'in' in text or 'submit' in text:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                        time.sleep(0.3)
                        self.driver.execute_script("arguments[0].click();", btn)
                        print(f"   ✅ Clicked button: '{btn.text}'")
                        return True
        except:
            pass
        
        # Method 6: Submit the form directly
        try:
            form = self.driver.find_element(By.TAG_NAME, "form")
            self.driver.execute_script("arguments[0].submit();", form)
            print("   ✅ Submitted form directly")
            return True
        except:
            pass
        
        print("   ❌ Could not click login button")
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

    def click_task_tab(self):
        try:
            selectors = [
                "//*[contains(text(), 'Task')]",
                "//button[contains(text(), 'Task')]",
                "//*[contains(@class, 'task')]",
                "//*[contains(@class, 'tab-task')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.click_element(element)
                            print("   📋 Clicked Task tab")
                            time.sleep(2)
                            self.screenshot("task_tab_clicked")
                            return True
                except:
                    continue
            return False
        except:
            return False

    def do_tasks(self):
        print("   📋 Starting tasks...")
        
        self.click_task_tab()
        time.sleep(2)
        self.screenshot("tasks_page")
        
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
                
                self.scroll_down(100)
                time.sleep(0.3)
                
            except Exception as e:
                print(f"   ⚠️ Task error: {e}")
                self.screenshot(f"task_error")
                self.scroll_down(200)
                time.sleep(0.5)
                continue
        
        print(f"   ✅ Completed {total_tasks} tasks")
        self.screenshot("tasks_completed")
        return total_tasks

    # ============================================
    # WITHDRAWAL - CLICK CONFIRM
    # ============================================

    def complete_withdrawal(self):
        print(f"   💰 Going to withdrawal page...")
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(3)
            self.screenshot("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except:
            print("   ❌ Could not load withdrawal page")
            return False
        
        return self.click_green_button("Confirm")

    # ============================================
    # FUND PASSWORD
    # ============================================

    def set_fund_password(self, fund_password):
        print("   🔑 Setting fund password...")
        try:
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(3)
            self.screenshot("01_user_info_page")
            print("   ✅ User info page loaded")
        except Exception as e:
            print(f"   ❌ Could not load user info page: {e}")
            return False

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

        try:
            new_pw = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the new funds password']"))
            )
            self.type_text(new_pw, fund_password)
            self.screenshot("03_new_password_entered")
            print(f"   ✅ Entered new fund password: {fund_password}")
        except Exception as e:
            print(f"   ❌ Could not find new password field: {e}")
            return False

        try:
            confirm_pw = self.driver.find_element(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
            self.type_text(confirm_pw, fund_password)
            self.screenshot("04_confirm_password_entered")
            print(f"   ✅ Confirmed fund password: {fund_password}")
        except Exception as e:
            print(f"   ❌ Could not find confirm password field: {e}")
            return False

        return self.click_green_button("Submit")

    # ============================================
    # AUTHENTICATION + BANK DETAILS
    # ============================================

    def authenticate_and_add_bank(self, login_data):
        print("   🔐 Starting authentication and bank setup...")
        
        if not self.click_green_button("Authenticate now"):
            print("   ❌ Could not click Authenticate now")
            return False
        
        time.sleep(2)
        self.screenshot("01_authenticate_clicked")

        try:
            name_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter a real name']"))
            )
            self.type_text(name_input, login_data['real_name'])
            self.screenshot("02_real_name_entered")
            print(f"   👤 Entered real name: {login_data['real_name']}")
        except Exception as e:
            print(f"   ❌ Could not find real name field: {e}")
            return False

        if not self.click_green_button("Submit"):
            print("   ❌ Could not submit real name")
            return False
        
        time.sleep(2)
        self.screenshot("03_real_name_submitted")

        try:
            bank_select = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '--Please select the bank name--')]"))
            )
            self.click_element(bank_select)
            time.sleep(1)
            self.screenshot("04_bank_select_clicked")
            print("   ✅ Clicked bank selector")
        except Exception as e:
            print(f"   ❌ Could not find bank selector: {e}")
            return False

        try:
            bank_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//*[contains(text(), '{login_data['bank_name']}')]"))
            )
            self.click_element(bank_option)
            time.sleep(1)
            self.screenshot("05_bank_selected")
            print(f"   🏦 Selected bank: {login_data['bank_name']}")
        except Exception as e:
            print(f"   ❌ Could not select bank: {e}")
            return False

        try:
            account_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the bank account number']"))
            )
            self.type_text(account_input, login_data['bank_account'])
            self.screenshot("06_account_entered")
            print(f"   🏦 Entered account: {login_data['bank_account']}")
        except Exception as e:
            print(f"   ❌ Could not find account number field: {e}")
            return False

        if not self.click_green_button("Add now"):
            print("   ❌ Could not add bank")
            return False
        
        time.sleep(2)
        self.screenshot("07_bank_added")
        print("   ✅ Bank card added successfully!")
        return True

    def add_bank_account(self, login_data):
        print("   🏦 Going to user info page to add bank...")
        try:
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(3)
            self.screenshot("00_user_info_for_bank")
            print("   ✅ User info page loaded")
        except Exception as e:
            print(f"   ❌ Could not load user info page: {e}")
            return False

        try:
            add_bank_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Add a bank account')]"))
            )
            self.click_element(add_bank_btn)
            time.sleep(2)
            self.screenshot("00_add_bank_clicked")
            print("   ✅ Clicked 'Add a bank account'")
        except Exception as e:
            print(f"   ❌ Could not find 'Add a bank account': {e}")
            return False

        return self.authenticate_and_add_bank(login_data)

    def sign_out(self):
        try:
            print("   🔍 Looking for Sign out...")
            signout_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Sign out')]"))
            )
            self.click_element(signout_btn)
            time.sleep(2)
            self.screenshot("06_signed_out")
            print("   ✅ Signed out")
            return True
        except Exception as e:
            print(f"   ❌ Could not sign out: {e}")
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
            
            # Use the dedicated login button clicker
            if not self.click_login_button():
                print("   ❌ Could not click login button")
                return False
            
            time.sleep(8)
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