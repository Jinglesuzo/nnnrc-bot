def set_fund_password(self, fund_password):
    print("   🔑 Setting fund password...")
    try:
        # GO TO USER/INFO
        self.driver.get("https://nnnrc.com/#/user/info")
        time.sleep(3)
        self.screenshot("01_user_info_page")
        print("   ✅ User info page loaded")
        
        # Click "Fund password"
        fund_pw_btn = self.find_clickable("//*[contains(text(), 'Fund password')]", timeout=10)
        if fund_pw_btn:
            self.click_element(fund_pw_btn)
            time.sleep(2)
            self.screenshot("02_fund_password_clicked")
            print("   ✅ Clicked Fund password")
        else:
            print("   ❌ Could not find Fund password button")
            return False

        # Enter new fund password
        new_pw = self.find_presence("//input[@placeholder='Please enter the new funds password']", timeout=10)
        if not new_pw:
            print("   ❌ Could not find new password input")
            return False
        new_pw.clear()
        new_pw.send_keys(fund_password)
        print(f"   ✅ Entered new fund password: {fund_password}")
        self.screenshot("05_new_password_entered")

        # Confirm fund password
        confirm_pw = self.find_presence("//input[@placeholder='Please confirm the fund password']", timeout=10)
        if not confirm_pw:
            print("   ❌ Could not find confirm password input")
            return False
        confirm_pw.clear()
        confirm_pw.send_keys(fund_password)
        print(f"   ✅ Confirmed fund password: {fund_password}")
        self.screenshot("07_confirm_password_entered")

        # ============================================
        # CLICK SUBMIT - USING ALL METHODS
        # ============================================
        print("   🔘 Looking for Submit button...")
        
        # Method 1: By text "Submit"
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[text()='Submit']")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by exact text)")
                self.screenshot("08_submit_clicked")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"   ⚠️ Method 1 failed: {e}")
        
        # Method 2: By contains text "Submit"
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by contains text)")
                self.screenshot("08_submit_clicked")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"   ⚠️ Method 2 failed: {e}")
        
        # Method 3: By type submit
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by type)")
                self.screenshot("08_submit_clicked")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"   ⚠️ Method 3 failed: {e}")
        
        # Method 4: By CSS class
        try:
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[class*='submit'], button[class*='green']")
            if submit_btn.is_displayed() and submit_btn.is_enabled():
                self.click_element(submit_btn)
                print("   ✅ Clicked Submit (by class)")
                self.screenshot("08_submit_clicked")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"   ⚠️ Method 4 failed: {e}")
        
        # Method 5: JavaScript click
        try:
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", submit_btn)
            print("   ✅ Clicked Submit (JavaScript)")
            self.screenshot("08_submit_clicked")
            time.sleep(2)
            return True
        except Exception as e:
            print(f"   ⚠️ Method 5 failed: {e}")
        
        # Method 6: Find any visible button on the page
        try:
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    text = btn.text.lower()
                    if 'submit' in text or 'confirm' in text:
                        self.click_element(btn)
                        print(f"   ✅ Clicked button: '{btn.text}' (by scanning)")
                        self.screenshot("08_submit_clicked")
                        time.sleep(2)
                        return True
        except Exception as e:
            print(f"   ⚠️ Method 6 failed: {e}")
        
        print("   ❌ Could not find Submit button")
        self.screenshot("09_submit_not_found")
        return False
                
    except Exception as e:
        self.log_exception("set_fund_password", e)
        return False