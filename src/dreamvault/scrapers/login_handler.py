"""
Login Handler for DreamVault ChatGPT Scraper

Handles ChatGPT login with credentials, manual login, and 2FA support.
"""

import time
import logging
from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

class LoginHandler:
    """Handles ChatGPT login with various methods."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, 
                 totp_secret: Optional[str] = None):
        """
        Initialize the login handler.
        
        Args:
            username: ChatGPT username/email
            password: ChatGPT password
            totp_secret: TOTP secret for 2FA
        """
        self.username = username
        self.password = password
        self.totp_secret = totp_secret
        self.timeout = 30
    
    def ensure_login(self, driver, allow_manual: bool = True, manual_timeout: int = 60) -> bool:
        """
        Ensure user is logged into ChatGPT.
        
        Args:
            driver: Selenium webdriver instance
            allow_manual: Allow manual login if automated fails
            manual_timeout: Timeout for manual login
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Navigate to ChatGPT
            driver.get("https://chat.openai.com")
            time.sleep(3)
            
            # Check if already logged in
            if self._is_logged_in(driver):
                logger.info("✅ Already logged in to ChatGPT")
                return True
            
            # Try automated login if credentials provided
            if self.username and self.password:
                if self._automated_login(driver):
                    return True
            
            # Try manual login if allowed
            if allow_manual:
                logger.info("🔄 Attempting manual login...")
                return self._manual_login(driver, manual_timeout)
            
            logger.error("❌ Login failed - no credentials and manual login not allowed")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def _is_logged_in(self, driver) -> bool:
        """Check if user is logged in to ChatGPT."""
        try:
            # Look for logged-in indicators
            logged_in_indicators = [
                "//button[contains(@data-testid, 'send-button')]",
                "//div[contains(@class, 'conversation')]",
                "//div[contains(@data-testid, 'conversation-turn')]",
                "//div[contains(@class, 'markdown')]"
            ]
            
            for indicator in logged_in_indicators:
                try:
                    element = driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        return True
                except:
                    continue
            
            # Check for login page indicators
            login_indicators = [
                "//button[contains(text(), 'Log in')]",
                "//input[@name='username']",
                "//input[@name='password']"
            ]
            
            for indicator in login_indicators:
                try:
                    element = driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        return False
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
    
    def _automated_login(self, driver) -> bool:
        """Perform automated login with credentials."""
        try:
            logger.info("🔄 Attempting automated login...")
            
            # Wait for login form
            wait = WebDriverWait(driver, self.timeout)
            
            # Find and fill username
            username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Click continue
            continue_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            continue_button.click()
            time.sleep(2)
            
            # Find and fill password
            password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login
            login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            time.sleep(3)
            
            # Handle 2FA if needed
            if self.totp_secret:
                if self._handle_2fa(driver):
                    logger.info("✅ 2FA completed")
                else:
                    logger.warning("⚠️ 2FA failed, continuing...")
            
            # Check if login successful
            if self._is_logged_in(driver):
                logger.info("✅ Automated login successful")
                return True
            else:
                logger.warning("⚠️ Automated login failed")
                return False
                
        except Exception as e:
            logger.error(f"Automated login error: {e}")
            return False
    
    def _handle_2fa(self, driver) -> bool:
        """Handle 2FA authentication."""
        try:
            # Look for 2FA input field
            totp_field = driver.find_element(By.XPATH, "//input[@name='totp']")
            
            # Generate TOTP code
            import pyotp
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            
            # Enter code
            totp_field.clear()
            totp_field.send_keys(code)
            
            # Submit
            submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logger.error(f"2FA error: {e}")
            return False
    
    def _manual_login(self, driver, timeout: int) -> bool:
        """Allow manual login with timeout."""
        try:
            logger.info(f"⏰ Manual login timeout: {timeout} seconds")
            logger.info("👤 Please log in manually in the browser...")
            
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self._is_logged_in(driver):
                    logger.info("✅ Manual login successful")
                    return True
                time.sleep(2)
            
            logger.error("❌ Manual login timeout")
            return False
            
        except Exception as e:
            logger.error(f"Manual login error: {e}")
            return False 