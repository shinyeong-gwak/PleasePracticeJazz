from fastapi import APIRouter, Request, Form
from starlette.responses import RedirectResponse, JSONResponse

from repositories import (
    playlist_repository,
    lick_repository,
    playlist_sync_repository,
    daily_repository,
)
from services import music_service
from core.render import render_page

router = APIRouter(prefix="/music")


@router.get("/playlist")
def playlist_page(request: Request):
    playlists = playlist_repository.get_all()
    sync_states = playlist_sync_repository.get_all()
    return render_page(
        request,
        "music/playlist.html",
        "음악",
        {
            "playlists": playlists,
            "sync_states": sync_states
        }
    )


@router.post("/playlist/add")
def add_playlist(name: str = Form(...), url: str = Form(...)):
    playlist_repository.add(name, url)
    return RedirectResponse("/music/playlist", status_code=303)


@router.post("/playlist/sync")
def sync_playlist(playlist_name: str = Form(...), url: str = Form(...)):
    music_service.sync(playlist_name, url)
    return RedirectResponse("/music/playlist", status_code=303)


@router.post("/playlist/delete")
def delete_playlist(name: str = Form(...), url: str = Form(...)):
    playlist_repository.delete(name, url)
    return RedirectResponse("/music/playlist", status_code=303)


@router.get("/licks")
def licks_page(request: Request):
    licks = lick_repository.get_all()
    return render_page(request, "music/licks.html",
                       "음악",{"licks": licks})


@router.get("/daily")
@router.get("/daliy")
def daily_page(request: Request):
    return render_page(
        request,
        "music/daily.html",
        "연습일지",
        {
            "daily_report": daily_repository.get_current_report()
        }
    )


@router.post("/daily/homework")
async def add_daily_homework(request: Request):
    payload = await request.json()
    item = daily_repository.add_homework(payload)
    return JSONResponse(item)


@router.delete("/daily/homework/{homework_id}")
def delete_daily_homework(homework_id: str):
    return JSONResponse(
        daily_repository.delete_homework(homework_id)
    )


@router.post("/daily/practice")
async def add_daily_practice(request: Request):
    payload = await request.json()
    item = daily_repository.add_practice(payload)
    return JSONResponse(item)


@router.delete("/daily/practice/{practice_id}")
def delete_daily_practice(practice_id: str):
    return JSONResponse(
        daily_repository.delete_practice(practice_id)
    )
