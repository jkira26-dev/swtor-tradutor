import os
import struct
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

game_path = get_game_path()
assets_dir = os.path.join(game_path, "Assets")

# Load target hashes
hash_list_path = "db/hashes_filename.txt"
hash_set = set()
hash_to_path = {}
with open(hash_list_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("#")
        if len(parts) >= 3:
            h1 = int(parts[0], 16)
            h2 = int(parts[1], 16)
            hash_set.add((h1, h2))
            hash_to_path[(h1, h2)] = parts[2]

print("Target hashes loaded:", len(hash_set))

tor_files = [f for f in os.listdir(assets_dir) if f.endswith(".tor")]
print("Testing combinations on all", len(tor_files), "archives...")

combos_count = {1:0, 2:0, 3:0, 4:0, 5:0, 6:0}
matches = []

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
                        
                    hashes_dummy = entry_data[20:32]
                    v1, v2, v3 = struct.unpack("<III", hashes_dummy)
                    
                    # Test the 6 combinations
                    if (v1, v2) in hash_set:
                        combos_count[1] += 1
                        matches.append((tor_file, v1, v2, 1))
                    if (v2, v1) in hash_set:
                        combos_count[2] += 1
                        matches.append((tor_file, v2, v1, 2))
                    if (v2, v3) in hash_set:
                        combos_count[3] += 1
                        matches.append((tor_file, v2, v3, 3))
                    if (v3, v2) in hash_set:
                        combos_count[4] += 1
                        matches.append((tor_file, v3, v2, 4))
                    if (v1, v3) in hash_set:
                        combos_count[5] += 1
                        matches.append((tor_file, v1, v3, 5))
                    if (v3, v1) in hash_set:
                        combos_count[6] += 1
                        matches.append((tor_file, v3, v1, 6))
                    
                current_table = next_table
    except Exception as e:
        print(f"Error reading {tor_file}: {e}")

print("Results for combinations:")
print("  Combo 1 (v1, v2):", combos_count[1])
print("  Combo 2 (v2, v1):", combos_count[2])
print("  Combo 3 (v2, v3):", combos_count[3])
print("  Combo 4 (v3, v2):", combos_count[4])
print("  Combo 5 (v1, v3):", combos_count[5])
print("  Combo 6 (v3, v1):", combos_count[6])

if matches:
    print("\nSample matches:")
    for m in matches[:10]:
        tor, h1, h2, combo_num = m
        print(f"  Found in {tor} using Combo {combo_num}: {h1:08X}#{h2:08X} -> {hash_to_path[(h1, h2)]}")
