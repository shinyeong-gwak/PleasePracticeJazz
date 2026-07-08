from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services import clip_service
from repositories import clip_repository
from core.render import render_page

router = APIRouter(prefix="/music", tags=["music"])

class ClipRequest(BaseModel):
    fileName: str
    startTime: float
    endTime: float
    clipName: str = ""


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
    out = clip_service.create_clip(
        req.fileName,
        req.startTime,
        req.endTime,
        req.clipName
    )
    return {"fileName": out.name}


class PitchRequest(BaseModel):
    fileName: str
    semitones: int


class FolderCreateRequest(BaseModel):
    parentPath: str = ""
    name: str


class FolderRenameRequest(BaseModel):
    path: str
    name: str


class FolderDeleteRequest(BaseModel):
    path: str


@router.post("/clips/pitch")
def pitch(req: PitchRequest):
    out = clip_service.create_pitch_version(req.fileName, req.semitones)
    return {"fileName": out.name}


@router.get("/clips/tree")
def clips_tree():
    return clip_repository.get_mp3_tree()


@router.post("/clips/folders")
def create_folder(req: FolderCreateRequest):
    try:
        return clip_repository.create_folder(req.parentPath, req.name)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.put("/clips/folders")
def rename_folder(req: FolderRenameRequest):
    try:
        return clip_repository.rename_folder(req.path, req.name)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.delete("/clips/folders")
def delete_folder(req: FolderDeleteRequest):
    try:
        return clip_repository.delete_folder(req.path)
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)
