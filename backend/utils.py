import os
import json
import subprocess
import requests
from PIL import Image
from io import BytesIO

POSTERS_DIR = "posters"
METADATA_FILE = "metadata.json"

def extract_media_info(filepath):
    """
    Extract metadata from video file using ffprobe.
    Returns dict with duration (seconds), width, height, codec_name.
    """
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-show_format",
            "-of", "json",
            filepath,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        stream = data["streams"][0]
        format_info = data["format"]
        duration = float(format_info.get("duration", 0))

        info = {
            "duration": duration,
            "width": stream.get("width"),
            "height": stream.get("height"),
            "codec": stream.get("codec_name"),
        }
        return info
    except Exception as e:
        print(f"Failed to extract media info from {filepath}: {e}")
        return {}

def download_poster(url, save_path):
    """
    Downloads and saves poster image locally.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))
        img.save(save_path)
        print(f"Poster saved to {save_path}")
        return True
    except Exception as e:
        print(f"Failed to download poster from {url}: {e}")
        return False
