from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pathlib import Path

app = FastAPI()

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # frontend runs on this port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MOVIES_DIR = Path(__file__).parent / "movies"
MOVIES_DIR.mkdir(exist_ok=True)  # create folder if it doesn’t exist

@app.get("/movies")
def list_movies():
    """Return list of available movies"""
    files = [f.name for f in MOVIES_DIR.glob("*") if f.is_file()]
    return {"movies": files}

@app.get("/stream/{filename}")
def stream_movie(filename: str, request: Request):
    """Stream a movie file in chunks"""
    filepath = MOVIES_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")

    def iterfile():
        with open(filepath, "rb") as f:
            while chunk := f.read(1024 * 1024):  # 1MB chunks
                yield chunk

    return StreamingResponse(iterfile(), media_type="video/mp4")
