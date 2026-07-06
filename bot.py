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
        except Exception as e:
            print(f"   ⚠️ Clear error: {e}")
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

    def scroll_down(self, amount=250):
        try:
            self.driver.execute_script(f"window.scrollBy(0, {amount});")
            time.sleep(0.3)
            return True
        except:
            return False

    def scroll_up(self, amount=150):
        try:
            self.driver.execute_script(f"window.scrollBy(0, -{amount});")
            time.sleep(0.3)
            return True
        except:
            return False

    def show_password(self):
        try:
            eye_selectors = [
                "//*[contains(@class, 'eye')]",
                "//*[contains(@class, 'show-password')]",
                "//button[@type='button']",
                "//*[contains(@class, 'fa-eye')]"
            ]
            for selector in eye_selectors:
                try:
                    eye_btn = self.driver.find_element(By.XPATH, selector)
                    if eye_btn.is_displayed() and eye_btn.is_enabled():
                        self.click_element(eye_btn)
                        print("   👁️ Clicked show password")
                        time.sleep(0.5)
                        self.screenshot("password_shown")
                        return True
                except:
                    pass
            return False
        except:
            return False

    def find_login_button(self):
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
    # TASKS - WITH SCROLLING
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

    def find_all_read_buttons(self):
        all_buttons = []
        
        selectors = [
            "//button[contains(text(), 'read')]",
            "//*[contains(text(), 'read')]",
            "//button[contains(text(), 'Read')]",
            "//button[contains(@class, 'read')]"
        ]
        
        for scroll_attempt in range(5):
            for selector in selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            if btn not in all_buttons:
                                all_buttons.append(btn)
                except:
                    pass
            
            self.scroll_down(300)
            time.sleep(0.5)
        
        self.scroll_up(500)
        time.sleep(0.5)
        
        unique_buttons = []
        for btn in all_buttons:
            if btn not in unique_buttons:
                unique_buttons.append(btn)
        
        return unique_buttons

    def do_tasks(self):
        print("   📋 Starting tasks...")
        
        self.click_task_tab()
        time.sleep(2)
        self.screenshot("tasks_page")
        
        total_tasks = 0
        max_tasks = 6
        
        while total_tasks < max_tasks:
            try:
                read_btns = self.find_all_read_buttons()
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
    # BANK DETAILS CONFIGURATION
    # ============================================

    def click_confirm_button(self):
        """Click the Confirm button when it appears"""
        try:
            confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
            if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                self.click_element(confirm_btn)
                print("   ✅ Clicked Confirm button")
                self.screenshot("confirm_clicked")
                time.sleep(2)
                return True
        except:
            pass
        return False

    def set_bank_details(self, login_data):
        """Set up bank details for withdrawal"""
        print("   🏦 Setting up bank details...")
        
        try:
            # 1. Click "My" tab
            my_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'My')] | //button[contains(text(), 'My')]")
            self.click_element(my_tab)
            time.sleep(2)
            self.screenshot("my_tab")
            
            # 2. Click "Add a bank account"
            try:
                add_bank = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Add a bank account')]")
                self.click_element(add_bank)
                time.sleep(2)
                self.screenshot("add_bank")
            except:
                print("   ℹ️ Bank already added")
            
            # 3. Click "Authenticate now" if needed
            try:
                auth_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Authenticate now')]")
                if auth_btn.is_displayed():
                    self.click_element(auth_btn)
                    time.sleep(2)
                    self.screenshot("authenticate")
                    
                    # Enter real name
                    name_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter a real name']")
                    self.type_text(name_input, login_data['real_name'])
                    print(f"   👤 Entered name: {login_data['real_name']}")
                    self.screenshot("name_entered")
                    
                    submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                    self.click_element(submit_btn)
                    time.sleep(2)
                    self.screenshot("name_submitted")
            except:
                pass
            
            # 4. Select bank
            try:
                bank_select = self.driver.find_element(By.XPATH, "//*[contains(text(), '--Please select the bank name--')]")
                self.click_element(bank_select)
                time.sleep(1)
                
                bank_option = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{login_data['bank_name']}')]")
                self.click_element(bank_option)
                print(f"   🏦 Selected bank: {login_data['bank_name']}")
                self.screenshot("bank_selected")
                time.sleep(1)
            except:
                print("   ℹ️ Bank already selected")
            
            # 5. Enter bank account number
            try:
                account_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter the bank account number']")
                self.type_text(account_input, login_data['bank_account'])
                print(f"   🏦 Entered account: {login_data['bank_account']}")
                self.screenshot("account_entered")
            except:
                print("   ℹ️ Account number already entered")
            
            # 6. Click Add now
            try:
                add_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add now')]")
                self.click_element(add_btn)
                print("   ✅ Bank card added")
                self.screenshot("bank_added")
                time.sleep(3)
            except:
                print("   ℹ️ Bank card already added")
            
            return True
        except Exception as e:
            print(f"   ⚠️ Bank setup error: {e}")
            self.screenshot("bank_setup_error")
            return False

    def set_fund_password(self, fund_password):
        """Set fund password"""
        print("   🔑 Setting fund password...")
        try:
            # Click on Fund password
            fund_pw_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Fund password')]")
            self.click_element(fund_pw_btn)
            time.sleep(1)
            self.screenshot("fund_password_page")
            
            # Find fund password inputs
            fund_inputs = self.driver.find_elements(By.XPATH, "//input[@placeholder='Please enter the new funds password']")
            if fund_inputs:
                self.type_text(fund_inputs[0], fund_password)
                print(f"   🔑 Entered fund password")
                
                confirm_inputs = self.driver.find_elements(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
                if confirm_inputs:
                    self.type_text(confirm_inputs[0], fund_password)
                    print(f"   🔑 Confirmed fund password")
                    
                    submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                    self.click_element(submit_btn)
                    print("   ✅ Fund password set")
                    self.screenshot("fund_password_set")
                    time.sleep(2)
                    return True
            return False
        except Exception as e:
            print(f"   ⚠️ Fund password error: {e}")
            self.screenshot("fund_password_error")
            return False

    def complete_withdrawal(self, fund_password, amount="1800"):
        """Complete withdrawal"""
        print(f"   💰 Processing withdrawal...")
        try:
            # Go to withdrawal page
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            self.screenshot("withdrawal_page")
            
            # Click Confirm if needed (for "You haven't linked your bank card yet" popup)
            if self.click_confirm_button():
                print("   ✅ Confirmed bank card message")
                time.sleep(2)
            
            # Select withdrawal method
            try:
                method_select = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
                self.click_element(method_select)
                time.sleep(1)
                
                bank_option = self.driver.find_element(By.XPATH, "//*[contains(text(), 'OPAY')]")
                self.click_element(bank_option)
                print("   💳 Selected OPAY")
                self.screenshot("method_selected")
                time.sleep(1)
                
                # Click Confirm after selecting bank
                self.click_confirm_button()
            except:
                print("   ℹ️ Withdrawal method already selected")
            
            # Enter fund password
            try:
                fund_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please input fund password']")
                self.type_text(fund_input, fund_password)
                print(f"   🔑 Entered fund password")
            except:
                print("   ℹ️ Fund password already entered")
            
            # Enter amount
            try:
                amount_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Withdrawal amount']")
                self.type_text(amount_input, amount)
                print(f"   💰 Entered amount: {amount}")
            except:
                print("   ℹ️ Amount already entered")
            
            # Submit
            try:
                submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                self.click_element(submit_btn)
                print("   ✅ Withdrawal submitted")
                self.screenshot("withdrawal_submitted")
                time.sleep(3)
            except:
                print("   ℹ️ Withdrawal already submitted")
            
            # Click final Confirm if appears
            self.click_confirm_button()
            
            return True
        except Exception as e:
            print(f"   ⚠️ Withdrawal error: {e}")
            self.screenshot("withdrawal_error")
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
            
            self.show_password()
            self.screenshot("04_password_visible")
            
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print(f"   ✅ Clicked login")
                self.screenshot("05_after_login_click")
            else:
                print(f"   ❌ Login button not found")
                self.screenshot("05_login_button_not_found")
                return False
            
            print("   ⏳ Waiting 10 seconds for login to process...")
            time.sleep(10)
            self.screenshot("06_after_login_wait")
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            print(f"   📍 Current URL: {current_url}")
            
            if "/logout" in current_url:
                print(f"   ❌ Redirected to logout - login failed")
                self.screenshot("07_login_failed_redirect")
                return False
            
            success_indicators = [
                "important notice",
                "cooperative wealth zone",
                "dashboard",
                "welcome to join nrc",
                "invite newcomers",
                "wealth center",
                "wish book",
                "surprise code",
                "deposit principal",
                "welcome"
            ]
            
            for indicator in success_indicators:
                if indicator in page_source:
                    print(f"   ✅✅✅ LOGIN SUCCESS! Found: '{indicator}'")
                    self.screenshot("07_login_success")
                    self.logged_in_accounts.append(phone)
                    return True
            
            if "dashboard" in current_url or "home" in current_url or "user" in current_url:
                print(f"   ✅✅✅ LOGIN SUCCESS! URL: {current_url}")
                self.screenshot("07_login_success")
                self.logged_in_accounts.append(phone)
                return True
            
            if "invalid" in page_source or "incorrect" in page_source or "error" in page_source:
                print(f"   ❌ Invalid credentials")
                self.screenshot("07_login_failed")
                return False
            
            print(f"   ❌ Login failed - unknown reason")
            self.screenshot("07_login_failed")
            return False
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.screenshot("error")
            return False

    # ============================================
    # PROCESS ACCOUNT (COMPLETE WORKFLOW)
    # ============================================

    def process_account(self, login_data):
        phone = login_data['phone']
        password = login_data['password']
        
        print(f"\n📱 Bot {self.bot_id} Account: {phone}")
        
        # 1. Login
        if not self.login(phone, password):
            print(f"   ❌ Login failed for {phone}")
            return False
        
        # 2. Remove Important Notice
        self.remove_important_notice()
        self.screenshot("after_popup_removal")
        
        # 3. Do tasks (6 tasks)
        self.do_tasks()
        self.screenshot("after_tasks")
        
        # 4. Set up bank details
        self.set_bank_details(login_data)
        
        # 5. Set fund password
        self.set_fund_password(login_data['fund_password'])
        
        # 6. Complete withdrawal
        self.complete_withdrawal(login_data['fund_password'], "1800")
        
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