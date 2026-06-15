from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi import Form

from repositories import playlist_repository, clip_repository, lick_repository

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from navigation import NAVIGATION

from services import music_service, clip_service

from pydantic import BaseModel

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

FFMPEG_BIN = (
        ROOT_DIR /
        "lib" /
        "ffmpeg" /
        "bin"
)

os.environ["PATH"] += ";" + str(FFMPEG_BIN)

print(os.environ["PATH"])
app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


def render_page(
        request: Request,
        template_name: str,
        page_title: str,
        context: dict = None):

    if context is None:
        context = {}

    context.update({
        "request": request,
        "navigation": NAVIGATION,
        "page_title": page_title
    })

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context=context
    )


@app.get("/")
def home(request: Request):

    return render_page(
        request,
        "music/index.html",
        "음악"
    )


@app.get("/music")
def music(request: Request):

    return render_page(
        request,
        "music/index.html",
        "음악"
    )


@app.get("/account")
def account(request: Request):

    return render_page(
        request,
        "account/index.html",
        "가계"
    )


@app.get("/dev")
def dev(request: Request):

    return render_page(
        request,
        "dev/index.html",
        "개발"
    )


@app.get("/music/playlist")
def playlist_page(request: Request):

    playlists = playlist_repository.get_all()

    print("PLAYLISTS =", playlists)

    return render_page(
        request,
        "music/playlist.html",
        "음악",
        {
            "playlists": playlists
        }
    )

from fastapi.responses import RedirectResponse

@app.post("/music/playlist/add")
def add_playlist(
        name: str = Form(...),
        url: str = Form(...)):

    playlist_repository.add(
        name,
        url
    )

    return RedirectResponse(
        "/music/playlist",
        status_code=303
    )


@app.post("/music/playlist/sync")
def sync_playlist(
        playlist_name: str = Form(...),
        url: str = Form(...)):

    music_service.sync(
        playlist_name,
        url
    )

    return RedirectResponse(
        "/music/playlist",
        status_code=303
    )


@app.get("/music/clips")
def clips_page(request: Request):

    mp3_files = clip_repository.get_mp3_files()

    return render_page(
        request,
        "music/clips.html",
        "Clip 생성",
        {
            "mp3_files": mp3_files
        }
    )

from fastapi.responses import FileResponse

@app.get("/music/audio/{filename}")
def audio(filename: str):

    path = Path("downloads/mp3") / filename

    return FileResponse(path)

from pydantic import BaseModel

class ClipRequest(BaseModel):

    fileName: str
    startTime: float
    endTime: float

@app.post("/music/clips/create")
def create_clip(
        request: ClipRequest):

    output_file = (
        clip_service.create_clip(
            request.fileName,
            request.startTime,
            request.endTime
        )
    )

    return {
        "fileName":
            output_file.name
    }

class PitchRequest(BaseModel):

    fileName: str
    semitones: int

@app.post("/music/clips/pitch")
def create_pitch_version(
        request: PitchRequest):

    output_file = (
        clip_service.create_pitch_version(
            request.fileName,
            request.semitones
        )
    )

    return {
        "fileName":
            output_file.name
    }

@app.get("/music/licks")
def licks_page(request: Request):

    licks = lick_repository.get_all()

    return render_page(
        request,
        "music/licks.html",
        "Lick 연습",
        {
            "licks": licks
        }
    )

from routers.audio_router import router as audio_router

app.include_router(audio_router)
app.mount("/static", StaticFiles(directory="static"), name="static")