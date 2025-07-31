"""
ChatGPT Scraper for DreamVault

Integrated scraper with cookies, manual login, rate limits, and model selection.
"""

import os
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Callable
from datetime import datetime

from .browser_manager import BrowserManager
from .cookie_manager import CookieManager
from .login_handler import LoginHandler
from .conversation_extractor import ConversationExtractor
from .adaptive_extractor import AdaptiveExtractor

logger = logging.getLogger(__name__)

class ChatGPTScraper:
    """
    Integrated ChatGPT scraper with all essential features.
    
    Features:
    - Cookie persistence
    - Manual login support
    - Rate limiting
    - Model selection
    - Conversation extraction
    - Resume functionality
    """
    
    def __init__(self, 
                 headless: bool = False,
                 use_undetected: bool = True,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 totp_secret: Optional[str] = None,
                 cookie_file: Optional[str] = None,
                 rate_limit_delay: float = 2.0,
                 progress_file: str = "data/scraper_progress.json"):
        """
        Initialize the ChatGPT scraper.
        
        Args:
            headless: Run browser in headless mode
            use_undetected: Use undetected-chromedriver
            username: ChatGPT username/email
            password: ChatGPT password
            totp_secret: TOTP secret for 2FA
            cookie_file: Path to cookie file
            rate_limit_delay: Delay between requests (seconds)
            progress_file: Path to progress tracking file
        """
        # Initialize components
        self.browser_manager = BrowserManager(headless=headless, use_undetected=use_undetected)
        self.cookie_manager = CookieManager(cookie_file)
        self.login_handler = LoginHandler(username, password, totp_secret)
        self.conversation_extractor = ConversationExtractor()
        self.adaptive_extractor = AdaptiveExtractor()
        
        # Configuration
        self.rate_limit_delay = rate_limit_delay
        self.driver = None
        self.progress_file = progress_file
        
        # Rate limiting state
        self.last_request_time = 0
        self.request_count = 0
        
        # Progress tracking
        self.processed_conversations = self._load_progress()
        
        logger.info("✅ ChatGPT Scraper initialized")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_driver()
    
    def start_driver(self) -> bool:
        """Start the web driver."""
        try:
            self.driver = self.browser_manager.create_driver()
            if self.driver:
                logger.info("✅ Driver started successfully")
                return True
            else:
                logger.error("❌ Failed to start driver")
                return False
        except Exception as e:
            logger.error(f"Failed to start driver: {e}")
            return False
    
    def close_driver(self):
        """Close the web driver."""
        if self.driver:
            self.browser_manager.close_driver()
            self.driver = None
            logger.info("✅ Driver closed")
    
    def ensure_login(self, allow_manual: bool = True, manual_timeout: int = 60) -> bool:
        """
        Ensure user is logged into ChatGPT.
        
        Args:
            allow_manual: Allow manual login if automated fails
            manual_timeout: Timeout for manual login
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Try to load cookies first
            if self.cookie_manager.has_valid_cookies():
                logger.info("🍪 Loading saved cookies...")
                self.cookie_manager.load_cookies(self.driver)
                
                # Check if cookies are still valid
                if self.login_handler._is_logged_in(self.driver):
                    logger.info("✅ Login successful with saved cookies")
                    return True
            
            # Perform login
            if self.login_handler.ensure_login(self.driver, allow_manual, manual_timeout):
                # Save cookies after successful login
                self.cookie_manager.save_cookies(self.driver)
                logger.info("✅ Login successful, cookies saved")
                return True
            else:
                logger.error("❌ Login failed")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def select_model(self, model: str = "") -> bool:
        """
        Select a specific ChatGPT model.
        
        Args:
            model: Model to select (e.g., "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo")
            
        Returns:
            True if model selection successful, False otherwise
        """
        if not model:
            logger.info("No specific model selected, using default")
            return True
        
        try:
            logger.info(f"🤖 Selecting model: {model}")
            
            # Navigate to ChatGPT
            self.driver.get("https://chat.openai.com")
            time.sleep(3)
            
            # Look for model selector
            model_selectors = [
                f"//button[contains(text(), '{model}')]",
                f"//div[contains(text(), '{model}')]",
                "//button[contains(@data-testid, 'model-selector')]"
            ]
            
            for selector in model_selectors:
                try:
                    element = self.driver.find_element_by_xpath(selector)
                    if element.is_displayed():
                        element.click()
                        time.sleep(2)
                        logger.info(f"✅ Model {model} selected")
                        return True
                except:
                    continue
            
            logger.warning(f"⚠️ Could not select model {model}, using default")
            return False
            
        except Exception as e:
            logger.error(f"Model selection error: {e}")
            return False
    
    def get_conversation_list(self, progress_callback: Optional[Callable] = None) -> List[Dict[str, str]]:
        """
        Get list of available conversations with self-healing.
        
        Args:
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of conversation dictionaries
        """
        try:
            self._rate_limit()
            
            # Try adaptive extractor first (self-healing)
            logger.info("🔄 Using adaptive extractor for self-healing...")
            conversations = self.adaptive_extractor.get_conversation_list(self.driver, progress_callback)
            
            if conversations:
                logger.info(f"✅ Adaptive extractor found {len(conversations)} conversations")
                return conversations
            
            # Fallback to original extractor
            logger.warning("🔄 Adaptive extractor failed, trying original extractor...")
            return self.conversation_extractor.get_conversation_list(self.driver, progress_callback)
            
        except Exception as e:
            logger.error(f"Failed to get conversation list: {e}")
            return []
    
    def extract_conversation(self, conversation_url: str, output_dir: str = "data/raw") -> bool:
        """
        Extract a single conversation.
        
        Args:
            conversation_url: URL of the conversation to extract
            output_dir: Directory to save extracted conversation
            
        Returns:
            True if extraction successful, False otherwise
        """
        try:
            self._rate_limit()
            
            # Create output directory
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Enter conversation
            if not self.conversation_extractor.enter_conversation(self.driver, conversation_url):
                return False
            
            # Extract content
            conversation_data = self.conversation_extractor.get_conversation_content(self.driver)
            
            # Generate filename
            conversation_id = conversation_url.split("/c/")[-1] if "/c/" in conversation_url else f"conv_{int(time.time())}"
            filename = f"{conversation_id}.json"
            output_file = Path(output_dir) / filename
            
            # Save conversation
            if self.conversation_extractor.save_conversation(conversation_data, str(output_file)):
                logger.info(f"✅ Extracted conversation: {filename}")
                return True
            else:
                logger.error(f"❌ Failed to save conversation: {filename}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to extract conversation: {e}")
            return False
    
    def extract_all_conversations(self, limit: Optional[int] = None, 
                                output_dir: str = "data/raw",
                                progress_callback: Optional[Callable] = None,
                                skip_processed: bool = True) -> Dict[str, int]:
        """
        Extract all available conversations with resume functionality.
        
        Args:
            limit: Maximum number of conversations to extract
            output_dir: Directory to save extracted conversations
            progress_callback: Optional callback for progress updates
            skip_processed: Skip already processed conversations
            
        Returns:
            Dictionary with extraction statistics
        """
        try:
            logger.info("🚀 Starting conversation extraction...")
            
            # Get progress stats
            progress_stats = self.get_progress_stats()
            if progress_stats["total_processed"] > 0:
                logger.info(f"📊 Resume mode: {progress_stats['successful']} conversations already processed")
            
            # Get conversation list
            conversations = self.get_conversation_list(progress_callback)
            
            if limit:
                conversations = conversations[:limit]
            
            # Filter out already processed conversations
            if skip_processed:
                original_count = len(conversations)
                conversations = [conv for conv in conversations if not self._is_conversation_processed(conv)]
                skipped_count = original_count - len(conversations)
                if skipped_count > 0:
                    logger.info(f"⏭️ Skipping {skipped_count} already processed conversations")
            
            logger.info(f"📋 Found {len(conversations)} conversations to extract")
            
            if len(conversations) == 0:
                logger.info("✅ All conversations already processed!")
                return {
                    "total": 0,
                    "extracted": 0,
                    "failed": 0,
                    "skipped": progress_stats["total_processed"],
                    "errors": []
                }
            
            stats = {
                "total": len(conversations),
                "extracted": 0,
                "failed": 0,
                "skipped": progress_stats["total_processed"],
                "errors": []
            }
            
            for i, conversation in enumerate(conversations):
                try:
                    logger.info(f"📝 Extracting conversation {i+1}/{len(conversations)}: {conversation.get('title', 'Unknown')}")
                    
                    if self.extract_conversation(conversation['url'], output_dir):
                        stats["extracted"] += 1
                        self._mark_conversation_processed(conversation, success=True)
                    else:
                        stats["failed"] += 1
                        self._mark_conversation_processed(conversation, success=False)
                        stats["errors"].append(f"Failed to extract {conversation.get('id', 'unknown')}")
                    
                    if progress_callback:
                        progress_callback(i + 1, len(conversations))
                        
                except Exception as e:
                    stats["failed"] += 1
                    self._mark_conversation_processed(conversation, success=False)
                    stats["errors"].append(f"Error extracting {conversation.get('id', 'unknown')}: {e}")
                    logger.error(f"Error extracting conversation: {e}")
            
            logger.info(f"✅ Extraction complete: {stats['extracted']}/{stats['total']} successful")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to extract conversations: {e}")
            return {"total": 0, "extracted": 0, "failed": 0, "errors": [str(e)]}
    
    def get_rate_limit_info(self) -> Dict[str, any]:
        """Get current rate limiting information."""
        return {
            "request_count": self.request_count,
            "rate_limit_delay": self.rate_limit_delay,
            "last_request_time": self.last_request_time
        }
    
    def get_adaptive_health_status(self) -> Dict[str, any]:
        """Get health status of the adaptive extractor."""
        return self.adaptive_extractor.get_health_status() 

    def _load_progress(self) -> Dict[str, Dict]:
        """Load progress from file."""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    logger.info(f"📊 Loaded progress: {len(progress)} conversations already processed")
                    return progress
        except Exception as e:
            logger.warning(f"Failed to load progress: {e}")
        return {}
    
    def _save_progress(self):
        """Save progress to file."""
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            with open(self.progress_file, 'w') as f:
                json.dump(self.processed_conversations, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
    
    def _get_conversation_hash(self, conversation: Dict) -> str:
        """Generate hash for conversation identification."""
        content = f"{conversation.get('id', '')}{conversation.get('title', '')}{conversation.get('url', '')}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_conversation_processed(self, conversation: Dict) -> bool:
        """Check if conversation has already been processed."""
        conv_hash = self._get_conversation_hash(conversation)
        return conv_hash in self.processed_conversations
    
    def _mark_conversation_processed(self, conversation: Dict, success: bool = True):
        """Mark conversation as processed."""
        conv_hash = self._get_conversation_hash(conversation)
        self.processed_conversations[conv_hash] = {
            "id": conversation.get('id'),
            "title": conversation.get('title'),
            "url": conversation.get('url'),
            "processed_at": datetime.now().isoformat(),
            "success": success
        }
        self._save_progress()
    
    def reset_progress(self):
        """Reset progress tracking."""
        self.processed_conversations = {}
        if os.path.exists(self.progress_file):
            os.remove(self.progress_file)
        logger.info("🔄 Progress reset - will process all conversations")
    
    def get_progress_stats(self) -> Dict[str, any]:
        """Get progress statistics."""
        total_processed = len(self.processed_conversations)
        successful = sum(1 for conv in self.processed_conversations.values() if conv.get('success', False))
        failed = total_processed - successful
        
        return {
            "total_processed": total_processed,
            "successful": successful,
            "failed": failed,
            "progress_file": self.progress_file
        } 