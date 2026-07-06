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

# Configuration via environment
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
            # use the new headless mode where supported
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # common flags to avoid detection
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        print(f"🤖 Bot {self.bot_id} Starting Chrome (headless={HEADLESS})...")
        try:
            service = Service(CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=options)
            print(f"✅ Bot {self.bot_id} Chrome started (local chromedriver)!")
        except Exception:
            try:
                # fallback to webdriver_manager if chromedriver not available
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
                print(f"✅ Bot {self.bot_id} Chrome started (webdriver_manager)!")
            except Exception as e:
                print("❌ Could not start Chrome webdriver:", e)
                raise

        # small implicit wait
        self.driver.implicitly_wait(2)

    # -----------------------
    # Utilities & diagnostics
    # -----------------------
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
                # attempt to skip header if present
                first = next(reader)
                # if first looks like phone/password header, continue; else treat it as data
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
            print("⚠️ logins.csv not found — using default dummy account (for testing)")
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
        # case-insensitive contains on the element text
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

    # -----------------------
    # LOGIN
    # -----------------------
    def login(self, phone, password):
        print(f"\n🔑 Logging in: {phone}")
        try:
            self.driver.get("https://nnnrc.com/#/login")
            time.sleep(2)
            self.screenshot("01_login_page")

            # phone field candidates
            phone_xps = [
                "//input[@placeholder='Please enter your phone number']",
                "//input[contains(@placeholder,'phone')]",
                "//input[@name='phone']",
                "//input[@type='tel']",
                "//input[@type='text']"
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
                self.screenshot("login_phone_not_found")
                self.save_html("login_phone_not_found")
                return False
            phone_field.clear()
            phone_field.send_keys(phone)
            print(f"   ✅ Phone: {phone}")
            self.screenshot("02_phone_entered")

            # password field candidates
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
                self.screenshot("login_password_not_found")
                self.save_html("login_password_not_found")
                return False
            password_field.clear()
            password_field.send_keys(password)
            print("   ✅ Password entered")
            self.screenshot("03_password_entered")

            # login button candidates
            btn_xps = [
                "//button[contains(., 'Log in now')]",
                "//button[" + self.xpath_contains_ci("logging") + "]",
                "//button[" + self.xpath_contains_ci("log in") + "]",
                "//button[@type='submit']",
            ]
            clicked = False
            for xp in btn_xps:
                try:
                    btn = self.find_clickable(xp, timeout=4)
                    if btn:
                        # log what we clicked for debugging
                        try:
                            label = btn.text.strip()[:60]
                        except:
                            label = xp
                        print(f"   🔘 Clicking login button (candidate): {label!r}")
                        if self.click_element(btn):
                            clicked = True
                            break
                except Exception:
                    continue
            if not clicked:
                print("   ❌ Login button not found/clickable.")
                self.screenshot("login_button_not_found")
                self.save_html("login_button_not_found")
                return False

            # wait for post-login indicator
            try:
                WebDriverWait(self.driver, 10).until(lambda d: "/#/user" in d.current_url.lower() or "important notice" in d.page_source.lower() or "logout" in d.page_source.lower() or self.xpath_contains_ci("welcome") in "")
            except Exception:
                # not fatal — check heuristics
                pass

            time.sleep(1)
            self.screenshot("04_after_login_wait")
            page_source = self.driver.page_source.lower()
            if any(k in page_source for k in ("important notice", "cooperative wealth zone", "welcome", "logout", "/#/user")) or "/#/user" in self.driver.current_url.lower():
                print("   ✅ Login success!")
                self.logged_in_accounts.append(phone)
                return True
            else:
                print("   ❌ Login failed (no post-login indicator).")
                self.screenshot("06_login_failed")
                self.save_html("06_login_failed")
                return False
        except Exception as e:
            self.log_exception("login", e)
            return False

    # -----------------------
    # POPUP REMOVAL
    # -----------------------
    def remove_important_notice(self):
        print("   ℹ️ remove_important_notice: checking for popups...")
        try:
            # find common welcome/important text
            xp_notices = f"//*[ {self.xpath_contains_ci('important notice')} ] | //*[ {self.xpath_contains_ci('welcome')} ] | //*[ {self.xpath_contains_ci('important')} ]"
            notices = self.driver.find_elements(By.XPATH, xp_notices)
            if not notices:
                print("   ℹ️ No Important Notice found")
                return True
            print("   📋 Found Important Notice / Welcome")
            self.screenshot("important_notice_found")

            close_xpaths = [
                "//button[" + self.xpath_contains_ci("got it") + "]",
                "//button[" + self.xpath_contains_ci("ok") + "]",
                "//button[" + self.xpath_contains_ci("close") + "]",
                "//*[contains(@class, 'modal-close')]",
                "//*[contains(@class, 'close')]",
                "//*[text()='×']",
                "//button[@aria-label='Close']",
                "//button[" + self.xpath_contains_ci("news") + "]",
            ]
            for xp in close_xpaths:
                try:
                    elems = self.driver.find_elements(By.XPATH, xp)
                    for el in elems:
                        if el.is_displayed() and el.is_enabled():
                            if self.click_element(el):
                                print(f"   🚫 Closed popup using xpath: {xp}")
                                time.sleep(0.6)
                except Exception as e:
                    print("   ⚠️ close xpath check failed:", xp, e)

            # last resort: click any visible modal-close icons inside modals
            try:
                candidates = self.driver.find_elements(By.XPATH, "//*[contains(@class,'modal')]//*[contains(@class,'close') or contains(@class,'close-btn') or contains(@class,'close-icon')] | //*[contains(@class,'overlay')]//button")
                for c in candidates:
                    if c.is_displayed() and c.is_enabled():
                        if self.click_element(c):
                            time.sleep(0.5)
            except Exception:
                pass

            self.screenshot("popups_removed")
            return True
        except Exception as e:
            self.log_exception("remove_important_notice", e)
            return True

    # -----------------------
    # TASKS
    # -----------------------
    def do_tasks(self):
        print("   📋 Starting tasks...")
        try:
            # try to open Tasks tab
            try:
                task_tab = self.driver.find_elements(By.XPATH, f"//*[ {self.xpath_contains_ci('task')} ]")
                if task_tab:
                    self.click_element(task_tab[0])
                    time.sleep(1.5)
                    self.screenshot("tasks_page")
            except Exception:
                pass

            total = 0
            attempts = 0
            while total < TASK_COUNT and attempts < TASK_COUNT * 2:
                attempts += 1
                # look for read buttons or links
                read_xp = f"//button[{self.xpath_contains_ci('read')}] | //a[{self.xpath_contains_ci('read')}] | //button[{self.xpath_contains_ci('start')}]"
                candidates = self.driver.find_elements(By.XPATH, read_xp)
                btn = None
                for c in candidates:
                    try:
                        if c.is_displayed() and c.is_enabled():
                            btn = c
                            break
                    except:
                        continue
                if not btn:
                    # try locating inside a task list
                    try:
                        list_items = self.driver.find_elements(By.XPATH, "//*[contains(@class,'task') or contains(@class,'task-list') or contains(@class,'task-item')]//button")
                        for c in list_items:
                            try:
                                if c.is_displayed() and c.is_enabled() and 'read' in (c.text or '').lower():
                                    btn = c
                                    break
                            except:
                                continue
                    except:
                        pass

                if not btn:
                    # nothing found right now — wait a bit and retry
                    time.sleep(1)
                    continue

                # click and wait TASK_WAIT seconds
                try:
                    self.click_element(btn)
                    total += 1
                    print(f"   📖 Task {total} started - waiting {TASK_WAIT}s")
                    time.sleep(TASK_WAIT)
                    print(f"   ✅ Task {total} done")
                    # close possible modals
                    try:
                        close_btns = self.driver.find_elements(By.XPATH, "//button[" + self.xpath_contains_ci("close") + "] | //button[" + self.xpath_contains_ci("got it") + "] | //button[text()='×']")
                        for cb in close_btns:
                            if cb.is_displayed() and cb.is_enabled():
                                self.click_element(cb)
                                time.sleep(0.4)
                    except:
                        pass
                    self.screenshot(f"task_{total}_done")
                except Exception as e:
                    print("   ⚠️ Error performing a task:", e)
                    if DEBUG:
                        self.screenshot("task_click_error")
                        self.save_html("task_click_error")
                    time.sleep(1)
            print(f"   ✅ Completed {total} tasks")
            self.screenshot("tasks_completed")
            return total
        except Exception as e:
            self.log_exception("do_tasks", e)
            return 0

    # -----------------------
    # WITHDRAWAL (kept minimal)
    # -----------------------
    def complete_withdrawal(self):
        print(f"   💰 Processing withdrawal (attempt)...")
        try:
            self.driver.get("https://nnnrc.com/#/user/withdraw")
            time.sleep(1.5)
            self.screenshot("withdrawal_page")
            confirm_btn = self.find_clickable("//button[" + self.xpath_contains_ci("confirm") + "]", timeout=6) or self.find_clickable("//button[contains(., 'Confirm')]", timeout=4)
            if confirm_btn:
                confirm_btn.click()
                print("   ✅ Clicked Confirm")
                time.sleep(1.5)
                self.screenshot("confirm_clicked")
                return True
            else:
                print("   ⚠️ Confirm button not found")
                return False
        except Exception as e:
            self.log_exception("complete_withdrawal", e)
            return False

    # -----------------------
    # FUND PASSWORD
    # -----------------------
    def set_fund_password(self, fund_password):
        print("   🔑 Setting fund password...")
        try:
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(2)
            self.screenshot("user_info_page")

            # attempt to trigger fund password UI
            fund_pw_btn = self.find_clickable(f"//*[ {self.xpath_contains_ci('fund password')} ] | //button[{self.xpath_contains_ci('fund password')}]", timeout=6)
            if fund_pw_btn:
                self.click_element(fund_pw_btn)
                time.sleep(0.8)
                self.screenshot("fund_password_clicked")
            else:
                print("   ⚠️ Fund password button not found; continuing to look for inputs")

            # find inputs
            new_pw = self.find_presence("//input[@placeholder='Please enter the new funds password']", timeout=4) or \
                     self.find_presence("//input[contains(@placeholder,'fund') and @type='password']", timeout=3) or \
                     self.find_presence("//input[@name='fundPassword']", timeout=3)
            confirm_pw = self.find_presence("//input[@placeholder='Please confirm the fund password']", timeout=3) or \
                         self.find_presence("//input[contains(@placeholder,'confirm') and @type='password']", timeout=3)

            if not new_pw or not confirm_pw:
                print("   ❌ Fund password inputs not found")
                self.screenshot("fundpw_inputs_missing")
                self.save_html("fundpw_inputs_missing")
                return False

            new_pw.clear(); new_pw.send_keys(fund_password)
            confirm_pw.clear(); confirm_pw.send_keys(fund_password)
            self.screenshot("fund_password_entered")

            submit_btn = self.find_clickable("//button[" + self.xpath_contains_ci("submit") + "]", timeout=6) or self.find_clickable("//button[contains(., 'Submit')]", timeout=4)
            if submit_btn:
                self.click_element(submit_btn)
                print("   ✅ Fund password set (submit clicked)")
                time.sleep(1.5)
                self.screenshot("fund_password_submitted")
                return True
            else:
                print("   ❌ Submit button for fund password not found")
                self.save_html("fundpw_submit_missing")
                return False
        except Exception as e:
            self.log_exception("set_fund_password", e)
            return False

    # -----------------------
    # ADD BANK ACCOUNT
    # -----------------------
    def add_bank_account(self, login_data):
        print("   🏦 Adding bank account...")
        try:
            self.driver.get("https://nnnrc.com/#/user/info")
            time.sleep(1.5)
            self.screenshot("bank_page")

            # click "Add a bank account" if present
            add_bank_btn = self.find_clickable(f"//*[ {self.xpath_contains_ci('add a bank account')} ] | //button[{self.xpath_contains_ci('add bank')}] | //a[{self.xpath_contains_ci('add bank')}]", timeout=6)
            if add_bank_btn:
                self.click_element(add_bank_btn)
                time.sleep(1)
                self.screenshot("add_bank_clicked")
            else:
                print("   ⚠️ Add bank button not found; continuing")

            # click authenticate now
            auth_btn = self.find_clickable("//button[" + self.xpath_contains_ci("authenticate now") + "] | //button[" + self.xpath_contains_ci("authenticate") + "]", timeout=6)
            if auth_btn:
                self.click_element(auth_btn)
                time.sleep(0.8)
                self.screenshot("authenticate_clicked")
            else:
                print("   ⚠️ Authenticate button not found; continuing")

            # enter real name
            name_input = self.find_presence("//input[@placeholder='Please enter a real name']", timeout=6) or self.find_presence("//input[contains(@placeholder,'real name') or contains(@placeholder,'name')]", timeout=4)
            if not name_input:
                print("   ❌ Name input not found")
                self.screenshot("name_input_missing")
                self.save_html("name_input_missing")
                return False
            name_input.clear()
            name_input.send_keys(login_data.get('real_name', 'John Penn'))
            print(f"   👤 Entered name: {login_data.get('real_name')}")
            self.screenshot("name_entered")

            # submit name if required
            try:
                name_submit = self.find_clickable("//button[" + self.xpath_contains_ci("submit") + "]", timeout=3)
                if name_submit:
                    self.click_element(name_submit)
                    time.sleep(0.8)
            except:
                pass

            # select bank: support <select>/<option> or custom dropdowns
            bank_name = login_data.get('bank_name', '')
            bank_selected = False
            try:
                # try native select
                options = self.driver.find_elements(By.XPATH, f"//option[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{bank_name.lower()}')]")
                if options:
                    options[0].click()
                    bank_selected = True
                else:
                    # try to open dropdown then pick list item
                    dropdown = self.find_clickable("//*[contains(@class,'bank-select')] | //*[contains(@class,'select')] | //select", timeout=4)
                    if dropdown:
                        self.click_element(dropdown)
                        time.sleep(0.6)
                        # try list items
                        li = self.find_clickable(f"//*[ {self.xpath_contains_ci(bank_name)} ]", timeout=4)
                        if li:
                            self.click_element(li)
                            bank_selected = True
            except Exception as e:
                print("   ⚠️ Bank select attempt failed:", e)
            if bank_selected:
                print(f"   🏦 Selected bank: {bank_name}")
                self.screenshot("bank_selected")
            else:
                print("   ⚠️ Bank option not found (continuing)")

            # enter account number
            account_input = self.find_presence("//input[@placeholder='Please enter the bank account number']", timeout=6) or self.find_presence("//input[contains(@placeholder,'account') or contains(@name,'account')]", timeout=4)
            if not account_input:
                print("   ❌ Account input not found")
                self.screenshot("account_input_missing")
                self.save_html("account_input_missing")
                return False
            account_input.clear()
            account_input.send_keys(login_data.get('bank_account', ''))
            print(f"   🏦 Entered account: {login_data.get('bank_account')}")
            self.screenshot("account_entered")

            # click add now / add
            add_btn = self.find_clickable("//button[" + self.xpath_contains_ci("add now") + "] | //button[" + self.xpath_contains_ci("add") + "]", timeout=6)
            if add_btn:
                self.click_element(add_btn)
                time.sleep(1.2)
                print("   ✅ Bank card added (clicked)")
                self.screenshot("bank_added")
                return True
            else:
                print("   ❌ Add bank button not found")
                self.save_html("add_bank_button_missing")
                return False

        except Exception as e:
            self.log_exception("add_bank_account", e)
            return False

    # -----------------------
    # SIGN OUT
    # -----------------------
    def sign_out(self):
        try:
            self.driver.get("https://nnnrc.com/#/logout")
            time.sleep(1)
            print("   ✅ Signed out")
            self.screenshot("signed_out")
            return True
        except Exception as e:
            print("   ⚠️ sign_out failed:", e)
            return False

    # -----------------------
    # PROCESS ACCOUNT (main workflow)
    # -----------------------
    def process_account(self, login_data):
        phone = login_data.get('phone')
        password = login_data.get('password')
        fund_password = login_data.get('fund_password', '3333')

        print(f"\n📱 Account: {phone}")

        if not self.login(phone, password):
            print("   ❌ Login failed for", phone)
            return False

        # remove popups
        self.remove_important_notice()
        self.screenshot("after_popup_removal")

        # do tasks
        self.do_tasks()
        self.screenshot("after_tasks")

        # optional withdrawal (kept safe)
        try:
            self.complete_withdrawal()
        except Exception:
            pass

        # set fund password
        self.set_fund_password(fund_password)

        # add bank account
        self.add_bank_account(login_data)

        # sign out
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
                print("   ❌ Unexpected error processing account:", e)
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