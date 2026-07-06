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
import traceback

# Configuration
HEADLESS = os.environ.get("HEADLESS", "1").lower() not in ("0", "false", "no")
DEBUG = os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")
TASK_COUNT = int(os.environ.get("TASK_COUNT", "6"))
TASK_WAIT = int(os.environ.get("TASK_WAIT", "20"))
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

class NRCBot:
    def __init__(self, bot_id=1):
        self.bot_id = bot_id
        self.step = 0
        self.logged_in_accounts = []
        self.load_logins()

        options = Options()
        if HEADLESS:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        print(f"🤖 Bot {self.bot_id} Starting Chrome...")
        try:
            service = Service(CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started!")
        except Exception:
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ Bot {self.bot_id} Chrome started (webdriver_manager)!")
            except Exception as e:
                print("❌ Could not start Chrome webdriver:", e)
                raise

        self.driver.implicitly_wait(2)

    def screenshot(self, name):
        self.step += 1
        try:
            filename = f"bot{self.bot_id}_{self.step:03d}_{name}.png"
            self.driver.save_screenshot(filename)
            print(f"   📸 {filename}")
        except Exception as e:
            print("   ⚠️ Screenshot failed:", e)

    def save_html(self, name):
        if not DEBUG:
            return
        try:
            filename = f"bot{self.bot_id}_{name}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"   💾 Saved page HTML: {filename}")
        except Exception as e:
            print("   ⚠️ Save HTML failed:", e)

    def log_exception(self, where, exc):
        print(f"   ❌ {where} exception: {exc}")
        if DEBUG:
            self.screenshot(f"{where}_exception")
            self.save_html(f"{where}_exception")
            traceback.print_exc()

    def load_logins(self):
        try:
            with open('logins.csv', 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                first = next(reader)
                if all(s.lower() in ("phone", "password", "real_name", "bank_name", "bank_account", "fund_password") for s in [c.strip().lower() for c in first]):
                    rows = list(reader)
                else:
                    rows = [first] + list(reader)
                self.logins = []
                for row in rows:
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
                            'real_name': row[2].strip() if len(row) > 2 else 'John Penn',
                            'bank_name': row[3].strip() if len(row) > 3 else 'OPAY',
                            'bank_account': row[4].strip() if len(row) > 4 else '9074331299',
                            'fund_password': row[5].strip() if len(row) > 5 else '3333'
                        })
            print(f"📋 Bot {self.bot_id} Loaded {len(self.logins)} login(s)")
        except FileNotFoundError:
            print("⚠️ logins.csv not found — using default dummy account")
            self.logins = [{'phone': '08057536473', 'password': 'people56', 'real_name': 'John Penn', 'bank_name': 'OPAY', 'bank_account': '9074331299', 'fund_password': '3333'}]
        except Exception as e:
            print("❌ Error loading logins.csv:", e)
            self.logins = []

    def clear_field(self, element):
        try:
            element.click()
            time.sleep(0.05)
            element.clear()
            time.sleep(0.05)
            return True
        except Exception:
            try:
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
                return True
            except:
                return False

    def type_text(self, element, text):
        self.clear_field(element)
        element.send_keys(text)
        time.sleep(0.08)

    def click_element(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.15)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            try:
                element.click()
                return True
            except Exception:
                return False

    def xpath_contains_ci(self, text):
        return f"contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')"

    def find_presence(self, xpath, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except Exception:
            return None

    def find_clickable(self, xpath, timeout=8):
        try:
            return WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        except Exception:
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

            phone_xps = [
                "//input[@placeholder='Please enter your phone number']",
                "//input[contains(@placeholder,'phone')]",
                "//input[@name='phone']",
                "//input[@type='tel']",
            ]
            phone_field = None
            for xp in phone_xps:
                try:
                    phone_field = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
                    if phone_field:
                        break
                except Exception:
                    continue
            if not phone_field:
                print("   ❌ Phone input not found.")
                return False
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")

            pw_xps = [
                "//input[@placeholder='Please enter login password']",
                "//input[contains(@placeholder,'password')]",
                "//input[@type='password']"
            ]
            password_field = None
            for xp in pw_xps:
                try:
                    password_field = WebDriverWait(self.driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
                    if password_field:
                        break
                except Exception:
                    continue
            if not password_field:
                print("   ❌ Password input not found.")
                return False
            password_field.clear()
            password_field.send_keys(password)
            print("   ✅ Password entered")
            self.screenshot("03_password_entered")

            # Click login button
            btn_xps = [
                "//button[contains(., 'Log in now')]",
                "//button[@type='submit']",
            ]
            clicked = False
            for xp in btn_xps:
                try:
                    btn = self.find_clickable(xp, timeout=4)
                    if btn:
                        print(f"   🔘 Clicking login button")
                        if self.click_element(btn):
                            clicked = True
                            break
                except Exception:
                    continue
            if not clicked:
                print("   ❌ Login button not found/clickable.")
                return False

            time.sleep(5)
            self.screenshot("04_after_login_wait")
            page_source = self.driver.page_source.lower()
            if any(k in page_source for k in ("important notice", "cooperative wealth zone", "welcome", "logout")) or "/#/user" in self.driver.current_url.lower():
                print("   ✅ Login success!")
                self.logged_in_accounts.append(phone)
                return True
            else:
                print("   ❌ Login failed")
                return False
        except Exception as e:
            self.log_exception("login", e)
            return False

    # ============================================
    # POPUP REMOVAL
    # ============================================
    def remove_important_notice(self):
        print("   ℹ️ Checking for popups...")
        try:
            # Click NEWS button if present
            try:
                news_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'NEWS')] | //button[contains(text(), 'NEWS')]")
                if news_btn.is_displayed() and news_btn.is_enabled():
                    self.click_element(news_btn)
                    print("   📰 Clicked NEWS button")
                    time.sleep(2)
                    self.screenshot("news_clicked")
            except:
                pass

            # Close any popups
            close_xpaths = [
                "//button[contains(text(), 'Got it')]",
                "//button[contains(text(), 'OK')]",
                "//button[contains(text(), 'Close')]",
                "//*[contains(@class, 'modal-close')]",
                "//*[contains(@class, 'close')]",
                "//*[text()='×']",
            ]
            for xp in close_xpaths:
                try:
                    elems = self.driver.find_elements(By.XPATH, xp)
                    for el in elems:
                        if el.is_displayed() and el.is_enabled():
                            self.click_element(el)
                            print(f"   🚫 Closed popup")
                            time.sleep(0.5)
                except:
                    pass

            self.screenshot("popups_removed")
            return True
        except Exception as e:
            self.log_exception("remove_important_notice", e)
            return True

    # ============================================
    # TASKS
    # ============================================
    def do_tasks(self):
        print("   📋 Starting tasks...")
        
        # Click Task tab
        try:
            task_tab = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Task')] | //button[contains(text(), 'Task')]")
            self.click_element(task_tab)
            print("   📋 Clicked Task tab")
            time.sleep(2)
            self.screenshot("tasks_tab_clicked")
        except Exception as e:
            print(f"   ⚠️ Could not click Task tab: {e}")

        # Find and click read buttons
        total = 0
        max_attempts = 30
        
        for attempt in range(max_attempts):
            if total >= TASK_COUNT:
                break
                
            try:
                read_btn = None
                
                # Method 1: By text "read"
                try:
                    read_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'read')]")
                except:
                    pass
                
                # Method 2: By text "Read"
                if not read_btn:
                    try:
                        read_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Read')]")
                    except:
                        pass
                
                # Method 3: By any element with "read"
                if not read_btn:
                    try:
                        read_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'read')]")
                    except:
                        pass
                
                if not read_btn:
                    print(f"   ⏳ No read tasks found (attempt {attempt+1})")
                    time.sleep(1)
                    continue
                
                if read_btn.is_displayed() and read_btn.is_enabled():
                    self.click_element(read_btn)
                    total += 1
                    print(f"   📖 Task {total} started - waiting {TASK_WAIT}s")
                    self.screenshot(f"task_{total}_started")
                    time.sleep(TASK_WAIT)
                    print(f"   ✅ Task {total} done")
                    self.screenshot(f"task_{total}_done")
                    
                    # Close any popups
                    try:
                        close_btns = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Close')] | //button[contains(text(), '×')] | //*[contains(@class, 'close')]")
                        for cb in close_btns:
                            if cb.is_displayed() and cb.is_enabled():
                                self.click_element(cb)
                                time.sleep(0.3)
                    except:
                        pass
                else:
                    print(f"   ⚠️ Read button not clickable")
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"   ⚠️ Task error: {e}")
                time.sleep(1)
                continue
        
        print(f"   ✅ Completed {total} tasks")
        self.screenshot("tasks_completed")
        return total

    # ============================================
    # FUND PASSWORD - FIXED
    # ============================================
    def set_fund_password(self, fund_password):
        print("   🔑 Setting fund password...")
        try:
            # GO TO USER/INFO
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(3)
            self.screenshot("01_user_info_page")
            print("   ✅ User info page loaded")
            
            # Click "Fund password" (Click Settings)
            fund_pw_btn = self.find_clickable("//*[contains(text(), 'Fund password')]", timeout=10)
            if fund_pw_btn:
                self.click_element(fund_pw_btn)
                time.sleep(2)
                self.screenshot("02_fund_password_clicked")
                print("   ✅ Clicked Fund password")
            else:
                print("   ❌ Could not find Fund password button")
                self.screenshot("03_fund_password_not_found")
                return False

            # Enter new fund password
            new_pw = self.find_presence("//input[@placeholder='Please enter the new funds password']", timeout=10)
            if not new_pw:
                print("   ❌ Could not find 'Please enter the new funds password' input")
                self.screenshot("04_new_password_not_found")
                return False
            new_pw.clear()
            new_pw.send_keys(fund_password)
            print(f"   ✅ Entered new fund password: {fund_password}")
            self.screenshot("05_new_password_entered")

            # Confirm fund password
            confirm_pw = self.find_presence("//input[@placeholder='Please confirm the fund password']", timeout=10)
            if not confirm_pw:
                print("   ❌ Could not find 'Please confirm the fund password' input")
                self.screenshot("06_confirm_password_not_found")
                return False
            confirm_pw.clear()
            confirm_pw.send_keys(fund_password)
            print(f"   ✅ Confirmed fund password: {fund_password}")
            self.screenshot("07_confirm_password_entered")

            # Click Submit
            submit_btn = self.find_clickable("//button[contains(text(), 'Submit')]", timeout=10)
            if submit_btn:
                self.click_element(submit_btn)
                time.sleep(2)
                self.screenshot("08_submit_clicked")
                print("   ✅ Fund password set successfully!")
                return True
            else:
                print("   ❌ Could not find Submit button")
                self.screenshot("09_submit_not_found")
                return False
                
        except Exception as e:
            self.log_exception("set_fund_password", e)
            return False

    # ============================================
    # WITHDRAWAL
    # ============================================
    def complete_withdrawal(self):
        print(f"   💰 Processing withdrawal...")
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(2)
            self.screenshot("withdrawal_page")
            confirm_btn = self.find_clickable("//button[contains(text(), 'Confirm')]", timeout=6)
            if confirm_btn:
                self.click_element(confirm_btn)
                print("   ✅ Clicked Confirm")
                time.sleep(2)
                self.screenshot("confirm_clicked")
                return True
            else:
                print("   ⚠️ Confirm button not found")
                return False
        except Exception as e:
            self.log_exception("complete_withdrawal", e)
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

            add_bank_btn = self.find_clickable("//*[contains(text(), 'Add a bank account')]", timeout=6)
            if add_bank_btn:
                self.click_element(add_bank_btn)
                time.sleep(1)
                self.screenshot("add_bank_clicked")
            else:
                print("   ⚠️ Add bank button not found")

            auth_btn = self.find_clickable("//button[contains(text(), 'Authenticate now')]", timeout=6)
            if auth_btn:
                self.click_element(auth_btn)
                time.sleep(1)
                self.screenshot("authenticate_clicked")

            name_input = self.find_presence("//input[@placeholder='Please enter a real name']", timeout=6)
            if name_input:
                name_input.clear()
                name_input.send_keys(login_data.get('real_name', 'John Penn'))
                print(f"   👤 Entered name: {login_data.get('real_name')}")
                self.screenshot("name_entered")
                
                submit_btn = self.find_clickable("//button[contains(text(), 'Submit')]", timeout=3)
                if submit_btn:
                    self.click_element(submit_btn)
                    time.sleep(1)

            # Select bank
            bank_name = login_data.get('bank_name', 'OPAY')
            try:
                bank_select = self.find_clickable("//*[contains(text(), '--Please select the bank name--')]", timeout=6)
                if bank_select:
                    self.click_element(bank_select)
                    time.sleep(1)
                    bank_option = self.find_clickable(f"//*[contains(text(), '{bank_name}')]", timeout=4)
                    if bank_option:
                        self.click_element(bank_option)
                        print(f"   🏦 Selected bank: {bank_name}")
                        self.screenshot("bank_selected")
            except:
                pass

            account_input = self.find_presence("//input[@placeholder='Please enter the bank account number']", timeout=6)
            if account_input:
                account_input.clear()
                account_input.send_keys(login_data.get('bank_account', ''))
                print(f"   🏦 Entered account: {login_data.get('bank_account')}")
                self.screenshot("account_entered")

            add_btn = self.find_clickable("//button[contains(text(), 'Add now')]", timeout=6)
            if add_btn:
                self.click_element(add_btn)
                time.sleep(2)
                print("   ✅ Bank card added")
                self.screenshot("bank_added")
                return True
            else:
                print("   ❌ Add bank button not found")
                return False

        except Exception as e:
            self.log_exception("add_bank_account", e)
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
        except Exception as e:
            print("   ⚠️ sign_out failed:", e)
            return False

    # ============================================
    # PROCESS ACCOUNT
    # ============================================
    def process_account(self, login_data):
        phone = login_data.get('phone')
        password = login_data.get('password')
        fund_password = login_data.get('fund_password', '3333')

        print(f"\n📱 Account: {phone}")

        if not self.login(phone, password):
            print("   ❌ Login failed for", phone)
            return False

        self.remove_important_notice()
        self.screenshot("after_popup_removal")

        self.do_tasks()
        self.screenshot("after_tasks")

        try:
            self.complete_withdrawal()
        except Exception:
            pass

        # SET FUND PASSWORD
        self.set_fund_password(fund_password)

        self.add_bank_account(login_data)

        self.sign_out()

        return True

    def run(self):
        print("="*50)
        print(f"🤖 BOT {self.bot_id} STARTING")
        print("="*50)

        for login_data in self.logins:
            try:
                ok = self.process_account(login_data)
                if ok:
                    print(f"   ✅ SUCCESS for {login_data.get('phone')}")
                else:
                    print(f"   ❌ FAILED for {login_data.get('phone')}")
            except Exception as e:
                print("   ❌ Unexpected error:", e)
                if DEBUG:
                    traceback.print_exc()
            time.sleep(2)

        try:
            self.driver.quit()
        except:
            pass
        print(f"\n✅ Bot {self.bot_id} Done!")


if __name__ == "__main__":
    bot_id = int(os.environ.get('BOT_ID', "1"))
    bot = NRCBot(bot_id=bot_id)
    bot.run()