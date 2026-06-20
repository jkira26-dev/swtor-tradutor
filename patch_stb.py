import os
import sys
import sqlite3

sys.path.append("patcher_br")
from myp_parser import MYPArchive, load_hash_list
from stb_parser import STBFile

def run():
    game_path = r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic"
    tor_path = os.path.join(game_path, "Assets", "swtor_en-us_global_1.tor")
    hash_list_path = "db/hashes_filename.txt"
    db_path = "db/translate_pt.db3"
    
    print("Loading hash list...")
    hash_map = load_hash_list(hash_list_path)
    
    print(f"Loading archive {tor_path}...")
    archive = MYPArchive(tor_path)
    archive.load()
    archive.resolve_names(hash_map)
    
    print("Finding abl.stb...")
    abl_entry = None
    for entry in archive.entries:
        if entry.file_name == "/resources/en-us/str/abl.stb":
            abl_entry = entry
            break
            
    if not abl_entry:
        print("abl.stb not found!")
        return
        
    print("Extracting abl.stb...")
    raw_data = archive.extract_entry_data(abl_entry)
    
    print("Parsing STB...")
    stb = STBFile.from_bytes(raw_data)
    print(f"Loaded {len(stb.entries)} entries from STB.")
    
    print("Connecting to translation DB...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT text_en, text_pt_m, text_pt_w FROM Translated WHERE fileinfo='abl.stb' AND text_pt_m IS NOT NULL AND text_pt_m != ''")
    translations = cursor.fetchall()
    
    print(f"Found {len(translations)} translations for abl.stb.")
    
    # Create mapping from english text to pt text
    en_to_pt = {}
    for row in translations:
        text_en, pt_m, pt_w = row
        new_text = pt_m if pt_m else pt_w
        if text_en and new_text:
            # We use html.unescape because DB seems to use HTML entities (e.g., &#193; for Á)
            import html
            en_to_pt[html.unescape(text_en)] = html.unescape(new_text)
            
    replaced_count = 0
    for entry in stb.entries:
        if entry.text in en_to_pt:
            entry.text = en_to_pt[entry.text]
            replaced_count += 1
            
    print(f"Replaced {replaced_count} strings in memory.")
    
    # We will NOT inject yet to avoid messing up the user's install without a backup,
    # but we can test if serialization works.
    print("Serializing STB to bytes...")
    new_raw_data = stb.to_bytes()
    print(f"Original size: {len(raw_data)}, New size: {len(new_raw_data)}")
    
    print("Test complete.")

if __name__ == "__main__":
    run()
