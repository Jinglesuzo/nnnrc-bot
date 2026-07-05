from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import csv
import os
import sys

class NRCBot:
    def __init__(self, bot_id=1, start_index=0):
        self.bot_id = bot_id
        self.start_index = start_index
        self.logins = []
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.max_login_retries = 3

        self.load_logins()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--remote-debugging-port=9222")

        print(f"🤖 Bot {self.bot_id} Starting...")
        try:
            options.binary_location = "/usr/bin/google-chrome"
            service = Service('/usr/bin/chromedriver')
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Failed: {e}")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ Bot {self.bot_id} Chrome started with fallback!")
            except Exception as e2:
                print(f"❌ Bot {self.bot_id} Still failed: {e2}")
                sys.exit(1)

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
            print(f"📋 Bot {self.bot_id} Loaded {len(self.logins)} logins")
        except Exception as e:
            print(f"❌ Bot {self.bot_id} Failed to load logins: {e}")
            sys.exit(1)

    def human_type(self, element, text):
        element.click()
        element.clear()
        time.sleep(0.1)
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(0.2)

    def human_click(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(element).perform()
                time.sleep(0.2)
                element.click()
                return True
            except:
                return False

    def take_screenshot(self, name):
        try:
            self.driver.save_screenshot(f"bot{self.bot_id}_{name}.png")
            print(f"   📸 Screenshot: {name}")
        except:
            pass

    def wait_for_page_load(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print(f"   ⏰ Page load timeout (30s)")
            return False

    def click_login_button(self):
        """Try EVERY possible way to click the login button"""
        print(f"   🔍 Looking for login button...")
        
        # Method 1: By text "Log in now"
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if btn.is_displayed():
                print(f"   ✅ Found 'Log in now' button")
                self.human_click(btn)
                return True
        except:
            pass
        
        # Method 2: By text "Login"
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            if btn.is_displayed():
                print(f"   ✅ Found 'Login' button")
                self.human_click(btn)
                return True
        except:
            pass
        
        # Method 3: By button type submit
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if btn.is_displayed():
                print(f"   ✅ Found submit button")
                self.human_click(btn)
                return True
        except:
            pass
        
        # Method 4: Any green/primary button
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed():
                    # Check if it's green or primary
                    classes = btn.get_attribute('class') or ''
                    style = btn.get_attribute('style') or ''
                    if 'green' in classes.lower() or 'primary' in classes.lower() or 'login' in classes.lower():
                        print(f"   ✅ Found green button")
                        self.human_click(btn)
                        return True
        except:
            pass
        
        # Method 5: Last resort - find ANY visible button
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    print(f"   ✅ Found any visible button")
                    self.human_click(btn)
                    return True
        except:
            pass
        
        print(f"   ❌ Could NOT find login button")
        return False

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        
        for attempt in range(self.max_login_retries):
            try:
                print(f"   Attempt {attempt + 1}/{self.max_login_retries}")
                
                self.driver.get("https://nnnrc.com/#/login")
                time.sleep(2)
                
                if not self.wait_for_page_load(30):
                    print(f"   ⏰ Page load timeout, reloading...")
                    self.driver.refresh()
                    time.sleep(3)
                    continue
                
                # Phone field
                try:
                    phone_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
                    )
                except TimeoutException:
                    print(f"   ⏰ Phone field not found, reloading...")
                    self.driver.refresh()
                    time.sleep(3)
                    continue
                
                phone_field.click()
                phone_field.clear()
                time.sleep(0.2)
                self.human_type(phone_field, phone)
                print(f"   ✅ Entered phone: {phone}")
                
                # Password field
                try:
                    password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter login password']")
                except:
                    try:
                        password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter the login password']")
                    except:
                        print(f"   ⏰ Password field not found, reloading...")
                        self.driver.refresh()
                        time.sleep(3)
                        continue
                
                password_field.click()
                password_field.clear()
                time.sleep(0.2)
                self.human_type(password_field, password)
                print(f"   ✅ Entered password")
                
                # === CLICK LOGIN BUTTON ===
                if self.click_login_button():
                    print(f"   ✅ Clicked login button")
                else:
                    print(f"   ❌ Login button not found - retrying...")
                    time.sleep(2)
                    continue
                
                time.sleep(4)
                
                page_source = self.driver.page_source.lower()
                current_url = self.driver.current_url.lower()
                
                if "cooperative wealth zone" in page_source or "dashboard" in current_url or "welcome" in page_source:
                    print(f"   ✅ Login successful!")
                    self.take_screenshot(f"login_success_{phone}")
                    return True
                
                if "log in now" in page_source.lower() or "login" in page_source.lower():
                    if "invalid" in page_source or "incorrect" in page_source or "error" in page_source:
                        print(f"   ❌ Invalid credentials")
                        self.take_screenshot(f"login_invalid_{phone}")
                        return False
                    
                    print(f"   ❌ Login failed, retrying...")
                    time.sleep(2)
                    continue
                
                print(f"   ❌ Login failed, retrying...")
                time.sleep(2)
                continue
                    
            except Exception as e:
                print(f"   ⚠️ Login error: {e}, retrying...")
                time.sleep(2)
                continue
        
        print(f"   ❌ Failed to login after {self.max_login_retries} attempts")
        self.take_screenshot(f"login_failed_{phone}")
        return False

    def click_news_button(self):
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
                            self.human_click(element)
                            print("   📰 Clicked NEWS")
                            time.sleep(1.5)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def close_welcome_popup(self):
        try:
            selectors = [
                "//*[contains(text(), 'Welcome to join NRC')]",
                "//*[contains(text(), 'Thank you for your trust')]",
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
                            self.human_click(element)
                            print("   🚫 Closed Welcome popup")
                            time.sleep(0.5)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def close_remaining_popups(self):
        try:
            selectors = [
                "//*[contains(@class, 'close')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[text()='×']",
                "//*[text()='✕']",
                "//button[contains(@class, 'btn-close')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            time.sleep(0.3)
                except:
                    continue
            return True
        except:
            return False

    def handle_popups(self):
        print("   📋 Handling popups...")
        self.click_news_button()
        self.close_welcome_popup()
        self.close_remaining_popups()
        print("   ✅ Popups handled")

    def click_task_tab(self):
        try:
            selectors = [
                "//*[contains(text(), 'Task')]",
                "//*[contains(@class, 'task')]",
                "//button[contains(text(), 'Task')]",
                "//*[contains(@class, 'tab-task')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            print("   📋 Clicked Task")
                            time.sleep(1)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def do_tasks(self):
        print("   📋 Doing tasks...")
        
        self.click_task_tab()
        time.sleep(1)
        
        read_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'read')] | //*[contains(text(), 'read')]")
        if not read_buttons:
            read_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Read')]")
        
        count = 0
        for btn in read_buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                    time.sleep(0.5)
                    self.human_click(btn)
                    print(f"   📖 Clicked read task {count + 1}")
                    time.sleep(1)
                    print(f"   ⏳ Waiting 20 seconds for task to complete...")
                    time.sleep(20)
                    self.close_remaining_popups()
                    time.sleep(1)
                    count += 1
            except Exception as e:
                print(f"   ⚠️ Task error: {e}")
        
        print(f"   ✅ Completed {count} tasks")
        self.take_screenshot("tasks_completed")
        return count

    def click_my_tab(self):
        try:
            selectors = [
                "//*[contains(text(), 'My')]",
                "//*[contains(@class, 'my')]",
                "//button[contains(text(), 'My')]",
                "//*[contains(@class, 'tab-my')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            print("   👤 Clicked My")
                            time.sleep(1)
                            return True
                except:
                    continue
            return False
        except:
            return False

    def click_withdrawal(self):
        try:
            selectors = [
                "//*[contains(text(), 'Withdrawal')]",
                "//*[contains(text(), 'withdrawal')]",
                "//button[contains(text(), 'Withdrawal')]",
                "//a[contains(@href, 'withdraw')]"
            ]
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            self.human_click(element)
                            print("   💰 Clicked Withdrawal")
                            time.sleep(2)
                            return True
                except:
                    continue
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            return True
        except:
            return False

    def set_fund_password(self, password):
        try:
            fund_inputs = self.driver.find_elements(By.XPATH, "//input[@placeholder='Please enter the new funds password']")
            if fund_inputs:
                self.human_type(fund_inputs[0], password)
                print("   🔑 Entered fund password")
                
                confirm_inputs = self.driver.find_elements(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
                if confirm_inputs:
                    self.human_type(confirm_inputs[0], password)
                    print("   🔑 Confirmed fund password")
                    
                    submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
                    self.human_click(submit_btn)
                    print("   ✅ Fund password set")
                    time.sleep(2)
                    
                    confirm_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm')]")
                    if confirm_btn:
                        self.human_click(confirm_btn[0])
                        time.sleep(1)
                    return True
            return False
        except Exception as e:
            print(f"   ⚠️ Fund password error: {e}")
            return False

    def authenticate_real_name(self, name):
        try:
            auth_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Authenticate now')]")
            if auth_btn:
                self.human_click(auth_btn[0])
                time.sleep(2)
            
            name_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter a real name']")
            self.human_type(name_input, name)
            print(f"   👤 Entered name: {name}")
            
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.human_click(submit_btn)
            print("   ✅ Real name authenticated")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"   ⚠️ Authentication error: {e}")
            return False

    def add_bank_card(self, real_name, bank_name, account_number):
        try:
            bank_select = self.driver.find_element(By.XPATH, "//*[contains(text(), '--Please select the bank name--')]")
            self.human_click(bank_select)
            time.sleep(1)
            
            bank_option = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{bank_name}')]")
            self.human_click(bank_option)
            print(f"   🏦 Selected bank: {bank_name}")
            time.sleep(1)
            
            confirm_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm')]")
            if confirm_btn:
                self.human_click(confirm_btn[0])
                time.sleep(1)
            
            account_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter the bank account number']")
            self.human_type(account_input, account_number)
            print(f"   🏦 Entered account: {account_number}")
            
            add_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add now')]")
            self.human_click(add_btn)
            print("   ✅ Bank card added")
            time.sleep(3)
            
            confirm_btn2 = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm')]")
            if confirm_btn2:
                self.human_click(confirm_btn2[0])
                time.sleep(1)
            
            return True
        except Exception as e:
            print(f"   ⚠️ Bank card error: {e}")
            return False

    def complete_withdrawal(self, amount="1800", fund_password="3333"):
        try:
            self.click_my_tab()
            time.sleep(1)
            self.click_withdrawal()
            time.sleep(2)
            
            method_select = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
            self.human_click(method_select)
            time.sleep(1)
            
            bank_option = self.driver.find_element(By.XPATH, "//*[contains(text(), 'OPAY')]")
            self.human_click(bank_option)
            print("   💳 Selected OPAY")
            time.sleep(1)
            
            confirm_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Confirm')]")
            self.human_click(confirm_btn)
            time.sleep(1)
            
            fund_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please input fund password']")
            self.human_type(fund_input, fund_password)
            print("   🔑 Entered fund password")
            time.sleep(1)
            
            amount_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Withdrawal amount']")
            self.human_type(amount_input, amount)
            print(f"   💰 Entered amount: {amount}")
            time.sleep(1)
            
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.human_click(submit_btn)
            print("   ✅ Withdrawal submitted")
            time.sleep(3)
            
            final_confirm = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm')]")
            if final_confirm:
                self.human_click(final_confirm[0])
                time.sleep(1)
            
            return True
        except Exception as e:
            print(f"   ⚠️ Withdrawal error: {e}")
            return False

    def logout(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print("   ✅ Logged out")
            return True
        except:
            return False

    def process_day(self, login_data, day):
        phone = login_data['phone']
        password = login_data['password']
        real_name = login_data['real_name']
        bank_name = login_data['bank_name']
        bank_account = login_data['bank_account']
        fund_password = login_data['fund_password']

        print(f"\n{'='*50}")
        print(f"📅 DAY {day} - {phone}")
        print(f"{'='*50}")

        if not self.login(phone, password):
            print(f"   ❌ Login failed - skipping day {day}")
            return False

        self.handle_popups()
        self.take_screenshot(f"day{day}_logged_in")

        self.do_tasks()
        self.take_screenshot(f"day{day}_tasks_done")

        if day == 3:
            print("   💰 Day 3 - Processing withdrawal...")
            
            self.click_my_tab()
            time.sleep(1)
            
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            
            page_source = self.driver.page_source.lower()
            if "bind bank card" in page_source or "authenticate now" in page_source:
                print("   🏦 Setting up bank details...")
                
                self.click_my_tab()
                time.sleep(1)
                
                add_bank_links = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Add a bank account')]")
                if add_bank_links:
                    self.human_click(add_bank_links[0])
                    time.sleep(2)
                
                auth_btn = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Authenticate now')]")
                if auth_btn:
                    self.authenticate_real_name(real_name)
                    time.sleep(2)
                
                self.add_bank_card(real_name, bank_name, bank_account)
                time.sleep(2)
                
                fund_inputs = self.driver.find_elements(By.XPATH, "//input[@placeholder='Please enter the new funds password']")
                if fund_inputs:
                    self.set_fund_password(fund_password)
                    time.sleep(2)
            
            self.complete_withdrawal("1800", fund_password)
            self.take_screenshot(f"day{day}_withdrawal_done")
        
        self.logout()
        self.take_screenshot(f"day{day}_logged_out")
        return True

    def process_account(self, login_data):
        phone = login_data['phone']
        print(f"\n{'#'*60}")
        print(f"📱 Processing account: {phone}")
        print(f"🏦 Bank: {login_data['bank_name']}")
        print(f"{'#'*60}")

        for day in range(1, 4):
            if not self.process_day(login_data, day):
                print(f"❌ Day {day} failed for {phone} - skipping remaining days")
                return False
            if day < 3:
                time.sleep(random.uniform(3, 6))

        self.successful += 1
        return True

    def run(self):
        print("="*60)
        print(f"🤖 BOT {self.bot_id} STARTING")
        print(f"📋 Total logins: {len(self.logins)}")
        print(f"📅 Each account processed for 3 days")
        print("="*60)

        for i, login_data in enumerate(self.logins):
            print(f"\n{'#'*50}")
            print(f"📱 Account {i + 1}/{len(self.logins)}")
            print(f"{'#'*50}")

            self.process_account(login_data)

            if i < len(self.logins) - 1:
                delay = random.uniform(5, 10)
                print(f"⏳ Waiting {delay:.1f}s before next account...")
                time.sleep(delay)

        print("\n" + "="*60)
        print(f"📊 BOT {self.bot_id} COMPLETE")
        print(f"✅ Successfully processed: {self.successful}")
        print(f"❌ Failed: {self.failed}")
        print("="*60)

        self.driver.quit()

if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', 1))
    start_index = int(os.environ.get('START_INDEX', 0))

    bot = NRCBot(bot_id=bot_id, start_index=start_index)
    bot.run()