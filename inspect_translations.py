import sqlite3
import os

db_path = "db/translate_pt.db3"
hash_list_path = "db/hashes_filename.txt"

# Load hash map {hash1_dec: (hash1_hex, hash2_hex, path)}
hash_map = {}
if os.path.exists(hash_list_path):
    with open(hash_list_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("#")
            if len(parts) >= 3:
                h1_hex = parts[0].upper()
                h2_hex = parts[1].upper()
                h1_dec = int(h1_hex, 16)
                hash_map[h1_dec] = (h1_hex, h2_hex, parts[2])

print(f"Loaded {len(hash_map)} hashes from hash list.")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get unique STB files and their hash from Translated table
cursor.execute("SELECT DISTINCT fileinfo, hash FROM Translated LIMIT 20")
rows = cursor.fetchall()
print("\nSample STB files from Database:")
for row in rows:
    fileinfo, h_val = row
    try:
        h_dec = int(h_val)
    except (ValueError, TypeError):
        print(f"  fileinfo={fileinfo}, hash={h_val} (invalid int)")
        continue
        
    if h_dec in hash_map:
        h1_hex, h2_hex, path = hash_map[h_dec]
        print(f"  fileinfo={fileinfo}, hash={h_dec} -> Path={path} (Key={h1_hex}#{h2_hex})")
    else:
        print(f"  fileinfo={fileinfo}, hash={h_dec} -> PATH NOT FOUND in hashes_filename.txt")

conn.close()
