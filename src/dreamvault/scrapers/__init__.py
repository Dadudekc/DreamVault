"""
DreamVault Scrapers Module

Contains the essential ChatGPT scraping logic duplicated from Dreamscape
for standalone operation with cookies, manual login, rate limits, and model selection.
"""

from .chatgpt_scraper import ChatGPTScraper
from .browser_manager import BrowserManager
from .conversation_extractor import ConversationExtractor
from .cookie_manager import CookieManager
from .login_handler import LoginHandler

__all__ = [
    "ChatGPTScraper",
    "BrowserManager", 
    "ConversationExtractor",
    "CookieManager",
    "LoginHandler"
] 