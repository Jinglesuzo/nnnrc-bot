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
    # WITHDRAWAL - CLICK CONFIRM ONLY
    # ============================================

    def click_confirm_only(self):
        """Click the Confirm button - NO LOGOUT"""
        print("   🔘 Looking for Confirm button...")
        try:
            confirm_selectors = [
                "//button[contains(text(), 'Confirm')]",
                "//button[text()='Confirm']",
                "//*[contains(@class, 'confirm')]",
                "//button[contains(@class, 'confirm')]"
            ]
            
            for selector in confirm_selectors:
                try:
                    confirm_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if confirm_btn.is_displayed() and confirm_btn.is_enabled():
                        self.click_element(confirm_btn)
                        print("   ✅ Clicked Confirm button")
                        time.sleep(2)
                        self.screenshot("confirm_clicked")
                        return True
                except:
                    continue
            
            print("   ❌ Could not find Confirm button")
            return False
        except Exception as e:
            print(f"   ❌ Error clicking Confirm: {e}")
            return False

    def complete_withdrawal(self, fund_password, amount="1800"):
        """Go to withdrawal page and click Confirm ONLY"""
        print(f"   💰 Processing withdrawal...")
        
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(3)
            self.screenshot("withdrawal_page")
            print("   ✅ Withdrawal page loaded")
        except Exception as e:
            print(f"   ❌ Could not load withdrawal page: {e}")
            return False
        
        if self.click_confirm_only():
            print("   ✅ Confirm clicked! Taking screenshot...")
            time.sleep(2)
            self.screenshot("after_confirm_clicked")
            print("   ✅ Screenshot saved: after_confirm_clicked.png")
            return True
        else:
            print("   ❌ Could not click Confirm")
            self.screenshot("confirm_not_found")
            return False

    # ============================================
    # FUND PASSWORD + SIGN OUT
    # ============================================

    def set_fund_password_and_signout(self, fund_password):
        """Click Fund Password, enter 3333, click Submit, then Sign out"""
        
        # 1. Click "Fund password" (Click Settings)
        print("   🔑 Looking for Fund password...")
        try:
            fund_pw_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Fund password')]")
            if fund_pw_btn.is_displayed() and fund_pw_btn.is_enabled():
                self.click_element(fund_pw_btn)
                time.sleep(2)
                self.screenshot("01_fund_password_clicked")
                print("   ✅ Clicked Fund password")
            else:
                print("   ❌ Fund password not found")
                self.screenshot("01_fund_password_not_found")
                return False
        except Exception as e:
            print(f"   ❌ Error clicking Fund password: {e}")
            return False

        # 2. Enter new fund password (3333)
        try:
            new_password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter the new funds password']"))
            )
            self.type_text(new_password_field, fund_password)
            print(f"   ✅ Entered new fund password: {fund_password}")
            self.screenshot("02_fund_password_entered")
        except Exception as e:
            print(f"   ❌ Could not find new password field: {e}")
            return False

        # 3. Confirm fund password (3333)
        try:
            confirm_password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
            self.type_text(confirm_password_field, fund_password)
            print(f"   ✅ Confirmed fund password: {fund_password}")
            self.screenshot("03_fund_password_confirmed")
        except Exception as e:
            print(f"   ❌ Could not find confirm password field: {e}")
            return False

        # 4. Click Submit
        try:
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
            )
            self.click_element(submit_btn)
            time.sleep(2)
            self.screenshot("04_fund_password_submitted")
            print("   ✅ Submitted fund password")
        except Exception as e:
            print(f"   ❌ Could not click Submit: {e}")
            return False

        # 5. Click Sign out
        print("   🔍 Looking for Sign out...")
        try:
            signout_selectors = [
                "//*[contains(text(), 'Sign out')]",
                "//*[contains(text(), 'Logout')]",
                "//button[contains(text(), 'Sign out')]",
                "//a[contains(text(), 'Sign out')]",
                "//*[contains(@class, 'signout')]",
                "//*[contains(@class, 'logout')]"
            ]
            
            signout_btn = None
            for selector in signout_selectors:
                try:
                    signout_btn = self.driver.find_element(By.XPATH, selector)
                    if signout_btn.is_displayed() and signout_btn.is_enabled():
                        print(f"   ✅ Found Sign out: {selector}")
                        break
                except:
                    continue
            
            if signout_btn:
                self.click_element(signout_btn)
                time.sleep(2)
                self.screenshot("05_signed_out")
                print("   ✅ Signed out successfully")
                return True
            else:
                print("   ❌ Sign out not found")
                self.screenshot("05_signout_not_found")
                return False
        except Exception as e:
            print(f"   ❌ Error clicking Sign out: {e}")
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
    # PROCESS ACCOUNT
    # ============================================

    def process_account(self, login_data):
        phone = login_data['phone']
        password = login_data['password']
        fund_password = login_data['fund_password']
        
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
        
        # 4. Go to withdrawal and click Confirm
        self.complete_withdrawal(fund_password, "1800")
        
        # 5. Set fund password and sign out
        self.set_fund_password_and_signout(fund_password)
        
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
        print(f"📊 Successful accounts: {len(self.logged_in_accounts)}")

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    bot = NRCBot(bot_id=bot_id)
    bot.run()