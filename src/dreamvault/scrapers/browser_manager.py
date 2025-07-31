"""
Browser Manager for DreamVault ChatGPT Scraper

Handles browser initialization, driver management, and undetected Chrome setup.
"""

import os
import logging
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

class BrowserManager:
    """Manages browser driver creation and configuration."""
    
    def __init__(self, headless: bool = False, use_undetected: bool = True):
        """
        Initialize the browser manager.
        
        Args:
            headless: Run browser in headless mode
            use_undetected: Use undetected-chromedriver if available
        """
        self.headless = headless
        self.use_undetected = use_undetected
        self.driver = None
        
    def create_driver(self) -> Optional[webdriver.Chrome]:
        """
        Create and configure Chrome driver.
        
        Returns:
            Configured Chrome driver or None if failed
        """
        try:
            if self.use_undetected:
                return self._create_undetected_driver()
            else:
                return self._create_standard_driver()
        except Exception as e:
            logger.error(f"Failed to create driver: {e}")
            return None
    
    def _create_undetected_driver(self) -> Optional[webdriver.Chrome]:
        """Create undetected Chrome driver."""
        try:
            import undetected_chromedriver as uc
            
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            
            # Add basic anti-detection arguments (undetected-chromedriver handles the rest)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Create undetected driver
            driver = uc.Chrome(options=options)
            
            logger.info("✅ Undetected Chrome driver created successfully")
            return driver
            
        except ImportError:
            logger.warning("undetected-chromedriver not available, falling back to standard driver")
            return self._create_standard_driver()
        except Exception as e:
            logger.error(f"Failed to create undetected driver: {e}")
            return None
    
    def _create_standard_driver(self) -> Optional[webdriver.Chrome]:
        """Create standard Chrome driver."""
        try:
            options = Options()
            
            if self.headless:
                options.add_argument("--headless")
            
            # Add anti-detection arguments
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Create standard driver
            driver = webdriver.Chrome(options=options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Standard Chrome driver created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to create standard driver: {e}")
            return None
    
    def close_driver(self):
        """Close the current driver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✅ Driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None 