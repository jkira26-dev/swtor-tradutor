"""
Deep analysis of the translation pipeline to find all bugs.
"""
import os
import sys
import io
import sqlite3
import struct
import html

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.append("patcher_br")
from myp_parser import MYPArchive, load_hash_list
from stb_parser import STBFile

# === CONFIG ===
GAME_PATH = r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic"
ASSETS_DIR = os.path.join(GAME_PATH, "Assets")
DB_PATH = "db/translate_pt.db3"
HASH_LIST = "db/hashes_filename.txt"

# === 1. Inspect DB structure ===
print("=" * 60)
print("PART 1: Database Structure Analysis")
print("=" * 60)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Get table info
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables: {[t[0] for t in tables]}")

for table in tables:
    cursor.execute(f"PRAGMA table_info({table[0]})")
    cols = cursor.fetchall()
    print(f"\nTable '{table[0]}' columns:")
    for col in cols:
        print(f"  {col[1]} ({col[2]})")

# Sample data
print("\n--- Sample rows from Translated ---")
cursor.execute("SELECT * FROM Translated LIMIT 3")
cols = [d[0] for d in cursor.description]
print(f"Columns: {cols}")
for row in cursor.fetchall():
    for i, col in enumerate(cols):
        val = row[i]
        if isinstance(val, str) and len(val) > 80:
            val = val[:80] + "..."
        print(f"  {col}: {val}")
    print("  ---")

# === 2. Check key_unic vs string_id mapping ===
print("\n" + "=" * 60)
print("PART 2: key_unic Analysis")
print("=" * 60)

cursor.execute("SELECT fileinfo, key_unic, text_en FROM Translated WHERE fileinfo='abl.stb' LIMIT 10")
rows = cursor.fetchall()
print("\nDB entries for abl.stb (first 10):")
for row in rows:
    print(f"  key_unic={row[1]}, text_en='{row[2][:60] if row[2] else ''}'")

# === 3. Compare DB key_unic with actual STB string_id ===
print("\n" + "=" * 60)
print("PART 3: DB key_unic vs STB string_id comparison")
print("=" * 60)

hash_map = load_hash_list(HASH_LIST)
tor_path = os.path.join(ASSETS_DIR, "swtor_en-us_global_1.tor")
archive = MYPArchive(tor_path)
archive.load()
archive.resolve_names(hash_map)

abl_entry = None
for entry in archive.entries:
    if entry.file_name and entry.file_name.endswith("abl.stb"):
        abl_entry = entry
        break

if abl_entry:
    raw = archive.extract_entry_data(abl_entry)
    stb = STBFile.from_bytes(raw)
    
    stb_ids = {e.string_id for e in stb.entries}
    
    cursor.execute("SELECT key_unic FROM Translated WHERE fileinfo='abl.stb'")
    db_keys = set()
    for row in cursor.fetchall():
        try:
            db_keys.add(int(row[0]))
        except:
            pass
    
    overlap = stb_ids & db_keys
    only_stb = stb_ids - db_keys
    only_db = db_keys - stb_ids
    
    print(f"STB string_ids: {len(stb_ids)}")
    print(f"DB key_unic values: {len(db_keys)}")
    print(f"Overlap (matched): {len(overlap)}")
    print(f"Only in STB (no translation): {len(only_stb)}")
    print(f"Only in DB (orphaned): {len(only_db)}")

# === 4. Check how build_patcher matches translations ===
print("\n" + "=" * 60)
print("PART 4: build_patcher Match Method Analysis")
print("=" * 60)
print("build_patcher matches by TEXT CONTENT (text_en == stb_entry.text)")
print("This means it searches by English text, NOT by string_id/key_unic!")

# Check for potential mismatches
cursor.execute(
    "SELECT text_en, text_pt_m FROM Translated WHERE fileinfo='abl.stb' AND text_pt_m IS NOT NULL AND text_pt_m != '' LIMIT 5"
)
rows = cursor.fetchall()
print("\nSample translations from DB:")
for row in rows:
    en = html.unescape(row[0]) if row[0] else ""
    pt = html.unescape(row[1]) if row[1] else ""
    print(f"  EN: '{en[:60]}'")
    print(f"  PT: '{pt[:60]}'")
    
    # Check if this EN text exists in the STB
    found = False
    for e in stb.entries:
        if e.text == en:
            found = True
            break
    print(f"  Found in STB: {found}")
    print()

# === 5. STB repack with translation - simulate and check sizes ===
print("\n" + "=" * 60)
print("PART 5: Simulated Translation Repack - Size Analysis")
print("=" * 60)

cursor.execute(
    "SELECT text_en, text_pt_m FROM Translated WHERE fileinfo='abl.stb' AND text_pt_m IS NOT NULL AND text_pt_m != ''"
)
translations = cursor.fetchall()
en_to_pt = {}
for row in translations:
    en = html.unescape(row[0]) if row[0] else ""
    pt = html.unescape(row[1]) if row[1] else ""
    if en and pt:
        en_to_pt[en] = pt

print(f"Total translations available: {len(en_to_pt)}")

# Clone STB and apply translations
stb2 = STBFile.from_bytes(raw)
replaced = 0
len2_mismatches = 0
for e in stb2.entries:
    if e.text in en_to_pt:
        old_text = e.text
        new_text = en_to_pt[e.text]
        old_encoded_len = len(old_text.encode('utf-8')) + 1
        new_encoded_len = len(new_text.encode('utf-8')) + 1
        
        e.text = new_text
        replaced += 1
        
        # Check len2 problem
        if e.len2 != new_encoded_len:
            len2_mismatches += 1
            if len2_mismatches <= 5:
                print(f"  len2 MISMATCH: id={e.string_id}")
                print(f"    old text: '{old_text[:50]}'")
                print(f"    new text: '{new_text[:50]}'")
                print(f"    old len2={e.len2}, new encoded len={new_encoded_len}")

print(f"\nReplaced: {replaced}")
print(f"len2 mismatches: {len2_mismatches}")

# Now generate bytes and compare structure
new_bytes = stb2.to_bytes()
print(f"\nOriginal STB bytes: {len(raw)}")
print(f"Translated STB bytes: {len(new_bytes)}")

# Verify the translated STB can be re-parsed
try:
    stb3 = STBFile.from_bytes(new_bytes)
    print(f"Re-parsed successfully: {len(stb3.entries)} entries")
    
    # Check if offsets are valid
    bad_offsets = 0
    for e in stb3.entries:
        if not e.text and e.string_id != 0:
            bad_offsets += 1
    print(f"Entries with empty text after re-parse: {bad_offsets}")
except Exception as ex:
    print(f"RE-PARSE FAILED: {ex}")

# === 6. Compression method analysis ===
print("\n" + "=" * 60)
print("PART 6: inject_file compression method check")
print("=" * 60)
print(f"Original entry compression_method: {abl_entry.compression_method}")
print(f"inject_file sets compression_method to: 1 (zlib)")
print(f"But it uses zstandard to compress!")
print(f"MISMATCH: compression_method=1 means zlib, but data is zstd!")

conn.close()
print("\n=== ANALYSIS COMPLETE ===")
