#!/usr/bin/env python3
"""Simple test for IP extraction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dreamvault.resurrection.ip_extractor import IPExtractor

# Test data with IP patterns
test_conversation = {
    "summary": "I want to build an AI-powered task management app that could revolutionize productivity. I also need to create a workflow for automated code reviews. I abandoned the blockchain identity system due to complexity.",
    "topics": [
        {"topic": "AI task management app development", "confidence": 0.9},
        {"topic": "automated code review workflow", "confidence": 0.8}
    ]
}

print("🛰️ Testing IP Extraction...")

config = {"paths": {"lost_inventions": "data/resurrection/lost_inventions"}}
ip_extractor = IPExtractor(config)

extracted_ip = ip_extractor.extract_ip_from_conversation(test_conversation, "test_conv")

print(f"Product ideas found: {len(extracted_ip['product_ideas'])}")
print(f"Workflows found: {len(extracted_ip['workflows'])}")
print(f"Abandoned ideas found: {len(extracted_ip['abandoned_ideas'])}")
print(f"Potential value: ${extracted_ip['potential_value']:,}")

if extracted_ip['product_ideas']:
    print("Product ideas:")
    for idea in extracted_ip['product_ideas']:
        print(f"  - {idea['text']}")

if extracted_ip['abandoned_ideas']:
    print("Abandoned ideas:")
    for abandoned in extracted_ip['abandoned_ideas']:
        print(f"  - {abandoned['text']}")

print("✅ Test completed!") 