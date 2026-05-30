import sqlite3
import json
import os

# Connect directly to SQLite file
conn = sqlite3.connect('db.sqlite3')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print("Tables found:", tables)

all_data = {}

for table in tables:
    try:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        all_data[table] = [dict(row) for row in rows]
        print(f"  {table}: {len(rows)} records")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

conn.close()

# Save to file
with open('sqlite_backup.json', 'w', encoding='utf-8', errors='replace') as f:
    json.dump(all_data, f, indent=2, default=str, ensure_ascii=False)

print("\n✅ Done! Saved to sqlite_backup.json")