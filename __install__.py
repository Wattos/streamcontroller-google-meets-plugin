from streamcontroller_plugin_tools.installation_helpers import create_venv
from os.path import join, abspath, dirname
import json
import urllib.request
import zipfile
import os
import shutil

toplevel = dirname(abspath(__file__))

# Create virtual environment for backend
create_venv(join(toplevel, "backend", ".venv"), join(toplevel, "backend", "requirements.txt"))

# Download and extract Chrome extension
def download_and_extract_extension():
    """Download the Chrome extension from GitHub releases and extract it."""
    try:
        # Read plugin version from manifest.json
        manifest_path = join(toplevel, "manifest.json")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            version = manifest['version']

        # Construct download URL
        extension_filename = f"google-meet-streamcontroller-extension-{version}.zip"
        download_url = f"https://github.com/Wattos/streamcontroller-google-meets-plugin/releases/download/v{version}/{extension_filename}"

        # Create dist directory
        dist_dir = join(toplevel, "dist")
        os.makedirs(dist_dir, exist_ok=True)

        # Download path
        download_path = join(dist_dir, extension_filename)

        print(f"Downloading Chrome extension v{version}...")
        print(f"URL: {download_url}")

        # Download the zip file
        urllib.request.urlretrieve(download_url, download_path)

        # Extract to dist/chrome_extension
        extract_dir = join(dist_dir, "chrome_extension")

        # Remove existing directory if it exists
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)

        os.makedirs(extract_dir, exist_ok=True)

        print(f"Extracting to {extract_dir}...")

        # Extract the zip file
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Clean up the zip file
        os.remove(download_path)

        print(f"Chrome extension v{version} installed successfully!")
        print(f"Location: {extract_dir}")

    except Exception as e:
        print(f"Warning: Failed to download Chrome extension: {e}")
        print("You can manually download it from:")
        print("https://github.com/Wattos/streamcontroller-google-meets-plugin/releases")

# Download the extension
download_and_extract_extension()