from fastapi import APIRouter, Request
from pydantic import BaseModel

from services import clip_service
from repositories import clip_repository
from core.render import render_page

router = APIRouter(prefix="/music", tags=["music"])

class ClipRequest(BaseModel):
    fileName: str
    startTime: float
    endTime: float


@router.get("/clips")
def clips_page(request: Request):
    mp3_files = clip_repository.get_mp3_files()

    return render_page(
        request,
        "music/clips.html",
        "Clip 생성",
        {"mp3_files": mp3_files}
    )

@router.post("/clips/create")
def create_clip(req: ClipRequest):
    out = clip_service.create_clip(req.fileName, req.startTime, req.endTime)
    return {"fileName": out.name}


class PitchRequest(BaseModel):
    fileName: str
    semitones: int


@router.post("/clips/pitch")
def pitch(req: PitchRequest):
    out = clip_service.create_pitch_version(req.fileName, req.semitones)
    return {"fileName": out.name}