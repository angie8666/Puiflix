from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils import MOVIES_DIR, STATIC_DIR, fetch_poster, download_subtitles, get_tracks, fetch_rating
import ffmpeg

BASE_DIR = Path(__file__).parent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/posters", StaticFiles(directory=BASE_DIR / "posters"), name="posters")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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

@app.get("/stream/{filename}")
def stream_movie(filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    def iterfile():
        with open(filepath, "rb") as f:
            while chunk := f.read(1024*1024):
                yield chunk
    return StreamingResponse(iterfile(), media_type="video/mp4")

@app.get("/tracks/{filename}")
def tracks(filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    download_subtitles(filepath, "eng")
    return get_tracks(filepath)

@app.get("/subtitles/{filename}/{index}")
def subtitle(filename: str, index: int):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    out_path = STATIC_DIR / f"{filepath.stem}_s{index}.srt"
    if not out_path.exists():
        ffmpeg.input(str(filepath)).output(str(out_path), map=f"0:{index}").overwrite_output().run()
    return FileResponse(out_path, media_type="text/plain")

@app.get("/audio/{filename}/{index}")
def audio(filename: str, index: int):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    out_path = STATIC_DIR / f"{filepath.stem}_audio{index}.mp4"
    if not out_path.exists():
        ffmpeg.input(str(filepath)).output(str(out_path), map=f"0:{index}", c="copy").overwrite_output().run()
    return FileResponse(out_path, media_type="audio/mp4")
