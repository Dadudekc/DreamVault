"""
Adaptive Conversation Extractor for DreamVault

Self-healing system that adapts to ChatGPT interface changes.
"""

import time
import json
import logging
from typing import List, Dict, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

class AdaptiveExtractor:
    """Self-healing conversation extractor that adapts to interface changes."""
    
    def __init__(self, timeout: int = 30, selector_cache_file: str = "data/selector_cache.json"):
        """
        Initialize the adaptive extractor.
        
        Args:
            timeout: Timeout for web operations
            selector_cache_file: File to cache successful selectors
        """
        self.timeout = timeout
        self.selector_cache_file = selector_cache_file
        self.successful_selectors = self._load_selector_cache()
        
        # Comprehensive selector library
        self.selector_library = {
            "conversation_links": [
                "//a[contains(@href, '/c/')]//span",
                "//a[contains(@href, '/c/')]",
                "//div[contains(@class, 'conversation')]//a",
                "//nav//a[contains(@href, '/c/')]",
                "//a[contains(@href, 'chatgpt.com/c/')]",
                "//a[contains(@href, 'chat.openai.com/c/')]",
                "//div[contains(@class, 'group')]//a[contains(@href, '/c/')]",
                "//div[contains(@class, 'flex')]//a[contains(@href, '/c/')]",
                "//nav//div[contains(@class, 'conversation')]//a",
                "//div[contains(@class, 'conversation')]//div[contains(@class, 'title')]//a",
                "//a[contains(@href, '/c/')]//div[contains(@class, 'text')]",
                "//div[contains(@class, 'conversation')]//a[contains(@href, '/c/')]",
                "//nav//div[contains(@class, 'conversation')]//a",
                "//div[contains(@class, 'conversation')]//div[contains(@class, 'title')]//a",
                "//a[contains(@href, '/c/')]//span",
                "//div[contains(@class, 'conversation')]//span",
                "//nav//span",
                "//a[contains(@href, '/c/')]//div",
                "//div[contains(@class, 'conversation')]//div",
                "//nav//div"
            ],
            "url_patterns": [
                "https://chatgpt.com",
                "https://chat.openai.com",
                "https://chatgpt.co"
            ]
        }
    
    def _load_selector_cache(self) -> Dict[str, List[str]]:
        """Load cached successful selectors."""
        try:
            if self.selector_cache_file and self.selector_cache_file:
                with open(self.selector_cache_file, 'r') as f:
                    cache = json.load(f)
                    logger.info(f"📊 Loaded {len(cache.get('selectors', []))} cached selectors")
                    return cache
        except Exception as e:
            logger.warning(f"Failed to load selector cache: {e}")
        return {"selectors": [], "urls": []}
    
    def _save_selector_cache(self):
        """Save successful selectors to cache."""
        try:
            import os
            os.makedirs(os.path.dirname(self.selector_cache_file), exist_ok=True)
            with open(self.selector_cache_file, 'w') as f:
                json.dump(self.successful_selectors, f, indent=2)
            logger.info("💾 Saved selector cache")
        except Exception as e:
            logger.error(f"Failed to save selector cache: {e}")
    
    def _test_selector(self, driver, selector: str) -> Tuple[bool, List]:
        """Test a selector and return success status and elements."""
        try:
            elements = driver.find_elements(By.XPATH, selector)
            if elements:
                # Validate elements contain conversation data
                valid_elements = []
                for element in elements:
                    try:
                        if element.tag_name == "span":
                            parent = element.find_element(By.XPATH, "./..")
                            href = parent.get_attribute("href")
                        else:
                            href = element.get_attribute("href")
                        
                        text = element.text.strip()
                        if href and text and "/c/" in href:
                            valid_elements.append(element)
                    except:
                        continue
                
                return len(valid_elements) > 0, valid_elements
            return False, []
        except Exception as e:
            logger.debug(f"Selector failed: {selector} - {e}")
            return False, []
    
    def _discover_working_url(self, driver) -> str:
        """Discover the working ChatGPT URL."""
        for url_pattern in self.selector_library["url_patterns"]:
            try:
                logger.info(f"🔍 Testing URL: {url_pattern}")
                driver.get(url_pattern)
                time.sleep(3)
                
                # Check if page loaded successfully
                if "chat" in driver.title.lower() or "gpt" in driver.title.lower():
                    logger.info(f"✅ Found working URL: {url_pattern}")
                    return url_pattern
                    
            except Exception as e:
                logger.debug(f"URL failed: {url_pattern} - {e}")
                continue
        
        # Default fallback
        return "https://chatgpt.com"
    
    def _extract_conversations_from_elements(self, elements: List) -> List[Dict[str, str]]:
        """Extract conversation data from elements."""
        conversations = []
        
        for i, element in enumerate(elements):
            try:
                # Get the parent link element if we're on a span
                if element.tag_name == "span":
                    parent = element.find_element(By.XPATH, "./..")
                    href = parent.get_attribute("href")
                else:
                    href = element.get_attribute("href")
                
                title = element.text.strip()
                
                if href and title and "/c/" in href:
                    conversation = {
                        "id": href.split("/c/")[-1] if "/c/" in href else f"conv_{i}",
                        "title": title,
                        "url": href
                    }
                    conversations.append(conversation)
                    
            except Exception as e:
                logger.warning(f"Failed to extract conversation {i}: {e}")
                continue
        
        return conversations
    
    def _extract_conversations_with_scrolling(self, driver, selector: str) -> List[Dict[str, str]]:
        """Extract conversations with infinite scrolling."""
        logger.info("🔄 Starting infinite scroll to load all conversations...")
        conversations = []
        seen_urls = set()
        scroll_attempts = 0
        max_scroll_attempts = 50  # Prevent infinite loops
        last_count = 0
        no_new_conversations_count = 0
        
        while scroll_attempts < max_scroll_attempts:
            # Get current conversations
            elements = driver.find_elements(By.XPATH, selector)
            current_count = len(elements)
            
            logger.info(f"📊 Current conversations found: {current_count}")
            
            # Extract new conversations
            new_conversations = 0
            for i, element in enumerate(elements):
                try:
                    # Get the parent link element if we're on a span
                    if element.tag_name == "span":
                        parent = element.find_element(By.XPATH, "./..")
                        href = parent.get_attribute("href")
                    else:
                        href = element.get_attribute("href")
                    
                    title = element.text.strip()
                    
                    if href and title and "/c/" in href and href not in seen_urls:
                        conversation = {
                            "id": href.split("/c/")[-1] if "/c/" in href else f"conv_{i}",
                            "title": title,
                            "url": href
                        }
                        conversations.append(conversation)
                        seen_urls.add(href)
                        new_conversations += 1
                        
                except Exception as e:
                    logger.warning(f"Failed to extract conversation {i}: {e}")
                    continue
            
            logger.info(f"✅ Found {new_conversations} new conversations (Total: {len(conversations)})")
            
            # Check if we're still finding new conversations
            if new_conversations == 0:
                no_new_conversations_count += 1
                if no_new_conversations_count >= 3:  # Stop if no new conversations for 3 attempts
                    logger.info("🛑 No new conversations found after 3 scroll attempts, stopping...")
                    break
            else:
                no_new_conversations_count = 0
            
            # Scroll down to load more conversations
            try:
                # Scroll to the bottom of the conversation list
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # Wait for new content to load
                
                # Alternative: scroll the conversation container specifically
                conversation_containers = driver.find_elements(By.XPATH, "//nav | //div[contains(@class, 'conversation')] | //div[contains(@class, 'sidebar')]")
                for container in conversation_containers:
                    try:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
                    except:
                        continue
                
                time.sleep(1)  # Additional wait for content to load
                
            except Exception as e:
                logger.warning(f"Scroll attempt {scroll_attempts + 1} failed: {e}")
            
            scroll_attempts += 1
            
            # Safety check: if we haven't found new conversations in a while, stop
            if len(conversations) == last_count:
                if scroll_attempts > 10:  # After 10 attempts with no new conversations
                    logger.info("🛑 No new conversations found after 10 scroll attempts, stopping...")
                    break
            else:
                last_count = len(conversations)
        
        logger.info(f"✅ Extracted {len(conversations)} conversations after {scroll_attempts} scroll attempts")
        return conversations
    
    def get_conversation_list(self, driver, progress_callback=None) -> List[Dict[str, str]]:
        """
        Get list of available conversations with self-healing and infinite scrolling.
        
        Args:
            driver: Selenium webdriver instance
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of conversation dictionaries
        """
        try:
            logger.info("📋 Fetching conversation list with adaptive extraction and infinite scrolling...")
            
            # Discover working URL
            working_url = self._discover_working_url(driver)
            driver.get(working_url)
            time.sleep(5)
            
            # Try cached selectors first
            selectors_to_try = []
            
            # Add cached successful selectors first
            if self.successful_selectors.get("selectors"):
                selectors_to_try.extend(self.successful_selectors["selectors"])
                logger.info(f"🔄 Trying {len(self.successful_selectors['selectors'])} cached selectors first")
            
            # Add all library selectors
            selectors_to_try.extend(self.selector_library["conversation_links"])
            
            # Remove duplicates while preserving order
            seen = set()
            selectors_to_try = [s for s in selectors_to_try if not (s in seen or seen.add(s))]
            
            logger.info(f"🔍 Testing {len(selectors_to_try)} selectors...")
            
            for i, selector in enumerate(selectors_to_try):
                try:
                    logger.debug(f"Testing selector {i+1}/{len(selectors_to_try)}: {selector}")
                    
                    success, elements = self._test_selector(driver, selector)
                    
                    if success and elements:
                        logger.info(f"✅ Found {len(elements)} conversations using selector: {selector}")
                        
                        # Extract conversations with infinite scrolling
                        conversations = self._extract_conversations_with_scrolling(driver, selector)
                        
                        if conversations:
                            # Cache successful selector
                            if selector not in self.successful_selectors.get("selectors", []):
                                if "selectors" not in self.successful_selectors:
                                    self.successful_selectors["selectors"] = []
                                self.successful_selectors["selectors"].insert(0, selector)  # Add to front
                                self.successful_selectors["urls"] = [working_url]
                                self._save_selector_cache()
                            
                            logger.info(f"✅ Extracted {len(conversations)} conversations")
                            return conversations
                        else:
                            logger.warning(f"Selector found elements but no valid conversations: {selector}")
                    
                except Exception as e:
                    logger.debug(f"Selector failed: {selector} - {e}")
                    continue
            
            # If no selectors worked, try fallback approach
            logger.warning("❌ No selectors worked, trying fallback approach...")
            return self._fallback_extraction(driver)
            
        except Exception as e:
            logger.error(f"Failed to get conversation list: {e}")
            return []
    
    def _fallback_extraction(self, driver) -> List[Dict[str, str]]:
        """Fallback extraction method when all selectors fail."""
        try:
            logger.info("🔄 Attempting fallback extraction...")
            
            # Get all links and filter for conversation URLs
            all_links = driver.find_elements(By.TAG_NAME, "a")
            conversations = []
            
            for link in all_links:
                try:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    
                    if href and text and "/c/" in href:
                        conversation = {
                            "id": href.split("/c/")[-1],
                            "title": text,
                            "url": href
                        }
                        conversations.append(conversation)
                        
                except Exception as e:
                    continue
            
            if conversations:
                logger.info(f"✅ Fallback found {len(conversations)} conversations")
                return conversations
            
            logger.error("❌ Fallback extraction also failed")
            return []
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, any]:
        """Get health status of the adaptive extractor."""
        return {
            "cached_selectors": len(self.successful_selectors.get("selectors", [])),
            "selector_library_size": len(self.selector_library["conversation_links"]),
            "last_working_url": self.successful_selectors.get("urls", [None])[0],
            "cache_file": self.selector_cache_file
        } 