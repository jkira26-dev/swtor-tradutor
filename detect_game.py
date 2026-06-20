import os
import re
import winreg

def detect_steam_swtor():
    # 1. Get Steam installation path
    steam_path = None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Valve\Steam") as key:
            steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
    except FileNotFoundError:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
        except FileNotFoundError:
            pass

    if not steam_path:
        print("Steam not found in registry.")
        return None

    print(f"Steam Install Path: {steam_path}")
    
    # 2. Read libraryfolders.vdf
    vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vdf_path):
        print("libraryfolders.vdf not found.")
        return None
        
    try:
        with open(vdf_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading libraryfolders.vdf: {e}")
        return None

    # Find paths in the VDF file (format: "path" "C:\\SteamLibrary")
    paths = re.findall(r'"path"\s+"([^"]+)"', content)
    # Replace double backslashes
    paths = [p.replace("\\\\", "\\") for p in paths]
    
    for library_path in paths:
        candidate = os.path.join(library_path, "steamapps", "common", "Star Wars - The Old Republic")
        print(f"Checking library candidate: {candidate}")
        if os.path.exists(candidate):
            return candidate

    return None

def detect_swtor_registry():
    # Check SWTOR standalone installation registry keys
    paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\BioWare\Star Wars-The Old Republic"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\BioWare\Star Wars-The Old Republic"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\BioWare\Star Wars-The Old Republic")
    ]
    for hive, key_path in paths:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                return winreg.QueryValueEx(key, "Install Dir")[0]
        except FileNotFoundError:
            pass
    return None

def main():
    game_path = detect_swtor_registry()
    if game_path:
        print(f"Found SWTOR standalone installation: {game_path}")
    else:
        print("SWTOR standalone registry keys not found. Checking Steam...")
        game_path = detect_steam_swtor()
        
    if game_path:
        print(f"SUCCESS: SWTOR found at: {game_path}")
        assets_dir = os.path.join(game_path, "Assets")
        print(f"Assets directory: {assets_dir} (Exists: {os.path.exists(assets_dir)})")
    else:
        print("FAILED: Could not auto-detect SWTOR installation directory.")

if __name__ == "__main__":
    main()
