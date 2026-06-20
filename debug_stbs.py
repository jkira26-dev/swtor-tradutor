import os, sys
sys.path.append("patcher_br")
from myp_parser import MYPArchive, load_hash_list
hash_list_path = "db/hashes_filename.txt"
hash_map = load_hash_list(hash_list_path)
tor_path = r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic\Assets\swtor_en-us_global_1.tor"
archive = MYPArchive(tor_path)
archive.load()
archive.resolve_names(hash_map)
for entry in archive.entries[:200]:
    if entry.file_name and entry.file_name.endswith('.stb'):
        decompressed_data = archive.extract_entry_data(entry)
        print(f"File: {entry.file_name}")
        import struct
        magic, num_rows = struct.unpack("<ii", decompressed_data[:8])
        print(f"  Magic: {magic}, NumRows: {num_rows}")
