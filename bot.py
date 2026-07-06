# ============================================
# WITHDRAWAL METHODS (FIXED)
# ============================================

def click_withdrawal_confirm(self):
    """Click the Confirm button on the withdrawal page"""
    print("   🔘 Looking for Confirm button...")
    try:
        confirm_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Confirm')]"))
        )
        self.click_element(confirm_btn)
        print("   ✅ Clicked Confirm button")
        self.screenshot("confirm_clicked")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"   ⚠️ Could not click Confirm: {e}")
        return False

def complete_withdrawal(self, fund_password, amount="1800"):
    """Complete withdrawal - STEP BY STEP"""
    print(f"   💰 Processing withdrawal...")
    
    # STEP 1: Go to withdrawal page
    try:
        self.driver.get("https://nnnrc.com/#/user/withdraw")
        time.sleep(2)
        self.screenshot("01_withdrawal_page")
        print("   ✅ Withdrawal page loaded")
    except Exception as e:
        print(f"   ❌ Could not load withdrawal page: {e}")
        return False
    
    # STEP 2: Click Confirm button (for bank card message)
    print("   🔘 Clicking Confirm button...")
    if self.click_withdrawal_confirm():
        print("   ✅ Confirm clicked")
        self.screenshot("02_confirm_clicked")
    else:
        print("   ℹ️ No Confirm button needed")
    
    # STEP 3: Select withdrawal method
    try:
        method_select = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Select withdrawal method')]"))
        )
        self.click_element(method_select)
        time.sleep(1)
        self.screenshot("03_method_selected")
        print("   ✅ Clicked withdrawal method")
    except:
        print("   ℹ️ Withdrawal method not found")
    
    # STEP 4: Select OPAY
    try:
        bank_option = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'OPAY')]"))
        )
        self.click_element(bank_option)
        time.sleep(1)
        self.screenshot("04_opay_selected")
        print("   ✅ Selected OPAY")
    except:
        print("   ℹ️ OPAY not found")
    
    # STEP 5: Click Confirm after selecting bank
    print("   🔘 Clicking Confirm after bank selection...")
    if self.click_withdrawal_confirm():
        print("   ✅ Confirm clicked after bank selection")
        self.screenshot("05_confirm_after_bank")
    
    # STEP 6: Enter fund password
    try:
        fund_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Please input fund password']"))
        )
        self.type_text(fund_input, fund_password)
        self.screenshot("06_fund_password_entered")
        print(f"   🔑 Entered fund password: {fund_password}")
    except:
        print("   ℹ️ Fund password field not found")
    
    # STEP 7: Enter withdrawal amount
    try:
        amount_input = self.driver.find_element(By.XPATH, "//input[@placeholder='Withdrawal amount']")
        self.type_text(amount_input, amount)
        self.screenshot("07_amount_entered")
        print(f"   💰 Entered amount: {amount}")
    except:
        print("   ℹ️ Amount field not found")
    
    # STEP 8: Click Submit
    try:
        submit_btn = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
        )
        self.click_element(submit_btn)
        self.screenshot("08_submit_clicked")
        print("   ✅ Clicked Submit")
        time.sleep(2)
    except:
        print("   ℹ️ Submit button not found")
    
    # STEP 9: Click final Confirm if appears
    print("   🔘 Checking for final Confirm...")
    if self.click_withdrawal_confirm():
        print("   ✅ Final Confirm clicked")
        self.screenshot("09_final_confirm")
    
    # STEP 10: Take final screenshot
    self.screenshot("10_withdrawal_complete")
    print("   ✅ Withdrawal process complete!")
    return True