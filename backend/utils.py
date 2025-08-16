import subprocess
import requests
import os

# Extract metadata (duration, codec, resolution) with ffprobe
def extract_media_info(filepath: str) -> dict:
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,duration",
            "-of", "default=noprint_wrappers=1:nokey=0",
            filepath,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k.strip()] = v.strip()
        return {
            "codec": info.get("codec_name"),
            "width": int(info.get("width")) if info.get("width") else None,
            "height": int(info.get("height")) if info.get("height") else None,
            "duration": float(info.get("duration")) if info.get("duration") else None,
        }
    except Exception as e:
        print(f"ffprobe failed: {e}")
        return {}


# Download poster image
def download_poster(url: str, save_path: str):
    try:
        resp = requests.get(url, stream=True)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        print(f"Poster saved: {save_path}")
    except Exception as e:
        print(f"Poster download failed: {e}")


# Download subtitles using OpenSubtitles API (needs API key in env)
def download_subtitle(title: str, year: str, save_path: str):
    api_key = os.getenv("OPENSUBTITLES_API_KEY")
    if not api_key:
        print("⚠️ No OPENSUBTITLES_API_KEY set, skipping subtitle download")
        return

    try:
        url = "https://api.opensubtitles.com/api/v1/subtitles"
        headers = {
            "Api-Key": api_key,
            "Content-Type": "application/json",
        }
        params = {"query": title, "languages": "en"}
        if year:
            params["year"] = year

        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("data"):
            print(f"No subtitles found for {title} ({year})")
            return

        # Take the first subtitle match
        file_id = data["data"][0]["attributes"]["files"][0]["file_id"]

        # Request download link
        dl_url = "https://api.opensubtitles.com/api/v1/download"
        dl_resp = requests.post(dl_url, headers=headers, json={"file_id": file_id})
        dl_resp.raise_for_status()
        link = dl_resp.json()["link"]

        # Download subtitle file
        sub_resp = requests.get(link)
        sub_resp.raise_for_status()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(sub_resp.content)

        print(f"Subtitle saved: {save_path}")
    except Exception as e:
        print(f"Subtitle download failed: {e}")
