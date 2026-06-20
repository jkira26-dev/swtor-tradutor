import os, sys
sys.path.append("patcher_br")
from myp_parser import MYPArchive, load_hash_list
hash_list_path = "db/hashes_filename.txt"
hash_map = load_hash_list(hash_list_path)
tor_path = r"D:\SteamLibrary\steamapps\common\Star Wars - The Old Republic\Assets\swtor_en-us_global_1.tor"
archive = MYPArchive(tor_path)
archive.load()
archive.resolve_names(hash_map)
for entry in archive.entries:
    if entry.file_name == "/resources/en-us/str/abl.stb":
        decompressed_data = archive.extract_entry_data(entry)
        print("Decompressed size:", len(decompressed_data))
        print("First 32 bytes:", decompressed_data[:32].hex())
        
        import struct
        magic, num_rows = struct.unpack("<ii", decompressed_data[:8])
        print(f"STB Magic/Version: {magic}, NumRows: {num_rows}")
        
        # print first row index
        first_id, first_offset = struct.unpack("<qi", decompressed_data[8:20])
        print(f"Row 1 - ID: {first_id}, offset: {first_offset} (hex {first_offset & 0xFFFFFFFF:08X})")
        break
