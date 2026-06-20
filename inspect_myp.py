import struct
import os

filepath = "db/main_gfx_1.tor"
hash_list_path = "db/hashes_filename.txt"

# Load hash map
hash_map = {}
if os.path.exists(hash_list_path):
    with open(hash_list_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("#")
            if len(parts) >= 3:
                # Key format: HASH1#HASH2 in uppercase hex
                key = f"{parts[0].upper()}#{parts[1].upper()}"
                hash_map[key] = parts[2]
    print(f"Loaded {len(hash_map)} hashes from hash list.")

with open(filepath, "rb") as f:
    header_data = f.read(24)
    magic, version, unknown, table_offset, files_per_table = struct.unpack("<4sIIQI", header_data)
    
    current_table = table_offset
    total_entries = 0
    resolved_stb = 0
    resolved_others = 0
    unresolved = 0
    
    while current_table != 0:
        f.seek(current_table)
        table_header = f.read(12)
        if len(table_header) < 12:
            break
        num_files, next_table = struct.unpack("<IQ", table_header)
        
        for i in range(num_files):
            entry_data = f.read(34)
            if len(entry_data) < 34:
                break
            
            offset, header_size, zsize, size = struct.unpack("<QIII", entry_data[:20])
            hashes_dummy = entry_data[20:32]
            zip_method = struct.unpack("<H", entry_data[32:34])[0]
            
            if offset == 0:
                continue
                
            total_entries += 1
            hash1, hash2, extra = struct.unpack("<III", hashes_dummy)
            key = f"{hash1:08X}#{hash2:08X}"
            
            if key in hash_map:
                filename = hash_map[key]
                if filename.endswith(".stb"):
                    resolved_stb += 1
                    print(f"STB Found: {filename} (hash1={hash1:08X}, hash2={hash2:08X})")
                else:
                    resolved_others += 1
            else:
                unresolved += 1
                
        current_table = next_table
        
    print(f"Total entries: {total_entries}")
    print(f"Resolved STB files: {resolved_stb}")
    print(f"Resolved other files: {resolved_others}")
    print(f"Unresolved files: {unresolved}")
