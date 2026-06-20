import sqlite3
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

db_path = os.path.join('db', 'translate_pt.db3')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=== TABLES ===")
for t in tables:
    print(f"  {t[0]}")

# For each table, show schema and sample data
for t in tables:
    table_name = t[0]
    print(f"\n=== TABLE: {table_name} ===")
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    cols = cursor.fetchall()
    for col in cols:
        print(f"  Column: {col[1]} (type={col[2]})")
    
    cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
    count = cursor.fetchone()[0]
    print(f"  Total rows: {count}")
    
    # Show 3 sample rows
    cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 3")
    rows = cursor.fetchall()
    for i, row in enumerate(rows):
        print(f"  Sample {i+1}: {row}")

conn.close()
