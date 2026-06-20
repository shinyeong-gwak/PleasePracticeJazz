from fastapi import APIRouter, Request, Form
from starlette.responses import RedirectResponse

from repositories import playlist_repository, lick_repository
from services import music_service
from core.render import render_page

router = APIRouter(prefix="/music")


@router.get("/playlist")
def playlist_page(request: Request):
    playlists = playlist_repository.get_all()
    return render_page(request, "music/playlist.html",
                       "음악",{"playlists": playlists})


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
