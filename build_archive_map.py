import os
import struct
import json
import time
import winreg

def get_game_path():
    for hive, key_path in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\BioWare\Star Wars-The Old Republic"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BioWare\Star Wars-The Old Republic"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\BioWare\Star Wars-The Old Republic")
    ]:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                return winreg.QueryValueEx(key, "Install Dir")[0]
        except FileNotFoundError:
            pass
    return r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic"

def build_archive_map():
    game_path = get_game_path()
    if not game_path:
        print("Error: Could not detect SWTOR path.")
        return
        
    assets_dir = os.path.join(game_path, "Assets")
    if not os.path.exists(assets_dir):
        print(f"Error: Assets directory not found at {assets_dir}")
        return
        
    hash_list_path = "db/hashes_filename.txt"
    if not os.path.exists(hash_list_path):
        print(f"Error: Hash list file not found at {hash_list_path}")
        return
        
    # Load target hashes
    target_hashes = set()
    hash_to_path = {}
    with open(hash_list_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("#")
            if len(parts) >= 3:
                h1_hex = parts[0].upper()
                h2_hex = parts[1].upper()
                stb_path = parts[2]
                h1_dec = int(h1_hex, 16)
                h2_dec = int(h2_hex, 16)
                target_hashes.add((h1_dec, h2_dec))
                hash_to_path[f"{h1_dec}#{h2_dec}"] = stb_path
                
    print(f"Loaded {len(target_hashes)} target STB hashes from {hash_list_path}")
    
    tor_files = [f for f in os.listdir(assets_dir) if f.startswith("swtor_en-us_") and f.endswith(".tor")]
    print(f"Found {len(tor_files)} swtor_en-us_*.tor archives to scan.")
    
    archive_map = {} # {stb_path: tor_filename}
    start_time = time.time()
    
    for tor_file in tor_files:
        tor_path = os.path.join(assets_dir, tor_file)
        try:
            with open(tor_path, "rb") as f:
                header = f.read(24)
                if len(header) < 24 or header[:4] != b"MYP\x00":
                    continue
                version, unknown, table_offset, files_per_table = struct.unpack("<IIQI", header[4:24])
                
                current_table = table_offset
                while current_table != 0:
                    f.seek(current_table)
                    table_header = f.read(12)
                    if len(table_header) < 12:
                        break
                    num_files, next_table = struct.unpack("<IQ", table_header)
                    
                    for _ in range(num_files):
                        entry_data = f.read(34)
                        if len(entry_data) < 34:
                            break
                        offset = struct.unpack("<Q", entry_data[:8])[0]
                        if offset == 0:
                            continue
                            
                        # Layout has FileHash2 first, then FileHash1
                        hash2, hash1 = struct.unpack("<II", entry_data[20:28])
                        key_dec = (hash1, hash2)
                        
                        if key_dec in target_hashes:
                            stb_path = hash_to_path[f"{hash1}#{hash2}"]
                            archive_map[stb_path] = tor_file
                            
                    current_table = next_table
        except Exception as e:
            print(f"Error scanning {tor_file}: {e}")
            
    elapsed = time.time() - start_time
    print(f"Scan complete in {elapsed:.2f} seconds. Mapped {len(archive_map)} STB files to archives.")
    
    output_path = "db/archive_map.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(archive_map, f, indent=4)
    print(f"Saved archive map to {output_path}")

if __name__ == "__main__":
    build_archive_map()
