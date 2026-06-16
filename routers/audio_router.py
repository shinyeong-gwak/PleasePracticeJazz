# routers/audio_router.py

from fastapi import APIRouter
from pydantic import BaseModel
from pathlib import Path
from fastapi.responses import FileResponse

from services.audio_service import process_audio

router = APIRouter()


# ---------- request model ----------
class AudioProcessRequest(BaseModel):
    file: str
    pitch: int
    tempo: float


# ---------- process audio ----------
@router.post("/api/audio/process")
def audio_process(req: AudioProcessRequest):

    out_file = process_audio(
        req.file,
        req.pitch,
        req.tempo
    )

    return {
        "url": f"/audio/processed/{out_file}"
    }


# ---------- serve original ----------
@router.get("/audio/lick/{filename}")
def serve_lick(filename: str):
    return FileResponse(Path("downloads/licks") / filename)


# ---------- serve processed ----------
@router.get("/audio/processed/{filename}")
def serve_processed(filename: str):
    return FileResponse(Path("downloads/processed") / filename)

@router.get("/music/audio/{filename}")
def audio(filename: str):

    path = Path("downloads/mp3") / filename

    return FileResponse(path)