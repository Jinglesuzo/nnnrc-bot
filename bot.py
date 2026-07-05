from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import time
import random
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
                    if len(row) >= 2:
                        self.logins.append({
                            'phone': row[0].strip(),
                            'password': row[1].strip()
                        })
            print(f"📋 Bot {self.bot_id} Loaded {len(self.logins)} login(s)")
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Error loading logins.csv: {e}")
            self.logins = [{'phone': '08057536473', 'password': 'people56'}]

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

    def show_password(self):
        try:
            eye_selectors = [
                "//*[contains(@class, 'eye')]",
                "//*[contains(@class, 'show-password')]",
                "//*[contains(@class, 'password-toggle')]",
                "//*[contains(@class, 'toggle-password')]",
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

    def click_news_button(self):
        """Click the NEWS button on Important Notice"""
        try:
            selectors = [
                "//*[contains(text(), 'NEWS')]",
                "//*[contains(text(), 'News')]",
                "//button[contains(text(), 'NEWS')]",
                "//*[contains(@class, 'news')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.click_element(element)
                            print("   📰 Clicked NEWS button")
                            time.sleep(2)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def close_welcome_popup(self):
        """Close the Welcome popup"""
        try:
            selectors = [
                "//button[contains(text(), 'Got it')]",
                "//button[contains(text(), 'OK')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[text()='×']"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            self.click_element(element)
                            print("   🚫 Closed Welcome popup")
                            time.sleep(1)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def close_remaining_popups(self):
        """Close any remaining popups or ads"""
        try:
            selectors = [
                "//*[contains(@class, 'close')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[text()='×']",
                "//button[contains(@class, 'btn-close')]"
            ]
            closed = 0
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.click_element(element)
                            closed += 1
                            time.sleep(0.3)
                except:
                    continue
            if closed > 0:
                print(f"   🚫 Closed {closed} remaining popup(s)")
            return True
        except:
            return False

    def handle_popups(self):
        """Complete popup handling flow"""
        print("   📋 Handling popups...")
        self.click_news_button()
        self.close_welcome_popup()
        self.close_remaining_popups()
        self.screenshot("popups_handled")
        print("   ✅ Popups handled")

    # ============================================
    # TASKS
    # ============================================

    def click_task_tab(self):
        """Click the Task tab"""
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
                            return True
                except:
                    continue
            return False
        except:
            return False

    def do_tasks(self):
        """Do all 6 tasks (click read buttons, wait 20s each)"""
        print("   📋 Doing tasks...")
        
        self.click_task_tab()
        time.sleep(2)
        self.screenshot("tasks_page")
        
        # Find all read buttons
        read_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'read')] | //*[contains(text(), 'read')]")
        if not read_buttons:
            read_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Read')]")
        
        if not read_buttons:
            print("   ⚠️ No read tasks found")
            self.screenshot("no_tasks_found")
            return 0
        
        count = 0
        for btn in read_buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    # Scroll to button
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    
                    # Click read
                    self.click_element(btn)
                    count += 1
                    print(f"   📖 Clicked read task {count}")
                    self.screenshot(f"task_{count}_clicked")
                    
                    # Wait for task to complete (20 seconds)
                    time.sleep(1)
                    print(f"   ⏳ Waiting 20 seconds for task {count} to complete...")
                    time.sleep(20)
                    self.screenshot(f"task_{count}_done")
                    
                    # Close any popups that appear
                    self.close_remaining_popups()
                    time.sleep(1)
            except Exception as e:
                print(f"   ⚠️ Task error: {e}")
        
        print(f"   ✅ Completed {count} tasks")
        self.screenshot("tasks_completed")
        return count

    # ============================================
    # LOGIN
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Bot {self.bot_id} Logging in: {phone}")
        print(f"   📝 Password: {password} (length: {len(password)})")
        
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
            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
            )
            self.type_text(password_field, password)
            print(f"   ✅ Password entered")
            self.screenshot("03_password_entered")
            
            # Show password
            self.show_password()
            self.screenshot("04_password_visible")
            
            # Click login
            login_btn = self.find_login_button()
            if login_btn:
                self.click_element(login_btn)
                print(f"   ✅ Clicked login")
                self.screenshot("05_after_login_click")
            else:
                print(f"   ❌ Login button not found")
                self.screenshot("05_login_button_not_found")
                return False
            
            # Wait for page to load
            print("   ⏳ Waiting 10 seconds for login to process...")
            time.sleep(10)
            self.screenshot("06_after_login_wait")
            
            # Check current state
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            print(f"   📍 Current URL: {current_url}")
            
            # Check if we're on the logout page (login failed)
            if "/logout" in current_url:
                print(f"   ❌ Redirected to logout - login failed")
                self.screenshot("07_login_failed_redirect")
                return False
            
            # Check for success indicators
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
            
            # Check URL for success
            if "dashboard" in current_url or "home" in current_url or "user" in current_url:
                print(f"   ✅✅✅ LOGIN SUCCESS! URL: {current_url}")
                self.screenshot("07_login_success")
                self.logged_in_accounts.append(phone)
                return True
            
            # Check for login failure
            if "invalid" in page_source or "incorrect" in page_source or "error" in page_source:
                print(f"   ❌ Invalid credentials")
                self.screenshot("07_login_failed")
                return False
            
            # If still on login page, login failed
            if "log in now" in page_source or "login" in page_source:
                print(f"   ❌ Still on login page - login failed")
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

    def process_account(self, phone, password):
        """Full account process: Login → Popups → Tasks → Stay logged in"""
        if not self.login(phone, password):
            return False
        
        # Handle popups after login
        self.handle_popups()
        self.screenshot("after_popups")
        
        # Do tasks
        self.do_tasks()
        self.screenshot("after_tasks")
        
        return True

    def logout_all(self):
        """Logout once at the very end"""
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
            phone = login_data['phone']
            password = login_data['password']
            print(f"\n📱 Bot {self.bot_id} Account: {phone}")
            
            if self.process_account(phone, password):
                print(f"   ✅ SUCCESS for {phone}")
            else:
                print(f"   ❌ FAILED for {phone}")
            
            time.sleep(2)

        # Logout once at the end
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