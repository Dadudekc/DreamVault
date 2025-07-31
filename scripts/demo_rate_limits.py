#!/usr/bin/env python3
"""
ShadowArchive Rate Limiting Demo

Demonstrates ChatGPT model-aware rate limiting capabilities.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from shadowarchive import Config, RateLimiter


def demo_rate_limits():
    """Demonstrate rate limiting with different ChatGPT models."""
    print("⏱️  ShadowArchive Rate Limiting Demo")
    print("=" * 50)
    
    # Load configuration
    config = Config()
    rate_limiter = RateLimiter(config.get("rate_limits", {}))
    
    # Test different models
    models = ["gpt4o", "gpt45", "o3_mini_high", "gpt4o_mini"]
    
    print("\n🤖 Testing ChatGPT Model Rate Limits:")
    print("-" * 40)
    
    for model in models:
        print(f"\n📊 Model: {model}")
        
        # Try to acquire tokens
        success = rate_limiter.try_acquire(model=model, tokens=1)
        print(f"  Acquire 1 token: {'✅' if success else '❌'}")
        
        if success:
            # Try to acquire more tokens
            success2 = rate_limiter.try_acquire(model=model, tokens=2)
            print(f"  Acquire 2 more tokens: {'✅' if success2 else '❌'}")
        
        # Get stats for this model
        stats = rate_limiter.get_stats(model=model)
        if "chatgpt_model" in stats:
            model_stats = stats["chatgpt_model"]
            tokens = model_stats.get("tokens", 0)
            capacity = model_stats.get("capacity", 0)
            utilization = model_stats.get("utilization", 0)
            print(f"  Current: {tokens:.1f}/{capacity} tokens ({utilization:.1%} used)")
    
    # Show all model statistics
    print(f"\n📈 All Model Statistics:")
    print("-" * 30)
    all_stats = rate_limiter.get_stats()
    chatgpt_models = all_stats.get("chatgpt_models", {})
    
    for model_name, model_stats in chatgpt_models.items():
        tokens = model_stats.get("tokens", 0)
        capacity = model_stats.get("capacity", 0)
        leak_rate = model_stats.get("leak_rate", 0)
        utilization = model_stats.get("utilization", 0)
        
        print(f"  {model_name}:")
        print(f"    Tokens: {tokens:.1f}/{capacity}")
        print(f"    Leak rate: {leak_rate:.6f} tokens/sec")
        print(f"    Utilization: {utilization:.1%}")
    
    # Demonstrate waiting for tokens
    print(f"\n⏳ Demonstrating token waiting:")
    print("-" * 30)
    
    # Exhaust gpt4o tokens
    print("  Exhausting gpt4o tokens...")
    while rate_limiter.try_acquire(model="gpt4o", tokens=1):
        pass
    
    print("  gpt4o tokens exhausted. Waiting for replenishment...")
    
    # Wait for tokens to replenish
    start_time = time.time()
    success = rate_limiter.wait_for_tokens(model="gpt4o", tokens=1, timeout=5.0)
    wait_time = time.time() - start_time
    
    if success:
        print(f"  ✅ Token acquired after {wait_time:.2f} seconds")
    else:
        print(f"  ❌ Timeout after {wait_time:.2f} seconds")
    
    # Show final stats
    print(f"\n📊 Final Statistics:")
    print("-" * 20)
    final_stats = rate_limiter.get_stats()
    global_stats = final_stats.get("global", {})
    print(f"  Global: {global_stats.get('tokens', 0):.1f}/{global_stats.get('capacity', 0)} tokens")
    
    for model_name, model_stats in final_stats.get("chatgpt_models", {}).items():
        tokens = model_stats.get("tokens", 0)
        capacity = model_stats.get("capacity", 0)
        print(f"  {model_name}: {tokens:.1f}/{capacity} tokens")


if __name__ == "__main__":
    demo_rate_limits() 