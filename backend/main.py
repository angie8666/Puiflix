from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import os, json, re

from tmdbv3api import TMDb, Movie
from utils import extract_media_info, download_poster, download_subtitles

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

MOVIES_DIR = "movies"
POSTERS_DIR = "posters"
SUBTITLES_DIR = "subtitles"
METADATA_FILE = "metadata.json"

os.makedirs(POSTERS_DIR, exist_ok=True)
os.makedirs(SUBTITLES_DIR, exist_ok=True)

app.mount("/posters", StaticFiles(directory=POSTERS_DIR), name="posters")
app.mount("/subtitles", StaticFiles(directory=SUBTITLES_DIR), name="subtitles")

# TMDb setup
tmdb = TMDb()
tmdb.api_key = os.getenv("TMDB_API_KEY", "YOUR_TMDB_API_KEY")
tmdb.language = "en"
movie_api = Movie()


def extract_title_year(filename):
    name, _ = os.path.splitext(filename)
    match = re.match(r"(.+?)\s*\(?(\d{4})?\)?$", name)
    if match:
        title = match.group(1).replace('.', ' ').strip()
        year = match.group(2)
        return title, int(year) if year else None
    return name, None


def search_movie_on_tmdb(title, year=None):
    results = movie_api.search(title)
    for result in results:
        if year and result.release_date and result.release_date.startswith(str(year)):
            return result
    return results[0] if results else None


def refresh_metadata():
    metadata = []
    for filename in os.listdir(MOVIES_DIR):
        if not filename.lower().endswith((".mp4", ".mkv", ".avi")):
            continue

        filepath = os.path.join(MOVIES_DIR, filename)
        title, year = extract_title_year(filename)
        tmdb_movie = search_movie_on_tmdb(title, year)

        # Poster
        poster_url, movie_title, movie_year = None, title, year
        if tmdb_movie:
            movie_title = tmdb_movie.title
            movie_year = tmdb_movie.release_date[:4] if tmdb_movie.release_date else None
            if tmdb_movie.poster_path:
                poster_url = f"https://image.tmdb.org/t/p/w500{tmdb_movie.poster_path}"

        poster_local_path = None
        if poster_url:
            safe_title = movie_title.replace(" ", "_")
            ext = os.path.splitext(poster_url)[1] or ".jpg"
            poster_local_path = os.path.join(POSTERS_DIR, safe_title + ext)
            if not os.path.exists(poster_local_path):
                download_poster(poster_url, poster_local_path)

        # Subtitles (multi-language, e.g. English, Spanish, French)
        subtitle_files = download_subtitles(title, year, SUBTITLES_DIR, langs=["en", "es", "fr"])

        # Media info
        media_info = extract_media_info(filepath)

        metadata.append({
            "filename": filename,
            "title": movie_title,
            "year": movie_year,
            "poster": f"/posters/{os.path.basename(poster_local_path)}" if poster_local_path else None,
            "subtitles": {lang: f"/subtitles/{os.path.basename(path)}" for lang, path in subtitle_files.items()},
            "duration": media_info.get("duration"),
            "width": media_info.get("width"),
            "height": media_info.get("height"),
            "codec": media_info.get("codec"),
        })

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


@app.get("/movies")
def get_movies():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return refresh_metadata()


@app.get("/stream/{movie_filename}")
def stream_movie(movie_filename: str):
    movie_path = os.path.join(MOVIES_DIR, movie_filename)
    if not os.path.exists(movie_path):
        return {"error": "Movie not found"}

    def iterfile():
        with open(movie_path, "rb") as f:
            yield from f

    return StreamingResponse(iterfile(), media_type="video/mp4")


@app.post("/refresh")
def refresh_metadata_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_metadata)
    return JSONResponse({"message": "Metadata refresh started in background."})


@app.get("/subtitles/{movie_filename}")
def get_subtitles(movie_filename: str):
    # Example return format
    return [
        {
            "language": "en",
            "language_name": "English",
            "path": f"/subtitles/{movie_filename}/en.vtt"
        },
        {
            "language": "es",
            "language_name": "Spanish",
            "path": f"/subtitles/{movie_filename}/es.vtt"
        }
    ]
