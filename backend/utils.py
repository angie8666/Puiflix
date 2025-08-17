import subprocess, json, requests, os
from PIL import Image
from io import BytesIO
from subliminal import download_best_subtitles, region, Video, save_subtitles
from babelfish import Language

POSTERS_DIR = "posters"

def extract_media_info(filepath):
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name",
            "-show_format", "-of", "json", filepath
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        stream = data["streams"][0]
        duration = float(data["format"].get("duration", 0))
        return {"duration": duration, "width": stream.get("width"), "height": stream.get("height"), "codec": stream.get("codec_name")}
    except Exception as e:
        print(f"ffprobe failed: {e}")
        return {}

def download_poster(url, save_path):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content))
        img.save(save_path)
        return True
    except Exception as e:
        print(f"Poster download failed: {e}")
        return False

def download_subtitles(title, year, subtitles_dir, langs=["en"]):
    os.makedirs(subtitles_dir, exist_ok=True)
    video_path = os.path.join("movies", f"{title} ({year}).mp4")
    if not os.path.exists(video_path):
        return {}
    
    video = Video.fromname(video_path)
    region.configure('dogpile.cache.memory')

    subtitle_files = {}
    subtitles = download_best_subtitles({video}, {Language(lang) for lang in langs})
    for lang in langs:
        if lang in subtitles[video]:
            path = os.path.join(subtitles_dir, f"{title}_{lang}.srt")
            save_subtitles(video, {Language(lang): subtitles[video][lang]}, directory=subtitles_dir)
            subtitle_files[lang] = path
    return subtitle_files
