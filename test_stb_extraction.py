import os
import sys

sys.path.append("patcher_br")
from myp_parser import MYPArchive, load_hash_list
from stb_parser import STBFile

# Auto-detect game path
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
tor_path = os.path.join(game_path, "Assets", "swtor_en-us_global_1.tor")
hash_list_path = "db/hashes_filename.txt"

print(f"Loading hash list...")
hash_map = load_hash_list(hash_list_path)

print(f"Loading archive: {tor_path}...")
archive = MYPArchive(tor_path)
archive.load()
print(f"Archive loaded. Resolving entry names...")
archive.resolve_names(hash_map)

# Find abl.stb
abl_entry = None
for entry in archive.entries:
    if entry.file_name == "/resources/en-us/str/abl.stb":
        abl_entry = entry
        break

if not abl_entry:
    print("Could not find abl.stb in archive.")
    sys.exit(1)

print(f"Found abl.stb entry: {abl_entry}")
print(f"Extracting data...")
raw_data = archive.extract_entry_data(abl_entry)
print(f"Raw data size: {len(raw_data)} bytes")

print(f"Parsing STB data...")
stb = STBFile.from_bytes(raw_data)
print(f"STB parsed successfully! Magic: {stb.magic}, Rows: {len(stb.entries)}")

print("\nFirst 10 strings in abl.stb:")
for i, entry in enumerate(stb.entries[:10]):
    print(f"  ID={entry.string_id}: '{entry.text}'")
