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
            
    steam_path = None
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, r"SOFTWARE\Wow6432Node\Valve\Steam" if hive == winreg.HKEY_LOCAL_MACHINE else r"Software\Valve\Steam") as key:
                steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
                break
        except FileNotFoundError:
            pass
            
    if steam_path:
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            try:
                import re
                with open(vdf_path, "r", encoding="utf-8") as f:
                    content = f.read()
                paths = re.findall(r'"path"\s+"([^"]+)"', content)
                for library_path in paths:
                    library_path = library_path.replace("\\\\", "\\")
                    candidate = os.path.join(library_path, "steamapps", "common", "Star Wars - The Old Republic")
                    if os.path.exists(candidate):
                        return candidate
            except Exception:
                pass
    return None

game_path = get_game_path()
assets_dir = os.path.join(game_path, "Assets")

# Let's load the hash list
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

# Scan all .tor files
tor_files = [f for f in os.listdir(assets_dir) if f.endswith(".tor")]
print("Total .tor files to scan:", len(tor_files))

found_count = 0
for tor_file in tor_files:
    tor_path = os.path.join(assets_dir, tor_file)
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
                hash1, hash2 = struct.unpack("<II", entry_data[20:28])
                
                if (hash1, hash2) in hash_set:
                    found_count += 1
                    print(f"Found {(hash1, hash2)} in {tor_file}: {hash_to_path[(hash1, hash2)]}")
                    if found_count >= 10:
                        break
            if found_count >= 10:
                break
            current_table = next_table
    if found_count >= 10:
        break
