from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import os
import json
import re
from tmdbv3api import TMDb, Movie

from utils import extract_media_info, download_poster

app = FastAPI()

# CORS settings to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

MOVIES_DIR = "movies"
POSTERS_DIR = "posters"
METADATA_FILE = "metadata.json"

tmdb = TMDb()
tmdb.api_key = "df66fbf62cb100b4898a31454454a8b1"  # <-- Replace with your TMDb API key
tmdb.language = "en"
movie_api = Movie()

os.makedirs(POSTERS_DIR, exist_ok=True)
app.mount("/posters", StaticFiles(directory=POSTERS_DIR), name="posters")

def extract_title_year(filename):
    name, _ = os.path.splitext(filename)
    match = re.match(r"(.+?)\s*\(?(\d{4})?\)?$", name)
    if match:
        title = match.group(1).replace('.', ' ').strip()
        year = match.group(2)
        if year:
            year = int(year)
        else:
            year = None
        return title, year
    else:
        return name, None

def search_movie_on_tmdb(title, year=None):
    results = movie_api.search(title)
    for result in results:
        if year and result.release_date:
            if result.release_date.startswith(str(year)):
                return result
        else:
            return result
    return None

def refresh_metadata():
    metadata = []

    for filename in os.listdir(MOVIES_DIR):
        if not filename.lower().endswith((".mp4", ".mkv", ".avi")):
            continue

        filepath = os.path.join(MOVIES_DIR, filename)
        title, year = extract_title_year(filename)
        print(f"Refreshing: {title} ({year})")

        tmdb_movie = search_movie_on_tmdb(title, year)
        if tmdb_movie:
            poster_url = f"https://image.tmdb.org/t/p/w500{tmdb_movie.poster_path}" if tmdb_movie.poster_path else None
            movie_title = tmdb_movie.title
            movie_year = tmdb_movie.release_date[:4] if tmdb_movie.release_date else None
        else:
            poster_url = None
            movie_title = title
            movie_year = year

        # Download poster if not exists locally
        poster_local_path = None
        if poster_url:
            ext = os.path.splitext(poster_url)[1]
            safe_title = movie_title.replace(" ", "_").replace("/", "_")
            poster_local_path = os.path.join(POSTERS_DIR, safe_title + ext)
            if not os.path.exists(poster_local_path):
                success = download_poster(poster_url, poster_local_path)
                if not success:
                    poster_local_path = None
            else:
                print(f"Poster already exists: {poster_local_path}")

        # Extract video metadata
        media_info = extract_media_info(filepath)

        metadata.append({
            "filename": filename,
            "title": movie_title,
            "year": movie_year,
            "poster": f"/posters/{os.path.basename(poster_local_path)}" if poster_local_path else None,
            "duration": media_info.get("duration"),
            "width": media_info.get("width"),
            "height": media_info.get("height"),
            "codec": media_info.get("codec"),
        })

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata refreshed for {len(metadata)} movies.")
    return metadata

@app.get("/movies")
def get_movies():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        return refresh_metadata()

@app.get("/stream/{movie_filename}")
def stream_movie(movie_filename: str):
    movie_path = os.path.join(MOVIES_DIR, movie_filename)
    if not os.path.exists(movie_path):
        return {"error": "Movie not found"}

    def iterfile():
        with open(movie_path, mode="rb") as file_like:
            yield from file_like

    return StreamingResponse(iterfile(), media_type="video/mp4")

@app.post("/refresh")
def refresh_metadata_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(refresh_metadata)
    return JSONResponse({"message": "Metadata refresh started in background."})
