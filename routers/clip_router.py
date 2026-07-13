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
    try:
        out = clip_service.create_clip(
            req.fileName,
            req.startTime,
            req.endTime,
            req.clipName
        )
        clip_repository.register_generated_clip(
            out,
            req.fileName,
            req.startTime,
            req.endTime,
            pitch_shift=0,
            tempo_ratio=1.0,
        )
        return {"fileName": out.name}
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


class PitchRequest(BaseModel):
    fileName: str
    semitones: int


class FolderCreateRequest(BaseModel):
    parentId: str = ""
    name: str


class FolderRenameRequest(BaseModel):
    folderId: str
    name: str


class FolderDeleteRequest(BaseModel):
    folderId: str


class LibraryItemRequest(BaseModel):
    trackId: str
    folderId: str = ""


class MoveLibraryItemRequest(BaseModel):
    trackId: str
    folderId: str = ""


class ReorderLibraryItemRequest(BaseModel):
    trackId: str
    direction: str


@router.post("/clips/pitch")
def pitch(req: PitchRequest):
    out = clip_service.create_pitch_version(req.fileName, req.semitones)
    clip_repository.register_generated_clip(
        out,
        req.fileName,
        start_sec=None,
        end_sec=None,
        pitch_shift=req.semitones,
        tempo_ratio=1.0,
    )
    return {"fileName": out.name}


@router.get("/clips/tree")
def clips_tree():
    return clip_repository.get_mp3_tree()


@router.post("/clips/folders")
def create_folder(req: FolderCreateRequest):
    try:
        clip_repository.create_folder(req.parentId, req.name)
        return clip_repository.get_mp3_tree()
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.put("/clips/folders")
def rename_folder(req: FolderRenameRequest):
    try:
        clip_repository.rename_folder(req.folderId, req.name)
        return clip_repository.get_mp3_tree()
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.delete("/clips/folders")
def delete_folder(req: FolderDeleteRequest):
    try:
        clip_repository.delete_folder(req.folderId)
        return clip_repository.get_mp3_tree()
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.post("/clips/library-items")
def add_library_item(req: LibraryItemRequest):
    try:
        clip_repository.add_track_to_library(req.trackId, req.folderId)
        return clip_repository.get_mp3_tree()
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.put("/clips/library-items/move")
def move_library_item(req: MoveLibraryItemRequest):
    try:
        clip_repository.move_track_to_folder(req.trackId, req.folderId)
        return clip_repository.get_mp3_tree()
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)


@router.put("/clips/library-items/reorder")
def reorder_library_item(req: ReorderLibraryItemRequest):
    try:
        clip_repository.reorder_track(req.trackId, req.direction)
        return clip_repository.get_mp3_tree()
    except ValueError as exc:
        return JSONResponse({"message": str(exc)}, status_code=400)
