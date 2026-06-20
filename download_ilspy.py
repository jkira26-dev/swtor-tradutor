import urllib.request
import json
import zipfile
import os

url = "https://api.github.com/repos/icsharpcode/ILSpy/releases/latest"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode())

download_url = None
for asset in data.get("assets", []):
    name = asset["name"].lower()
    if "ilspycmd" in name and "win-x64" in name:
        download_url = asset["browser_download_url"]
        break

if not download_url:
    print("Could not find ilspycmd asset.")
    exit(1)

print(f"Downloading from {download_url}...")
zip_path = "ilspycmd.zip"
urllib.request.urlretrieve(download_url, zip_path)

print("Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall("ilspycmd")

os.remove(zip_path)
print("Done!")
