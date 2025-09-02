import subliminal
from babelfish import Language
import requests
import os
from pathlib import Path
from dotenv import load_dotenv
import re
import ffmpeg

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
POSTERS_DIR = Path(__file__).parent / "posters"
POSTERS_DIR.mkdir(exist_ok=True)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

def download_subtitles(video_path: Path, lang="en"):
    subtitle_path = video_path.with_suffix(".srt")
    if subtitle_path.exists():
        return subtitle_path
    subliminal.region.configure('dogpile.cache.memory')
    videos = [subliminal.Video.fromname(str(video_path))]
    subtitles = subliminal.download_best_subtitles(videos, {Language(lang)})
    for video, subs in subtitles.items():
        if subs:
            best = subs.pop()
            subliminal.save_subtitles(video, [best])
            return subtitle_path
    return None

def sanitize_movie_name(filename: str) -> str:
    name = filename.rsplit(".", 1)[0]
    name = name.replace(".", " ").replace("_", " ")
    name = re.sub(r"\b(1080p|720p|x264|x265|BluRay|WEBRip|HDRip|BRRip)\b", "", name, flags=re.I)
    name = re.sub(r"\s+", " ", name).strip()
    return name

def fetch_movie_info(filename: str):
    info = {"title": filename, "overview": None, "poster": "/static/placeholder.jpg", "release_date": None}
    if not TMDB_API_KEY:
        return info
    query_name = sanitize_movie_name(filename)
    url = "https://api.themoviedb.org/3/search/movie"
    params = {"api_key": TMDB_API_KEY, "query": query_name}
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        if data["results"]:
            movie = data["results"][0]
            info["title"] = movie.get("title")
            info["overview"] = movie.get("overview")
            info["release_date"] = movie.get("release_date")
            poster_path = movie.get("poster_path")
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                local_file = re.sub(r'\s+', '_', query_name) + ".jpg"
                local_path = POSTERS_DIR / local_file
                if not local_path.exists():
                    r = requests.get(poster_url)
                    if r.status_code == 200:
                        with open(local_path, "wb") as f:
                            f.write(r.content)
                info["poster"] = f"/posters/{local_path.name}"
    except Exception as e:
        print("TMDb fetch error:", e)
    return info

def get_video_streams(video_path: Path):
    info = {"audio": [], "subtitles": []}
    try:
        probe = ffmpeg.probe(str(video_path))
        for stream in probe['streams']:
            if stream['codec_type'] == 'audio':
                lang = stream.get('tags', {}).get('language', 'und')
                info['audio'].append({"index": stream['index'], "codec": stream['codec_name'], "lang": lang})
            elif stream['codec_type'] == 'subtitle':
                lang = stream.get('tags', {}).get('language', 'und')
                info['subtitles'].append({"index": stream['index'], "codec": stream['codec_name'], "lang": lang})
    except Exception as e:
        print("ffprobe error:", e)
    return info

def refresh_movie_cache(MOVIE_CACHE, MOVIES_DIR):
    for f in MOVIES_DIR.glob("*"):
        if f.is_file() and f.name not in MOVIE_CACHE:
            info = fetch_movie_info(f.name)
            MOVIE_CACHE[f.name] = info
