#!/usr/bin/env python3
"""Simple test script to verify the database is working."""

import sqlite3
import json

print("🛰️ Testing DreamVault Database...")

# Connect to database
conn = sqlite3.connect('data/conversations.db')
cursor = conn.cursor()

# Test basic queries
cursor.execute("SELECT COUNT(*) FROM conversations")
count = cursor.fetchone()[0]
print(f"✅ Found {count} conversations in database")

# Get a sample conversation
cursor.execute("SELECT id, summary FROM conversations LIMIT 1")
row = cursor.fetchone()
if row:
    print(f"📋 Sample conversation: {row[0]}")
    print(f"📝 Summary: {row[1][:100]}...")

# Get unique tags
cursor.execute("SELECT tags FROM conversations WHERE tags != '[]' LIMIT 5")
tags_data = cursor.fetchall()
print(f"🏷️  Sample tags from conversations:")
for row in tags_data:
    try:
        tags = json.loads(row[0])
        print(f"  - {tags}")
    except:
        print(f"  - {row[0]}")

# Test full-text search
cursor.execute("SELECT COUNT(*) FROM conversations_fts")
fts_count = cursor.fetchone()[0]
print(f"🔍 Full-text search index: {fts_count} entries")

conn.close()
print("✅ Database test completed!") 