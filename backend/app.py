from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from utils import MOVIES_DIR, STATIC_DIR, fetch_poster, download_subtitles, get_tracks, fetch_rating
import ffmpeg
import re
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/posters", StaticFiles(directory=Path(__file__).parent / "posters"), name="posters")
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


def stream_file(filepath: Path, request: Request, content_type="application/octet-stream"):
    """Stream a file with HTTP Range support."""
    if not filepath.exists():
        raise HTTPException(status_code=404)
    file_size = os.path.getsize(filepath)
    range_header = request.headers.get("range")
    if range_header:
        match = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if match:
            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1
            length = end - start + 1

            def iter_bytes():
                with open(filepath, "rb") as f:
                    f.seek(start)
                    yield f.read(length)

            headers = {
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(length),
                "Content-Type": content_type,
            }
            return StreamingResponse(iter_bytes(), status_code=206, headers=headers, media_type=content_type)

    return FileResponse(filepath, media_type=content_type, headers={"Accept-Ranges": "bytes"})


@app.get("/stream/{filename}")
def stream_movie(filename: str, request: Request):
    filepath = MOVIES_DIR / filename
    return stream_file(filepath, request, content_type="video/mp4")


@app.get("/tracks/{filename}")
def tracks(filename: str):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    download_subtitles(filepath, "en")
    return get_tracks(filepath)


@app.get("/subtitles/{filename}/{index}")
def subtitle(filename: str, index: int, request: Request):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    out_path = STATIC_DIR / f"{filepath.stem}_s{index}.srt"
    if not out_path.exists():
        ffmpeg.input(str(filepath)).output(str(out_path), map=f"0:{index}").overwrite_output().run()
    return stream_file(out_path, request, content_type="text/plain")


@app.get("/audio/{filename}/{index}")
def audio(filename: str, index: int, request: Request):
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404)
    out_path = STATIC_DIR / f"{filepath.stem}_audio{index}.mp4"
    if not out_path.exists():
        ffmpeg.input(str(filepath)).output(str(out_path), map=f"0:{index}", c="copy").overwrite_output().run()
    return stream_file(out_path, request, content_type="audio/mp4")
