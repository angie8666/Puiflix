from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils import MOVIES_DIR, STATIC_DIR, POSTERS_DIR, fetch_poster, get_tracks, fetch_rating
import os

BASE_DIR = Path(__file__).parent
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/posters", StaticFiles(directory=POSTERS_DIR), name="posters")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# List movies
@app.get("/movies")
def list_movies():
    movies = []
    for f in MOVIES_DIR.glob("*"):
        if f.is_file():
            movies.append({
                "name": f.name,
                "title": f.name,
                "poster": fetch_poster(f.name),
                "rating": fetch_rating(f.name)
            })
    return {"movies": movies}

# Stream movie with HTTP range support
@app.get("/stream/{filename}")
def stream_movie(request: Request, filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)

    file_size = os.path.getsize(filepath)
    range_header = request.headers.get("range")
    if range_header:
        byte1, byte2 = 0, None
        m = range_header.replace("bytes=", "").split("-")
        if len(m) == 2:
            if m[0]: byte1 = int(m[0])
            if m[1]: byte2 = int(m[1])
        length = (byte2 or file_size - 1) - byte1 + 1
        with open(filepath, "rb") as f:
            f.seek(byte1)
            data = f.read(length)
        headers = {
            "Content-Range": f"bytes {byte1}-{byte1+length-1}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(data, status_code=206, headers=headers)
    else:
        return FileResponse(filepath, media_type="video/mp4")

# Get audio/subtitle tracks
@app.get("/tracks/{filename}")
def tracks(filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    return get_tracks(filepath)

# Subtitles
@app.get("/subtitles/{filename}/{index}")
def subtitle(filename: str, index: int):
    out_path = STATIC_DIR / f"{Path(filename).stem}_s{index}.srt"
    if out_path.exists():
        return FileResponse(out_path, media_type="text/plain")
    return FileResponse(out_path, media_type="text/plain")

# Audio tracks
@app.get("/audio/{filename}/{index}")
def audio(filename: str, index: int):
    out_path = STATIC_DIR / f"{Path(filename).stem}_audio{index}.mp4"
    if out_path.exists():
        return FileResponse(out_path, media_type="audio/mp4")
    return FileResponse(out_path, media_type="audio/mp4")

# Movie suggestions
@app.post("/suggest_movie")
def suggest_movie(movie_title: str = Body(..., embed=True)):
    suggestions_file = BASE_DIR / "suggestions.txt"
    with open(suggestions_file, "a", encoding="utf-8") as f:
        f.write(movie_title.strip() + "\n")
    return {"status": "success"}
