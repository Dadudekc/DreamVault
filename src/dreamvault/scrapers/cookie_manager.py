"""
Cookie Manager for DreamVault ChatGPT Scraper

Handles cookie persistence and session management for ChatGPT login.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)

class CookieManager:
    """Manages cookie persistence and session management."""
    
    def __init__(self, cookie_file: Optional[str] = None):
        """
        Initialize the cookie manager.
        
        Args:
            cookie_file: Path to cookie file for persistence
        """
        self.cookie_file = cookie_file or "data/cookies.json"
        self.cookie_path = Path(self.cookie_file)
        self.cookie_path.parent.mkdir(parents=True, exist_ok=True)
    
    def save_cookies(self, driver: WebDriver) -> bool:
        """
        Save cookies from the current driver session.
        
        Args:
            driver: Selenium webdriver instance
            
        Returns:
            True if cookies saved successfully, False otherwise
        """
        try:
            cookies = driver.get_cookies()
            
            with open(self.cookie_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(f"✅ Saved {len(cookies)} cookies to {self.cookie_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False
    
    def load_cookies(self, driver: WebDriver) -> bool:
        """
        Load cookies into the current driver session.
        
        Args:
            driver: Selenium webdriver instance
            
        Returns:
            True if cookies loaded successfully, False otherwise
        """
        try:
            if not self.cookie_path.exists():
                logger.warning(f"Cookie file not found: {self.cookie_file}")
                return False
            
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            
            # Add cookies to driver
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    logger.warning(f"Failed to add cookie: {e}")
            
            logger.info(f"✅ Loaded {len(cookies)} cookies from {self.cookie_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def has_valid_cookies(self) -> bool:
        """
        Check if valid cookies exist.
        
        Returns:
            True if cookie file exists and is not empty
        """
        if not self.cookie_path.exists():
            return False
        
        try:
            with open(self.cookie_path, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            return len(cookies) > 0
        except Exception:
            return False
    
    def clear_cookies(self) -> bool:
        """
        Clear saved cookies.
        
        Returns:
            True if cookies cleared successfully, False otherwise
        """
        try:
            if self.cookie_path.exists():
                self.cookie_path.unlink()
                logger.info("✅ Cookies cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cookies: {e}")
            return False 