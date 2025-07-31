#!/usr/bin/env python3
"""Show database contents."""

import sqlite3
import json

print("🛰️ DreamVault Database Contents")
print("=" * 40)

try:
    conn = sqlite3.connect('data/conversations.db')
    cursor = conn.cursor()
    
    # Count conversations
    cursor.execute("SELECT COUNT(*) FROM conversations")
    count = cursor.fetchone()[0]
    print(f"📊 Total conversations: {count}")
    
    # Show first few conversations
    cursor.execute("SELECT id, summary FROM conversations LIMIT 5")
    rows = cursor.fetchall()
    
    print(f"\n📋 First {len(rows)} conversations:")
    for row in rows:
        conv_id, summary = row
        print(f"  {conv_id}: {summary[:80]}...")
    
    # Show tags
    cursor.execute("SELECT tags FROM conversations WHERE tags != '[]' LIMIT 3")
    tag_rows = cursor.fetchall()
    
    print(f"\n🏷️  Sample tags:")
    for row in tag_rows:
        try:
            tags = json.loads(row[0])
            print(f"  {tags}")
        except:
            print(f"  {row[0]}")
    
    conn.close()
    print("\n✅ Database query successful!")
    
except Exception as e:
    print(f"❌ Error: {e}") 