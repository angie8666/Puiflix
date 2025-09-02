import os
from pathlib import Path
import re
import requests
from dotenv import load_dotenv
import ffmpeg
import subliminal
from babelfish import Language

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
BASE_DIR = Path(__file__).parent
MOVIES_DIR = BASE_DIR / "movies"
POSTERS_DIR = BASE_DIR / "posters"
STATIC_DIR = BASE_DIR / "static"

MOVIES_DIR.mkdir(exist_ok=True)
POSTERS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)


def sanitize_movie_name(filename: str) -> str:
    name = filename.rsplit(".", 1)[0]
    name = name.replace(".", " ").replace("_", " ")
    name = re.sub(r"\b(1080p|720p|x264|x265|BluRay|WEBRip|HDRip|BRRip)\b", "", name, flags=re.I)
    return name.strip()


def fetch_poster(filename: str):
    query_name = sanitize_movie_name(filename)
    local_file = re.sub(r'\s+', '_', query_name) + ".jpg"
    local_path = POSTERS_DIR / local_file
    if local_path.exists():
        return f"/posters/{local_file}"

    if not TMDB_API_KEY:
        return "/static/placeholder.jpg"

    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": query_name}
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        if data["results"]:
            poster_path = data["results"][0].get("poster_path")
            if poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
                r = requests.get(poster_url)
                if r.status_code == 200:
                    with open(local_path, "wb") as f:
                        f.write(r.content)
                return f"/posters/{local_file}"
    except Exception as e:
        print("Poster fetch error:", e)
    return "/static/placeholder.jpg"


def download_subtitles(file_path: Path, lang="en"):
    out_file = STATIC_DIR / f"{file_path.stem}_{lang}.srt"
    if out_file.exists():
        return out_file

    try:
        subliminal.region.configure('dogpile.cache.memory')
        video = subliminal.Video.fromname(str(file_path))
        subs = subliminal.download_best_subtitles([video], {Language(lang)})
        if subs.get(video):
            subliminal.save_subtitles(video, [subs[video].pop()])
            return out_file
    except Exception as e:
        print(f"Subtitle download failed: {e}")
    return None  # No dummy subtitles


def get_tracks(file_path: Path):
    audio, subtitles = [], []
    try:
        info = ffmpeg.probe(str(file_path))
        for stream in info["streams"]:
            if stream["codec_type"] == "audio":
                audio.append({
                    "index": stream["index"],
                    "codec": stream["codec_name"],
                    "lang": stream.get("tags", {}).get("language", "und")
                })
            elif stream["codec_type"] == "subtitle":
                subtitles.append({
                    "index": stream["index"],
                    "codec": stream["codec_name"],
                    "lang": stream.get("tags", {}).get("language", "und")
                })
    except Exception as e:
        print("ffprobe error:", e)

    if not audio:
        audio.append({"index": 0, "codec": "unknown", "lang": "und"})
    return {"audio": audio, "subtitles": subtitles}


def fetch_rating(filename: str):
    """Fetch movie rating from TMDB"""
    query_name = sanitize_movie_name(filename)
    if not TMDB_API_KEY:
        return None
    try:
        url = "https://api.themoviedb.org/3/search/movie"
        params = {"api_key": TMDB_API_KEY, "query": query_name}
        res = requests.get(url, params=params).json()
        if res.get("results"):
            return res["results"][0].get("vote_average")
    except:
        pass
    return None
