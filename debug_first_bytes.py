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
        print(f"File: {entry.file_name}, offset: {entry.offset}, compress method: {entry.compression_method}, raw size: {entry.compressed_size}")
        with open(archive.filepath, "rb") as f:
            f.seek(entry.data_offset)
            raw_data = f.read(16)
            print("First 16 bytes:", raw_data.hex())
        break
