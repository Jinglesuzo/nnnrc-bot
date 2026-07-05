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
        self.max_login_retries = 2
        self.step_counter = 0

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

    def screenshot(self, name):
        self.step_counter += 1
        try:
            filename = f"bot{self.bot_id}_{self.step_counter:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
            return True
        except:
            return False

    def type_text(self, element, text):
        try:
            element.click()
            time.sleep(0.1)
            element.clear()
            time.sleep(0.1)
            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.03, 0.07))
            return True
        except Exception as e:
            print(f"   ⚠️ Type error: {e}")
            return False

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

    def wait_for_page(self, timeout=30):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            return True
        except TimeoutException:
            print(f"   ⏰ Page load timeout")
            return False

    # === FIND GREEN LOGIN BUTTON ===
    def find_login_button(self):
        print(f"   🔍 Looking for login button...")
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[text()='Log in now']")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found 'Log in now'")
                return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in now')]")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found 'Log in now' (contains)")
                return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log in')]")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found 'Log in'")
                return btn
        except:
            pass
        
        try:
            btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if btn.is_displayed() and btn.is_enabled():
                print(f"   ✅ Found submit button")
                return btn
        except:
            pass
        
        print(f"   ❌ No login button found")
        self.screenshot("login_button_not_found")
        return None

    # === LOGIN ===
    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        
        for attempt in range(self.max_login_retries):
            try:
                print(f"   Attempt {attempt + 1}/{self.max_login_retries}")
                
                self.driver.get("https://nnnrc.com/#/login")
                time.sleep(2)
                self.screenshot("login_page")
                
                if not self.wait_for_page(30):
                    print(f"   ⏰ Timeout, reloading...")
                    self.driver.refresh()
                    time.sleep(2)
                    continue
                
                # Phone
                phone_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter your phone number']"))
                )
                self.type_text(phone_field, phone)
                print(f"   ✅ Phone: {phone}")
                self.screenshot("phone_entered")
                
                # Password
                password_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please enter login password']"))
                )
                self.type_text(password_field, password)
                print(f"   ✅ Password entered")
                self.screenshot("password_entered")
                
                # Find and click login button
                login_btn = self.find_login_button()
                if login_btn:
                    self.click_element(login_btn)
                    print(f"   ✅ Clicked login")
                    self.screenshot("after_login_click")
                else:
                    print(f"   ❌ No login button found, retrying...")
                    time.sleep(1)
                    continue
                
                time.sleep(5)
                self.screenshot("after_login_wait")
                
                # Check if login successful - LOOK FOR "Important Notice" TOO
                page_source = self.driver.page_source.lower()
                current_url = self.driver.current_url.lower()
                
                # SUCCESS: Important Notice means login worked!
                if "important notice" in page_source:
                    print(f"   ✅ Login SUCCESS! (Important Notice found)")
                    self.screenshot("login_success_important_notice")
                    return True
                
                if "cooperative wealth zone" in page_source or "dashboard" in current_url:
                    print(f"   ✅ Login SUCCESS!")
                    self.screenshot("login_success")
                    return True
                
                if "invalid" in page_source or "incorrect" in page_source:
                    print(f"   ❌ Invalid credentials")
                    self.screenshot("login_invalid")
                    return False
                
                print(f"   ❌ Login failed, retrying...")
                time.sleep(2)
                
            except Exception as e:
                print(f"   ⚠️ Login error: {e}")
                self.screenshot("login_error")
                time.sleep(2)
                continue
        
        print(f"   ❌ Login failed after {self.max_login_retries} attempts")
        self.screenshot("login_failed")
        return False

    # === HANDLE POPUPS ===
    def handle_popups(self):
        print("   📋 Handling Important Notice popup...")
        self.screenshot("before_popup_handling")
        
        # Look for Important Notice
        try:
            important_notice = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Important Notice')]")
            if important_notice.is_displayed():
                print("   📋 Found Important Notice popup")
                self.screenshot("important_notice_found")
                
                # Look for NEWS button (green button that says NEWS)
                try:
                    news_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'NEWS')] | //*[contains(text(), 'News')] | //button[contains(text(), 'NEWS')]")
                    if news_btn.is_displayed() and news_btn.is_enabled():
                        self.click_element(news_btn)
                        print("   📰 Clicked NEWS button")
                        self.screenshot("after_news_click")
                        time.sleep(3)
                except Exception as e:
                    print(f"   ⚠️ NEWS button not found: {e}")
                    # Try to find any green button
                    try:
                        green_btns = self.driver.find_elements(By.XPATH, "//button[contains(@style, 'green')] | //*[contains(@class, 'green')]")
                        for btn in green_btns:
                            if btn.is_displayed() and btn.is_enabled():
                                self.click_element(btn)
                                print("   📰 Clicked green button (NEWS)")
                                self.screenshot("after_news_click")
                                time.sleep(3)
                                break
                    except:
                        pass
                
                # Close Welcome popup if present
                try:
                    welcome_close = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Got it')] | //button[contains(text(), 'OK')] | //*[contains(@class, 'modal-close')] | //*[text()='×']")
                    if welcome_close.is_displayed() and welcome_close.is_enabled():
                        self.click_element(welcome_close)
                        print("   🚫 Closed Welcome popup")
                        self.screenshot("after_popup_close")
                        time.sleep(1)
                except:
                    pass
                
                # Close any remaining ads/popups
                try:
                    close_btns = self.driver.find_elements(By.XPATH, "//*[contains(@class, 'close')] | //*[text()='×'] | //*[text()='✕'] | //button[contains(@class, 'btn-close')]")
                    for btn in close_btns:
                        if btn.is_displayed() and btn.is_enabled():
                            self.click_element(btn)
                            time.sleep(0.3)
                    print("   ✅ Closed remaining popups")
                except:
                    pass
                
                self.screenshot("after_all_popups")
                print("   ✅ Popups handled successfully")
                return True
        except:
            pass
        
        print("   ✅ No popups found")
        self.screenshot("no_popups")
        return True

    # === TASKS ===
    def do_tasks(self):
        print("   📋 Doing tasks...")
        self.screenshot("before_tasks")
        
        # Click Task tab
        try:
            task_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Task')] | //button[contains(text(), 'Task')]")
            self.click_element(task_tab)
            print("   📋 Clicked Task tab")
            self.screenshot("after_task_click")
            time.sleep(2)
        except:
            print("   ⚠️ Could not find Task tab")
            self.screenshot("task_tab_error")
        
        # Find read buttons
        read_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'read')] | //*[contains(text(), 'read')]")
        if not read_buttons:
            read_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Read')]")
        
        count = 0
        for btn in read_buttons:
            try:
                if btn.is_displayed() and btn.is_enabled():
                    self.click_element(btn)
                    print(f"   📖 Clicked read task {count + 1}")
                    self.screenshot(f"task_{count+1}_clicked")
                    time.sleep(1)
                    print(f"   ⏳ Waiting 20 seconds...")
                    time.sleep(20)
                    self.screenshot(f"task_{count+1}_done")
                    count += 1
            except Exception as e:
                print(f"   ⚠️ Task error: {e}")
                self.screenshot(f"task_{count+1}_error")
        
        print(f"   ✅ Completed {count} tasks")
        self.screenshot("tasks_completed")
        return count

    # === WITHDRAWAL ===
    def click_my_tab(self):
        try:
            my_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'My')] | //button[contains(text(), 'My')]")
            self.click_element(my_tab)
            print("   👤 Clicked My")
            self.screenshot("after_my_click")
            time.sleep(1)
            return True
        except:
            print("   ⚠️ Could not find My tab")
            return False

    def click_withdrawal(self):
        try:
            withdrawal = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Withdrawal')] | //button[contains(text(), 'Withdrawal')]")
            self.click_element(withdrawal)
            print("   💰 Clicked Withdrawal")
            self.screenshot("after_withdrawal_click")
            time.sleep(2)
            return True
        except:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            return True

    def set_fund_password(self, password):
        try:
            fund_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter the new funds password']")
            self.type_text(fund_input, password)
            print("   🔑 Entered fund password")
            
            confirm_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please confirm the fund password']")
            self.type_text(confirm_input, password)
            print("   🔑 Confirmed fund password")
            
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.click_element(submit_btn)
            print("   ✅ Fund password set")
            self.screenshot("fund_password_set")
            time.sleep(2)
            return True
        except:
            return False

    def authenticate_real_name(self, name):
        try:
            auth_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Authenticate now')]")
            self.click_element(auth_btn)
            time.sleep(2)
            
            name_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter a real name']")
            self.type_text(name_input, name)
            print(f"   👤 Entered name: {name}")
            
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.click_element(submit_btn)
            print("   ✅ Real name authenticated")
            self.screenshot("real_name_authenticated")
            time.sleep(2)
            return True
        except:
            return False

    def add_bank_card(self, bank_name, account_number):
        try:
            bank_select = self.driver.find_element(By.XPATH, "//*[contains(text(), '--Please select the bank name--')]")
            self.click_element(bank_select)
            time.sleep(1)
            
            bank_option = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{bank_name}')]")
            self.click_element(bank_option)
            print(f"   🏦 Selected bank: {bank_name}")
            time.sleep(1)
            
            account_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter the bank account number']")
            self.type_text(account_input, account_number)
            print(f"   🏦 Entered account: {account_number}")
            
            add_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add now')]")
            self.click_element(add_btn)
            print("   ✅ Bank card added")
            self.screenshot("bank_card_added")
            time.sleep(3)
            return True
        except:
            return False

    def complete_withdrawal(self, amount="1800", fund_password="3333"):
        try:
            self.click_my_tab()
            time.sleep(1)
            self.click_withdrawal()
            time.sleep(2)
            
            method_select = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Select withdrawal method')]")
            self.click_element(method_select)
            time.sleep(1)
            
            bank_option = self.driver.find_element(By.XPATH, "//*[contains(text(), 'OPAY')]")
            self.click_element(bank_option)
            print("   💳 Selected OPAY")
            time.sleep(1)
            
            fund_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Please input fund password']")
            self.type_text(fund_input, fund_password)
            print("   🔑 Entered fund password")
            
            amount_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Withdrawal amount']")
            self.type_text(amount_input, amount)
            print(f"   💰 Entered amount: {amount}")
            
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.click_element(submit_btn)
            print("   ✅ Withdrawal submitted")
            self.screenshot("withdrawal_submitted")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"   ⚠️ Withdrawal error: {e}")
            return False

    def logout(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(2)
            print("   ✅ Logged out")
            self.screenshot("logged_out")
            return True
        except:
            return False

    # === PROCESS DAY ===
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
        self.screenshot(f"day{day}_after_popups")

        self.do_tasks()
        self.screenshot(f"day{day}_after_tasks")

        if day == 3:
            print("   💰 Day 3 - Processing withdrawal...")
            self.screenshot(f"day{day}_before_withdrawal")
            
            self.click_my_tab()
            time.sleep(1)
            
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            
            page_source = self.driver.page_source.lower()
            if "bind bank card" in page_source or "authenticate now" in page_source:
                print("   🏦 Setting up bank details...")
                self.screenshot("bank_setup_start")
                
                self.click_my_tab()
                time.sleep(1)
                
                try:
                    add_bank = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Add a bank account')]")
                    self.click_element(add_bank)
                    time.sleep(2)
                except:
                    pass
                
                if "authenticate now" in page_source:
                    self.authenticate_real_name(real_name)
                    time.sleep(2)
                
                self.add_bank_card(bank_name, bank_account)
                time.sleep(2)
                
                try:
                    self.set_fund_password(fund_password)
                    time.sleep(2)
                except:
                    pass
            
            self.complete_withdrawal("1800", fund_password)
            self.screenshot(f"day{day}_withdrawal_done")
        
        self.logout()
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