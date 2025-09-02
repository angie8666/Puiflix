from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils import download_subtitles, fetch_movie_info, get_video_streams, refresh_movie_cache
import ffmpeg

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOVIES_DIR = Path(__file__).parent / "movies"
MOVIES_DIR.mkdir(exist_ok=True)
POSTERS_DIR = Path(__file__).parent / "posters"
POSTERS_DIR.mkdir(exist_ok=True)
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)

app.mount("/posters", StaticFiles(directory=POSTERS_DIR), name="posters")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

MOVIE_CACHE = {}
refresh_movie_cache(MOVIE_CACHE, MOVIES_DIR)

@app.get("/movies")
def list_movies():
    refresh_movie_cache(MOVIE_CACHE, MOVIES_DIR)
    movies_list = []
    for f in MOVIES_DIR.glob("*"):
        if f.is_file():
            info = MOVIE_CACHE.get(f.name) or fetch_movie_info(f.name)
            MOVIE_CACHE[f.name] = info
            movies_list.append({
                "name": f.name,
                "title": info["title"],
                "overview": info["overview"],
                "poster": info["poster"],
                "release_date": info["release_date"]
            })
    return {"movies": movies_list}

@app.get("/stream/{filename}")
def stream_movie(filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    def iterfile():
        with open(filepath, "rb") as f:
            while chunk := f.read(1024*1024):
                yield chunk
    return StreamingResponse(iterfile(), media_type="video/mp4")

@app.get("/tracks/{filename}")
def list_tracks(filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    info = get_video_streams(filepath)
    for i, track in enumerate(info['audio']):
        if 'index' not in track:
            track['index'] = i
    for i, track in enumerate(info['subtitles']):
        if 'index' not in track:
            track['index'] = i
    return info

@app.get("/subtitles/{filename}/{index}")
def extract_subtitle(filename: str, index: int):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    out_path = STATIC_DIR / f"{filename}_sub{index}.srt"
    ffmpeg.input(str(filepath)).output(str(out_path), map=f"0:{index}").overwrite_output().run()
    return FileResponse(out_path, media_type="text/plain")

@app.get("/audio/{filename}/{index}")
def extract_audio(filename: str, index: int):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    out_path = STATIC_DIR / f"{filename}_audio{index}.mp4"
    ffmpeg.input(str(filepath)).output(str(out_path), map=f"0:{index}", c="copy").overwrite_output().run()
    return FileResponse(out_path, media_type="audio/mp4")
