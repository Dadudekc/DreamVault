"""
Conversation Extractor for DreamVault ChatGPT Scraper

Handles conversation listing, extraction, and content retrieval operations.
"""

import time
import json
import logging
from typing import List, Dict, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

logger = logging.getLogger(__name__)

class ConversationExtractor:
    """Handles conversation extraction and content retrieval from ChatGPT."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize the conversation extractor.
        
        Args:
            timeout: Timeout for web operations
        """
        self.timeout = timeout
    
    def get_conversation_list(self, driver, progress_callback=None) -> List[Dict[str, str]]:
        """
        Get list of available conversations with infinite scrolling.
        
        Args:
            driver: Selenium webdriver instance
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of conversation dictionaries
        """
        try:
            logger.info("📋 Fetching conversation list with infinite scrolling...")
            
            # Navigate to ChatGPT
            driver.get("https://chatgpt.com")
            time.sleep(5)  # Wait longer for page to load
            
            # Wait for conversation list to load
            wait = WebDriverWait(driver, self.timeout)
            
            # Look for conversation list elements
            conversation_selectors = [
                "//a[contains(@href, '/c/')]//span",
                "//a[contains(@href, '/c/')]",
                "//div[contains(@class, 'conversation')]//a",
                "//nav//a[contains(@href, '/c/')]"
            ]
            
            # Find the working selector first
            working_selector = None
            for selector in conversation_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} conversations using selector: {selector}")
                        working_selector = selector
                        break
                except:
                    continue
            
            if not working_selector:
                logger.error("❌ No working conversation selector found")
                return []
            
            # Scroll to load all conversations
            logger.info("🔄 Starting infinite scroll to load all conversations...")
            conversations = []
            seen_urls = set()
            scroll_attempts = 0
            max_scroll_attempts = 50  # Prevent infinite loops
            last_count = 0
            no_new_conversations_count = 0
            
            while scroll_attempts < max_scroll_attempts:
                # Get current conversations
                elements = driver.find_elements(By.XPATH, working_selector)
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
                            
                            if progress_callback:
                                progress_callback(len(conversations), current_count)
                        
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
            
        except Exception as e:
            logger.error(f"Failed to get conversation list: {e}")
            return []
    
    def enter_conversation(self, driver, conversation_url: str) -> bool:
        """
        Navigate to a specific conversation.
        
        Args:
            driver: Selenium webdriver instance
            conversation_url: URL of the conversation to enter
            
        Returns:
            True if successfully entered conversation, False otherwise
        """
        try:
            logger.info(f"📋 Navigating to conversation: {conversation_url}")
            
            # Navigate to conversation URL
            driver.get(conversation_url)
            time.sleep(3)
            
            # Wait for conversation content to load
            wait = WebDriverWait(driver, self.timeout)
            
            # Look for conversation content indicators
            content_indicators = [
                "//div[contains(@class, 'markdown')]",
                "//div[contains(@class, 'message')]",
                "//div[contains(@class, 'conversation')]//div[contains(@class, 'text')]",
                "//main//div[contains(@class, 'prose')]"
            ]
            
            content_found = False
            for indicator in content_indicators:
                try:
                    element = wait.until(EC.presence_of_element_located((By.XPATH, indicator)))
                    if element.is_displayed():
                        content_found = True
                        logger.info(f"Conversation content found using: {indicator}")
                        break
                except TimeoutException:
                    continue
            
            if not content_found:
                logger.warning("Conversation content not found")
                return False
            
            logger.info("✅ Successfully entered conversation")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to enter conversation: {e}")
            return False
    
    def get_conversation_content(self, driver) -> Dict[str, str]:
        """
        Extract content from the current conversation.
        
        Args:
            driver: Selenium webdriver instance
            
        Returns:
            Dictionary containing conversation content
        """
        try:
            logger.info("📝 Extracting conversation content...")
            
            # Extract conversation title
            title = ""
            title_selectors = [
                "//h1",
                "//div[contains(@class, 'title')]",
                "//div[contains(@class, 'conversation-title')]"
            ]
            
            for selector in title_selectors:
                try:
                    element = driver.find_element(By.XPATH, selector)
                    title = element.text.strip()
                    if title:
                        break
                except:
                    continue
            
            # Extract messages
            messages = []
            message_selectors = [
                "//div[contains(@data-testid, 'conversation-turn')]",
                "//div[contains(@class, 'message')]",
                "//div[contains(@class, 'markdown')]"
            ]
            
            for selector in message_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, selector)
                    if elements:
                        for element in elements:
                            try:
                                text = element.text.strip()
                                if text:
                                    # Try to determine role (user/assistant)
                                    role = "assistant"  # Default
                                    if "user" in element.get_attribute("class") or "user" in element.get_attribute("data-testid"):
                                        role = "user"
                                    
                                    messages.append({
                                        "role": role,
                                        "content": text
                                    })
                            except Exception as e:
                                logger.warning(f"Failed to extract message: {e}")
                                continue
                        break
                except:
                    continue
            
            # Extract conversation metadata
            metadata = {
                "title": title,
                "message_count": len(messages),
                "extracted_at": time.time()
            }
            
            logger.info(f"✅ Extracted {len(messages)} messages from conversation")
            
            return {
                "title": title,
                "messages": messages,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to extract conversation content: {e}")
            return {
                "title": "",
                "messages": [],
                "metadata": {"error": str(e)}
            }
    
    def save_conversation(self, conversation_data: Dict, output_file: str) -> bool:
        """
        Save conversation data to file.
        
        Args:
            conversation_data: Conversation data to save
            output_file: Output file path
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved conversation to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False 