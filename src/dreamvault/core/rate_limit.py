"""
Leaky bucket rate limiter for ShadowArchive.
"""

import time
import threading
from typing import Dict, Optional, Any
from collections import defaultdict


class LeakyBucket:
    """Leaky bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, leak_rate: float):
        """
        Initialize leaky bucket.
        
        Args:
            capacity: Maximum number of tokens in bucket
            leak_rate: Tokens per second that leak out
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def _leak_tokens(self) -> None:
        """Leak tokens based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_update
        tokens_to_leak = time_passed * self.leak_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_leak)
        self.last_update = now
    
    def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        with self.lock:
            self._leak_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_tokens(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Wait for tokens to become available.
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if tokens were acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.try_acquire(tokens):
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            # Calculate wait time
            with self.lock:
                self._leak_tokens()
                if self.tokens >= tokens:
                    continue
                
                # Calculate time until enough tokens
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.leak_rate
                
                if timeout:
                    remaining_timeout = timeout - (time.time() - start_time)
                    wait_time = min(wait_time, remaining_timeout)
            
            if wait_time <= 0:
                return False
            
            time.sleep(min(wait_time, 0.1))  # Sleep in small increments
    
    def get_stats(self) -> Dict[str, float]:
        """Get current bucket statistics."""
        with self.lock:
            self._leak_tokens()
            return {
                "tokens": self.tokens,
                "capacity": self.capacity,
                "leak_rate": self.leak_rate,
                "utilization": (self.capacity - self.tokens) / self.capacity
            }


class RateLimiter:
    """Rate limiter with global, per-host, and ChatGPT-specific buckets."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize rate limiter.
        
        Args:
            config: Configuration with global, per-host, and ChatGPT rate limits
        """
        self.global_config = config.get("global", {})
        self.per_host_config = config.get("per_host", {})
        self.chatgpt_config = config.get("chatgpt", {})
        
        # Global bucket
        global_rpm = self.global_config.get("requests_per_minute", 0.83)
        global_burst = self.global_config.get("burst_size", 5)
        
        self.global_bucket = LeakyBucket(
            capacity=global_burst,
            leak_rate=global_rpm / 60.0
        )
        
        # Per-host buckets
        self.host_buckets: Dict[str, LeakyBucket] = {}
        self.host_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        # Per-host configuration
        self.host_rpm = self.per_host_config.get("requests_per_minute", 0.28)
        self.host_burst = self.per_host_config.get("burst_size", 3)
        
        # ChatGPT-specific buckets
        self.chatgpt_buckets: Dict[str, LeakyBucket] = {}
        self.chatgpt_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)
        
        # Initialize ChatGPT buckets
        self._init_chatgpt_buckets()
    
    def _init_chatgpt_buckets(self) -> None:
        """Initialize ChatGPT-specific rate limit buckets."""
        # GPT-4o: 150 messages per 3 hours
        gpt4o_config = self.chatgpt_config.get("gpt4o", {})
        gpt4o_messages = gpt4o_config.get("messages_per_3hrs", 150)
        gpt4o_burst = gpt4o_config.get("burst_size", 10)
        
        self.chatgpt_buckets["gpt4o"] = LeakyBucket(
            capacity=gpt4o_burst,
            leak_rate=gpt4o_messages / (3 * 3600)  # messages per second
        )
        
        # GPT-4.5: 50 messages per week
        gpt45_config = self.chatgpt_config.get("gpt45", {})
        gpt45_messages = gpt45_config.get("messages_per_week", 50)
        gpt45_burst = gpt45_config.get("burst_size", 5)
        
        self.chatgpt_buckets["gpt45"] = LeakyBucket(
            capacity=gpt45_burst,
            leak_rate=gpt45_messages / (7 * 24 * 3600)  # messages per second
        )
        
        # o3-mini-high: 50 messages per day
        o3_config = self.chatgpt_config.get("o3_mini_high", {})
        o3_messages = o3_config.get("messages_per_day", 50)
        o3_burst = o3_config.get("burst_size", 3)
        
        self.chatgpt_buckets["o3_mini_high"] = LeakyBucket(
            capacity=o3_burst,
            leak_rate=o3_messages / (24 * 3600)  # messages per second
        )
    
    def _get_chatgpt_bucket(self, model: str) -> Optional[LeakyBucket]:
        """Get ChatGPT bucket for specific model."""
        if model in self.chatgpt_buckets:
            return self.chatgpt_buckets[model]
        
        # Handle auto-throttle for gpt4o_mini
        if model == "gpt4o_mini":
            gpt4o_mini_config = self.chatgpt_config.get("gpt4o_mini", {})
            if gpt4o_mini_config.get("auto_throttle", False):
                fallback = gpt4o_mini_config.get("fallback_to", "gpt4o")
                return self.chatgpt_buckets.get(fallback)
        
        return None
    
    def _get_host_bucket(self, host: str) -> LeakyBucket:
        """Get or create bucket for a specific host."""
        with self.host_locks[host]:
            if host not in self.host_buckets:
                self.host_buckets[host] = LeakyBucket(
                    capacity=self.host_burst,
                    leak_rate=self.host_rpm / 60.0
                )
            return self.host_buckets[host]
    
    def try_acquire(self, host: Optional[str] = None, tokens: int = 1, model: Optional[str] = None) -> bool:
        """
        Try to acquire tokens from global, host, and ChatGPT model buckets.
        
        Args:
            host: Host identifier for per-host limiting
            tokens: Number of tokens to acquire
            model: ChatGPT model identifier (e.g., "gpt4o", "gpt45")
            
        Returns:
            True if tokens were acquired from all applicable buckets
        """
        # Try global bucket first
        if not self.global_bucket.try_acquire(tokens):
            return False
        
        # If host is specified, try host bucket
        if host:
            host_bucket = self._get_host_bucket(host)
            if not host_bucket.try_acquire(tokens):
                return False
        
        # If model is specified, try ChatGPT model bucket
        if model:
            chatgpt_bucket = self._get_chatgpt_bucket(model)
            if chatgpt_bucket and not chatgpt_bucket.try_acquire(tokens):
                return False
        
        return True
    
    def wait_for_tokens(
        self, 
        host: Optional[str] = None, 
        tokens: int = 1, 
        timeout: Optional[float] = None,
        model: Optional[str] = None
    ) -> bool:
        """
        Wait for tokens to become available in both buckets.
        
        Args:
            host: Host identifier for per-host limiting
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if tokens were acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.try_acquire(host, tokens, model):
                return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            # Calculate wait times for all applicable buckets
            global_wait = self._calculate_wait_time(self.global_bucket, tokens)
            wait_times = [global_wait]
            
            if host:
                host_bucket = self._get_host_bucket(host)
                host_wait = self._calculate_wait_time(host_bucket, tokens)
                wait_times.append(host_wait)
            
            if model:
                chatgpt_bucket = self._get_chatgpt_bucket(model)
                if chatgpt_bucket:
                    model_wait = self._calculate_wait_time(chatgpt_bucket, tokens)
                    wait_times.append(model_wait)
            
            wait_time = max(wait_times)
            
            if timeout:
                remaining_timeout = timeout - (time.time() - start_time)
                wait_time = min(wait_time, remaining_timeout)
            
            if wait_time <= 0:
                return False
            
            time.sleep(min(wait_time, 0.1))
    
    def _calculate_wait_time(self, bucket: LeakyBucket, tokens: int) -> float:
        """Calculate wait time for a bucket to have enough tokens."""
        stats = bucket.get_stats()
        if stats["tokens"] >= tokens:
            return 0.0
        
        tokens_needed = tokens - stats["tokens"]
        return tokens_needed / stats["leak_rate"]
    
    def acquire_with_backoff(
        self,
        host: Optional[str] = None,
        tokens: int = 1,
        max_retries: int = 3,
        base_delay: float = 1.0,
        model: Optional[str] = None
    ) -> bool:
        """
        Acquire tokens with exponential backoff retry.
        
        Args:
            host: Host identifier for per-host limiting
            tokens: Number of tokens to acquire
            max_retries: Maximum number of retry attempts
            base_delay: Base delay for exponential backoff
            
        Returns:
            True if tokens were acquired, False if all retries failed
        """
        for attempt in range(max_retries + 1):
            if self.try_acquire(host, tokens, model):
                return True
            
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
        
        return False
    
    def get_stats(self, host: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        stats = {
            "global": self.global_bucket.get_stats()
        }
        
        if host:
            host_bucket = self._get_host_bucket(host)
            stats["host"] = host_bucket.get_stats()
        
        if model:
            chatgpt_bucket = self._get_chatgpt_bucket(model)
            if chatgpt_bucket:
                stats["chatgpt_model"] = chatgpt_bucket.get_stats()
        
        # Add all ChatGPT model stats
        stats["chatgpt_models"] = {}
        for model_name, bucket in self.chatgpt_buckets.items():
            stats["chatgpt_models"][model_name] = bucket.get_stats()
        
        return stats
    
    def reset_host_bucket(self, host: str) -> None:
        """Reset the bucket for a specific host."""
        with self.host_locks[host]:
            if host in self.host_buckets:
                del self.host_buckets[host]
    
    def get_all_hosts(self) -> list:
        """Get list of all hosts with buckets."""
        return list(self.host_buckets.keys()) 