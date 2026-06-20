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

target_h1 = 0x8154956D

print(f"Searching for hash1={target_h1:08X} in all .tor archives...")

tor_files = [f for f in os.listdir(assets_dir) if f.endswith(".tor")]
found = False

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
                    hash1, hash2 = struct.unpack("<II", entry_data[20:28])
                    
                    if hash1 == target_h1:
                        print(f"FOUND MATCH! file={tor_file}, hash2={hash2:08X}")
                        found = True
                        break
                if found:
                    break
                current_table = next_table
    except Exception as e:
        print(f"Error reading {tor_file}: {e}")
    if found:
        break

if not found:
    print("Could not find hash1 in any archive.")
