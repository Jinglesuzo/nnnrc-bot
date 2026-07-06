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
            element.clear()
            time.sleep(0.1)
            return True
        except:
            return False

    def type_text(self, element, text):
        self.clear_field(element)
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

    # helper: case-insensitive contains(text(), ...)
    def xpath_contains_ci(self, text):
        # returns an xpath snippet for case-insensitive contains(text(), text)
        return f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')"

    def find_clickable(self, xpath, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except:
            return None

    def find_presence(self, xpath, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except:
            return None

    # ============================================
    # LOGIN - SIMPLE AND RELIABLE
    # ============================================

    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")
            
            # Phone
            phone_field = self.find_presence("//input[@placeholder='Please enter your phone number']", timeout=10) or \
                          self.find_presence("//input[contains(@placeholder, 'phone')]", timeout=5)
            if not phone_field:
                print("   ❌ Phone input not found")
                return False
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")
            
            # Password
            password_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Please enter login password']") if \
                             self.find_presence("//input[@placeholder='Please enter login password']", timeout=3) else \
                             self.find_presence("//input[@type='password']", timeout=5)
            if not password_field:
                print("   ❌ Password input not found")
                return False
            password_field.clear()
            password_field.send_keys(password)
            print(f"   ✅ Password entered")
            self.screenshot("03_password_entered")
            
            # Login button - SIMPLE CLICK
            login_btn = self.find_clickable("//button[contains(., 'Log in now')]", timeout=10) or \
                        self.find_clickable("//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in')]", timeout=5)
            if not login_btn:
                print("   ❌ Login button not found")
                return False
            login_btn.click()
            print(f"   ✅ Clicked login")
            self.screenshot("04_after_login_click")
            
            # Wait for login to process
            time.sleep(5)
            self.screenshot("05_after_login_wait")
            
            # Check if login successful
            page_source = self.driver.page_source.lower()
            if "important notice" in page_source or "cooperative wealth zone" in page_source or "welcome" in page_source:
                print(f"   ✅ Login success!")
                self.logged_in_accounts.append(phone)
                return True
            else:
                # try another indicator: presence of user menu or /user path
                if "/#/user" in self.driver.current_url or self.find_presence("//*[contains(@class,'user')]", timeout=3):
                    print(f"   ✅ Login success (url or user element detected)!")
                    self.logged_in_accounts.append(phone)
                    return True
                print(f"   ❌ Login failed")
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
            # find any elements that contain "important notice" (case-insensitive)
            notices = self.driver.find_elements(By.XPATH, f"//*[ {self.xpath_contains_ci('important notice')} ] | //*[ {self.xpath_contains_ci('welcome')} ] | //*[ {self.xpath_contains_ci('important')} ]")
            if notices:
                print("   📋 Found Important Notice / Welcome")
                self.screenshot("important_notice_found")

                # First try known buttons like NEWS, Got it, OK, Close, ×, modal close
                close_xpaths = [
                    "//button[" + self.xpath_contains_ci("got it") + "]",
                    "//button[" + self.xpath_contains_ci("ok") + "]",
                    "//button[" + self.xpath_contains_ci("close") + "]",
                    "//*[contains(@class, 'modal-close')]",
                    "//*[contains(@class, 'close')]",
                    "//*[text()='×']",
                    "//button[@aria-label='Close']",
                ]
                for xp in close_xpaths:
                    try:
                        elems = self.driver.find_elements(By.XPATH, xp)
                        for el in elems:
                            if el.is_displayed() and el.is_enabled():
                                self.click_element(el)
                                print(f"   🚫 Closed popup using xpath: {xp}")
                                time.sleep(0.8)
                    except Exception as e:
                        # don't fail the whole flow if one xpath fails
                        print(f"   ⚠️ close xpath failed: {xp} -> {e}")

                # try clicking any NEWS buttons if present
                try:
                    news_btns = self.driver.find_elements(By.XPATH, f"//*[ {self.xpath_contains_ci('news')} ] | //button[{self.xpath_contains_ci('news')}]")
                    for nb in news_btns:
                        if nb.is_displayed() and nb.is_enabled():
                            self.click_element(nb)
                            print("   📰 Clicked NEWS button")
                            time.sleep(0.8)
                except Exception as e:
                    print(f"   ⚠️ news button check failed: {e}")

                # last resort: click any visible modal close icons/buttons
                try:
                    candidates = self.driver.find_elements(By.XPATH, "//*[contains(@class,'modal')]//*[contains(@class,'close') or contains(@class,'close-btn')] | //*[contains(@class,'overlay')]//button")
                    for c in candidates:
                        if c.is_displayed() and c.is_enabled():
                            self.click_element(c)
                            time.sleep(0.5)
                except:
                    pass

                self.screenshot("popups_removed")
                return True
            else:
                print("   ℹ️ No Important Notice found")
                return True
        except Exception as e:
            print(f"   ❌ remove_important_notice error: {e}")
            return True

    # ============================================
    # TASKS
    # ============================================
    def do_tasks(self):
        print("   📋 Starting tasks...")
        
        # Click Task tab if present
        try:
            task_tab = self.driver.find_elements(By.XPATH, f"//*[ {self.xpath_contains_ci('task')} ]")
            if task_tab:
                self.click_element(task_tab[0])
                time.sleep(2)
                self.screenshot("tasks_page")
        except:
            print("   ⚠️ Could not find Task tab")

        total = 0
        # Try to perform up to 6 tasks; wait 20s per task as requested
        for i in range(6):
            try:
                # look for buttons that contain 'read' (case-insensitive)
                read_btns = self.driver.find_elements(By.XPATH, f"//button[{self.xpath_contains_ci('read')}] | //a[{self.xpath_contains_ci('read')}]")
                btn = None
                for b in read_btns:
                    if b.is_displayed() and b.is_enabled():
                        btn = b
                        break
                if not btn:
                    break
                self.click_element(btn)
                total += 1
                print(f"   📖 Task {total} started - waiting 20s")
                time.sleep(20)
                print(f"   ✅ Task {total} done")
                # try to close any task modal or go back
                try:
                    close_btns = self.driver.find_elements(By.XPATH, "//button[" + self.xpath_contains_ci("close") + "] | //button[" + self.xpath_contains_ci("got it") + "] | //button[text()='×']")
                    for cb in close_btns:
                        if cb.is_displayed() and cb.is_enabled():
                            self.click_element(cb)
                            time.sleep(0.5)
                except:
                    pass
            except Exception as e:
                print(f"   ⚠️ Task loop exception: {e}")
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
            
            # Click Confirm
            confirm_btn = self.find_clickable("//button[" + self.xpath_contains_ci("confirm") + "]", timeout=10) or \
                          self.find_clickable("//button[contains(., 'Confirm')]", timeout=5)
            if confirm_btn:
                confirm_btn.click()
                print("   ✅ Clicked Confirm")
                time.sleep(2)
                self.screenshot("confirm_clicked")
                return True
            else:
                print("   ⚠️ Confirm button not found")
                return False
        except Exception as e:
            print(f"   ❌ Could not complete withdrawal: {e}")
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
            
            # Click Fund password (case-insensitive)
            fund_pw_btn = self.find_clickable(f"//*[ {self.xpath_contains_ci('fund password')} ] | //button[{self.xpath_contains_ci('fund password')}]", timeout=10)
            if fund_pw_btn:
                self.click_element(fund_pw_btn)
                time.sleep(1)
                self.screenshot("fund_password_clicked")
            else:
                print("   ⚠️ Fund password button not found (continuing)")
            
            # Enter new password
            new_pw = self.find_presence("//input[@placeholder='Please enter the new funds password']", timeout=6) or \
                     self.find_presence("//input[contains(@placeholder,'fund') or contains(@placeholder,'funds') or @type='password']", timeout=4)
            if not new_pw:
                print("   ❌ New fund password input not found")
                return False
            new_pw.clear()
            new_pw.send_keys(fund_password)
            
            # Confirm password
            confirm_pw = self.driver.find_element(By.XPATH, "//input[@placeholder='Please confirm the fund password']") if \
                         self.find_presence("//input[@placeholder='Please confirm the fund password']", timeout=3) else \
                         self.find_presence("//input[contains(@placeholder,'confirm') and @type='password']", timeout=4)
            if not confirm_pw:
                print("   ❌ Confirm fund password input not found")
                return False
            confirm_pw.clear()
            confirm_pw.send_keys(fund_password)
            self.screenshot("fund_password_entered")
            
            # Click Submit
            submit_btn = self.find_clickable("//button[" + self.xpath_contains_ci("submit") + "]", timeout=10) or \
                         self.find_clickable("//button[contains(., 'Submit')]", timeout=5)
            if submit_btn:
                submit_btn.click()
                print("   ✅ Fund password set")
                time.sleep(2)
                self.screenshot("fund_password_submitted")
                return True
            else:
                print("   ❌ Submit button not found for fund password")
                return False
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
            
            # Click Add a bank account
            add_bank = self.find_clickable(f"//*[ {self.xpath_contains_ci('add a bank account')} ] | //button[{self.xpath_contains_ci('add a bank account')}]", timeout=8) or \
                       self.find_clickable("//button[" + self.xpath_contains_ci("add bank") + "]", timeout=5)
            if add_bank:
                self.click_element(add_bank)
                time.sleep(1)
                self.screenshot("add_bank_clicked")
            else:
                print("   ⚠️ Add bank button not found (continuing, trying to find authenticate directly)")

            # Click Authenticate now
            auth_btn = self.find_clickable("//button[" + self.xpath_contains_ci("authenticate now") + "]", timeout=8) or \
                       self.find_clickable("//button[" + self.xpath_contains_ci("authenticate") + "]", timeout=5)
            if auth_btn:
                self.click_element(auth_btn)
                time.sleep(1)
                self.screenshot("authenticate_clicked")
            else:
                print("   ⚠️ Authenticate now button not found (continuing)")

            # Enter real name
            name_input = self.find_presence("//input[@placeholder='Please enter a real name']", timeout=8) or \
                         self.find_presence("//input[contains(@placeholder,'real name') or contains(@placeholder,'name')]", timeout=4)
            if not name_input:
                print("   ❌ Name input not found")
                return False
            name_input.clear()
            name_input.send_keys(login_data['real_name'])
            print(f"   👤 Entered name: {login_data['real_name']}")
            self.screenshot("name_entered")

            # Submit real name if there's a submit
            submit_btn = self.find_clickable("//button[" + self.xpath_contains_ci("submit") + "]", timeout=4)
            if submit_btn:
                submit_btn.click()
                time.sleep(1)
                self.screenshot("name_submitted")

            # Select bank (open dropdown and pick option)
            try:
                bank_select = self.find_clickable("//*[contains(., '--Please select the bank name--')] | //select", timeout=6)
                if bank_select:
                    self.click_element(bank_select)
                    time.sleep(0.8)
                # try to click bank option by visible text
                bank_option = None
                # option element (select > option)
                try:
                    opts = self.driver.find_elements(By.XPATH, f"//option[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{login_data['bank_name'].lower()}')]")
                    if opts:
                        opts[0].click()
                        bank_option = opts[0]
                except:
                    pass
                if not bank_option:
                    # fallback clickable items
                    bank_option = self.find_clickable(f"//*[ {self.xpath_contains_ci(login_data['bank_name'])} ]", timeout=6)
                    if bank_option:
                        self.click_element(bank_option)
                if bank_option:
                    print(f"   🏦 Selected bank: {login_data['bank_name']}")
                    self.screenshot("bank_selected")
                else:
                    print("   ⚠️ Bank option not found (continuing)")
            except Exception as e:
                print(f"   ⚠️ Bank selection issue: {e}")

            # Enter account number
            account_input = self.find_presence("//input[@placeholder='Please enter the bank account number']",
                                               timeout=8) or self.find_presence("//input[contains(@placeholder,'account') or contains(@name,'account')]", timeout=4)
            if not account_input:
                print("   ❌ Account input not found")
                return False
            account_input.clear()
            account_input.send_keys(login_data['bank_account'])
            print(f"   🏦 Entered account: {login_data['bank_account']}")
            self.screenshot("account_entered")

            # Click Add now / Add button
            add_btn = self.find_clickable("//button[" + self.xpath_contains_ci("add now") + "]", timeout=8) or \
                      self.find_clickable("//button[" + self.xpath_contains_ci("add") + "]", timeout=5)
            if add_btn:
                add_btn.click()
                print("   ✅ Bank card added")
                time.sleep(2)
                self.screenshot("bank_added")
                return True
            else:
                print("   ❌ Add bank button not found")
                return False
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
        fund_password = login_data.get('fund_password', '3333')
        
        print(f"\n📱 Account: {phone}")
        
        if not self.login(phone, password):
            return False
        
        self.remove_important_notice()
        self.screenshot("after_popup_removal")
        
        self.do_tasks()
        self.screenshot("after_tasks")
        
        # try withdrawal (optional)
        try:
            self.complete_withdrawal()
        except:
            pass
        
        # set fund password
        self.set_fund_password(fund_password)
        
        # add bank account
        self.add_bank_account(login_data)
        
        self.sign_out()
        
        return True

    def run(self):
        print("="*50)
        print(f"